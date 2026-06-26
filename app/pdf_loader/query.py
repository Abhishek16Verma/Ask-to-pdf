from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import MessagesPlaceholder
from loguru import logger
from typing import AsyncGenerator
from operator import itemgetter

from app.utils.config import get_settings

class PDFQuery:
    def __init__(self, settings=None):
        if settings is None:
            settings = get_settings()
        self.qdrant_host = settings.qdrant_host
        self.collection_name = settings.collection_name
        self.model_name = settings.model_name
        self.model_device = settings.model_device
        self.groq_model = settings.groq_model
        self.groq_api_key = settings.groq_api_key
        self.session_storage: dict[str, InMemoryChatMessageHistory] = {}

    def get_embeddings(self):
        return HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": self.model_device}        )

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self.session_storage:
            self.session_storage[session_id] = InMemoryChatMessageHistory()
            logger.info(f"Created new chat history for session: {session_id}")
        return self.session_storage[session_id]


    def build_chain(self, filename: str | None = None, use_groq: bool = True):
        
        logger.info("Building the RAG chain...")
        # Vectorstore setup
        vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=self.get_embeddings(),
            collection_name=self.collection_name,
            url=self.qdrant_host,
        )

        #filter by filename if provided
        if filename:
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.filename",
                        match=MatchValue(value=filename)
                                )
                     ]
            )
        
            retriver = vectorstore.as_retriever(search_kwargs={"k": 3, "filter": search_filter})
            logger.info(f"Retriever initialized with filter for filename: {filename}")
        else:
            retriver = vectorstore.as_retriever(search_kwargs={"k": 3})
            logger.info("Search from all PDFs")
        logger.info("Vector store and retriever initialized.")

        # LLM setup
        if use_groq:
            llm = ChatGroq(model=self.groq_model, api_key=self.groq_api_key)
        else:
            llm = ChatOllama(model="llama3.2")

        # Prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that answers questions based on the provided context."
            "Answer based only on context provided."
            "Use conversation history to follow up on questions and provide relevant answers."
            "If the context does not contain the answer, respond with 'I don't know.'"),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{context}\n\nQuestion: {question}\nAnswer:")
        ])
        logger.info("LLM and prompt template initialized.")
        # LCEL chain setup
        chain = (
            {
                "context": itemgetter("question") | retriver | self.format_docs,
                "question": itemgetter("question"),
            }
            | prompt_template
            | llm
            | StrOutputParser()
        )
        return RunnableWithMessageHistory(
            chain,
            self.get_session_history,
            input_messages_key="question",
            history_messages_key="history",
        )
    async def stream_chain(self, chain, question: str, session_id: str) -> AsyncGenerator[str, None]:
        logger.info("Starting to stream the response...")
        async for response in chain.astream(
            {"question": question},
            config={"configurable": {"session_id": session_id}},
        ):
            yield response
query_object = PDFQuery()
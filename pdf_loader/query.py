import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_qdrant import QdrantVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.prompts import MessagesPlaceholder
from loguru import logger
from utils.config import get_settings
from typing import AsyncGenerator

load_dotenv(Path(__file__).with_name(".env"))

class PDFQuery:
    def __init__(self, settings = get_settings()):
        self.qdrant_host = settings.qdrant_host
        self.collection_name = settings.collection_name
        self.model_name = settings.model_name
        self.model_device = settings.model_device
        self.groq_model = settings.groq_model
        self.groq_api_key = settings.groq_api_key

    def get_embeddings(self):
        return HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={"device": self.model_device}        )

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        # In a real application, you would retrieve this from a database or cache
        session_storage = {}
        if session_id not in session_storage:
            session_storage[session_id] = InMemoryChatMessageHistory()
            logger.info(f"Created new chat history for session: {session_id}")
        return session_storage[session_id]


    def build_chain(self, use_qroq: bool = True):
        
        # Vectorstore setup
        vectorstore = QdrantVectorStore.from_existing_collection(
            embedding=self.get_embeddings(),
            collection_name=self.collection_name,
            url=self.qdrant_host,
        )
        # Retriever setup
        retriver = vectorstore.as_retriever(search_kwargs={"k": 3})
        logger.info("Vector store and retriever initialized.")

        # LLM setup
        if use_qroq:
            llm = ChatGroq(model=self.groq_model, api_key=self.groq_api_key)
        else:
            llm = ChatOllama(model="llama3.2")

        # Prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that answers questions based on the provided context."),
            MessagesPlaceholder(variable_name="history", optional=True),
            ("human", "{context}\n\nQuestion: {question}\nAnswer:")
        ])
        logger.info("LLM and prompt template initialized.")
        # LCEL chain setup
        chain = (
            {
                "context": retriver | self.format_docs,
                "question": RunnablePassthrough(),
            }
            | prompt_template
            | llm
            | StrOutputParser()
        )
        return chain
    async def stream_chain(self, chain, question: str, session_id: str, use_qroq: bool = True) -> AsyncGenerator[str, None]:
        logger.info("Starting to stream the response...")
        async for response in chain.astream(question):
            yield response
query_object = PDFQuery()
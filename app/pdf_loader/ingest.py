import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from pypdf import PdfReader

load_dotenv(Path(__file__).with_name(".env"))

class PDFIngestor:
    def __init__(self):
        self.qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        self.collection_name = os.environ.get("COLLECTION_NAME", "ask_to_pdf_collection")
        self.model_name = os.environ.get("MODEL_NAME", "all-MiniLM-L6-v2")
        self.model_device = os.environ.get("MODEL_DEVICE", "cpu")
        self._embeddings = None

    def get_embeddings(self):
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": self.model_device},
            )
        return self._embeddings
    
    # Load PDF, split into chunks, create embeddings, and save to Qdrant
    def ingest_pdf(self, pdf_path: str):
        logger.info(f"Starting ingestion for PDF: {pdf_path}")
        filename = Path(pdf_path).name
        logger.info(f"Processing file: {filename}")

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        for doc in documents:
            doc.metadata["source"] = filename  # Add source metadata to each document
            doc.metadata["filename"] = filename  # Add filename metadata to each document
        logger.info(f"Loaded {len(documents)} pages loaded, documents from {pdf_path}")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split documents into {len(chunks)} chunks")
        logger.info("Creating embeddings and saving to Qdrant...")

        embeddings = self.get_embeddings()
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=self.qdrant_url,
            collection_name=self.collection_name,
        )
        logger.info("Ingestion completed successfully.")
        logger.info(f"{len(chunks)} chunks ingested into Qdrant collection ")
        return {"chunks_count": len(chunks),
                "filename": filename,
                "pages": len(documents)}
        
ingestor = PDFIngestor()
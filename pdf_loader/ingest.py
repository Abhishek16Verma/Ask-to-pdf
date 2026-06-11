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
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
    
    # Load PDF, split into chunks, create embeddings, and save to Qdrant
    def ingest_pdf(self, pdf_path: str):
        logger.info(f"Starting ingestion for PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} pages loaded, documents from {pdf_path}")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Split documents into {len(chunks)} chunks")
        logger.info("Creating embeddings and saving to Qdrant...")
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=self.qdrant_url,
            collection_name=self.collection_name,
        )
        logger.info("Ingestion completed successfully.")
        logger.info(f"{len(chunks)} chunks ingested into Qdrant collection ")
        return len(chunks)
        
# if __name__ == "__main__":
#     ingestor = PDFIngestor()
#     ingestor.ingest_pdf("/home/ver_114737/ai_agents/Noida Office Newsletter_May 2026.pdf")

ingestor = PDFIngestor()
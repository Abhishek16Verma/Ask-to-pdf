import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pdf_loader.query import query_object
from pdf_loader.ingest import ingestor
from utils.config import get_settings
from loguru import logger
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
import uuid

chain = None  # Global variable to hold the RAG chain instance
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    logger.info("Starting up the application...")
    # Perform any startup tasks here (e.g., database connections, loading models)
    logger.info("FastAPI application initialized...")
    chain = query_object.build_chain()
    
    logger.info("RAG chain built and ready to use.")
    yield
    logger.info("Shutting down the application...")
    # Perform any cleanup tasks here (e.g., closing database connections)
app = FastAPI(
    title="Ask to PDF",
    description="RAG pipeline with FastAPI, LangChain, and Qdrant.",
    version="1.0.0",
    lifespan=lifespan
)   


class QueryRequest(BaseModel):
    question: str
    session_id: str | uuid.UUID = Field(default_factory=uuid.uuid4)

class QueryResponse(BaseModel):
    question: str
    answer: str
    session_id: str | uuid.UUID = Field(default_factory=uuid.uuid4)

class UploadRequest(BaseModel):
    pdf_path: str

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

@app.post("/upload", response_model=UploadRequest, tags=["Upload-PDF"])
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.strip():
        raise HTTPException(status_code=400, detail="PDF path cannot be empty.")
    try:
        file_path = UPLOAD_DIR / f"{uuid.uuid4()}.pdf"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        chunks_count = ingestor.ingest_pdf(str(file_path))
        logger.info(f"PDF uploaded and ingested successfully: {file_path}, chunks created: {chunks_count}")
        return {"pdf_path": str(file_path), "chunks_count": chunks_count}
    except Exception as e:
        logger.exception(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while uploading the PDF.")

@app.post("/ask", response_model=QueryResponse, tags=["Ask-Questions"])
async def ask_question(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if chain is None:
        raise HTTPException(status_code=503, detail="Chain is not initialized yet. Please try again later.")
    try:
        answer = chain.invoke(request.question, config={"configurable": {"session_id": request.session_id}})
        return QueryResponse(question=request.question, answer=answer)
    except Exception as e:
        logger.exception(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your question.")

@app.post("/ask-stream", response_model=QueryResponse, tags=["Ask-Questions"])
async def ask_question_stream(request: QueryRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if chain is None:
        raise HTTPException(status_code=503, detail="Chain is not initialized yet. Please try again later.")
    try:
        print(chain,"===============================")
        answer = ""
        return StreamingResponse(
            query_object.stream_chain(chain, request.question, request.session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Accel-Buffering": "no"  # Disable buffering for Nginx
            },
        )
    except Exception as e:
        logger.exception(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your question.")
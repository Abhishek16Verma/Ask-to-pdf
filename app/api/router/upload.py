import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.middleware.rate_limit import UPLOAD_LIMIT, limiter
from app.pdf_loader.ingest import ingestor
from app.utils.config import get_upload_dir
from app.utils.log import get_logger
from app.utils.models import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse, tags=["Upload-PDF"])
@limiter.limit(UPLOAD_LIMIT)
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=400, detail="PDF filename cannot be empty.")

    upload_dir = getattr(request.app.state, "upload_dir", get_upload_dir())
    file_path = upload_dir / f"{uuid.uuid4()}.pdf"
    log = get_logger(request)

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with open(file_path, "wb") as output_file:
            output_file.write(contents)

        ingest_result = ingestor.ingest_pdf(str(file_path))
        chunks_count = int(ingest_result.get("chunks_count", 0))
        filename = ingest_result.get("filename")

        log.info(f"PDF uploaded and ingested: {file_path} (chunks={chunks_count})")
        return UploadResponse(
            pdf_path=str(file_path),
            chunks_count=chunks_count,
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while uploading the PDF.")

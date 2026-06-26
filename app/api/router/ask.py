from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.middleware.rate_limit import ASK_LIMIT, limiter
from app.pdf_loader.query import query_object
from app.utils.log import get_logger
from app.utils.models import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/ask", response_model=QueryResponse, tags=["Ask-Questions"])
@limiter.limit(ASK_LIMIT)
async def ask_question(request: Request, payload: QueryRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    chain = getattr(request.app.state, "chain", None)
    if chain is None:
        raise HTTPException(status_code=503, detail="Chain is not initialized yet. Please try again later.")

    log = get_logger(request)
    try:
        answer = await chain.ainvoke(
            {"question": payload.question},
            config={"configurable": {"session_id": str(payload.session_id)}},
        )
        return QueryResponse(
            question=payload.question,
            answer=answer,
            session_id=payload.session_id,
        )
    except Exception as e:
        log.exception(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your question.")


@router.post("/ask-stream", tags=["Ask-Questions"])
@limiter.limit(ASK_LIMIT)
async def ask_question_stream(request: Request, payload: QueryRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    chain = getattr(request.app.state, "chain", None)
    if chain is None:
        raise HTTPException(status_code=503, detail="Chain is not initialized yet. Please try again later.")

    log = get_logger(request)
    try:
        log.info(f"Received question with session_id: {payload.session_id}")
        return StreamingResponse(
            query_object.stream_chain(chain, payload.question, str(payload.session_id)),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        log.exception(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your question.")
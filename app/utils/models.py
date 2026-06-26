import uuid

from pydantic import AliasChoices, BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(validation_alias=AliasChoices("question", "query"))
    session_id: str | uuid.UUID = Field(
        default_factory=uuid.uuid4,
        validation_alias=AliasChoices("session_id", "sessionId"),
    )


class QueryResponse(BaseModel):
    question: str
    answer: str
    session_id: str | uuid.UUID


class UploadResponse(BaseModel):
    pdf_path: str
    chunks_count: int
    filename: str | None = None


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    user_id: str
    auth_type: str
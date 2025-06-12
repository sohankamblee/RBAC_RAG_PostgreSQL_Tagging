from pydantic import BaseModel

class UploadRequest(BaseModel):
    title: str
    content: str
    tags: list[str]

class QueryRequest(BaseModel):
    query: str

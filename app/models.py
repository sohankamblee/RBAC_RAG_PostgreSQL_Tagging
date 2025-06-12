from pydantic import BaseModel

# This file defines the data models used in the application.
# Pydantic is used for data validation and serialization.
# BaseModel is the base class for all Pydantic models.
# Pydantic models allow defining the schema of the data,

class UploadRequest(BaseModel):
    title: str
    content: str
    tags: list[str]

class QueryRequest(BaseModel):
    query: str

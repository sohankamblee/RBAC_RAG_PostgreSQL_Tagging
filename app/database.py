#database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Integer, Table, ForeignKey, ARRAY, Text, DateTime, select, insert
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import os
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv
from sqlalchemy import cast, ARRAY
load_dotenv()

# --- Database URL ---
DATABASE_URL = os.getenv("DATABASE_URL")

# --- SQLAlchemy Setup ---

# create_async_engine is used for asynchronous database operations
# declarative_base is used to create a base class for declarative models for SQL Database
# sessionmaker creates a session factory for managing database sessions
# session is needed to interact with the database
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# creating the database tables
# --- TABLE: users ---

# table to store user information
class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    roles = Column(ARRAY(Text))
    departments = Column(ARRAY(Text))
    access_tags = Column(ARRAY(Text))

# --- TABLE: document_metadata ---

# table to store metadata of documents
class DocumentMetadata(Base):
    __tablename__ = 'document_metadata'
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    content = Column(Text)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    departments = Column(ARRAY(Text))
    roles = Column(ARRAY(Text))
    access_tags = Column(ARRAY(Text))
    access_level = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())





# --- FUNCTION: get_user_by_token ---

# Function to retrieve user information based on the username extracted from the JWT token
# returns a dictionary with user details
# result stores user information from the database
# scalar_one_or_none() returns a single result or None if no result is found
async def get_user_by_token(username: str) -> dict:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user:
            return {
                "id": str(user.id),
                "username": user.username,
                "roles": user.roles,
                "departments": user.departments,
                "access_tags": user.access_tags,
            }
        return None
    



# --- FUNCTION: store_metadata ---

# Function to store document metadata in the PostgreSQL database
# metadata is an instance of DocumentMetadata
# title, content, user_info, and tags are parameters to store in the metadata
# session.commit() commits the transaction (add metadata) to the database
# function returns the document_id of the stored metadata
async def store_metadata(title: str, content: str,  user_info: dict, tags: dict):
    async with async_session() as session:
        metadata = DocumentMetadata(
            title=title,
            content=content,
            created_by=user_info["id"],
            departments=tags.get("departments", []),
            roles=tags.get("roles", []),
            access_tags=tags.get("access_tags", []),
            access_level=tags.get("access_level", "general_access"),
        )
        session.add(metadata)
        await session.commit()
        return str(metadata.document_id)




# --- FUNCTION: get_documents_by_filter ---

# Function to retrieve documents based on the user's access tags
# execute() helps to execute SQL query
# SQL QUERY is selecting documents from DocumentMetadata where access_tags match the user's access_tags
# function returns a list of documents with title, content, and document_id
async def get_documents_by_filter(user_info: dict):
    async with async_session() as session:
        result = await session.execute(
            select(DocumentMetadata)
            .where(
                DocumentMetadata.access_tags.op("&&")(
                    cast(user_info["access_tags"], ARRAY(Text))
                )
            )
        )
        documents = result.scalars().all()
        return [{
            "title": doc.title,
            "content": doc.content,
            "doc_id": str(doc.document_id)
        } for doc in documents]



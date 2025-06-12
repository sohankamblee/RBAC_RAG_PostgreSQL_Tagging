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
engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# --- TABLE: users ---
class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    roles = Column(ARRAY(Text))
    departments = Column(ARRAY(Text))
    access_tags = Column(ARRAY(Text))

# --- TABLE: document_metadata ---
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



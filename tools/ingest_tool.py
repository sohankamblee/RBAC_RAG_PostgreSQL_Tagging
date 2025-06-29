#tools/ingest_tool.py
from langchain_core.tools import tool
from app.doc_ingestor_mcp import ingest_pdfs as real_ingest
from fastapi import UploadFile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool(description="Ingest PDFs with access_tags into ChromaDB")
def ingest_pdfs_tool(file_paths: list[str], access_tags: list = None, user: dict = {}):
    logger.info(f"ingest_pdfs tool in use...")
    return real_ingest(file_paths, access_tags, user)

from mcp_agent.agents.agent import Agent
from tools.ingest_tool import ingest_pdfs_tool

ingestion_agent = Agent(
    name="IngestionAgent",
    instruction="You ingest PDFs with the provided access_tags and store them in ChromaDB, with the help of the tool you have access to",
    tools=[ingest_pdfs_tool]
)



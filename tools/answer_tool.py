#tools/answer_tool.py
import logging
from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool(description='Tool that generates an answer based on filtered documents(wrapper) as context.' )
async def generate_answer_tool(query: str, filtered_docs: list[dict]) -> str:
    """
    AnswerTool
    Tool that generates an answer based on filtered documents as context.
    """
    logger.info(f"[AnswerTool] Received query: {query}")
    from app.rag_engine_mcp import generate_answer

    if not filtered_docs:
        logger.info("[AnswerTool] No authorized documents found.")
        return "Final Answer: Sorry, you are not authorized to access this information."

    response = await generate_answer(query, filtered_docs)
    #mcp.context["response"] = response  # Optional: store in MCP context for later use
    return response

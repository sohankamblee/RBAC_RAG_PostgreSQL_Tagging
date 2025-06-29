#tools/rbac_filter_tool.py
import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool(description = "tool that filters the documents from vector DB on the basis of user\'s RBAC (Role-based Access Control) access_tags.")
async def rbac_filter_docs_tool(query: str, user: dict) -> list[dict]:
    """
    RBACFilterTool
    A tool which filters the documents from vector DB on the basis of user\'s RBAC (Role-based Access Control) access_tags.
    """
    logger.info(f"[RBACFilterTool] Running for query: {query}, user: {user}")

    from app.rbac_tool import rbac_filter
    
    context_part = await rbac_filter(query, user)
    
    #mcp.context["filtered_docs"] = docs

    wrapped = [{"content": d} for d in context_part]  
    return wrapped





# async def rbac_filter_docs_tool(query: str, user: dict) -> list[str]:
#     """
#     RBACFilterTool
#     FastMCP-compatible RBAC filter tool.
#     A tool which filters the documents from vector DB on the basis of user\'s RBAC (Role-based Access Control) access_tags.
#     """
#     logger.info(f"[RBACFilterTool] Running for query: {query}, user: {user}")
    
#     docs = await rbac_filter(query, user)
    
#     mcp.context["filtered_docs"] = docs

#     wrapped = [{"content": d} for d in docs]  
#     return wrapped

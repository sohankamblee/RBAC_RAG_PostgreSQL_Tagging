#app/fastmcp_server.py
from mcp.server.fastmcp import FastMCP

# Export a global MCP instance
mcp = FastMCP(name = "RBAC RAG MCP")



# from fastapi import FastAPI
# from pydantic import BaseModel
# from mcp.server.fastmcp import FastMCP
# from typing import Optional
# import uvicorn
# import logging
# from agents.react_agent import _react_agent
# from agents.direct_agent import _direct_agent
# from agents.toolcalling_agent import _toolcalling_agent

# # Optional: Import authentication if needed
# # from app.auth import get_current_user

# # Logging setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI()

# # -------------------------------
# # Custom FastMCP Class with run() override
# # -------------------------------
# class CustomFastMCP(FastMCP):
#     def __init__(self):
#         super().__init__()  # ✅ Ensures base FastMCP sets up agents
#         self._react_agent = _react_agent(tools=self.tool)
#         self._direct_agent = _direct_agent(tools=self.tool)
#         self._toolcalling_agent = _toolcalling_agent(tools=self.tool)
    
#     def run(self, prompt: str, config: dict = {}, user: dict = None):
#         # ✅ Custom run method that accepts prompt, config, and user
#         return self.execute_prompt(prompt=prompt, config=config, user=user)

#     def execute_prompt(self, prompt: str, config: dict = {}, user: dict = None):
#         # Store user in context
#         self.context = {"user": user or {}}

#         # Determine which agent to use
#         transport = config.get("transport")

#         if transport == "react":
#             agent = self._react_agent
#         elif transport == "direct":
#             agent = self._direct_agent
#         elif transport == "toolcall":
#             agent = self._toolcalling_agent
#         else:
#             raise ValueError(f"Unknown transport: {transport}")

#         # Run agent with the given prompt and config
#         return agent.run(prompt, config)

# # Initialize your custom MCP server
# mcp = CustomFastMCP()

# # -------------------------------
# # Pydantic model for input
# # -------------------------------
# class MCPRequest(BaseModel):
#     prompt: str
#     config: Optional[dict] = {}
#     user: Optional[dict] = {}

# # -------------------------------
# # Example Tools using MCP Context
# # -------------------------------
# @mcp.tool(name="RBACFilter", description="Filter documents using user access tags")
# def rbac_filter_tool(input_str: str) -> str:
#     from tools.rbac_filter_tool import RBACFilterTool
#     tool = RBACFilterTool()
#     user = mcp.context.get("user", {})  # ✅ Get user from context
#     return str(tool.run(input_str, user))

# @mcp.tool(name="GenerateAnswer", description="Generate answer from filtered documents")
# def answer_tool(input_str: str) -> str:
#     from tools.answer_tool import AnswerTool
#     tool = AnswerTool()
#     filtered_docs = mcp.context.get("filtered_docs", [])  # ✅ Use filtered docs if stored
#     return str(tool.run(input_str, filtered_docs))

# # ----------------- --------------
# # Endpoint to handle agent calls
# # -------------------------------
# @app.post("/mcp")
# async def run_agent(request: MCPRequest):
#     logger.info(f"MCP called with prompt: {request.prompt}")
#     logger.info(f"User data: {request.user}")

#     try:
#         result = mcp.run(prompt=request.prompt, config=request.config, user=request.user)
#         logger.info(f"✅ MCP run successful. Result: {result}")
#         return {"response": result}  # ✅ Always return with 'response' key
#     except Exception as e:
#         logger.exception(f"❌ MCP execution failed: {e}")
#         return {"error": str(e)}

# # -------------------------------
# # Run the server
# # -------------------------------
# if __name__ == "__main__":
#     uvicorn.run("fastmcp_server:app", host="0.0.0.0", port=8000, reload=True)

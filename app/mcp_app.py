# mcp_app.py
from mcp_agent.app import MCPApp
from mcp_agents.base_orchestrator import RBACOrchestrator

app = MCPApp()
orchestrator = RBACOrchestrator()
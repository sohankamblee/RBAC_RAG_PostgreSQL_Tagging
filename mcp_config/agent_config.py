#mcp_config/agent_config.py
from agents.query_agent import QueryAgent

def setup_mcp(mcp):
    print("🔧 Registering tools...")
    import tools.rbac_filter_tool 
    import tools.answer_tool

    print("🤖 Registering QueryAgent...")
    mcp.add_agent("QueryAgent", QueryAgent)

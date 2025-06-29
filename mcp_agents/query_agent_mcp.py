# mcp_agents/query_agent.py
from mcp_agent.agents.agent import Agent
from tools.answer_tool import generate_answer_tool
from tools.rbac_filter_tool import rbac_filter_docs_tool

query_agent = Agent(
    name="QueryAgent",
    instruction=(
        "You are a reasoning agent with access to tools.\n"
        "First call RBACFilter(docs, user_tags) to filter docs by user's access_tags.\n"
        "If any results (wrapper) are returned, pass them to GenerateAnswer(wrapper) to answer the question.\n"
        "If RBACFilter returns an empty list, respond with:\n 'Final Answer: Sorry, you are not authorized to access this information.'"
    ),
    tools=[rbac_filter_docs_tool, generate_answer_tool]
)

# agents/query_agent.py

class QueryAgent:
    def __init__(self):
        self.name = "QueryAgent"
        self.description = (
            "You are a reasoning agent with access to tools.\n"
            "Before answering any query, always check user authorization using the RBACFilter tool.\n"
            "Only proceed to GenerateAnswer if RBACFilter returns at least one authorized document.\n"
            "If no authorized documents are found, respond with:\n"
            "'Final Answer: Sorry, you are not authorized to access this information.'"
        )


# #agents/query_agent.py
# from agents.base_agent import ReActAgent
# from tools.rbac_filter_tool import RBACFilterTool
# from tools.answer_tool import AnswerTool
# import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class QueryAgent(ReActAgent):
#     def __init__(self):
#         tools = {
#             "RBACFilter": RBACFilterTool(),
#             "GenerateAnswer": AnswerTool()
#         }
#         logger.info("Initializing QueryAgent with RBACFilter and GenerateAnswer tools.")
#         super().__init__("QueryAgent", "Multi-step reasoning agent", tools)    

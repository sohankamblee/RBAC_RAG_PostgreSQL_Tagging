# agents/base_agent.py
import requests
from abc import ABC, abstractmethod
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FASTMCP_ENDPOINT = "http://localhost:8000/mcp"

class BaseAgent(ABC):
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def send_to_fastmcp(self, prompt: str, config: dict , user: dict ):
        payload = {
            "prompt": prompt,
            "config": config,
            "user": user
        }
        response = requests.post(FASTMCP_ENDPOINT, json=payload)

        logger.info(f" Sent to MCP: {payload}")
        logger.info(f" Status code from MCP: {response.status_code}")
        logger.info(f" Text from MCP: {response.text}")
        
        try:
            result = response.json()
        except Exception as e:
                logger.error(f"❌ Failed to parse JSON: {e}")
                logger.error(f"❌ Response text: {response.text}")
                raise

        if "response" not in result:
            logger.error(f"❌ 'response' key not found in MCP output. Full JSON: {result}")
            raise KeyError("Missing 'response' in MCP server reply")

        return result["response"]

    @abstractmethod
    def run(self, input_data):
        pass


class ReActAgent(BaseAgent):
    def __init__(self, name, description, tools: dict):
        super().__init__(name, description)
        self.tools = tools

    def parse_action(self, output: str):
        # Detect Action: ToolName("args")
        if "Action:" in output:
            action_line = output.split("Action:")[1].strip()
            tool_name, args = action_line.split("(", 1)
            args = args.rstrip(")")
            return tool_name.strip(), args.strip()
        return None, None

    def run(self, user_query: str, config: dict, user: dict):
        history = f"User asked: {user_query}\n"
        logger.info(f"[{self.name}] Starting reasoning for query: {user_query}")    
        

        config["transport"] = "react"
        config["system"] = (
                    "You are a reasoning agent with access to tools.\n"
                    "Before answering any query, always check user authorization using the RBACFilter tool.\n"
                    "Only proceed to GenerateAnswer if RBACFilter returns at least one authorized document.\n"
                    "If no authorized documents are found, respond with:\n"
                    "'Final Answer: Sorry, you are not authorized to access this information.'"
                )
        config["user"] = user

        for _ in range(3):  # 3-step ReAct loop
            prompt = history + "Thought:"
            model_output = self.send_to_fastmcp(prompt, config, user)
            logger.info(f"[{self.name}] Model output: {model_output}")

            history += model_output + "\n"

            if "Final Answer:" in model_output:
                logger.info(f"[{self.name}] Final answer found: {model_output}")
                return model_output.split("Final Answer:")[1].strip()
                

            tool_name, tool_input = self.parse_action(model_output)
            logger.info(f"[{self.name}] Parsed tool name: {tool_name}, input: {tool_input}")


            if tool_name and tool_name in self.tools:
                try:
                    observation = self.tools[tool_name].run(tool_input)
                except Exception as e:
                    # Record the failure and break out
                    error_msg = f"Tool failed: {tool_name} error={e}"
                    history += f"Observation: {error_msg}\n"
                    logger.error(f"[{self.name}] {error_msg}")
                    return f"Final Answer: Sorry, I encountered an internal error."
                # On success, inject into history
                history += f"Observation: {observation}\n"
            else:
                history += "Observation: Tool not recognized.\n"
        
        logger.warning(f"[{self.name}] Unable to reach a final answer after 3 steps.")
        return "I couldn't complete the reasoning."

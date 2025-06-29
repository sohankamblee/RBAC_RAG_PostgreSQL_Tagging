# mcp_agents/base_orchestrator.py
from mcp_agent.workflows.orchestrator.orchestrator import Orchestrator
from mcp_agents.ingestion_agent import ingestion_agent
from mcp_agents.query_agent_mcp import query_agent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# from langchain_ollama import OllamaLLM as Ollama
# #from mcp_agent.mcp.gen_client import LLMFactory

# llm = Ollama(model="mistral", temperature=0.3)
# factory = lambda agent: llm



# # Patch MCP context with dummy OpenAI settings (required even for Ollama)
# llm.context = Context(config={
#     "openai": OpenAISettings(api_key="dummy")  # Required due to internal schema
# })
from mcp_agent.core.context import Context
from mcp_agent.config import OpenAISettings
# from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
from mcp_agent.executor import executor

from mcp_agent.workflows.llm.augmented_llm import A

from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

# Setup dummy context (needed by MCP framework)
context = Context(config={
    "openai": OpenAISettings(api_key="dummy")
})

# Define a factory that attaches context + model + temperature
factory = lambda agent: OpenAIAugmentedLLM(
    agent=agent,
    temperature=0.3,
    context=context
    # executor=agent.executor
)

# class OllamaLLMFactory(LLMFactory):
#     def create_llm(self, **kwargs):
#         return 

class RBACOrchestrator(Orchestrator):
    def __init__(self):
        super().__init__(name="RBACOrchestrator", agents=[ingestion_agent, query_agent], llm_factory=factory)

    async def plan(self, task: str, user: dict, access_tags: list[str] = None, file_paths: list[str] = None):
        
        logger.info(f"RBACOrchestrator Agent running..\n\n")
        if not user:
            return "User not found...UNAUTHORIZED"

        access_tags = user["access_tags"]
        is_admin = "admin" in access_tags

        # Decide based on task content
        if "ingest" in task.lower() and is_admin:
            logger.info(f"Initialiazing IngestionAgent...")

            from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
            llm = await ingestion_agent.attach_llm(self.llm_factory)
            result = await llm.generate(tool_name="ingest_pdfs", input={
                "file_paths": file_paths,
                "access_tags": access_tags,
                "user": user
            })
            return {"result": result}
        
        elif "answer" in task.lower():
            logger.info(f"Initialiazing QueryAgent...")
            
            from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
            llm = await query_agent.attach_llm(self.llm_factory)
            if llm.executor is None:
                llm.executor = query_agent.context.executor 
            
            result = await llm.generate_str(task)
            return {"result": result}
        
        elif "ingest" in task.lower() and not is_admin:
            return "❌ You are not authorized to ingest documents."
        
        else:
            return "❌ Could not understand task type."

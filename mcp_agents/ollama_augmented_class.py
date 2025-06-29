from mcp_agent.workflows.llm.augmented_llm import AugmentedLLM
from langchain_ollama import OllamaLLM as Ollama

class OllamaAugmentedLLM(AugmentedLLM):
    def __init__(self, agent=None, model="mistral", temperature=0.3, context=None):
        super().__init__(agent=agent, context=context)
        self.model = model
        self.ollama = Ollama(model=model, temperature=temperature)

    async def generate_str(self, prompt: str) -> str:
        return self.ollama.invoke(prompt)
    
    

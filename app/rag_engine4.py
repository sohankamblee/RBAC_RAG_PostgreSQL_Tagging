import logging
import json
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM as Ollama
from app.embedder import embed_query_to_vector
from app.vector_store import chroma_collection
from app.rbac_tool import rbac_filter
from langchain.tools import tool
from langchain.agents import initialize_agent, AgentType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = Ollama(
    model="mistral",
    temperature=0.3
)

# Wrap the RBAC filter as a LangChain tool (single string input for ZeroShotAgent)
@tool("rbac_filter")
def rbac_filter_tool(input_str: str) -> str:
    """
    Expects a JSON string with keys 'context_chunks' (list of dicts) and 'user_access_tags' (list of str).
    Returns a JSON string of the filtered chunk texts.
    """
    data = json.loads(input_str)
    filtered = rbac_filter(data["context_chunks"], data["user_access_tags"])
    return json.dumps(filtered)

# Agent setup
agent = initialize_agent(
    tools=[rbac_filter_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

async def generate_answer4(query: str, user):
    logger.info(f"Received query: {query}")
    query_embedding = embed_query_to_vector(query)
    logger.info("Query embedding generated.")

    # Vector search in ChromaDB
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    logger.info(f"ChromaDB query returned {len(docs)} docs.")

    # Prepare context chunks for the tool
    context_chunks = []
    for doc, meta in zip(docs, metas):
        access_tags = [tag.strip() for tag in meta.get("access_tags", "").split(",") if tag.strip()]
        context_chunks.append({"text": doc, "access_tags": access_tags})

    # Prepare the tool input as a JSON string
    tool_input = json.dumps({
        "context_chunks": context_chunks,
        "user_access_tags": user["access_tags"]
    })

    agent_prompt = f"""
You are a company assistant with access to a tool called 'rbac_filter' that can filter context chunks based on user access tags.

To use the tool, respond exactly as follows:
Action: rbac_filter
Action Input: <JSON string with 'context_chunks' and 'user_access_tags'>

When you have the answer, respond exactly as follows:
Final Answer: <your answer>

If no chunks are accessible, respond with exactly:
Final Answer: Sorry, you are not authorized to access this info.

If the answer is not explicitly stated in the accessible context, respond with exactly:
Final Answer: Sorry, this information is not available.

Example:
User Query: What is the HR policy?
Action: rbac_filter
Action Input: {{"context_chunks": [{{"text": "HR Policy: ...", "access_tags": ["hr_user"]}}], "user_access_tags": ["hr_user"]}}
Observation: ["HR Policy: ..."]
Final Answer: The HR policy is ...

User Query: {query}
Tool Input Example: {tool_input}
"""
    logger.info(f"Agent prompt:\n{agent_prompt}")
    print("\n\nAgent prompt:\n", agent_prompt)

    # Run the agent (synchronously for LangChain agents)
    response = agent.run(agent_prompt)
    logger.info(f"Agent response: {response.strip()}")
    print("\n\nAgent response:", response.strip())
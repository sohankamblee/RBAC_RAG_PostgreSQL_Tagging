import asyncio
from app.rag_engine import generate_answer

# Define the test user (role + access tags)
test_user = {
    "roles": ["it_user"],
    "access_tags": ["it_only", "it_user"]
}

# Canary query that should only be answered from injected context
canary_query = "Who should be contacted for a High/Critical IT issue?"

async def run_canary_test():
    print(f"🔍 Sending Canary Query: {canary_query}")
    answer = await generate_answer(canary_query, test_user)
    print("\n📢 Model Response:")
    print(answer)

if __name__ == "__main__":
    asyncio.run(run_canary_test())

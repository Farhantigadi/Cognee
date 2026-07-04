import os
from dotenv import load_dotenv

load_dotenv()

os.environ["SYSTEM_ROOT_DIRECTORY"] = r"C:\ChronoResearch\cognee_data\system"
os.environ["DATA_ROOT_DIRECTORY"] = r"C:\ChronoResearch\cognee_data\data"
os.environ["LLM_PROVIDER"] = "custom"
os.environ["LLM_MODEL"] = "groq/llama-3.3-70b-versatile"
os.environ["LLM_ENDPOINT"] = "https://api.groq.com/openai/v1"
os.environ["LLM_API_KEY"] = os.environ["GROQ_API_KEY"]
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"
os.environ["EMBEDDING_PROVIDER"] = "fastembed"
os.environ["EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["EMBEDDING_DIMENSIONS"] = "384"

import asyncio
import cognee

async def test():
    await cognee.remember("Transformers were introduced in the paper Attention Is All You Need in 2017 by Vaswani et al.")
    result = await cognee.recall("Who introduced transformers?")
    print("Result:", result)

asyncio.run(test())

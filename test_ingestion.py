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
import urllib.request
from backend.ingestion import ingest_pdf, IngestionStatus

PDF_URL = "https://arxiv.org/pdf/1706.03762"
PDF_PATH = r"C:\ChronoResearch\attention_is_all_you_need.pdf"


def download_pdf(url: str, dest: str):
    if not os.path.exists(dest):
        print(f"Downloading paper from {url} ...")
        urllib.request.urlretrieve(url, dest)
        print(f"Saved to {dest}")
    else:
        print(f"PDF already exists at {dest}, skipping download.")


async def main():
    download_pdf(PDF_URL, PDF_PATH)

    print("Starting ingestion...")
    result = await ingest_pdf(PDF_PATH)

    print(f"\n--- Ingestion Result ---")
    print(f"Paper     : {result.paper_name}")
    print(f"Status    : {result.status}")
    print(f"Chunks    : {result.chunks_ingested}")
    if result.error:
        print(f"Error     : {result.error}")


asyncio.run(main())

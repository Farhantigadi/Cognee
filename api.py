import os
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# CRITICAL: env vars before importing cognee (lru_cache freezes config at import)
load_dotenv()

os.environ["SYSTEM_ROOT_DIRECTORY"] = r"C:\ChronoResearch\cognee_data\system"
os.environ["DATA_ROOT_DIRECTORY"]   = r"C:\ChronoResearch\cognee_data\data"
os.environ["LLM_PROVIDER"]          = "custom"
os.environ["LLM_MODEL"]             = "groq/llama-3.3-70b-versatile"
os.environ["LLM_ENDPOINT"]          = "https://api.groq.com/openai/v1"
os.environ["LLM_API_KEY"]           = os.environ.get("GROQ_API_KEY", "")
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"
os.environ["EMBEDDING_PROVIDER"]    = "fastembed"
os.environ["EMBEDDING_MODEL"]       = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["EMBEDDING_DIMENSIONS"]  = "384"

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.ingestion import ingest_pdf, IngestionStatus
from backend.memory_engine import (
    recall_from_papers,
    improve_memory,
    forget_paper,
    list_papers,
    get_memory_stats,
)

app = FastAPI(title="ChronoResearch API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RecallRequest(BaseModel):
    question: str

class ImproveRequest(BaseModel):
    dataset: Optional[str] = "main_dataset"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        result = await ingest_pdf(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if result.status == IngestionStatus.FAILED:
        raise HTTPException(status_code=422, detail=result.error)

    stats = await get_memory_stats()

    return {
        "paper_name": result.paper_name,
        "chunks": result.chunks_ingested,
        "nodes": stats.get("total_nodes", 0),
        "edges": stats.get("total_edges", 0),
        "status": result.status.value,
    }


@app.post("/recall")
async def recall(body: RecallRequest):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = await recall_from_papers(body.question)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "answer": result.get("answer"),
        "sources": result.get("papers", []),
        "related_concepts": result.get("related_concepts", []),
        "confidence": result.get("confidence", 0.0),
    }


@app.post("/improve")
async def improve(body: ImproveRequest = ImproveRequest()):
    result = await improve_memory(dataset=body.dataset)
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return {"status": "completed", "message": f"Memory enriched for dataset '{body.dataset}'."}


@app.delete("/paper/{paper_name}")
async def delete_paper(paper_name: str):
    result = await forget_paper(paper_name)
    if result.get("status") == "failed":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return {"status": "success", "message": result["message"]}


@app.get("/papers")
async def papers():
    result = await list_papers()
    # Surface any backend error as HTTP 500
    if result and "error" in result[0]:
        raise HTTPException(status_code=500, detail=result[0]["error"])
    return [
        {
            "name": p["name"],
            "date": p.get("ingestion_date"),
            "chunks": p.get("chunk_count", 0),
        }
        for p in result
    ]


@app.get("/stats")
async def stats():
    result = await get_memory_stats()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {
        "total_papers": result.get("total_papers", 0),
        "total_nodes":  result.get("total_nodes", 0),
        "total_edges":  result.get("total_edges", 0),
    }

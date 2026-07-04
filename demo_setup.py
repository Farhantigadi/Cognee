"""
ChronoResearch — Demo Setup Script
Downloads 5 landmark AI papers, ingests them into Cognee memory,
runs 5 test queries, and prints a final report for hackathon judges.
"""

import os
import sys
import time
from dotenv import load_dotenv

# CRITICAL: set env vars before importing cognee
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

import asyncio
from pathlib import Path

import requests
import cognee
from backend.ingestion import extract_text, chunk_text
from backend.memory_engine import get_memory_stats, recall_from_papers

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PAPERS_DIR = Path(r"C:\ChronoResearch\demo_papers")

PAPERS = [
    {
        "name": "attention_is_all_you_need",
        "title": "Attention Is All You Need (2017)",
        "url": "https://arxiv.org/pdf/1706.03762",
    },
    {
        "name": "bert",
        "title": "BERT (2018)",
        "url": "https://arxiv.org/pdf/1810.04805",
    },
    {
        "name": "gpt3",
        "title": "GPT-3 (2020)",
        "url": "https://arxiv.org/pdf/2005.14165",
    },
    {
        "name": "lora",
        "title": "LoRA (2021)",
        "url": "https://arxiv.org/pdf/2106.09685",
    },
    {
        "name": "chain_of_thought",
        "title": "Chain of Thought (2022)",
        "url": "https://arxiv.org/pdf/2201.11903",
    },
]

QUERIES = [
    "Who introduced the transformer architecture?",
    "How does BERT differ from the original transformer?",
    "What is the relationship between attention and LoRA?",
    "How did prompting techniques evolve across these papers?",
    "Which paper introduced the concept of fine-tuning?",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sep(char="─", width=60):
    print(char * width)

def banner(text):
    sep("═")
    print(f"  {text}")
    sep("═")

def step(n, total, text):
    print(f"\n[{n}/{total}] {text}")

def ok(text):
    print(f"  ✅ {text}")

def warn(text):
    print(f"  ⚠️  {text}")

def err(text):
    print(f"  ❌ {text}")

def info(text):
    print(f"  ℹ  {text}")

# ---------------------------------------------------------------------------
# Phase 1 — Download
# ---------------------------------------------------------------------------

def download_papers() -> list[Path]:
    banner("PHASE 1 — Downloading Papers")
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for i, paper in enumerate(PAPERS, 1):
        pdf_path = PAPERS_DIR / f"{paper['name']}.pdf"
        step(i, len(PAPERS), paper["title"])

        if pdf_path.exists() and pdf_path.stat().st_size > 10_000:
            ok(f"Already exists ({pdf_path.stat().st_size / 1024:.0f} KB) — skipping download")
            downloaded.append(pdf_path)
            continue

        try:
            print(f"  Downloading {paper['url']} ...")
            resp = requests.get(
                paper["url"],
                headers=HEADERS,
                allow_redirects=True,
                timeout=60,
                stream=True,
            )
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type and "octet-stream" not in content_type:
                warn(f"Unexpected Content-Type: {content_type} — saving anyway")

            total_bytes = 0
            with open(pdf_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_bytes += len(chunk)

            size_kb = total_bytes / 1024
            if size_kb < 10:
                err(f"File too small ({size_kb:.1f} KB) — likely not a real PDF")
                pdf_path.unlink(missing_ok=True)
                continue

            ok(f"Downloaded {size_kb:.0f} KB → {pdf_path.name}")
            downloaded.append(pdf_path)

            # Be polite to arxiv — avoid rate limiting
            if i < len(PAPERS):
                time.sleep(2)

        except requests.RequestException as e:
            err(f"Download failed: {e}")

    print(f"\n  Downloaded {len(downloaded)}/{len(PAPERS)} papers")
    return downloaded

# ---------------------------------------------------------------------------
# Phase 2 — Ingest
# ---------------------------------------------------------------------------

async def ingest_paper(pdf_path: Path) -> dict:
    paper_name = pdf_path.stem
    try:
        text = extract_text(str(pdf_path))
        chunks = chunk_text(text)
        total = len(chunks)
        print(f"  Extracted {len(text):,} chars → {total} chunks")

        for idx, chunk in enumerate(chunks, 1):
            await cognee.remember(chunk, dataset_name=paper_name)
            # Print progress every 10 chunks
            if idx % 10 == 0 or idx == total:
                pct = idx / total * 100
                bar = "█" * (idx * 20 // total) + "░" * (20 - idx * 20 // total)
                print(f"  [{bar}] {idx}/{total} chunks ({pct:.0f}%)", end="\r")

        print()  # newline after progress bar
        return {"status": "completed", "name": paper_name, "chunks": total}

    except Exception as e:
        print()
        return {"status": "failed", "name": pdf_path.stem, "error": str(e)}


async def ingest_all(pdf_paths: list[Path]) -> list[dict]:
    banner("PHASE 2 — Ingesting Papers into Cognee Memory")
    results = []
    t_total_start = time.time()

    for i, pdf_path in enumerate(pdf_paths, 1):
        paper_meta = next((p for p in PAPERS if p["name"] == pdf_path.stem), None)
        title = paper_meta["title"] if paper_meta else pdf_path.stem
        step(i, len(pdf_paths), title)

        t_start = time.time()
        result = await ingest_paper(pdf_path)
        elapsed = time.time() - t_start

        if result["status"] == "completed":
            ok(f"Ingested {result['chunks']} chunks in {elapsed:.1f}s")
        else:
            err(f"Failed: {result.get('error', 'unknown')}")

        results.append(result)

    total_elapsed = time.time() - t_total_start
    completed = [r for r in results if r["status"] == "completed"]
    print(f"\n  Ingested {len(completed)}/{len(pdf_paths)} papers in {total_elapsed:.1f}s")
    return results

# ---------------------------------------------------------------------------
# Phase 3 — Test Queries
# ---------------------------------------------------------------------------

async def run_queries() -> list[dict]:
    banner("PHASE 3 — Running Test Queries")
    query_results = []

    for i, question in enumerate(QUERIES, 1):
        step(i, len(QUERIES), f'"{question}"')
        t_start = time.time()

        response = await recall_from_papers(question)
        elapsed = time.time() - t_start

        if "error" in response:
            err(f"Query failed: {response['error']}")
            query_results.append({"question": question, "error": response["error"]})
            continue

        answer = response.get("answer") or "(no answer returned)"
        papers = response.get("papers", [])
        concepts = response.get("related_concepts", [])
        confidence = response.get("confidence", 0.0)

        # Truncate long answers for console readability
        display_answer = answer[:300] + "..." if len(answer) > 300 else answer

        print(f"  Answer   : {display_answer}")
        print(f"  Sources  : {', '.join(papers) if papers else 'none identified'}")
        print(f"  Concepts : {', '.join(concepts[:5]) if concepts else 'none'}")
        print(f"  Confidence: {confidence:.0%}  |  Time: {elapsed:.1f}s")

        query_results.append({
            "question": question,
            "answer": answer,
            "papers": papers,
            "concepts": concepts,
            "confidence": confidence,
        })

    return query_results

# ---------------------------------------------------------------------------
# Phase 4 — Final Report
# ---------------------------------------------------------------------------

async def print_report(ingest_results: list[dict], query_results: list[dict]):
    banner("PHASE 4 — Final Report")

    stats = await get_memory_stats()

    sep()
    print("  KNOWLEDGE GRAPH STATS")
    sep()
    if "error" in stats:
        warn(f"Could not fetch stats: {stats['error']}")
    else:
        print(f"  Total papers  : {stats.get('total_papers', 0)}")
        print(f"  Total chunks  : {stats.get('total_chunks', 0)}")
        print(f"  Total nodes   : {stats.get('total_nodes', 0)}")
        print(f"  Total edges   : {stats.get('total_edges', 0)}")

    sep()
    print("  INGESTION SUMMARY")
    sep()
    for r in ingest_results:
        status_icon = "✅" if r["status"] == "completed" else "❌"
        chunks_str = f"{r['chunks']} chunks" if r.get("chunks") else r.get("error", "")
        print(f"  {status_icon} {r['name']:<35} {chunks_str}")

    sep()
    print("  QUERY RESULTS SUMMARY")
    sep()
    for r in query_results:
        if "error" in r:
            print(f"  ❌ {r['question'][:55]}")
            print(f"     Error: {r['error'][:80]}")
        else:
            answer_preview = (r["answer"] or "")[:120].replace("\n", " ")
            if len(r["answer"] or "") > 120:
                answer_preview += "..."
            print(f"  Q: {r['question']}")
            print(f"  A: {answer_preview}")
            print(f"     Sources: {', '.join(r['papers']) or 'none'}  |  Confidence: {r['confidence']:.0%}")
        print()

    sep("═")
    completed_ingests = sum(1 for r in ingest_results if r["status"] == "completed")
    answered = sum(1 for r in query_results if "error" not in r and r.get("answer"))
    print(f"  ✅ Demo ready: {completed_ingests}/5 papers ingested, {answered}/5 queries answered")
    print(f"  Run: streamlit run app.py")
    sep("═")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    banner("ChronoResearch — Demo Setup")
    print("  Papers That Talk To Each Other")
    print(f"  Papers dir : {PAPERS_DIR}")
    print(f"  Data dir   : {os.environ['DATA_ROOT_DIRECTORY']}")

    t_start = time.time()

    # Phase 1: Download
    pdf_paths = download_papers()
    if not pdf_paths:
        err("No papers downloaded. Check your internet connection.")
        sys.exit(1)

    # Phase 2: Ingest
    ingest_results = await ingest_all(pdf_paths)

    # Phase 3: Queries
    query_results = await run_queries()

    # Phase 4: Report
    await print_report(ingest_results, query_results)

    total_time = time.time() - t_start
    print(f"\n  Total time: {total_time / 60:.1f} minutes")


if __name__ == "__main__":
    asyncio.run(main())

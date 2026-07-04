# ChronoResearch — Papers That Talk To Each Other

## What It Does

Upload research papers as PDFs and ask questions that span all of them simultaneously. ChronoResearch uses Cognee to build a living knowledge graph that finds connections, contradictions, and concept evolution across papers — answers that no single paper could give you alone.

## The Problem It Solves

Reading 5 AI papers takes hours. Understanding how ideas *connect across* them takes days. You read about attention in one paper, fine-tuning in another, and chain-of-thought in a third — but the relationships between those ideas live only in your head, and they fade.

ChronoResearch externalises that synthesis. Upload your papers once, then ask:
- *"How did attention mechanisms evolve from 2017 to 2022?"*
- *"Which papers build on transformer fine-tuning?"*
- *"What's the relationship between LoRA and the original attention paper?"*

The knowledge graph answers across all papers at once.

## Demo

🎥 **Loom demo:** `[LINK TO BE ADDED]`

**Live demo papers pre-loaded:**
- Attention Is All You Need (Vaswani et al., 2017)
- BERT (Devlin et al., 2018)
- GPT-3 (Brown et al., 2020)
- LoRA (Hu et al., 2021)
- Chain-of-Thought Prompting (Wei et al., 2022)

## How Cognee Powers Everything

All four Cognee V2 APIs are used — not as a demo checkbox, but as the actual backbone of the app.

### `remember()` — Building the Knowledge Graph
Every PDF is extracted, split into 500-word chunks with 50-word overlap, and each chunk is fed to `cognee.remember()` with a `dataset_name` matching the paper title. This builds a per-paper subgraph while keeping all papers connected in the same knowledge space.

```python
for chunk in chunks:
    await cognee.remember(chunk, dataset_name=paper_name)
```

### `recall()` — Cross-Paper Question Answering
When a user asks a question, `cognee.recall()` runs hybrid search (vector similarity + graph traversal) across the entire knowledge graph — all papers simultaneously. It returns graph entries with source attribution, so we know which papers contributed to each answer.

```python
results = await cognee.recall(question)
# Each result has .text, .dataset_name, .metadata
```

### `improve()` — Getting Smarter From Feedback
When a user clicks 👍 on an answer, `cognee.improve()` runs triplet embedding enrichment on the contributing papers' datasets. This strengthens the graph connections that produced good answers, making future queries more accurate over time.

```python
# Called silently on thumbs-up feedback
await cognee.improve(dataset=paper_name)
```

### `forget()` — Clean Paper Removal
Users can remove any paper from memory with one click. `cognee.forget()` deletes the dataset's graph nodes, vector embeddings, and dataset record completely — no orphaned data.

```python
await cognee.forget(dataset=paper_name)
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit UI (app.py)               │
│   ┌──────────────┐        ┌────────────────────┐    │
│   │ Upload & Learn│        │    Ask Anything    │    │
│   │  (Tab 1)     │        │      (Tab 2)       │    │
│   └──────┬───────┘        └─────────┬──────────┘    │
└──────────┼──────────────────────────┼───────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────────────────────────────────────┐
│              Backend (backend/)                      │
│   ingestion.py              memory_engine.py         │
│   extract_text()            recall_from_papers()     │
│   chunk_text()              improve_memory()         │
│   ingest_pdf()              forget_paper()           │
│                             list_papers()            │
│                             get_memory_stats()       │
└─────────────────────────────────────────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────────────────────────────────────────┐
│                   Cognee 1.2.2                       │
│   remember() → recall() → improve() → forget()      │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐     ┌─────────────────┐
│   LanceDB    │     │   KuzuDB        │
│ (vectors)    │     │ (graph)         │
└──────────────┘     └─────────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────┐
        │  Groq API       │
        │  llama-3.3-70b  │
        │  (LLM)          │
        └─────────────────┘
```

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Memory / Knowledge Graph | Cognee 1.2.2 |
| LLM | Groq — llama-3.3-70b-versatile |
| Embeddings | fastembed — all-MiniLM-L6-v2 (local) |
| Vector DB | LanceDB (local) |
| Graph DB | KuzuDB (local) |
| PDF Extraction | PyMuPDF (fitz) |
| Language | Python 3.13 |

## How To Run

**1. Clone and set up environment**
```bash
git clone <repo-url>
cd ChronoResearch
python -m venv venv
venv\Scripts\activate        # Windows
pip install cognee streamlit pymupdf python-dotenv fastembed requests
```

**2. Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

**3. (Optional) Pre-load demo papers**
```bash
python demo_setup.py
# Downloads 5 landmark AI papers and ingests them (~8 minutes)
```

**4. Run the app**
```bash
streamlit run app.py
# Opens http://localhost:8501
```

## Example Queries

Once papers are loaded, try these:

- *"Who introduced the transformer architecture and what was their key insight?"*
- *"How does BERT's bidirectional training differ from GPT's approach?"*
- *"What is the relationship between attention mechanisms and LoRA's low-rank decomposition?"*
- *"How did the field's approach to prompting evolve from 2017 to 2022?"*
- *"Which papers discuss the limitations of scaling?"*

## Built For

**WeMakeDevs — "The Hangover Part AI" Hackathon**
June 29 – July 5, 2026

Built to demonstrate that Cognee's memory APIs can power real research workflows — not just toy demos.

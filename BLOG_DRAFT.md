# I Built AI That Reads Research Papers and Connects Them Across Time — Here's How

Last month I had 11 browser tabs open, each a different AI research paper. I was trying to understand how the field got from the original Transformer to modern prompting techniques. After two hours I had a headache, three pages of notes, and a nagging feeling I was missing connections that were obvious to someone who'd read these papers more carefully than me.

That's the problem I built ChronoResearch to solve.

---

## What I Built

ChronoResearch is a Streamlit app where you upload research papers as PDFs and then ask questions that span all of them at once. Not "summarise this paper" — that's just a wrapper around an LLM. I mean questions like:

*"How did the concept of attention evolve from 2017 to 2022?"*
*"Which papers build on transformer fine-tuning, and how?"*
*"What's the relationship between LoRA and the original attention mechanism?"*

The app builds a knowledge graph across all your papers and answers by traversing that graph — finding connections that exist across documents, not just within one.

I built it in about 4 days for the WeMakeDevs hackathon. Here's how it actually works.

---

## Why Cognee Was the Right Tool

I looked at a few options. RAG with a vector database was the obvious first choice — chunk the papers, embed them, retrieve by similarity. But pure vector search has a problem: it finds *similar* text, not *connected* ideas. If paper A introduces concept X and paper B extends it, a vector search for "concept X" might return chunks from both papers, but it won't tell you *how* they're related.

Cognee builds a knowledge graph on top of the embeddings. When you ingest text, it doesn't just store vectors — it extracts entities, relationships, and triplets, then connects them in a graph. That means when you query across papers, you're not just finding similar sentences. You're traversing a graph of concepts that Cognee built by actually understanding the text.

The API is also genuinely simple. Four functions: `remember`, `recall`, `improve`, `forget`. That's it. No pipeline configuration, no manual graph construction.

---

## How `remember()` Works in My App

The ingestion pipeline is in `backend/ingestion.py`. PyMuPDF extracts the raw text from each PDF page, then I split it into 500-word chunks with a 50-word overlap (so concepts that span chunk boundaries don't get cut off):

```python
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = re.split(r"\s+", text)
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks
```

Then each chunk goes to Cognee with the paper name as the dataset:

```python
for chunk in chunks:
    await cognee.remember(chunk, dataset_name=paper_name)
```

The `dataset_name` parameter is important. It keeps each paper in its own dataset, which means I can later `forget()` a specific paper without touching the others. Cognee handles the graph construction — entity extraction, relationship mapping, embedding — all from that one call.

For "Attention Is All You Need" (15 pages), this produces about 14 chunks and takes roughly 30 seconds. GPT-3 (75 pages) produces ~100 chunks and takes a few minutes. The first run also downloads the fastembed model (~90MB), so factor that in.

---

## How `recall()` Surfaces Cross-Paper Insights

This is where it gets interesting. The query function in `backend/memory_engine.py`:

```python
async def recall_from_papers(question: str) -> dict:
    results = await cognee.recall(question)

    answer_texts, papers, concepts = [], set(), set()
    for entry in results:
        if hasattr(entry, "text") and entry.text:
            answer_texts.append(entry.text)
        if hasattr(entry, "dataset_name") and entry.dataset_name:
            papers.add(entry.dataset_name)

    return {
        "answer": " | ".join(answer_texts),
        "papers": list(papers),
        "related_concepts": list(concepts),
        "confidence": min(1.0, len(results) * 0.2),
    }
```

`cognee.recall()` runs hybrid search — vector similarity to find relevant chunks, then graph traversal to find connected concepts. Each result has a `dataset_name` attribute telling you which paper it came from. So when I ask "how did attention evolve?", the answer might pull from three different papers, and I can show the user exactly which ones contributed.

The first time I asked "Who introduced the transformer architecture?" after ingesting five papers and got back `'Vaswani et al.'` with the source correctly attributed to `attention_is_all_you_need` — that was the moment I knew this was working.

---

## How `improve()` Makes It Smarter Over Time

When a user clicks 👍 on an answer, the app calls `improve()` on the papers that contributed to that answer:

```python
# On thumbs-up feedback
for paper_name in papers_cited:
    await cognee.improve(dataset=paper_name)
```

Under the hood, `improve()` runs triplet embedding enrichment — it extracts additional relationships from the graph nodes and strengthens the connections that produced good answers. It's not instant gratification (the graph doesn't visibly change after one click), but over time, with real usage, the answers get more precise.

This is the API I was most curious about. It's the difference between a static retrieval system and one that actually learns from how people use it.

---

## How `forget()` Handles Paper Removal

Clean deletion was something I didn't think about until I tried to remove a paper and realised most RAG systems make this painful — you have to manually track which vectors belong to which document and delete them individually.

Cognee's `forget()` handles it completely:

```python
await cognee.forget(dataset=paper_name)
```

That one call removes the graph nodes, vector embeddings, and dataset record. No orphaned data. In the UI, there's a 🗑️ button next to each paper in the sidebar. Click it, the paper is gone from memory, and subsequent queries won't reference it.

---

## The Demo Moment That Impressed Me Most

I loaded five papers spanning 2017–2022 and asked: *"What is the relationship between attention mechanisms and LoRA's low-rank decomposition?"*

These two papers are five years apart. LoRA never explicitly cites the attention paper in the context of its mathematical formulation. But Cognee's graph had connected the concept of weight matrices in attention heads to LoRA's decomposition of those same matrices — because it had built a graph of the underlying concepts, not just stored the text.

The answer wasn't perfect. But it was directionally correct in a way that pure vector search wouldn't have been, because vector search would have found similar words, not connected ideas.

---

## What I Learned

**The env var order matters more than you'd think.** Cognee uses `lru_cache` for its config, which means everything freezes at import time. You have to set all your environment variables *before* `import cognee`, or your config changes are silently ignored. Burned two hours on this.

**Chunking strategy affects answer quality significantly.** Too-small chunks lose context. Too-large chunks dilute the signal. 500 words with 50-word overlap worked well for academic papers — long enough to capture a complete argument, short enough to be specific.

**Graph-based retrieval is genuinely different from vector search.** Not always better for every query, but for questions about *relationships between concepts*, it surfaces things that similarity search misses entirely.

---

## Try It Yourself

The code is at `[REPO LINK]`. You need a free Groq API key (the LLM) and that's it — everything else runs locally.

```bash
git clone [repo]
cd ChronoResearch
pip install cognee streamlit pymupdf python-dotenv fastembed requests
# Add GROQ_API_KEY to .env
python demo_setup.py   # downloads and ingests 5 papers
streamlit run app.py
```

Then ask it something that spans multiple papers. The first good cross-paper answer you get will make the setup time worth it.

---

*Built for WeMakeDevs "The Hangover Part AI" Hackathon, June–July 2026.*

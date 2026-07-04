import os
from dotenv import load_dotenv

# CRITICAL: env vars must be set before importing cognee (lru_cache freezes config at import)
load_dotenv()

os.environ["SYSTEM_ROOT_DIRECTORY"] = r"C:\ChronoResearch\cognee_data\system"
os.environ["DATA_ROOT_DIRECTORY"] = r"C:\ChronoResearch\cognee_data\data"
os.environ["LLM_PROVIDER"] = "custom"
os.environ["LLM_MODEL"] = "groq/llama-3.3-70b-versatile"
os.environ["LLM_ENDPOINT"] = "https://api.groq.com/openai/v1"
os.environ["LLM_API_KEY"] = os.environ.get("GROQ_API_KEY", "")
os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"
os.environ["EMBEDDING_PROVIDER"] = "fastembed"
os.environ["EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"
os.environ["EMBEDDING_DIMENSIONS"] = "384"

import asyncio
import tempfile
from pathlib import Path

import streamlit as st

from backend.ingestion import ingest_pdf, IngestionStatus
from backend.memory_engine import (
    recall_from_papers,
    improve_memory,
    forget_paper,
    list_papers,
    get_memory_stats,
)


# ---------------------------------------------------------------------------
# Async bridge — Streamlit is sync; backend is async
# ---------------------------------------------------------------------------

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "question_history" not in st.session_state:
    st.session_state.question_history = []  # list of {question, answer, papers, concepts}
if "papers_cache" not in st.session_state:
    st.session_state.papers_cache = None
if "stats_cache" not in st.session_state:
    st.session_state.stats_cache = None


def refresh_sidebar_data():
    st.session_state.papers_cache = run_async(list_papers())
    st.session_state.stats_cache = run_async(get_memory_stats())


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ChronoResearch",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .answer-card {
        background: #f8f9fa;
        border-left: 4px solid #4CAF50;
        padding: 1rem 1.25rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .source-tag {
        display: inline-block;
        background: #e3f2fd;
        color: #1565c0;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        margin: 2px 3px;
    }
    .concept-tag {
        display: inline-block;
        background: #f3e5f5;
        color: #6a1b9a;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        margin: 2px 3px;
    }
    .history-item {
        background: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 0.6rem 0.9rem;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
    .stat-box {
        text-align: center;
        padding: 0.4rem;
    }
    .stat-number {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1565c0;
        line-height: 1.1;
    }
    .stat-label {
        font-size: 0.72rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("ChronoResearch 📚")
    st.caption("Papers That Talk To Each Other")
    st.divider()

    # Load data on first render
    if st.session_state.papers_cache is None:
        with st.spinner("Loading memory..."):
            refresh_sidebar_data()

    papers = st.session_state.papers_cache or []
    stats = st.session_state.stats_cache or {}

    # Memory stats
    if "error" not in stats:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="stat-box"><div class="stat-number">{stats.get("total_papers", 0)}</div>'
                f'<div class="stat-label">Papers</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="stat-box"><div class="stat-number">{stats.get("total_nodes", 0)}</div>'
                f'<div class="stat-label">Nodes</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="stat-box"><div class="stat-number">{stats.get("total_edges", 0)}</div>'
                f'<div class="stat-label">Edges</div></div>',
                unsafe_allow_html=True,
            )
        st.divider()

    # Papers in memory
    st.subheader("📄 Papers in Memory")

    valid_papers = [p for p in papers if "error" not in p]

    if not valid_papers:
        st.info("No papers yet. Upload a PDF to get started.", icon="💡")
    else:
        for paper in valid_papers:
            col_name, col_btn = st.columns([3, 1])
            with col_name:
                st.markdown(f"**{paper['name']}**")
                st.caption(f"{paper['chunk_count']} chunks")
            with col_btn:
                if st.button("🗑️", key=f"forget_{paper['id']}", help=f"Remove {paper['name']}"):
                    with st.spinner(f"Removing {paper['name']}..."):
                        result = run_async(forget_paper(paper["name"]))
                    if result.get("status") == "success":
                        st.success(result["message"])
                        refresh_sidebar_data()
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.get('error', 'Unknown error')}")

    st.divider()

    # Improve Memory button
    if st.button("🧠 Improve Memory", use_container_width=True, type="secondary"):
        if not valid_papers:
            st.warning("No papers in memory to improve.")
        else:
            with st.spinner("Enriching knowledge graph..."):
                # Run improve for each dataset
                results = [run_async(improve_memory(p["name"])) for p in valid_papers]
            completed = sum(1 for r in results if r.get("status") == "completed")
            failed = [r for r in results if r.get("status") == "failed"]
            if failed:
                st.error(f"Improve failed for {len(failed)} paper(s).")
            else:
                st.success(f"Memory enriched across {completed} paper(s).")
            refresh_sidebar_data()
            st.rerun()

    if st.button("🔄 Refresh", use_container_width=True):
        refresh_sidebar_data()
        st.rerun()


# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

tab_upload, tab_ask = st.tabs(["📤 Upload & Learn", "💬 Ask Anything"])


# ── TAB 1: Upload & Learn ──────────────────────────────────────────────────

with tab_upload:
    st.header("Upload a Research Paper")
    st.markdown("Upload a PDF and ChronoResearch will extract the text, chunk it, and build a knowledge graph.")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Supported: any text-based PDF (not scanned images)",
    )

    if uploaded_file is not None:
        st.info(f"**{uploaded_file.name}** — {uploaded_file.size / 1024:.1f} KB", icon="📄")

        if st.button("🚀 Ingest into Memory", type="primary"):
            # Save uploaded bytes to a temp file (PyMuPDF needs a real path)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            progress_bar = st.progress(0, text="Starting ingestion...")
            status_placeholder = st.empty()

            try:
                progress_bar.progress(15, text="Extracting text from PDF...")
                status_placeholder.info("Reading PDF pages...")

                progress_bar.progress(35, text="Chunking text...")
                status_placeholder.info("Splitting into chunks...")

                progress_bar.progress(50, text="Building knowledge graph (this takes a moment)...")
                status_placeholder.info("Sending chunks to Cognee memory...")

                result = run_async(ingest_pdf(tmp_path))

                progress_bar.progress(100, text="Done!")

                if result.status == IngestionStatus.COMPLETED:
                    status_placeholder.empty()
                    st.success(
                        f"✅ **{result.paper_name}** ingested successfully!\n\n"
                        f"- Chunks ingested: **{result.chunks_ingested}**\n"
                        f"- Status: {result.status.value}",
                    )
                    refresh_sidebar_data()
                    st.rerun()
                else:
                    status_placeholder.empty()
                    st.error(f"❌ Ingestion failed: {result.error}")

            finally:
                Path(tmp_path).unlink(missing_ok=True)
                progress_bar.empty()

    else:
        st.markdown("---")
        st.markdown("#### How it works")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**1. Upload**\nDrop any research paper PDF")
        with col2:
            st.markdown("**2. Extract**\nText is pulled from every page")
        with col3:
            st.markdown("**3. Remember**\nCognee builds a knowledge graph")
        with col4:
            st.markdown("**4. Ask**\nQuery across all papers at once")


# ── TAB 2: Ask Anything ───────────────────────────────────────────────────

with tab_ask:
    st.header("Ask Across All Papers")

    valid_papers_ask = [p for p in (st.session_state.papers_cache or []) if "error" not in p]

    if not valid_papers_ask:
        st.warning("No papers in memory yet. Upload a PDF first.", icon="⚠️")
    else:
        st.caption(f"Searching across **{len(valid_papers_ask)}** paper(s) in memory.")

    question = st.text_area(
        "Your question",
        placeholder="Ask a question across all your papers...\n\nExamples:\n• How did attention mechanisms evolve?\n• What are the key differences between BERT and GPT?\n• Which papers discuss transformer scaling laws?",
        height=120,
        label_visibility="collapsed",
    )

    ask_col, _ = st.columns([1, 3])
    with ask_col:
        ask_clicked = st.button("🔍 Ask", type="primary", use_container_width=True, disabled=not question.strip())

    if ask_clicked and question.strip():
        with st.spinner("Searching knowledge graph..."):
            response = run_async(recall_from_papers(question.strip()))

        if "error" in response:
            st.error(f"❌ Query failed: {response['error']}")
        else:
            answer = response.get("answer")
            papers_cited = response.get("papers", [])
            concepts = response.get("related_concepts", [])
            confidence = response.get("confidence", 0.0)

            # Answer card
            if answer:
                st.markdown(
                    f'<div class="answer-card">{answer}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("No answer found. Try rephrasing your question or upload more papers.", icon="🤔")

            # Confidence
            if confidence > 0:
                st.progress(confidence, text=f"Confidence: {confidence:.0%}")

            # Sources and concepts in columns
            if papers_cited or concepts:
                src_col, con_col = st.columns(2)

                with src_col:
                    st.markdown("**📚 Sources**")
                    if papers_cited:
                        tags = "".join(f'<span class="source-tag">{p}</span>' for p in papers_cited)
                        st.markdown(tags, unsafe_allow_html=True)
                    else:
                        st.caption("No specific sources identified.")

                with con_col:
                    st.markdown("**🔗 Related Concepts**")
                    if concepts:
                        tags = "".join(f'<span class="concept-tag">{c}</span>' for c in concepts[:10])
                        st.markdown(tags, unsafe_allow_html=True)
                    else:
                        st.caption("No related concepts found.")

            # Feedback buttons
            st.markdown("---")
            st.caption("Was this answer helpful?")
            fb_col1, fb_col2, _ = st.columns([1, 1, 6])

            with fb_col1:
                if st.button("👍", key=f"up_{len(st.session_state.question_history)}", help="Good answer"):
                    with st.spinner("Improving memory..."):
                        for p in (papers_cited or ["main_dataset"]):
                            run_async(improve_memory(p))
                    st.success("Memory improved!", icon="✨")

            with fb_col2:
                st.button("👎", key=f"down_{len(st.session_state.question_history)}", help="Poor answer")

            # Save to history
            st.session_state.question_history = (
                [{"question": question.strip(), "answer": answer, "papers": papers_cited, "concepts": concepts}]
                + st.session_state.question_history
            )[:5]

    # Recent questions history
    if st.session_state.question_history:
        st.markdown("---")
        st.subheader("🕘 Recent Questions")
        for i, item in enumerate(st.session_state.question_history):
            with st.expander(f"Q: {item['question'][:80]}{'...' if len(item['question']) > 80 else ''}", expanded=(i == 0)):
                if item["answer"]:
                    st.markdown(
                        f'<div class="answer-card">{item["answer"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("No answer returned.")
                if item["papers"]:
                    st.caption("Sources: " + ", ".join(item["papers"]))

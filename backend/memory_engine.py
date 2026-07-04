import cognee
from cognee.api.v1.datasets.datasets import datasets as cognee_datasets


async def recall_from_papers(question: str) -> dict:
    try:
        results = await cognee.recall(question)

        if not results:
            return {
                "answer": None,
                "papers": [],
                "related_concepts": [],
                "confidence": 0.0,
            }

        answer_texts, papers, concepts = [], set(), set()

        for entry in results:
            if hasattr(entry, "text") and entry.text:
                answer_texts.append(entry.text)
            if hasattr(entry, "dataset_name") and entry.dataset_name:
                papers.add(entry.dataset_name)
            if hasattr(entry, "metadata") and isinstance(entry.metadata, dict):
                for v in entry.metadata.values():
                    if isinstance(v, str):
                        concepts.add(v)

        return {
            "answer": " | ".join(answer_texts) if answer_texts else None,
            "papers": list(papers),
            "related_concepts": list(concepts),
            "confidence": min(1.0, len(results) * 0.2),
        }

    except Exception as e:
        return {"error": str(e), "answer": None, "papers": [], "related_concepts": []}


async def improve_memory(dataset: str = "main_dataset") -> dict:
    try:
        result = await cognee.improve(dataset=dataset)
        return {
            "status": "completed",
            "dataset": dataset,
            "nodes_enriched": len(result) if hasattr(result, "__len__") else 0,
        }
    except Exception as e:
        return {"status": "failed", "error": str(e), "nodes_enriched": 0}


async def forget_paper(paper_name: str) -> dict:
    try:
        await cognee.forget(dataset=paper_name)
        return {
            "status": "success",
            "message": f"Paper '{paper_name}' removed from memory.",
        }
    except Exception as e:
        return {"status": "failed", "paper": paper_name, "error": str(e)}


async def list_papers() -> list:
    try:
        all_datasets = await cognee_datasets.list_datasets()
        papers = []
        for ds in all_datasets:
            try:
                data_items = await cognee_datasets.list_data(ds.id)
                chunk_count = len(data_items) if data_items else 0
            except Exception:
                chunk_count = 0

            papers.append({
                "name": ds.name,
                "id": str(ds.id),
                "ingestion_date": ds.created_at.isoformat() if ds.created_at else None,
                "chunk_count": chunk_count,
            })
        return papers
    except Exception as e:
        return [{"error": str(e)}]


async def get_memory_stats() -> dict:
    try:
        all_datasets = await cognee_datasets.list_datasets()

        total_chunks = 0
        for ds in all_datasets:
            try:
                data_items = await cognee_datasets.list_data(ds.id)
                total_chunks += len(data_items) if data_items else 0
            except Exception:
                pass

        from cognee.infrastructure.databases.graph.get_graph_engine import get_graph_engine
        graph_engine = await get_graph_engine()
        nodes = await graph_engine.get_nodes()
        edges = await graph_engine.get_edges()

        return {
            "total_papers": len(all_datasets),
            "total_chunks": total_chunks,
            "total_nodes": len(nodes) if nodes else 0,
            "total_edges": len(edges) if edges else 0,
        }
    except Exception as e:
        return {"error": str(e)}

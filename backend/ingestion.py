import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import cognee


class IngestionStatus(str, Enum):
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IngestionResult:
    paper_name: str
    status: IngestionStatus
    chunks_ingested: int = 0
    nodes_extracted: int = 0
    error: Optional[str] = None


def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        raise ValueError("PDF has no pages.")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    text = text.strip()
    if not text:
        raise ValueError("PDF contains no extractable text.")
    return text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = re.split(r"\s+", text)
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


async def ingest_pdf(pdf_path: str) -> IngestionResult:
    path = Path(pdf_path)
    paper_name = path.stem
    result = IngestionResult(paper_name=paper_name, status=IngestionStatus.STARTED)

    try:
        result.status = IngestionStatus.PROCESSING
        text = extract_text(pdf_path)
        chunks = chunk_text(text)

        for chunk in chunks:
            await cognee.remember(chunk, dataset_name=paper_name)
            result.chunks_ingested += 1

        result.status = IngestionStatus.COMPLETED

    except (FileNotFoundError, fitz.FileDataError) as e:
        result.status = IngestionStatus.FAILED
        result.error = f"PDF error: {e}"
    except ValueError as e:
        result.status = IngestionStatus.FAILED
        result.error = str(e)
    except Exception as e:
        result.status = IngestionStatus.FAILED
        result.error = f"Unexpected error: {e}"

    return result

"""
UniFlow QA Agent — chunking.

Fixed-size sliding window over whitespace-tokenised words. Deliberately
simple: most rule/story documents in knowledge/ are well under one window
and become a single chunk; only the longer synthetic documents (the FAQ,
the draft memos) get split, which is intentional — Week 3 asks us to find
and document a chunking failure, and a document split mid-answer is the
cleanest way to produce one on purpose (see docs/Week3_Failures.md).
"""
from __future__ import annotations

from dataclasses import dataclass

from .ingest import Document

CHUNK_SIZE_WORDS = 70
CHUNK_OVERLAP_WORDS = 20


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    provenance: str
    status: str
    workflow: str
    text: str


def chunk_document(doc: Document, size: int = CHUNK_SIZE_WORDS,
                    overlap: int = CHUNK_OVERLAP_WORDS) -> list[Chunk]:
    words = doc.body.split()
    if not words:
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(words):
        end = min(start + size, len(words))
        idx += 1
        chunks.append(Chunk(
            chunk_id=f"{doc.doc_id}#{idx}",
            doc_id=doc.doc_id,
            title=doc.meta.get("title", doc.doc_id),
            provenance=doc.meta.get("provenance", ""),
            status=doc.meta.get("status", "approved"),
            workflow=doc.meta.get("workflow", ""),
            text=" ".join(words[start:end]),
        ))
        if end == len(words):
            break
        start = end - overlap
    return chunks

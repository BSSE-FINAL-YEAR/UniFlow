"""
UniFlow QA Agent — retrieval entry point.

ingest -> chunk -> index (BM25) -> retrieve(query, k)

The index is a small in-memory structure rebuilt from knowledge/ on first
use. Cheap enough (a few dozen documents) that a persisted index would be
premature optimisation.
"""
from __future__ import annotations

from .chunk import chunk_document
from .index import BM25Index, ScoredChunk
from .ingest import load_corpus

_INDEX: BM25Index | None = None


def build_index() -> BM25Index:
    docs = load_corpus()
    chunks = []
    for doc in docs:
        chunks.extend(chunk_document(doc))
    return BM25Index(chunks)


def get_index(force_rebuild: bool = False) -> BM25Index:
    global _INDEX
    if _INDEX is None or force_rebuild:
        _INDEX = build_index()
    return _INDEX


def retrieve(query: str, k: int = 4) -> list[ScoredChunk]:
    return get_index().search(query, k=k)

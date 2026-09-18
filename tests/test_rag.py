"""
Smoke tests for the Week 3 RAG pipeline. These do NOT call the LLM — they
only check ingestion, chunking and retrieval, so they run offline with no
API key. Run: python -m pytest tests/test_rag.py -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rag.chunk import chunk_document
from rag.ingest import load_corpus
from rag.retrieve import get_index, retrieve


def test_corpus_loads_and_matches_register():
    docs = load_corpus()
    assert len(docs) >= 10
    ids = {d.doc_id for d in docs}
    assert "KB-R04" in ids
    assert "KB-RETAKE-DRAFT" in ids


def test_every_document_produces_at_least_one_chunk():
    docs = load_corpus()
    for doc in docs:
        chunks = chunk_document(doc)
        assert chunks, f"{doc.doc_id} produced no chunks"


def test_long_document_is_split_into_multiple_chunks():
    docs = load_corpus()
    faq = next(d for d in docs if d.doc_id == "KB-REGISTRAR-FAQ")
    assert len(chunk_document(faq)) > 1


def test_index_builds():
    index = get_index(force_rebuild=True)
    assert index.n_docs > 0


def test_retrieve_course_load_question_hits_r04():
    results = retrieve("What is the maximum course load in Year 3?", k=4)
    doc_ids = [r.chunk.doc_id for r in results]
    assert "KB-R04" in doc_ids


def test_retrieve_evening_hours_question_hits_r05():
    # KB-REGISTRAR-FAQ's long, paraphrase-heavy chunk on the 16:00-16:30 gap
    # outranks KB-R05's terse original rule under plain BM25 — a real,
    # documented finding, see docs/Week3_Failures.md Failure 1. Asserting
    # "in the top-k" rather than "ranked first" keeps this a smoke test for
    # the pipeline mechanics, not a claim that ranking quality is perfect.
    results = retrieve("What are the teaching hours for evening classes?", k=5)
    doc_ids = [r.chunk.doc_id for r in results]
    assert "KB-R05" in doc_ids


def test_draft_documents_stay_flagged_unapproved():
    results = retrieve("Can a student retake a failed course?", k=6)
    draft_hits = [r for r in results if r.chunk.doc_id == "KB-RETAKE-DRAFT"]
    assert draft_hits, "expected the draft retake policy to be retrievable"
    assert draft_hits[0].chunk.status == "draft-unapproved"

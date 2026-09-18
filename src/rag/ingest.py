"""
UniFlow QA Agent — corpus ingestion.

Loads every knowledge/**/*.md file, parses its frontmatter, and cross-checks
it against docs/corpus_source_register.csv. A document not listed in the
register cannot enter the index, and a register row with no matching file
fails loudly — the same "two files, always both" discipline Week 2 used for
the rule pack (see RUNBOOK.md step 2). This is what makes provenance
traceable: every retrievable chunk can be traced back to a register row.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
KNOWLEDGE = ROOT / "knowledge"
REGISTER = ROOT / "docs" / "corpus_source_register.csv"


@dataclass
class Document:
    doc_id: str
    path: Path
    meta: dict
    body: str
    register_row: dict


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing frontmatter opening '---'")
    meta: dict = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i]
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        i += 1
    if i >= len(lines):
        raise ValueError("missing frontmatter closing '---'")
    body = "\n".join(lines[i + 1:]).strip()
    return meta, body


def load_register() -> dict[str, dict]:
    if not REGISTER.exists():
        raise FileNotFoundError(f"corpus source register not found: {REGISTER}")
    with REGISTER.open(newline="", encoding="utf-8") as fh:
        return {row["doc_id"]: row for row in csv.DictReader(fh)}


def load_corpus() -> list[Document]:
    register = load_register()
    docs: list[Document] = []
    seen: set[str] = set()

    for path in sorted(KNOWLEDGE.rglob("*.md")):
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        doc_id = meta.get("doc_id")
        if not doc_id:
            raise ValueError(f"{path}: frontmatter missing doc_id")
        if doc_id in seen:
            raise ValueError(f"duplicate doc_id {doc_id!r} ({path})")
        if doc_id not in register:
            raise ValueError(
                f"{path}: doc_id {doc_id!r} is not listed in "
                f"docs/corpus_source_register.csv — register it before it can be indexed"
            )
        seen.add(doc_id)
        docs.append(Document(doc_id=doc_id, path=path, meta=meta, body=body,
                              register_row=register[doc_id]))

    missing = set(register) - seen
    if missing:
        raise ValueError(
            "docs/corpus_source_register.csv lists doc_id(s) with no matching "
            f"knowledge/ file: {sorted(missing)}"
        )
    return docs

"""
UniFlow QA Agent — retrieval index.

Minimal, dependency-free BM25 (Robertson/Sparck-Jones). No external ranking
library: this corpus is small (a few dozen chunks), the formula is about 40
lines, and a hand-rolled implementation is one every team member can read
and defend at the demo rather than a black box import.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .chunk import Chunk

TOKEN_RE = re.compile(r"[a-z0-9]+")

K1 = 1.5
B = 0.75


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class ScoredChunk:
    chunk: Chunk
    score: float


class BM25Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.tokenized = [tokenize(c.text) for c in chunks]
        self.doc_lens = [len(t) for t in self.tokenized]
        self.avgdl = (sum(self.doc_lens) / len(self.doc_lens)) if self.doc_lens else 0.0
        self.n_docs = len(chunks)

        self.df: dict[str, int] = {}
        for tokens in self.tokenized:
            for term in set(tokens):
                self.df[term] = self.df.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        n = self.df.get(term, 0)
        return math.log((self.n_docs - n + 0.5) / (n + 0.5) + 1.0)

    def search(self, query: str, k: int = 4) -> list[ScoredChunk]:
        if not self.chunks:
            return []
        q_terms = tokenize(query)
        scores = [0.0] * self.n_docs

        for i, tokens in enumerate(self.tokenized):
            if not tokens:
                continue
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            dl = self.doc_lens[i]
            score = 0.0
            for term in q_terms:
                freq = tf.get(term)
                if not freq:
                    continue
                idf = self._idf(term)
                denom = freq + K1 * (1 - B + B * dl / (self.avgdl or 1))
                score += idf * (freq * (K1 + 1)) / (denom or 1)
            scores[i] = score

        ranked = sorted(range(self.n_docs), key=lambda i: scores[i], reverse=True)
        return [ScoredChunk(self.chunks[i], scores[i]) for i in ranked[:k]]

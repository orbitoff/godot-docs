"""Explainable query routing over generated knowledge artifacts."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from .extract import STOP_WORDS
from .index import read_jsonl
from .schema import normalize_term, tokenize


class KnowledgeIndex:
    def __init__(self, output: Path, expected_snapshot: str | None = None):
        self.output = output.resolve()
        self.manifest = json.loads((self.output / "manifest.json").read_text(encoding="utf-8"))
        self.snapshot_id = self.manifest["snapshot_id"]
        if expected_snapshot and expected_snapshot != self.snapshot_id:
            raise ValueError(
                f"snapshot mismatch: requested {expected_snapshot}, index is {self.snapshot_id}"
            )
        self.topics = read_jsonl(self.output / "topics.jsonl")
        self.entities = read_jsonl(self.output / "entities.jsonl")
        self.relations = read_jsonl(self.output / "relations.jsonl")
        self.terms = read_jsonl(self.output / "terms.jsonl")
        self.records = {record["id"]: record for record in [*self.topics, *self.entities]}
        self.term_by_value = {record["term"]: record for record in self.terms}
        self.adjacency: dict[str, set[str]] = defaultdict(set)
        for relation in self.relations:
            if relation.get("target_id"):
                self.adjacency[relation["source_id"]].add(relation["target_id"])
                self.adjacency[relation["target_id"]].add(relation["source_id"])

    def search(self, query: str, limit: int = 10) -> dict:
        normalized_query = normalize_term(query)
        query_tokens = {token for token in tokenize(query) if token not in STOP_WORDS}
        scores: dict[str, float] = defaultdict(float)
        reasons: dict[str, list[str]] = defaultdict(list)

        for record in self.terms:
            term = record["term"]
            term_tokens = set(record.get("tokens", []))
            phrase_match = bool(
                term
                and re.search(
                    r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])",
                    normalized_query,
                )
            )
            token_overlap = len(term_tokens & query_tokens)
            if not phrase_match and not token_overlap:
                continue
            overlap_ratio = token_overlap / max(len(term_tokens), 1)
            for candidate in record.get("candidates", []):
                score = float(candidate["weight"])
                if phrase_match:
                    score *= 1.5
                    reasons[candidate["id"]].append(f"{candidate['reason']}: {term}")
                elif token_overlap:
                    score *= 0.45 * overlap_ratio
                    reasons[candidate["id"]].append(
                        f"{candidate['reason']}: {term} ({token_overlap} token match)"
                    )
                scores[candidate["id"]] += score

        base_scores = dict(scores)
        for candidate_id, base_score in base_scores.items():
            related_scores = [
                (base_scores[related_id], related_id)
                for related_id in self.adjacency.get(candidate_id, set())
                if related_id in base_scores
            ]
            if related_scores:
                best_related_score, best_related_id = max(related_scores)
                scores[candidate_id] += min(best_related_score * 0.15, 2.0)
                reasons[candidate_id].append(f"related to {best_related_id}")

        matches = []
        for candidate_id, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:limit]:
            record = self.records.get(candidate_id, {})
            matches.append(
                {
                    "id": candidate_id,
                    "kind": record.get("kind"),
                    "name": record.get("name", record.get("title")),
                    "title": record.get("title", record.get("name")),
                    "source_path": record.get("source_path"),
                    "score": round(score, 4),
                    "reasons": sorted(set(reasons[candidate_id])),
                }
            )

        if not matches:
            status = "no_match"
        elif len(matches) > 1 and matches[1]["score"] >= matches[0]["score"] * 0.8:
            status = "ambiguous"
        else:
            status = "ok"
        return {
            "snapshot_id": self.snapshot_id,
            "query": query,
            "status": status,
            "matches": matches,
        }


__all__ = ["KnowledgeIndex"]

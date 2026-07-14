"""Resolve generated knowledge records into bounded AI context."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .index import read_jsonl

DEFAULT_MAX_CHARS = 32_000
SUPPORTED_ID_PREFIXES = frozenset({"topic", "entity", "member", "chunk"})


@dataclass(frozen=True)
class RetrievalIssue:
    """A retrieval error associated with an optional record ID."""

    code: str
    message: str
    record_id: str | None = None

    def as_dict(self) -> dict[str, str]:
        result = {"code": self.code, "message": self.message}
        if self.record_id is not None:
            result["id"] = self.record_id
        return result


@dataclass
class RetrievalResult:
    """Resolved records and rendering metadata for one retrieval request."""

    snapshot_id: str
    requested_ids: list[str]
    records: list[dict[str, Any]] = field(default_factory=list)
    errors: list[RetrievalIssue] = field(default_factory=list)
    allow_missing: bool = False
    status: str = "ok"
    truncated: bool = False
    omitted_ids: list[str] = field(default_factory=list)
    omitted_characters: int = 0
    max_chars: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "requested_ids": self.requested_ids,
            "status": self.status,
            "truncated": self.truncated,
            "omitted_ids": self.omitted_ids,
            "omitted_characters": self.omitted_characters,
            "records": self.records,
            "errors": [error.as_dict() for error in self.errors],
        }

    def to_json(self) -> str:
        payload = self.as_dict()
        pretty = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if self.max_chars is None or len(pretty) <= self.max_chars:
            return pretty

        compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        if len(compact) <= self.max_chars:
            return compact

        original_records = list(self.records)
        for keep_count in range(len(original_records), -1, -1):
            omitted_records = original_records[keep_count:]
            candidate = dict(payload)
            candidate["records"] = original_records[:keep_count]
            candidate["truncated"] = True
            candidate["status"] = "partial_truncated" if self.errors else "truncated"
            candidate["omitted_ids"] = [
                *self.omitted_ids,
                *(record["id"] for record in omitted_records),
            ]
            candidate["omitted_characters"] = self.omitted_characters + sum(
                len(_format_prompt_record(record)) for record in omitted_records
            )
            compact = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            if len(compact) <= self.max_chars:
                self.records = candidate["records"]
                self.truncated = True
                self.status = candidate["status"]
                self.omitted_ids = candidate["omitted_ids"]
                self.omitted_characters = candidate["omitted_characters"]
                return compact

        raise ValueError(
            f"max_chars={self.max_chars} is too small to encode the retrieval result as JSON"
        )

    def to_prompt(self) -> str:
        if self.status == "error":
            return ""

        lines = [
            "# Godot AI Context",
            "",
            f"Snapshot: `{self.snapshot_id}`",
            f"Requested IDs: {', '.join(f'`{identifier}`' for identifier in self.requested_ids)}",
        ]
        if self.truncated:
            lines.append("Notice: Context was truncated; see JSON metadata for omitted IDs.")
        if self.errors:
            lines.append("Notice: Some requested IDs could not be retrieved; see errors below.")
        lines.append("")

        for record in self.records:
            lines.append(_format_prompt_record(record))

        if self.errors:
            lines.append(_format_prompt_errors(self.errors))

        prompt = "\n".join(lines).rstrip() + "\n"
        if self.max_chars is not None and len(prompt) > self.max_chars:
            prompt = prompt[: self.max_chars]
        return prompt


class KnowledgeRetriever:
    """Load and resolve records from one generated knowledge snapshot."""

    def __init__(self, output: Path, expected_snapshot: str | None = None):
        self.output = output.resolve()
        manifest_path = self.output / "manifest.json"
        try:
            self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ValueError(f"missing knowledge manifest: {manifest_path}") from error
        except json.JSONDecodeError as error:
            raise ValueError(f"{manifest_path}: invalid JSON: {error}") from error

        self.snapshot_id = self.manifest.get("snapshot_id")
        if not isinstance(self.snapshot_id, str) or not self.snapshot_id:
            raise ValueError(f"{manifest_path}: missing snapshot_id")
        if expected_snapshot and expected_snapshot != self.snapshot_id:
            raise ValueError(
                f"snapshot mismatch: requested {expected_snapshot}, index is {self.snapshot_id}"
            )

        self._records: dict[str, dict[str, Any]] = {}
        self._invalid_records: dict[str, RetrievalIssue] = {}
        self._index_dataset("topics.jsonl")
        self._index_dataset("entities.jsonl")
        self._chunks: dict[str, dict[str, Any]] | None = None

    def retrieve(
        self,
        identifiers: Iterable[str],
        *,
        max_chars: int = DEFAULT_MAX_CHARS,
        allow_missing: bool = False,
    ) -> RetrievalResult:
        """Resolve identifiers and apply the configured content budget."""

        if max_chars <= 0:
            raise ValueError("max_chars must be greater than zero")

        requested_ids = _deduplicate(identifiers)
        errors: list[RetrievalIssue] = []
        records: list[dict[str, Any]] = []
        seen_record_ids: set[str] = set()

        for identifier in requested_ids:
            record, issue = self._resolve(identifier)
            if issue is not None:
                errors.append(issue)
                continue
            self._append_record(record, records, seen_record_ids)

            if record.get("kind") != "topic":
                continue
            for chunk_identifier in record.get("chunk_ids", []):
                chunk, chunk_issue = self._resolve(chunk_identifier)
                if chunk_issue is not None:
                    errors.append(
                        RetrievalIssue(
                            "missing_chunk",
                            f"{identifier} references {chunk_issue.message}",
                            chunk_identifier,
                        )
                    )
                    continue
                self._append_record(chunk, records, seen_record_ids)

        errors = _deduplicate_issues(errors)
        if errors and not allow_missing:
            return RetrievalResult(
                snapshot_id=self.snapshot_id,
                requested_ids=requested_ids,
                errors=errors,
                allow_missing=False,
                status="error",
                max_chars=max_chars,
            )

        result = RetrievalResult(
            snapshot_id=self.snapshot_id,
            requested_ids=requested_ids,
            records=[_normalize_record(record) for record in records],
            errors=errors,
            allow_missing=allow_missing,
            status="partial" if errors else "ok",
            max_chars=max_chars,
        )
        _apply_budget(result, max_chars)
        return result

    def _index_dataset(self, filename: str) -> None:
        for record in read_jsonl(self.output / filename):
            identifier = record.get("id")
            if not isinstance(identifier, str) or not identifier:
                continue
            if record.get("snapshot_id") != self.snapshot_id:
                self._invalid_records[identifier] = RetrievalIssue(
                    "snapshot_mismatch",
                    f"record snapshot is {record.get('snapshot_id')!r}, "
                    f"expected {self.snapshot_id!r}",
                    identifier,
                )
                continue
            if identifier in self._records:
                self._invalid_records[identifier] = RetrievalIssue(
                    "duplicate_id",
                    "record ID appears in more than one artifact",
                    identifier,
                )
                self._records.pop(identifier, None)
                continue
            self._records[identifier] = record

    def _load_chunks(self) -> None:
        if self._chunks is not None:
            return
        self._chunks = {}
        for record in read_jsonl(self.output / "chunks.jsonl"):
            identifier = record.get("id")
            if not isinstance(identifier, str) or not identifier:
                continue
            if record.get("snapshot_id") != self.snapshot_id:
                self._invalid_records[identifier] = RetrievalIssue(
                    "snapshot_mismatch",
                    f"record snapshot is {record.get('snapshot_id')!r}, "
                    f"expected {self.snapshot_id!r}",
                    identifier,
                )
                continue
            if identifier in self._records or identifier in self._chunks:
                self._invalid_records[identifier] = RetrievalIssue(
                    "duplicate_id",
                    "record ID appears in more than one artifact",
                    identifier,
                )
                self._chunks.pop(identifier, None)
                self._records.pop(identifier, None)
                continue
            self._chunks[identifier] = record

    def _resolve(self, identifier: str) -> tuple[dict[str, Any] | None, RetrievalIssue | None]:
        issue = _validate_identifier(identifier)
        if issue is not None:
            return None, issue

        prefix = identifier.split(":", 1)[0]
        if prefix == "chunk":
            self._load_chunks()
            assert self._chunks is not None
            record = self._chunks.get(identifier)
        else:
            record = self._records.get(identifier)

        if record is not None:
            return record, None
        if identifier in self._invalid_records:
            return None, self._invalid_records[identifier]
        return None, RetrievalIssue("unknown_id", "ID is not present in the knowledge index", identifier)

    @staticmethod
    def _append_record(
        record: dict[str, Any],
        records: list[dict[str, Any]],
        seen_record_ids: set[str],
    ) -> None:
        identifier = record["id"]
        if identifier in seen_record_ids:
            return
        seen_record_ids.add(identifier)
        records.append(record)


def _validate_identifier(identifier: str) -> RetrievalIssue | None:
    if not isinstance(identifier, str) or not identifier or any(
        character in identifier for character in "\r\n"
    ):
        return RetrievalIssue("malformed_id", "ID must be a non-empty single-line string", identifier)
    prefix, separator, suffix = identifier.partition(":")
    if not separator or prefix not in SUPPORTED_ID_PREFIXES or not suffix:
        return RetrievalIssue(
            "unsupported_id",
            "only topic:, entity:, member:, and chunk: IDs can be retrieved",
            identifier,
        )
    return None


def _deduplicate(identifiers: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for identifier in identifiers:
        if identifier in seen:
            continue
        seen.add(identifier)
        result.append(identifier)
    return result


def _deduplicate_issues(issues: Iterable[RetrievalIssue]) -> list[RetrievalIssue]:
    result: list[RetrievalIssue] = []
    seen: set[tuple[str, str | None]] = set()
    for issue in issues:
        key = (issue.code, issue.record_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(issue)
    return result


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    kind = record.get("kind", "unknown")
    title = record.get("title") or record.get("name")
    if kind == "detail_chunk":
        title = (record.get("heading_path") or [record.get("topic_id") or record["id"]])[-1]

    excluded = {
        "id",
        "kind",
        "title",
        "name",
        "source_path",
        "source_hash",
        "snapshot_id",
        "heading_path",
        "summary",
        "description",
        "signature",
        "text",
    }
    metadata = {key: value for key, value in record.items() if key not in excluded}
    if "heading_path" in record:
        metadata["heading_path"] = record["heading_path"]
    if "signature" in record:
        metadata["signature"] = record["signature"]

    if kind == "detail_chunk":
        content = record.get("text", "")
    elif kind in {"method", "property", "signal", "constant", "enum", "annotation", "theme_icon", "theme_style", "theme_constant", "theme_font", "theme_font_size"}:
        signature = record.get("signature", "")
        description = record.get("description", "")
        content = "\n\n".join(part for part in (signature, description) if part)
    else:
        content = record.get("summary", "")

    return {
        "id": record["id"],
        "kind": kind,
        "title": title,
        "name": record.get("name"),
        "source_path": record.get("source_path"),
        "source_hash": record.get("source_hash"),
        "snapshot_id": record.get("snapshot_id"),
        "content": content,
        "metadata": metadata,
    }


def _format_prompt_record(record: dict[str, Any]) -> str:
    kind = record["kind"]
    if kind == "topic":
        label = "Topic"
    elif kind == "class":
        label = "API entity"
    elif kind == "detail_chunk":
        label = "Detail chunk"
    else:
        label = "API member"

    lines = [
        f"<!-- BEGIN GODOT KNOWLEDGE RECORD: {record['id']} -->",
        f"## {label}: {record.get('title') or record['id']}",
        "",
        f"ID: `{record['id']}`",
        f"Kind: `{kind}`",
    ]
    if record.get("source_path"):
        lines.append(f"Source: `{record['source_path']}`")
    if record.get("source_hash"):
        lines.append(f"Source hash: `{record['source_hash']}`")
    if kind == "detail_chunk":
        heading_path = record.get("metadata", {}).get("heading_path", [])
        if heading_path:
            lines.append(f"Heading: {' > '.join(heading_path)}")

    metadata = record.get("metadata", {})
    if kind == "class":
        if metadata.get("inherits"):
            lines.append(f"Inherits: {', '.join(metadata['inherits'])}")
        if metadata.get("members"):
            lines.append(f"Members: {', '.join(metadata['members'])}")
    elif kind not in {"topic", "detail_chunk"}:
        if metadata.get("owner"):
            lines.append(f"Owner: `{metadata['owner']}`")
        if metadata.get("signature"):
            lines.append(f"Signature: `{metadata['signature']}`")

    content = record.get("content", "")
    if content:
        lines.extend(["", "Content:", "", content])
    lines.extend(["", f"<!-- END GODOT KNOWLEDGE RECORD: {record['id']} -->", ""])
    return "\n".join(lines)


def _format_prompt_errors(errors: list[RetrievalIssue]) -> str:
    lines = [
        "## Retrieval errors",
        "",
        "The following requested records were not included:",
        "",
    ]
    lines.extend(f"- `{error.record_id or '<request>'}`: {error.message}" for error in errors)
    lines.append("")
    return "\n".join(lines)


def _apply_budget(result: RetrievalResult, max_chars: int) -> None:
    result.max_chars = max_chars
    header = "\n".join(
        [
            "# Godot AI Context",
            "",
            f"Snapshot: `{result.snapshot_id}`",
            f"Requested IDs: {', '.join(f'`{identifier}`' for identifier in result.requested_ids)}",
            "",
        ]
    )
    truncation_notice = "Notice: Context was truncated; see JSON metadata for omitted IDs.\n"
    partial_notice = (
        "Notice: Some requested IDs could not be retrieved; see errors below.\n"
        if result.errors
        else ""
    )
    remaining = (
        max_chars
        - len(header)
        - len(truncation_notice)
        - len(partial_notice)
        - len(_format_prompt_errors(result.errors))
    )
    selected: list[dict[str, Any]] = []
    omitted_ids: list[str] = []
    omitted_characters = 0

    for index, record in enumerate(result.records):
        section = _format_prompt_record(record)
        if len(section) <= remaining:
            selected.append(record)
            remaining -= len(section)
            continue

        content = record.get("content", "")
        marker = "\n\n[Content truncated to fit the retrieval character budget.]"
        static_record = dict(record)
        static_record["content"] = ""
        static_length = len(_format_prompt_record(static_record))
        available = max(0, remaining - static_length - len(marker))
        if content and available:
            clipped = dict(record)
            clipped["content"] = content[:available] + marker
            clipped_section = _format_prompt_record(clipped)
            while len(clipped_section) > remaining and available > 0:
                available -= len(clipped_section) - remaining
                clipped["content"] = content[:available] + marker
                clipped_section = _format_prompt_record(clipped)
            if len(clipped_section) <= remaining:
                selected.append(clipped)
                omitted_characters += max(0, len(section) - len(clipped_section))
                remaining -= len(clipped_section)
            else:
                omitted_characters += len(section)
                omitted_ids.append(record["id"])
        else:
            omitted_characters += len(section)
            omitted_ids.append(record["id"])

        for omitted in result.records[index + 1 :]:
            omitted_ids.append(omitted["id"])
            omitted_characters += len(_format_prompt_record(omitted))
        break

    result.records = selected
    result.omitted_ids = omitted_ids
    result.omitted_characters = omitted_characters
    result.truncated = bool(omitted_ids or omitted_characters)
    if result.truncated:
        result.status = "partial_truncated" if result.errors else "truncated"


__all__ = [
    "DEFAULT_MAX_CHARS",
    "KnowledgeRetriever",
    "RetrievalIssue",
    "RetrievalResult",
]

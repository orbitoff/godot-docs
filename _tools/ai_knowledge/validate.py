"""Validation for generated knowledge artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import ARTIFACT_FILES, SCHEMA_VERSION
from .index import read_jsonl


def validate(output: Path, root: Path | None = None) -> list[str]:
    output = output.resolve()
    root = (root or output.parent).resolve()
    errors: list[str] = []
    manifest_path = output / "manifest.json"
    if not manifest_path.exists():
        return [f"missing {manifest_path}"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"{manifest_path}: invalid JSON: {error}"]

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"manifest schema_version is {manifest.get('schema_version')!r}, expected {SCHEMA_VERSION!r}"
        )
    for artifact in ARTIFACT_FILES:
        if not (output / artifact).exists():
            errors.append(f"missing artifact: {artifact}")

    try:
        taxonomy = json.loads((output / "taxonomy.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        taxonomy = {}
        errors.append(f"taxonomy.json: invalid JSON: {error}")

    datasets = {
        "topics": read_jsonl(output / "topics.jsonl"),
        "entities": read_jsonl(output / "entities.jsonl"),
        "relations": read_jsonl(output / "relations.jsonl"),
        "terms": read_jsonl(output / "terms.jsonl"),
        "chunks": read_jsonl(output / "chunks.jsonl"),
    }
    all_ids = set()
    source_ids = set()
    snapshot_id = manifest.get("snapshot_id")
    for name, records in datasets.items():
        for record in records:
            identifier = record.get("id")
            if not identifier:
                errors.append(f"{name}: record without id")
            elif identifier in all_ids:
                errors.append(f"duplicate record id: {identifier}")
            else:
                all_ids.add(identifier)
            if record.get("snapshot_id") != snapshot_id:
                errors.append(f"{name}:{identifier}: snapshot_id mismatch")

    counts = manifest.get("counts", {})
    expected_counts = {
        "topics": len(datasets["topics"]),
        "entities": len(datasets["entities"]),
        "members": sum(1 for record in datasets["entities"] if record.get("kind") != "class"),
        "classes": sum(1 for record in datasets["entities"] if record.get("kind") == "class"),
        "relations": len(datasets["relations"]),
        "terms": len(datasets["terms"]),
        "chunks": len(datasets["chunks"]),
    }
    for key, actual in expected_counts.items():
        if counts.get(key) != actual:
            errors.append(f"manifest count {key}={counts.get(key)!r}, expected {actual}")

    for file_record in manifest.get("files", []):
        relative = file_record.get("path")
        if not relative:
            errors.append("manifest file without path")
            continue
        source_path = root / Path(*relative.split("/"))
        source_ids.add("source:" + relative)
        if not source_path.exists():
            errors.append(f"missing source: {relative}")
            continue
        actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual_hash != file_record.get("source_hash"):
            errors.append(f"stale source hash: {relative}")

    topic_sources = {record.get("source_path") for record in datasets["topics"]}
    entity_sources = {
        record.get("source_path")
        for record in datasets["entities"]
        if record.get("kind") == "class"
    }
    for file_record in manifest.get("files", []):
        relative = file_record.get("path")
        if file_record.get("kind") == "topic" and relative not in topic_sources:
            errors.append(f"source page missing topic record: {relative}")
        if file_record.get("kind") == "entity" and relative not in entity_sources:
            errors.append(f"class source missing entity record: {relative}")

    valid_targets = all_ids | source_ids
    for relation in datasets["relations"]:
        target_id = relation.get("target_id")
        status = relation.get("resolution_status")
        if target_id and target_id not in valid_targets:
            errors.append(f"relation {relation.get('id')} targets unknown id {target_id}")
        if status == "unresolved":
            errors.append(
                f"unresolved internal reference {relation.get('raw_target')!r} "
                f"from {relation.get('source_path')}:{relation.get('line')}"
            )
        if status in {"external", "builtin"} and target_id:
            errors.append(f"relation {relation.get('id')} has target with {status} status")

    topic_ids = {record["id"] for record in datasets["topics"]}
    chunk_ids = {record["id"] for record in datasets["chunks"]}
    entity_ids = {record["id"] for record in datasets["entities"]}
    for topic in datasets["topics"]:
        for chunk_id in topic.get("chunk_ids", []):
            if chunk_id not in chunk_ids:
                errors.append(f"topic {topic['id']} references missing chunk {chunk_id}")
        for related_id in topic.get("related_ids", []):
            if related_id not in valid_targets:
                errors.append(f"topic {topic['id']} references unknown related id {related_id}")
    for entity in datasets["entities"]:
        if entity.get("kind") == "class":
            for member_id in entity.get("members", []):
                if member_id not in entity_ids:
                    errors.append(f"class {entity['id']} references missing member {member_id}")

    if taxonomy.get("snapshot_id") != snapshot_id:
        errors.append("taxonomy snapshot_id mismatch")
    if len(taxonomy.get("pages", [])) != len(manifest.get("files", [])):
        errors.append("taxonomy page count does not match manifest file count")
    if len(topic_ids) != len(datasets["topics"]):
        errors.append("duplicate topic IDs")

    return sorted(set(errors))


__all__ = ["validate"]

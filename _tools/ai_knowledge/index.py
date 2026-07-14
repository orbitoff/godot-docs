"""Build the versioned Godot documentation knowledge index."""

from __future__ import annotations

import json
import os
import posixpath
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Any

from . import ARTIFACT_FILES, GENERATOR_VERSION, SCHEMA_VERSION
from .extract import (
    ParsedPage,
    STOP_WORDS,
    class_member_label,
    discover_pages,
    page_keywords,
    page_summary,
    parse_class_entities,
    section_chunks,
)
from .schema import (
    chunk_id,
    entity_id,
    member_id,
    normalize_term,
    relation_id,
    source_id,
    tokenize,
    topic_id,
)

DEFAULT_ALIASES = {
    "user interface": ("ui",),
    "multiplayer": ("networking",),
    "network play": ("networking",),
    "gamepad": ("joypad",),
    "controller": ("joypad",),
    "two dimensional": ("2d",),
    "three dimensional": ("3d",),
    "shader programming": ("shaders",),
    "visual scripting": ("visualshader",),
}

BUILTIN_TARGETS = {
    "class_bool",
    "class_callable",
    "class_float",
    "class_int",
    "class_nil",
    "class_string",
    "class_stringname",
    "class_variant",
    "class_void",
}

INTERNAL_ROLES = {
    "attr",
    "class",
    "const",
    "doc",
    "enum",
    "func",
    "member",
    "meth",
    "prop",
    "ref",
    "signal",
}


def json_dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def jsonl_dump(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSONL: {error}") from error
    return records


def run_git(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def detect_version(root: Path) -> str:
    conf = root / "conf.py"
    if conf.exists():
        match = re.search(r'version\s*=\s*.*?"(?P<version>[0-9]+\.[0-9]+)"', conf.read_text(encoding="utf-8"))
        if match:
            return match.group("version")
    index = root / "index.rst"
    if index.exists():
        match = re.search(r"Godot Docs.*?([0-9]+\.[0-9]+)", index.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return "unknown"


def snapshot_metadata(root: Path) -> dict:
    version = detect_version(root)
    commit = run_git(root, "rev-parse", "HEAD")
    branch = run_git(root, "branch", "--show-current")
    snapshot_id = f"godot-{version}@{commit}"
    return {
        "project": "Godot Engine",
        "version": version,
        "branch": branch,
        "commit": commit,
        "snapshot_id": snapshot_id,
    }


class DocumentGraph:
    def __init__(self, pages: list[ParsedPage]):
        self.pages = {page.path: page for page in pages}
        self.aliases: dict[str, str] = {}
        self.labels: dict[str, str] = {}
        self.labels_lower: dict[str, str] = {}
        self.topic_paths: dict[str, str] = {}
        self.toctree_edges: list[tuple[str, str, int]] = []
        self.parents: dict[str, set[str]] = defaultdict(set)
        self.children: dict[str, set[str]] = defaultdict(set)
        self.reachable: set[str] = set()
        self._build_aliases()

    def _build_aliases(self) -> None:
        for path in self.pages:
            no_extension = str(PurePosixPath(path).with_suffix(""))
            aliases = {path, no_extension}
            if PurePosixPath(path).name == "index.rst":
                aliases.add(str(PurePosixPath(path).parent))
            for alias in aliases:
                self.aliases[normalize_path(alias)] = path

    def _build_toctree(self) -> None:
        for page in self.pages.values():
            for entry in page.toctree_entries:
                target = self.resolve_document(entry["target"], page.path)
                if target is None:
                    continue
                self.toctree_edges.append((page.path, target, entry["line"]))
                self.parents[target].add(page.path)
                self.children[page.path].add(target)

        root = "index.rst" if "index.rst" in self.pages else next(iter(self.pages), None)
        if root is None:
            return
        pending = [root]
        while pending:
            current = pending.pop()
            if current in self.reachable:
                continue
            self.reachable.add(current)
            pending.extend(sorted(self.children.get(current, ()), reverse=True))

    def _build_labels(self, topic_ids: dict[str, str], entity_labels: dict[str, str]) -> None:
        for page in self.pages.values():
            target_id = topic_ids.get(page.path)
            if target_id:
                for label in page.labels:
                    self.labels[label["label"]] = target_id
        self.labels.update(entity_labels)
        self.labels_lower = {label.lower(): identifier for label, identifier in self.labels.items()}

    def prepare(self, topic_ids: dict[str, str], entity_labels: dict[str, str]) -> None:
        self._build_toctree()
        self._build_labels(topic_ids, entity_labels)

    def resolve_document(self, value: str, current_path: str) -> str | None:
        value = value.strip().split("#", 1)[0]
        if not value or value.startswith(("http://", "https://", "mailto:")):
            return None
        value = value.replace("\\", "/")
        candidates = []
        if value.startswith("/"):
            candidates.append(value[1:])
        else:
            parent = str(PurePosixPath(current_path).parent)
            candidates.append(posixpath.join(parent, value))
            candidates.append(value)
        for candidate in candidates:
            normalized = normalize_path(candidate)
            if normalized in self.aliases:
                return self.aliases[normalized]
            if normalized + ".rst" in self.aliases:
                return self.aliases[normalized + ".rst"]
            if normalized.endswith("/index"):
                directory = normalized[: -len("/index")].rstrip("/")
                if directory in self.aliases:
                    return self.aliases[directory]
        return None


def normalize_path(value: str) -> str:
    value = value.replace("\\", "/")
    value = posixpath.normpath(value).lstrip("./")
    if value == ".":
        return ""
    return value


def source_record(page: ParsedPage, graph: DocumentGraph) -> dict:
    return {
        "id": page.source_id,
        "path": page.path,
        "kind": page.kind,
        "source_hash": page.sha256,
        "in_toctree": bool(graph.parents.get(page.path)) or page.path == "index.rst",
        "reachable": page.path in graph.reachable,
        "orphan": page.path not in graph.reachable,
    }


def topic_records(
    pages: list[ParsedPage],
    graph: DocumentGraph,
    snapshot_id: str,
) -> tuple[list[dict], list[dict]]:
    topics: list[dict] = []
    chunks: list[dict] = []
    for page in pages:
        if page.kind != "topic":
            continue
        identifier = topic_id(page.path)
        page_chunks = section_chunks(page)
        chunk_ids: list[str] = []
        for ordinal, chunk in enumerate(page_chunks):
            identifier_for_chunk = chunk_id(identifier, ordinal)
            chunk_ids.append(identifier_for_chunk)
            chunks.append(
                {
                    "id": identifier_for_chunk,
                    "kind": "detail_chunk",
                    "snapshot_id": snapshot_id,
                    "topic_id": identifier,
                    "source_path": page.path,
                    "source_hash": page.sha256,
                    "heading_path": chunk["heading_path"],
                    "line_start": chunk["line_start"],
                    "line_end": chunk["line_end"],
                    "part": chunk["part"],
                    "text": chunk["text"],
                }
            )
        topics.append(
            {
                "id": identifier,
                "kind": "topic",
                "snapshot_id": snapshot_id,
                "title": page.title,
                "source_path": page.path,
                "source_hash": page.sha256,
                "summary": page_summary(page),
                "keywords": page_keywords(page),
                "headings": [
                    {
                        "title": heading["title"],
                        "level": heading["level"],
                        "line": heading["line"],
                    }
                    for heading in page.headings
                ],
                "labels": sorted(label["label"] for label in page.labels),
                "code_blocks": page.code_blocks,
                "parent_ids": sorted(topic_id(parent) for parent in graph.parents.get(page.path, ())),
                "child_ids": sorted(topic_id(child) for child in graph.children.get(page.path, ()) if graph.pages[child].kind == "topic"),
                "reachable": page.path in graph.reachable,
                "orphan": page.path not in graph.reachable,
                "chunk_ids": chunk_ids,
                "related_ids": [],
            }
        )
    return sorted(topics, key=lambda item: item["id"]), sorted(chunks, key=lambda item: item["id"])


def entity_records(
    pages: list[ParsedPage],
    snapshot_id: str,
) -> tuple[list[dict], list[dict], dict[str, str], dict[str, str]]:
    entities: list[dict] = []
    members: list[dict] = []
    labels: dict[str, str] = {}
    names: dict[str, str] = {}
    for page in pages:
        if page.kind != "entity":
            continue
        entity, page_members = parse_class_entities(page)
        entity["snapshot_id"] = snapshot_id
        entity["inherits"] = [entity_id(name) for name in entity["inherits"]]
        entity["inherited_by"] = [entity_id(name) for name in entity["inherited_by"]]
        entities.append(entity)
        names[normalize_term(entity["name"])] = entity["id"]
        for label in entity["labels"]:
            labels[label] = entity["id"]
        for member in page_members:
            member["snapshot_id"] = snapshot_id
            members.append(member)
            labels[member["label"]] = member["id"]
            names[normalize_term(f"{entity['name']} {member['name']}")] = member["id"]
    entities.extend(members)
    entities.sort(key=lambda item: item["id"])
    return entities, members, labels, names


def resolve_reference(
    page: ParsedPage,
    reference: dict,
    graph: DocumentGraph,
    entity_names: dict[str, str],
) -> tuple[str | None, str]:
    target = reference["target"]
    role = reference["role"]
    if target.startswith(("http://", "https://", "mailto:")):
        return None, "external"
    if target in graph.labels:
        return graph.labels[target], "resolved"
    if target.lower() in graph.labels_lower:
        return graph.labels_lower[target.lower()], "resolved"
    if role == "doc":
        document = graph.resolve_document(target, page.path)
        if document:
            return topic_id(document), "resolved"
    normalized_target = normalize_term(target)
    if normalized_target in entity_names:
        return entity_names[normalized_target], "resolved"
    if target.startswith("doc_"):
        compact_target = normalize_term(target[4:]).replace(" ", "")
        for candidate, identifier in entity_names.items():
            if candidate.startswith("doc ") and candidate[4:].replace(" ", "") == compact_target:
                return identifier, "resolved"
    if target.lower() in BUILTIN_TARGETS:
        return None, "builtin"
    if target.startswith(("class_", "enum_", "doc_")):
        return None, "unresolved"
    if role == "ref":
        return None, "unresolved"
    return None, "external"


def add_relation(
    relations: list[dict],
    seen: set[tuple[str, str, str, str]],
    source: str,
    relation_type: str,
    target: str | None,
    source_path: str,
    source_hash: str,
    snapshot_id: str,
    raw_target: str | None = None,
    status: str = "resolved",
    line: int | None = None,
) -> None:
    target_key = target or raw_target or ""
    key = (source, relation_type, target_key, status)
    if key in seen:
        return
    seen.add(key)
    ordinal = sum(
        1
        for relation in relations
        if relation["source_id"] == source and relation["relation_type"] == relation_type
    )
    relations.append(
        {
            "id": relation_id(source, relation_type, target_key, ordinal),
            "kind": "relation",
            "snapshot_id": snapshot_id,
            "source_id": source,
            "source_path": source_path,
            "source_hash": source_hash,
            "relation_type": relation_type,
            "target_id": target,
            "raw_target": raw_target,
            "resolution_status": status,
            "line": line,
        }
    )


def build_relations(
    pages: list[ParsedPage],
    graph: DocumentGraph,
    entities: list[dict],
    members: list[dict],
    snapshot_id: str,
) -> list[dict]:
    entity_names = {
        normalize_term(item["name"]): item["id"]
        for item in entities
        if item["kind"] == "class"
    }
    class_by_id = {item["id"]: item for item in entities if item["kind"] == "class"}
    for item in class_by_id.values():
        entity_names["doc " + normalize_term(item["name"])] = item["id"]
    for item in members:
        owner = class_by_id.get(item["owner"])
        if owner:
            entity_names[normalize_term(f"{owner['name']} {item['name']}")] = item["id"]
    relations: list[dict] = []
    seen: set[tuple[str, str, str, str]] = set()
    for source_path, target_path, line in graph.toctree_edges:
        source_page = graph.pages[source_path]
        add_relation(
            relations,
            seen,
            topic_id(source_path) if source_page.kind == "topic" else source_id(source_path),
            "toctree",
            topic_id(target_path) if graph.pages[target_path].kind == "topic" else source_id(target_path),
            source_path,
            source_page.sha256,
            snapshot_id,
            raw_target=target_path,
            line=line,
        )

    for entity in class_by_id.values():
        source = entity["id"]
        for target in entity["inherits"]:
            add_relation(
                relations,
                seen,
                source,
                "inherits",
                target if target in class_by_id else None,
                entity["source_path"],
                entity["source_hash"],
                snapshot_id,
                raw_target=target,
                status="resolved" if target in class_by_id else "unresolved",
            )
        for target in entity["inherited_by"]:
            add_relation(
                relations,
                seen,
                source,
                "inherited_by",
                target if target in class_by_id else None,
                entity["source_path"],
                entity["source_hash"],
                snapshot_id,
                raw_target=target,
                status="resolved" if target in class_by_id else "unresolved",
            )

    for page in pages:
        source = topic_id(page.path) if page.kind == "topic" else source_id(page.path)
        for reference in page.refs:
            target, status = resolve_reference(page, reference, graph, entity_names)
            relation_type = reference["role"]
            if target is None and status == "external":
                continue
            add_relation(
                relations,
                seen,
                source,
                relation_type,
                target,
                page.path,
                page.sha256,
                snapshot_id,
                raw_target=reference["target"],
                status=status,
                line=reference["line"],
            )
    return sorted(relations, key=lambda item: item["id"])


def add_term(
    term_candidates: dict[str, dict[str, dict]],
    value: str,
    candidate_id: str,
    weight: float,
    reason: str,
) -> None:
    normalized = normalize_term(value)
    tokens = tokenize(normalized)
    if not tokens or all(token in STOP_WORDS or len(token) < 2 for token in tokens):
        return
    if len(tokens) == 1 and len(tokens[0]) < 2:
        return
    current = term_candidates[normalized].get(candidate_id)
    if current is None or weight > current["weight"]:
        term_candidates[normalized][candidate_id] = {
            "id": candidate_id,
            "weight": weight,
            "reason": reason,
        }


def build_terms(
    topics: list[dict],
    entities: list[dict],
    relations: list[dict],
    snapshot_id: str,
) -> list[dict]:
    candidates: dict[str, dict[str, dict]] = defaultdict(dict)
    for topic in topics:
        add_term(candidates, topic["title"], topic["id"], 10.0, "title")
        for keyword in topic["keywords"]:
            add_term(candidates, keyword, topic["id"], 3.0, "keyword")
        for label in topic["labels"]:
            add_term(candidates, label, topic["id"], 5.0, "label")
    for entity in entities:
        if entity["kind"] == "class":
            add_term(candidates, entity["name"], entity["id"], 12.0, "class_name")
            add_term(candidates, entity["title"], entity["id"], 8.0, "title")
        else:
            add_term(candidates, entity["name"], entity["id"], 11.0, "member_name")
            add_term(candidates, f"{entity['owner']} {entity['name']}", entity["id"], 12.0, "qualified_name")
            add_term(candidates, entity["kind"], entity["id"], 2.0, "member_kind")
            add_term(candidates, entity["label"], entity["id"], 10.0, "label")

    for alias, canonical_terms in DEFAULT_ALIASES.items():
        for canonical in canonical_terms:
            for candidate_id, match in candidates.get(normalize_term(canonical), {}).items():
                add_term(candidates, alias, candidate_id, match["weight"] - 1.0, "curated_alias")

    related: dict[str, set[str]] = defaultdict(set)
    for relation in relations:
        if relation["target_id"]:
            related[relation["source_id"]].add(relation["target_id"])
            related[relation["target_id"]].add(relation["source_id"])

    records = []
    for term in sorted(candidates):
        matches = sorted(
            candidates[term].values(),
            key=lambda item: (-item["weight"], item["id"]),
        )
        records.append(
            {
                "id": "term:" + term,
                "kind": "term",
                "snapshot_id": snapshot_id,
                "term": term,
                "tokens": tokenize(term),
                "candidates": matches,
            }
        )
    return records


def attach_related_ids(
    topics: list[dict],
    entities: list[dict],
    relations: list[dict],
) -> None:
    related: dict[str, set[str]] = defaultdict(set)
    for relation in relations:
        if relation["target_id"]:
            related[relation["source_id"]].add(relation["target_id"])
            related[relation["target_id"]].add(relation["source_id"])
    for record in topics:
        record["related_ids"] = sorted(related[record["id"]])


def previous_changes(output: Path, pages: list[ParsedPage]) -> dict:
    manifest_path = output / "manifest.json"
    if not manifest_path.exists():
        return {"added": sorted(page.path for page in pages), "removed": [], "changed": [], "unchanged": []}
    try:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"added": sorted(page.path for page in pages), "removed": [], "changed": [], "unchanged": []}
    old_hashes = {item["path"]: item.get("source_hash") for item in old.get("files", [])}
    current_hashes = {page.path: page.sha256 for page in pages}
    return {
        "added": sorted(set(current_hashes) - set(old_hashes)),
        "removed": sorted(set(old_hashes) - set(current_hashes)),
        "changed": sorted(
            path for path in set(current_hashes) & set(old_hashes) if current_hashes[path] != old_hashes[path]
        ),
        "unchanged": sorted(
            path for path in set(current_hashes) & set(old_hashes) if current_hashes[path] == old_hashes[path]
        ),
    }


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def generate(root: Path, output: Path, incremental: bool = False) -> dict:
    root = root.resolve()
    output = output.resolve()
    pages = discover_pages(root)
    metadata = snapshot_metadata(root)
    snapshot_id = metadata["snapshot_id"]
    graph = DocumentGraph(pages)
    topic_ids = {page.path: topic_id(page.path) for page in pages if page.kind == "topic"}
    entities, members, entity_labels, _ = entity_records(pages, snapshot_id)
    graph.prepare(topic_ids, entity_labels)
    topics, chunks = topic_records(pages, graph, snapshot_id)
    relations = build_relations(pages, graph, entities, members, snapshot_id)
    attach_related_ids(topics, entities, relations)
    terms = build_terms(topics, entities, relations, snapshot_id)

    changes = previous_changes(output, pages)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **metadata,
        "source_root": ".",
        "incremental": incremental,
        "change_summary": changes,
        "artifacts": list(ARTIFACT_FILES),
        "counts": {
            "source_files": len(pages),
            "topics": len(topics),
            "entities": len(entities),
            "classes": sum(1 for entity in entities if entity["kind"] == "class"),
            "members": len(members),
            "relations": len(relations),
            "terms": len(terms),
            "chunks": len(chunks),
        },
        "files": [source_record(page, graph) for page in pages],
    }
    taxonomy = {
        "schema_version": SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "root_id": topic_id("index.rst") if "index.rst" in graph.pages else None,
        "pages": [
            {
                "id": topic_id(page.path) if page.kind == "topic" else source_id(page.path),
                "path": page.path,
                "kind": page.kind,
                "title": page.title,
                "parent_ids": sorted(
                    topic_id(parent) if graph.pages[parent].kind == "topic" else source_id(parent)
                    for parent in graph.parents.get(page.path, ())
                ),
                "child_ids": sorted(
                    topic_id(child) if graph.pages[child].kind == "topic" else source_id(child)
                    for child in graph.children.get(page.path, ())
                ),
                "reachable": page.path in graph.reachable,
                "orphan": page.path not in graph.reachable,
            }
            for page in pages
        ],
    }

    output.mkdir(parents=True, exist_ok=True)
    for artifact in ARTIFACT_FILES:
        artifact_path = output / artifact
        if artifact_path.exists():
            artifact_path.unlink()
    json_dump(output / "manifest.json", manifest)
    json_dump(output / "taxonomy.json", taxonomy)
    jsonl_dump(output / "topics.jsonl", topics)
    jsonl_dump(output / "entities.jsonl", entities)
    jsonl_dump(output / "relations.jsonl", relations)
    jsonl_dump(output / "terms.jsonl", terms)
    jsonl_dump(output / "chunks.jsonl", chunks)
    return manifest


__all__ = [
    "DocumentGraph",
    "build_relations",
    "build_terms",
    "detect_version",
    "generate",
    "normalize_path",
    "snapshot_metadata",
]

"""Stable artifact schema and identifier helpers."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from . import ARTIFACT_FILES, GENERATOR_VERSION, SCHEMA_VERSION

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_WORD = re.compile(r"[^a-zA-Z0-9@.+-]+")
_WHITESPACE = re.compile(r"\s+")


def source_id(path: str) -> str:
    return "source:" + PurePosixPath(path).as_posix()


def topic_id(path: str) -> str:
    return "topic:" + PurePosixPath(path).with_suffix("").as_posix()


def entity_id(name: str) -> str:
    return "entity:" + name


def member_id(owner: str, kind: str, name: str) -> str:
    return f"member:{owner}:{kind}:{name}"


def relation_id(source: str, relation_type: str, target: str, ordinal: int) -> str:
    return f"relation:{source}:{relation_type}:{target}:{ordinal}"


def chunk_id(topic: str, ordinal: int) -> str:
    return f"chunk:{topic}:{ordinal:04d}"


def normalize_term(value: str) -> str:
    value = _CAMEL_BOUNDARY.sub(" ", value)
    value = value.replace("::", " ")
    value = _NON_WORD.sub(" ", value)
    return _WHITESPACE.sub(" ", value).strip().lower()


def tokenize(value: str) -> list[str]:
    normalized = normalize_term(value)
    return [token for token in normalized.split() if len(token) > 1]


__all__ = [
    "ARTIFACT_FILES",
    "GENERATOR_VERSION",
    "SCHEMA_VERSION",
    "chunk_id",
    "entity_id",
    "member_id",
    "normalize_term",
    "relation_id",
    "source_id",
    "tokenize",
    "topic_id",
]

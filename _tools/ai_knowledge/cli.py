"""Command-line interface for the Godot documentation AI knowledge index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .index import generate
from .query import KnowledgeIndex
from .validate import validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="generate the knowledge artifacts")
    generate_parser.add_argument("--root", type=Path, default=Path("."), help="documentation repository root")
    generate_parser.add_argument("--output", type=Path, default=Path("ai_knowledge"), help="artifact directory")
    generate_parser.add_argument(
        "--incremental",
        action="store_true",
        help="record source changes against the previous manifest",
    )

    validate_parser = subparsers.add_parser("validate", help="validate generated artifacts")
    validate_parser.add_argument("--root", type=Path, default=None, help="documentation repository root")
    validate_parser.add_argument("--output", type=Path, default=Path("ai_knowledge"), help="artifact directory")
    validate_parser.add_argument("--json", action="store_true", help="emit a JSON result")

    query_parser = subparsers.add_parser("query", help="route a natural-language query")
    query_parser.add_argument("text", help="query text")
    query_parser.add_argument("--index", type=Path, default=Path("ai_knowledge"), help="artifact directory")
    query_parser.add_argument("--limit", type=int, default=10, help="maximum number of matches")
    query_parser.add_argument("--snapshot", help="require an exact snapshot ID")
    query_parser.add_argument("--json", action="store_true", help="emit JSON (default)")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        manifest = generate(args.root, args.output, incremental=args.incremental)
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if args.command == "validate":
        errors = validate(args.output, args.root)
        result = {"valid": not errors, "errors": errors}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        elif errors:
            print("\n".join(errors))
        else:
            print("valid")
        return 0 if not errors else 1
    if args.command == "query":
        result = KnowledgeIndex(args.index, expected_snapshot=args.snapshot).search(args.text, args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    return 2


__all__ = ["build_parser", "main"]

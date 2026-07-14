## Why

The knowledge index can identify relevant Godot topics and API entities, but
the current query interface stops at IDs and source references. An assistant
or integration still needs custom logic to resolve those IDs, assemble
source-aligned content, preserve provenance, and avoid oversized prompts.

This change adds a deterministic retrieval interface so query results can be
turned into bounded, prompt-ready context locally without requiring an
embedding service, hosted database, or model-specific integration.

## What Changes

- Add a `retrieve` command to `_tools.ai_knowledge`.
- Accept one or more stable topic, entity, member, or chunk IDs.
- Resolve IDs against a single validated knowledge snapshot.
- Return prompt-ready Markdown by default, with structured JSON for
  integrations.
- Expand topic IDs into their ordered source-aligned chunks.
- Include entity and member metadata, source paths, snapshot identity, and
  retrieval delimiters.
- Preserve requested ordering, deduplicate repeated records, and report
  unknown or ambiguous IDs explicitly.
- Add configurable output-size limits and truncation metadata.
- Document examples for direct prompt inclusion and command pipelines.

## Capabilities

### New Capabilities

- `prompt-context-retrieval`: Resolve knowledge-record IDs into bounded,
  provenance-preserving context suitable for AI prompts or machine consumers.

### Modified Capabilities

## Impact

- Adds retrieval and formatting code under `_tools/ai_knowledge/`.
- Extends the command-line interface and `ai_knowledge/README.md`.
- Reads existing `manifest.json`, `topics.jsonl`, `entities.jsonl`, and
  `chunks.jsonl` artifacts without changing the authoritative documentation.
- Adds tests for topic, entity, member, chunk, ordering, size limits,
  snapshot consistency, and invalid-ID behavior.
- Introduces no external runtime dependencies and no required AI provider.

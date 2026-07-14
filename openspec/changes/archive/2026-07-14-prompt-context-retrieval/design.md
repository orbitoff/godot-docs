## Context

The existing `_tools.ai_knowledge` package generates a versioned, source-linked
snapshot and routes natural-language queries to topic and entity IDs. The
`query` command loads `topics.jsonl`, `entities.jsonl`, `relations.jsonl`, and
`terms.jsonl`, then returns JSON matches. It does not load `chunks.jsonl` or
assemble content for an AI prompt.

The retrieval layer must remain offline, deterministic, model-independent, and
strictly subordinate to the reStructuredText documentation. It must work with
the current JSONL artifact schema and preserve the snapshot and source
provenance already emitted by the generator.

## Goals / Non-Goals

**Goals:**

- Add a `retrieve` CLI command that accepts stable record IDs.
- Resolve topics, entities, members, and detail chunks from one snapshot.
- Produce deterministic prompt-ready Markdown and structured JSON.
- Preserve source paths, hashes, heading context, and snapshot identity.
- Bound output size and report truncation rather than silently dropping data.
- Keep query behavior and existing generated artifacts compatible.

**Non-Goals:**

- Reading arbitrary files from source paths supplied by a caller.
- Calling an AI model, embedding service, or hosted retrieval database.
- Replacing the `query` router or accepting natural-language text as the
  retrieval identifier.
- Automatically expanding all related topics, relations, or class members.
- Changing the generated artifact schema or regenerating the current snapshot.

## Decisions

### 1. Use exact stable IDs as the retrieval contract

The command will accept one or more positional IDs, with options for the
artifact directory, output format, expected snapshot, and character budget:

```text
py -3 -m _tools.ai_knowledge retrieve <id> [<id> ...] \
  --index ai_knowledge \
  --format prompt|json \
  --max-chars 32000 \
  --snapshot <snapshot-id>
```

Stable IDs are safer and more deterministic than accepting titles, aliases, or
filesystem paths. Natural-language routing remains the responsibility of
`query`. A future pipeline can add an IDs-only query format without making
retrieval resolve ambiguous names.

### 2. Add a lazy retrieval layer over the existing records

Add a retrieval module that shares the manifest and record-loading behavior
with `KnowledgeIndex` but loads `chunks.jsonl` only when retrieval is
requested. The retriever will build exact-ID maps for topics, entities, and
chunks, validate snapshot fields against the manifest, and expose a small
internal result model to the formatters.

Topic records will be expanded through their existing `chunk_ids` in stored
order. Entity records will include their existing member ID list; member IDs
will resolve to individual member records. Chunk IDs will resolve directly.
Related IDs and relation metadata will be reported as metadata only, avoiding
unbounded graph expansion.

### 3. Provide deterministic prompt and JSON renderers

Prompt output will be Markdown with a snapshot header and one clearly
delimited section per requested record. Each section will include the stable
ID, kind, title or name, source-relative path, source hash, and the source
aligned text when available. Chunk sections will include their heading path.
The renderer will preserve requested record order and topic chunk order.

JSON output will contain `snapshot_id`, `requested_ids`, `status`, `records`,
and `errors`. Records will retain structured metadata and text rather than
requiring a consumer to parse Markdown. stdout will contain only the selected
format; diagnostics will go to stderr.

### 4. Enforce a character budget at the rendering boundary

The default prompt budget will be 32,000 characters and can be overridden by a
positive `--max-chars` value. The retriever will reserve space for required
metadata, then include text in deterministic order until the budget is
exhausted. If a chunk does not fit completely, its text will be truncated at a
character boundary and the result will mark `truncated` with omitted-record or
omitted-character information.

The budget is expressed in characters rather than model tokens so the command
does not depend on a tokenizer or provider. The JSON and Markdown renderers
will apply the same budget semantics.

### 5. Fail closed on invalid or mixed identifiers

The default command will return a nonzero exit code when an ID is malformed,
unknown, or belongs to a different snapshot, and it will not emit a
success-shaped prompt. JSON errors will identify each failed ID. An
`--allow-missing` option may be provided for integrations that explicitly want
partial output; such output must retain the errors and use a non-success
status.

The command will never interpret `source_path` as a filesystem request.
Source paths remain citations. Exact source-file retrieval can be designed
separately with an explicit repository-root policy.

### 6. Keep the change isolated and backward compatible

The CLI will add a new subparser and the package will add retrieval tests and
README examples. `generate`, `validate`, and `query` behavior will remain
unchanged. Existing manifests and JSONL files remain valid; retrieval will use
the current schema without adding required fields.

## Risks / Trade-offs

- **[Prompt truncation can omit a caveat]** -> Preserve source and heading
  metadata, mark truncation explicitly, and allow callers to raise the
  character budget or retrieve narrower IDs.
- **[JSONL loading can consume memory]** -> Load chunks lazily for retrieval and
  keep the existing query path from loading them.
- **[Exact IDs are less convenient than names]** -> Keep `query` as the
  natural-language discovery step and document a two-command workflow.
- **[Markdown content may contain formatting or instruction-like text]** ->
  Delimit every record, preserve provenance, and keep the tool as a formatter
  rather than executing or interpreting documentation text.
- **[Snapshot drift can make copied IDs stale]** -> Require manifest-consistent
  records and expose the snapshot ID in every result.

## Migration Plan

1. Add the retriever, formatters, CLI arguments, and focused tests.
2. Update `ai_knowledge/README.md` with direct retrieval and JSON examples.
3. Run the existing unit tests and artifact validation against both fixtures
   and the current generated snapshot.
4. Roll back by removing the new subcommand and retrieval module; existing
   generation, validation, query behavior, and artifacts remain usable.

## Open Questions

- Whether a future change should add `query --format ids` and
  `retrieve --stdin` for shell pipelines.
- Whether a later tokenizer-aware budget should supplement the portable
  character budget.

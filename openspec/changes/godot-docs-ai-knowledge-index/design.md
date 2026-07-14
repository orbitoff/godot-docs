## Context

This repository is a Sphinx documentation source tree for Godot 4.7. The
current snapshot is on commit `0585d03be` and contains narrative documentation
under `about/`, `community/`, `engine_details/`, `getting_started/`, and
`tutorials/`, plus generated class reference pages under `classes/`.

The source already contains machine-readable structure that is useful for
retrieval: `toctree` relationships, document titles, explicit labels, Sphinx
cross-reference roles, code blocks, and generated class-reference tables. The
class pages are derived artifacts and explicitly must not be hand-edited.

The knowledge layer must reduce repeated context loading without becoming a
second, untraceable source of truth. It also needs to remain useful to tools
that do not share a particular embedding model or AI provider.

## Goals / Non-Goals

**Goals:**

- Represent the complete documentation snapshot with stable IDs and provenance.
- Give an assistant a small routing layer for finding relevant Godot topics and
  API entities from natural-language questions.
- Provide compact topic specifications plus source-aligned detail chunks that
  can be loaded selectively.
- Preserve hierarchy, cross-references, inheritance, and tutorial-to-API links.
- Make regeneration deterministic, version-aware, and safe to run alongside the
  existing Sphinx build.
- Keep the generated knowledge useful offline and independent of a hosted
  vector database or a specific AI model.

**Non-Goals:**

- Replacing the published reStructuredText documentation.
- Claiming that a generated summary is always sufficient for every technical
  answer.
- Editing or duplicating the Godot engine source that generates `classes/`.
- Making embeddings or an external AI service a required build dependency.
- Adding translations or indexing every language as part of the first snapshot.

## Decisions

### 1. Treat the source tree as authoritative

The generated artifacts will always record the source path, source hash,
documentation version, branch, and commit. A consumer can use compact records
for routing and context reduction, but can still verify a claim against the
exact source page. This is safer than treating an LLM-written synopsis as a
replacement for normative documentation.

### 2. Use a layered, portable artifact model

The generated output will live in a dedicated `ai_knowledge/` tree and use
newline-delimited JSON for large collections:

```text
ai_knowledge/
  README.md
  manifest.json
  taxonomy.json
  topics.jsonl
  entities.jsonl
  relations.jsonl
  terms.jsonl
  chunks.jsonl
```

- `manifest.json` identifies the snapshot, schemas, counts, generator, and
  source hashes.
- `taxonomy.json` contains the Sphinx-derived document hierarchy.
- `topics.jsonl` contains one record for each narrative/reference topic page,
  including a bounded summary, headings, keywords, source, and chunk IDs.
- `entities.jsonl` contains classes, global scopes, and class members.
- `relations.jsonl` contains typed links such as `toctree`, `ref`, `doc`,
  inheritance, tutorial, and related-topic relationships.
- `terms.jsonl` contains normalized names, aliases, and candidate IDs for
  deterministic routing.
- `chunks.jsonl` contains source-aligned sections or excerpts that can be
  loaded after routing when a compact topic record is not sufficient.

This keeps the first lookup small while preserving a loss-minimizing path to
the documented details. JSONL is chosen over one file per page so consumers
can stream or build their own local index without requiring a database.

### 3. Extract structure from Sphinx-compatible source

The generator will use the repository's existing Python/Sphinx ecosystem and a
parser that understands reStructuredText directives and roles. It will derive
titles, headings, labels, `toctree` entries, code blocks, links, and section
boundaries from source structure rather than relying only on regular
expressions. Class records will be parsed from the generated class pages and
will retain the generated XML-source reference when present.

The baseline generator will be deterministic and will not require an AI model.
Any semantic enrichment beyond source-derived text must be explicitly marked
as derived metadata and retain source references.

### 4. Separate narrative topics from API entities

Narrative pages answer workflow and conceptual questions; class pages answer
API questions. They will have different schemas and IDs while sharing the
relation graph. This avoids flattening a large class inheritance tree into
prose and makes queries such as "which class should I use for 2D movement?"
able to traverse from a tutorial topic to related classes.

### 5. Make routing explainable before making it semantic

The initial router will normalize query text and score exact names, labels,
headings, aliases, hierarchy terms, and cross-reference relationships. Each
candidate will include a reason and source path. Embeddings can be added later
as an optional accelerator, but the committed index must remain usable with
plain text tools and any AI model.

### 6. Refresh by source hashes and validate before publishing

Generation will support full and incremental modes. A changed source page
regenerates its topic, chunks, relations, and affected routing terms; unchanged
records remain stable. Validation will reject duplicate IDs, missing source
files, broken internal IDs, inconsistent manifest counts, stale class records,
and malformed JSONL. The knowledge output will be isolated from the Sphinx
published output and must not change existing documentation build behavior.

## Risks / Trade-offs

- **[Lossy summaries]** A compact summary may omit an important caveat ->
  retain source-aligned chunks and provenance, and make fallback to the source
  explicit.
- **[Source drift]** Generated records can become stale after a docs change ->
  include hashes, provide a refresh command, and validate freshness in CI or
  before consumption.
- **[Repository size]** Full chunks duplicate documentation text ->
  use JSONL, stable compact fields, and allow consumers to fetch only selected
  chunks; measure the initial snapshot before deciding on artifact packaging.
- **[Parser complexity]** reStructuredText and Sphinx extensions contain
  constructs that a simple parser may miss -> use Sphinx-compatible parsing and
  add fixtures for representative directives.
- **[Generated class references]** Class pages can change with the engine
  source independently of tutorial pages -> hash and regenerate `classes/`
  independently, without hand-editing those files.
- **[False relevance]** Lexical aliases can return plausible but wrong topics ->
  return multiple explainable candidates and preserve an explicit no-match
  result instead of fabricating a destination.

## Migration Plan

1. Add the schemas, generator, validator, and consumer documentation without
   changing the existing Sphinx sources.
2. Generate the first snapshot for the current 4.7 branch and validate its
   manifest, coverage, relations, and routing index.
3. The initial snapshot measures about 84 MB and is committed in full,
   including chunks, to preserve offline use. A later repository policy can
   package chunks separately without changing the schemas.
4. Add refresh and validation to the repository's normal documentation-change
   workflow.
5. To roll back, remove the generated `ai_knowledge/` output and disable the
   optional refresh step; the published documentation remains unchanged.

## Open Questions

- Should full source-aligned chunks be committed in Git, stored in release
  artifacts, or support both modes?
- Which retrieval interface should be the stable consumer contract: a small
  command-line query tool, a Python module, or only documented JSONL schemas?
- Should later snapshots include localized documentation or only the English
  source tree?
- Is semantic enrichment worth the review and reproducibility cost after the
  deterministic index is evaluated on real Godot questions?

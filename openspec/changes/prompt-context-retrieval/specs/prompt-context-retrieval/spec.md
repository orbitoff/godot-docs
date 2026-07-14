## ADDED Requirements

### Requirement: Stable-ID retrieval command

The knowledge tool SHALL provide a `retrieve` subcommand that accepts one or
more exact topic, entity, member, or chunk IDs and SHALL support selecting the
artifact directory, output format, expected snapshot, and maximum character
budget.

#### Scenario: Retrieving several records

- **WHEN** a caller runs `retrieve` with a topic ID and an entity ID
- **THEN** the command resolves both IDs from the selected knowledge directory
  and returns records in the requested output format

### Requirement: Snapshot-consistent resolution

The retriever SHALL load the manifest and SHALL resolve only records whose
snapshot identity matches the manifest snapshot. When an expected snapshot is
provided, it SHALL reject a different snapshot explicitly.

#### Scenario: Rejecting a stale snapshot request

- **WHEN** a caller requests retrieval with an expected snapshot ID that differs
  from `manifest.json`
- **THEN** the command exits unsuccessfully and reports the requested and actual
  snapshot IDs

### Requirement: Topic chunk expansion

When a topic ID is requested, the retriever SHALL include the topic metadata and
its referenced detail chunks in the `chunk_ids` order stored by the topic
record. Each included chunk SHALL retain its source path, source hash, heading
path, and source-aligned text.

#### Scenario: Retrieving a tutorial topic

- **WHEN** a caller retrieves a topic with multiple detail chunks
- **THEN** the result contains the topic record followed by its chunks in stable
  source order

### Requirement: Entity, member, and direct chunk retrieval

The retriever SHALL resolve entity IDs, member IDs, and chunk IDs directly.
Entity results SHALL preserve their member ID index and related metadata without
implicitly expanding every member or related record.

#### Scenario: Retrieving an API member

- **WHEN** a caller retrieves
  `member:CharacterBody2D:method:move_and_slide`
- **THEN** the result contains that member's signature, description, owner,
  source path, and provenance fields without requiring the entire class page

### Requirement: Provenance-preserving output

Prompt output SHALL be deterministic Markdown with a snapshot header and
delimited sections. JSON output SHALL contain the snapshot ID, requested IDs,
status, records, and errors. Every successful record SHALL include its stable
ID, kind, source-relative path, source hash, and title or name when available.

#### Scenario: Preparing context for an AI prompt

- **WHEN** a caller uses the default prompt format
- **THEN** stdout contains only bounded, delimited documentation context with
  enough provenance to cite the authoritative source

### Requirement: Stable ordering and deduplication

The retriever SHALL preserve the first occurrence order of requested IDs,
SHALL emit duplicate requested IDs only once, and SHALL preserve stored chunk
ordering within each expanded topic.

#### Scenario: Repeating an ID

- **WHEN** the same topic ID is supplied twice among several IDs
- **THEN** the output contains one section for that topic at the position of its
  first occurrence

### Requirement: Bounded retrieval output

The retriever SHALL enforce a configurable maximum character budget, SHALL
default to 32,000 characters, and SHALL report truncation and omitted content
when the budget prevents complete rendering.

#### Scenario: Truncating an oversized topic

- **WHEN** a topic's metadata and chunks exceed the requested `--max-chars`
- **THEN** the output does not exceed the budget and explicitly marks the
  result as truncated

### Requirement: Explicit invalid-ID handling

The retriever SHALL reject malformed, unknown, or mixed-snapshot IDs with a
nonzero exit status by default and SHALL identify each failed ID. It SHALL NOT
interpret a source path or arbitrary caller input as a file to read. An
explicit partial-retrieval mode MAY return available records, but it MUST
retain the errors and non-success status.

#### Scenario: Requesting an unknown ID

- **WHEN** a caller supplies an ID that is absent from all supported artifacts
- **THEN** the command reports the unknown ID and does not silently emit a
  success-shaped context result

## ADDED Requirements

### Requirement: Topic coverage

The knowledge layer SHALL create one topic record for every indexed narrative
or reference page outside the class-entity collection, including its title,
hierarchy position, source path, and stable topic ID.

#### Scenario: Representing a tutorial page

- **WHEN** a tutorial page is included in the source inventory
- **THEN** `topics.jsonl` contains a record for that page linked to its parent
  topic and source-relative path

### Requirement: Compact source-linked specification

Each topic record SHALL contain a bounded source-derived summary, section or
heading metadata, normalized keywords, related IDs, and the IDs of its
source-aligned detail chunks.

#### Scenario: Loading a topic before its details

- **WHEN** a consumer loads a topic record for a Godot concept
- **THEN** it can identify the concept's scope, likely subtopics, source page,
  and the detail chunks to load without reading the entire documentation tree

### Requirement: Hierarchy and cross-reference preservation

The topic layer SHALL preserve parent-child `toctree` relationships and expose
typed links to referenced documents, labels, classes, and related topics.

#### Scenario: Following a cross-topic reference

- **WHEN** a page references another page or Godot class using a Sphinx link
- **THEN** the generated relation is addressable by stable IDs and records the
  relation type and source of the link

### Requirement: Source-aligned detail

Detail chunks SHALL preserve the source section or heading path and SHALL NOT
present derived text as an authoritative fact without a source reference.

#### Scenario: Answering a detailed question

- **WHEN** a compact topic record does not contain enough detail for a query
- **THEN** a consumer can load source-aligned chunks with their source path and
  heading context instead of relying on an untraceable summary

### Requirement: Orphan visibility

Pages that are valid sources but are not reachable from the main `toctree`
SHALL remain discoverable and SHALL be marked as orphan or otherwise lower
confidence rather than silently omitted.

#### Scenario: Indexing an orphan page

- **WHEN** a valid source page is not present in a reachable `toctree`
- **THEN** it appears in the inventory and topic records with an orphan marker

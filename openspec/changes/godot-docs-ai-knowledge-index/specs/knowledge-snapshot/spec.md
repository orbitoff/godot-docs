## ADDED Requirements

### Requirement: Snapshot identity

The knowledge generator SHALL record the documentation version, source branch,
source commit, generator version, artifact schema version, and generation
timestamp in `manifest.json`.

#### Scenario: Generating the current branch snapshot

- **WHEN** the generator runs against the current 4.7 documentation worktree
- **THEN** the manifest identifies the 4.7 documentation version and the exact
  source commit used for the generated artifacts

### Requirement: Complete source inventory

The snapshot SHALL inventory every relevant reStructuredText source page under
the supported documentation roots, including whether the page is in a
`toctree`, is an orphan, or is a generated class-reference page.

#### Scenario: Indexing narrative and generated pages

- **WHEN** the inventory is generated
- **THEN** pages under the narrative documentation roots and `classes/` are
  represented with stable IDs and source-relative paths

### Requirement: Source provenance

Every topic, entity, relation, and detail chunk SHALL identify its source path
and source content hash, and SHALL identify the snapshot that produced it.

#### Scenario: Detecting a changed source page

- **WHEN** a source page changes after a snapshot is generated
- **THEN** its next generated record has a different source hash and remains
  traceable to the changed source path

### Requirement: Reproducible manifest counts

The generator SHALL produce stable record ordering and manifest counts for the
same source snapshot, apart from explicitly volatile metadata such as the
generation timestamp.

#### Scenario: Regenerating without source changes

- **WHEN** the generator runs twice against the same commit and configuration
- **THEN** all non-volatile artifact records and manifest counts are identical

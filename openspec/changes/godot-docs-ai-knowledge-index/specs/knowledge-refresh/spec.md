## ADDED Requirements

### Requirement: Documented generation entry point

The repository SHALL provide a documented command or module that can generate
the knowledge artifacts from a checked-out documentation worktree without
changing the published Sphinx source behavior.

#### Scenario: Running a full generation

- **WHEN** a contributor invokes the documented generation entry point
- **THEN** the knowledge artifacts are produced in the dedicated output tree
  and the normal documentation sources remain unchanged

### Requirement: Incremental refresh

The generator SHALL support identifying changed, added, removed, and unchanged
source inputs using the previous manifest and source hashes.

#### Scenario: Refreshing after a tutorial edit

- **WHEN** one tutorial page changes and the generator is run again
- **THEN** the affected topic, chunks, relations, and routing terms are
  refreshed while unrelated records remain stable

### Requirement: Artifact validation

The repository SHALL provide validation that detects duplicate IDs, malformed
records, missing source paths, invalid internal references, inconsistent
manifest counts, and stale records.

#### Scenario: Validating a complete snapshot

- **WHEN** validation runs after generation
- **THEN** it succeeds only if all records are well-formed, source-linked, and
  internally consistent

#### Scenario: Detecting a broken relation

- **WHEN** a relation points to an unknown topic or entity ID
- **THEN** validation fails with the relation and source record identified

### Requirement: Build isolation

Knowledge generation and validation SHALL be opt-in or explicitly integrated
without changing the output or success criteria of the existing Sphinx build
unless a repository maintainer enables that integration.

#### Scenario: Building the published documentation

- **WHEN** an existing Sphinx build is run without the knowledge command
- **THEN** it behaves as before and does not require an AI model or routing
  index

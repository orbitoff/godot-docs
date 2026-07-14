## ADDED Requirements

### Requirement: Explainable term routing

The routing index SHALL normalize documented names, titles, labels, headings,
aliases, and relevant terms to candidate topic or entity IDs.

#### Scenario: Routing a class-name query

- **WHEN** a query contains a documented Godot class name
- **THEN** the router returns that entity and records the exact-name match as a
  reason

### Requirement: Hierarchical candidate ranking

The router SHALL rank candidates using exact terms, aliases, topic hierarchy,
entity relationships, and cross-references, and SHALL return the source path
and reason for each candidate.

#### Scenario: Routing a conceptual query

- **WHEN** a query describes a Godot workflow without naming an exact page
- **THEN** the router returns relevant topic candidates with explainable
  matching terms and hierarchy or relation context

### Requirement: Version-aware results

Routing results SHALL identify the knowledge snapshot and SHALL NOT silently
combine records from different documentation versions.

#### Scenario: Querying a stale or mixed index

- **WHEN** a consumer requests routing against records from different
  snapshots
- **THEN** the router reports the snapshot mismatch or requires an explicit
  version selection

### Requirement: No-match and ambiguity handling

The router SHALL return an explicit no-match result when evidence is
insufficient and SHALL expose multiple candidates when the query is ambiguous.

#### Scenario: Querying an unknown Godot concept

- **WHEN** no indexed term or relationship provides a meaningful candidate
- **THEN** the result indicates no match and does not fabricate a topic or API
  destination

#### Scenario: Querying an overloaded term

- **WHEN** a term maps to multiple plausible topics or entities
- **THEN** the result includes the candidates and their distinct match reasons

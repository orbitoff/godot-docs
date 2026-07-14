## Purpose

Provide a source-linked index of generated Godot class-reference entities and
members for API retrieval.

## Requirements

### Requirement: Class coverage

The API entity index SHALL create a class or global-scope record for every
generated class-reference page in `classes/`.

#### Scenario: Indexing a generated class page

- **WHEN** a generated class-reference page exists under `classes/`
- **THEN** `entities.jsonl` contains its name, stable ID, source path, summary,
  and generated-source metadata when available

### Requirement: Member structure

The API entity index SHALL represent documented properties, methods, signals,
constants, enums, and other supported member kinds with stable member IDs,
declared class ownership, signatures, and links to their source class.

#### Scenario: Looking up a class method

- **WHEN** a class page documents a method
- **THEN** the method can be retrieved independently or through its owning class
  and retains its signature and source reference

### Requirement: Inheritance relationships

The index SHALL represent both declared inheritance and documented inherited
relationships when they are present in the generated class reference.

#### Scenario: Traversing a class hierarchy

- **WHEN** a class declares a base class or inherited classes
- **THEN** the relation graph exposes the appropriate inheritance edges using
  stable entity IDs

### Requirement: API-to-topic links

API entities SHALL retain links to tutorial or engine-detail pages referenced by
their documentation, and topic records SHALL be able to reference relevant
API entities.

#### Scenario: Connecting workflow and API knowledge

- **WHEN** a class page links to a tutorial or a tutorial links to a class
- **THEN** the relation graph supports traversal in both directions

### Requirement: Generated-source safety

The generator SHALL treat files under `classes/` as generated inputs and SHALL
not modify them while producing API records.

#### Scenario: Refreshing class records

- **WHEN** class-reference records are regenerated
- **THEN** only knowledge artifacts and generator metadata change, and the
  generated class source files remain untouched

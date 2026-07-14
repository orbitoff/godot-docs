## Why

The Godot documentation is authoritative but large and heterogeneous: this 4.7
branch contains tutorial content, engine details, and generated class reference
pages. An AI assistant currently has to search and reread source pages for each
question, while a one-time prose dump would be lossy, difficult to route, and
quickly become stale.

This change introduces a versioned, generated knowledge layer that lets an
assistant identify likely Godot topics and load compact, source-linked
specifications before consulting the original documentation when details or
ambiguity require it.

## What Changes

- Record the documentation snapshot (Godot version, branch, commit, source
  files, hashes, and generation metadata).
- Generate a hierarchical inventory from the Sphinx document tree, including
  domains, pages, headings, labels, and cross-references.
- Generate compact topic specifications that summarize concepts, workflows,
  constraints, examples, related topics, and authoritative source paths.
- Generate structured API/entity records for the class reference, including
  inheritance, members, links, and relationships to tutorial topics.
- Generate a relevance index with aliases, concepts, intent hints, and
  topic/entity candidates for natural-language Godot questions.
- Preserve provenance and freshness information so generated knowledge is
  refreshed when documentation or generated class reference files change.
- Keep the original reStructuredText and generated class reference as the
  authority; the knowledge layer must not silently replace source documentation.

## Capabilities

### New Capabilities

- `knowledge-snapshot`: Versioned inventory and provenance for the documentation
  snapshot used to build the AI knowledge layer.
- `topic-specifications`: Compact, hierarchical, source-linked specifications
  for the documented Godot concepts and workflows.
- `api-entity-index`: Structured records for classes and their members, with
  inheritance and cross-topic relationships.
- `relevance-routing`: Query-oriented indexing that maps Godot concepts,
  aliases, and user intents to candidate topic and API specifications.
- `knowledge-refresh`: Deterministic regeneration, change detection, and
  validation of the knowledge layer as the source documentation evolves.

### Modified Capabilities

None.

## Impact

The change will add a generation and validation workflow to this documentation
repository, plus generated knowledge artifacts and documentation for consuming
them. It will read the existing Sphinx source tree, `toctree` hierarchy,
cross-reference labels, and generated `classes/` reference pages. It should not
change the published documentation or its existing build behavior, and should
avoid treating generated class files as hand-edited source.

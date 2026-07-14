## 1. Establish the artifact contract

- [x] 1.1 Define versioned schemas and stable ID rules for manifests, topics, entities, relations, terms, and chunks.
- [x] 1.2 Decide the committed versus release-artifact policy for the initial full chunk output and document attribution requirements.
- [x] 1.3 Add the `ai_knowledge/README.md` consumer documentation, including the source-authority and stale-data rules.

## 2. Build the source inventory

- [ ] 2.1 Implement source snapshot detection for documentation version, branch, commit, generator version, and source hashes.
- [ ] 2.2 Parse Sphinx document structure into the taxonomy, including reachable and orphan pages.
- [ ] 2.3 Extract titles, headings, labels, code-block metadata, and typed cross-reference candidates.
- [ ] 2.4 Add fixtures covering representative tutorial pages, nested `toctree` trees, custom directives, and orphan pages.

## 3. Generate topic specifications

- [ ] 3.1 Generate stable topic records for every narrative and non-class reference page.
- [ ] 3.2 Generate bounded source-derived summaries, normalized keywords, related IDs, and source-aligned detail chunks.
- [ ] 3.3 Preserve source section paths and provenance on every detail chunk.
- [ ] 3.4 Add coverage checks proving that all indexed source pages have topic records or an explicit entity-only classification.

## 4. Generate API entity records

- [ ] 4.1 Parse generated class-reference pages without modifying files under `classes/`.
- [ ] 4.2 Extract class/global-scope records, member kinds, signatures, labels, and source references.
- [ ] 4.3 Build inheritance and API-to-topic relations from generated reference links.
- [ ] 4.4 Add fixtures for inherited members, enums, signals, global scopes, and special class names.

## 5. Generate and expose relevance routing

- [ ] 5.1 Normalize titles, class/member names, labels, headings, and curated aliases into the term index.
- [ ] 5.2 Implement explainable candidate ranking using exact matches, hierarchy, and relations.
- [ ] 5.3 Define and implement the stable query interface with snapshot selection, no-match results, and ambiguity results.
- [ ] 5.4 Add representative Godot query cases for 2D, scripting, input, networking, rendering, and class lookup.

## 6. Add refresh and validation workflow

- [ ] 6.1 Implement full and incremental generation using manifest source hashes.
- [ ] 6.2 Implement validation for schema shape, duplicate IDs, source coverage, relation targets, and manifest counts.
- [ ] 6.3 Document the generation and validation commands and keep them independent from the default Sphinx build.
- [ ] 6.4 Measure the first snapshot size and finalize whether chunks are committed, packaged, or both.

## 7. Produce the initial snapshot

- [ ] 7.1 Generate the knowledge layer for the current Godot 4.7 branch snapshot.
- [ ] 7.2 Run validation and resolve parser, coverage, relation, and routing failures.
- [ ] 7.3 Record the generated snapshot metadata and review sample outputs for tutorial, engine-detail, and class-reference questions.

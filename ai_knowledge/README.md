# Godot documentation AI knowledge index

This directory is generated from the checked-out Godot documentation sources.
It is a versioned retrieval layer for AI assistants, not a replacement for the
reStructuredText documentation or the generated class reference.

## Contents

- `manifest.json` identifies the Godot version, source commit, hashes, schema,
  generator, and record counts.
- `taxonomy.json` contains the document hierarchy and reachability metadata.
- `topics.jsonl` contains narrative and reference-page topic records.
- `entities.jsonl` contains classes, global scopes, and API members.
- `relations.jsonl` contains typed document, API, inheritance, and reference
  links.
- `terms.jsonl` contains normalized terms and routing candidates.
- `chunks.jsonl` contains source-aligned detail sections for selective loading.

Every record includes the source-relative path, source hash, and snapshot ID.
Use those fields to verify details against the authoritative source page.

## Generation and queries

Run these commands from the repository root:

```text
py -3 -m _tools.ai_knowledge generate
py -3 -m _tools.ai_knowledge validate
py -3 -m _tools.ai_knowledge query "how do I move a 2D character?"
```

The default generator writes the complete initial snapshot, including chunks,
to this directory so it can be used offline. The first 4.7 snapshot is about
84 MB, so this change keeps all artifacts, including `chunks.jsonl`, in Git
with the matching documentation snapshot. A later repository policy may
package chunks separately while retaining the manifest, routing, topic,
entity, and relation artifacts in Git.

Narrative documentation is derived from content licensed under CC BY 3.0.
Class-reference content is derived from Godot engine sources and is distributed
under the MIT license. Preserve the source repository attribution and consult
the repository `LICENSE.txt` for the complete terms.

Generated summaries are bounded and source-derived. They can omit important
caveats; consumers must use the linked chunks or source pages when a question
requires detail. Records from different documentation snapshots must not be
mixed silently.

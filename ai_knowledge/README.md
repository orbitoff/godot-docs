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

## Retrieving prompt context

Use `query` to discover stable IDs, then use `retrieve` to assemble bounded
context for an AI prompt. Retrieval accepts exact `topic:`, `entity:`,
`member:`, and `chunk:` IDs; source paths are citations and are not read as
arbitrary input.

```text
py -3 -m _tools.ai_knowledge retrieve `
  topic:tutorials/physics/physics_introduction `
  entity:CharacterBody2D `
  member:CharacterBody2D:method:move_and_slide `
  --index ai_knowledge `
  --format prompt `
  --max-chars 32000
```

The default `prompt` format writes Markdown to stdout with the snapshot ID,
record delimiters, source paths, source hashes, headings, and source-aligned
content. Redirect stdout when another tool expects a file:

```text
py -3 -m _tools.ai_knowledge retrieve entity:CharacterBody2D `
  --format prompt > godot_context.md
```

Use `--format json` for integrations that need structured records:

```text
py -3 -m _tools.ai_knowledge retrieve `
  topic:tutorials/physics/physics_introduction `
  --format json
```

Topic IDs include the topic record followed by its ordered detail chunks.
Entity IDs include class metadata and its member ID index; member and chunk IDs
resolve directly. Related topics and class members are not expanded
implicitly, which keeps prompts bounded and deterministic.

The default output budget is 32,000 characters and can be changed with
`--max-chars`. If the budget is exceeded, the result reports truncation and
omitted IDs. Unknown, malformed, or mixed-snapshot IDs fail with a nonzero exit
code by default. `--allow-missing` permits partial output, but preserves the
errors and still returns a non-success exit code. Use `--snapshot` when a
caller must require an exact generated snapshot.

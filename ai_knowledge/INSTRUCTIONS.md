# Godot AI Documentation Workflow

Copy this file into the Godot project using the instruction-file name
supported by the AI assistant, such as `AGENTS.md`,
`.github/copilot-instructions.md`, `CLAUDE.md`, or a Cursor rule file.

## Project and documentation rules

This is a Godot project. Before answering a Godot engine or API question:

1. Read `project.godot` and identify the project's Godot version.
2. Treat this project's scripts, scenes, and configuration as authoritative for
   project-specific behavior.
3. Use the local Godot knowledge index for engine, API, and documentation
   questions.
4. Do not invent classes, methods, properties, signals, or parameters.
5. If the documentation query has no match or is ambiguous, say so and
   investigate further instead of guessing.

The documentation repository is configured through the
`GODOT_DOCS_ROOT` environment variable:

```powershell
$env:GODOT_DOCS_ROOT = "C:\path\to\godot-docs"
```

The knowledge index is located at:

```text
$env:GODOT_DOCS_ROOT\ai_knowledge
```

## Query and retrieve workflow

Run the commands from the documentation repository because
`_tools.ai_knowledge` is a local Python module:

```powershell
$docs = $env:GODOT_DOCS_ROOT
Push-Location $docs
try {
    py -3 -m _tools.ai_knowledge query `
      "YOUR GODOT QUESTION" `
      --index "$docs\ai_knowledge"
}
finally {
    Pop-Location
}
```

Inspect the query matches, then retrieve the relevant IDs:

```powershell
$docs = $env:GODOT_DOCS_ROOT
Push-Location $docs
try {
    py -3 -m _tools.ai_knowledge retrieve `
      topic:tutorials/physics/using_character_body_2d `
      entity:CharacterBody2D `
      member:CharacterBody2D:method:move_and_slide `
      --index "$docs\ai_knowledge" `
      --format prompt `
      --max-chars 24000
}
finally {
    Pop-Location
}
```

Use the retrieved output as documentation context together with the project's
source files. Preserve the snapshot ID and source paths when citing the
documentation.

## Retrieval guidelines

- Query first; retrieve only the relevant topic, entity, member, or chunk IDs.
- Use a documentation snapshot matching the project's Godot version.
- Use `--format json` when structured records are easier to process.
- Increase `--max-chars` only when the retrieved context is insufficient.
- Treat truncation, no-match, and ambiguity results as signals to investigate
  further.
- Do not ask the model to read an absolute source path unless it has
  filesystem access; retrieved command output is the portable context.
- Temporary retrieved context files should not be committed to the project.

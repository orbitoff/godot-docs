## 1. Retrieval loading and resolution

- [x] 1.1 Add a retrieval module that loads the manifest and lazily indexes topic, entity, member, and chunk records.
- [x] 1.2 Validate record snapshot IDs against the manifest and support an optional exact expected-snapshot check.
- [x] 1.3 Resolve exact requested IDs, expand topic `chunk_ids` in stored order, resolve direct chunks, and preserve entity member indexes.
- [x] 1.4 Preserve first-request ordering and deduplicate repeated IDs without expanding related records implicitly.

## 2. Result formatting and limits

- [x] 2.1 Define retrieval result and error structures containing snapshot, requested IDs, records, status, and truncation metadata.
- [x] 2.2 Implement the default deterministic Markdown prompt renderer with snapshot headers, record delimiters, provenance, and heading context.
- [x] 2.3 Implement the structured JSON renderer with stable fields and source-aligned text.
- [x] 2.4 Enforce the default and configured character budgets, including deterministic truncation and omitted-content reporting.
- [x] 2.5 Reject malformed, unknown, and mixed-snapshot IDs by default, and implement explicit partial retrieval behavior for `--allow-missing`.

## 3. Command-line integration

- [x] 3.1 Add the `retrieve` subcommand with positional IDs and `--index`, `--format`, `--max-chars`, `--snapshot`, and `--allow-missing` options.
- [x] 3.2 Wire retrieval into the CLI entry point while keeping `generate`, `validate`, and `query` behavior unchanged.
- [x] 3.3 Ensure formatted results are written only to stdout and diagnostics use stderr with meaningful exit codes.

## 4. Automated coverage

- [x] 4.1 Add fixture tests for topic expansion, direct chunk retrieval, entity/member records, provenance, ordering, and deduplication.
- [x] 4.2 Add fixture tests for JSON and prompt output plus default and custom character budgets.
- [x] 4.3 Add tests for unknown IDs, malformed IDs, snapshot mismatch, mixed-snapshot records, and partial retrieval errors.
- [x] 4.4 Add a real-snapshot retrieval test covering a tutorial topic and a Godot API member when the generated snapshot is available.

## 5. Documentation and verification

- [x] 5.1 Document direct retrieval, prompt inclusion, JSON consumption, provenance, limits, and error behavior in `ai_knowledge/README.md`.
- [x] 5.2 Run the targeted retrieval tests, the existing AI knowledge test suite, and artifact validation against the fixture and current snapshot.

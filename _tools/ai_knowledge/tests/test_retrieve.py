from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from _tools.ai_knowledge.cli import main
from _tools.ai_knowledge.index import generate
from _tools.ai_knowledge.retrieve import KnowledgeRetriever
from _tools.ai_knowledge.tests.test_index import copy_fixture_tree


class KnowledgeRetrieverTests(unittest.TestCase):
    def build_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, Path, dict]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        copy_fixture_tree(root)
        output = root / "ai_knowledge"
        manifest = generate(root, output)
        return temporary, root, output, manifest

    def test_resolves_topics_entities_members_and_chunks_in_stable_order(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        chunk_id = "chunk:topic:tutorials/2d/index:0000"
        result = KnowledgeRetriever(output).retrieve(
            [
                "topic:tutorials/2d/index",
                "entity:TestThing",
                "member:TestThing:method:move",
                chunk_id,
                "entity:TestThing",
            ]
        )

        self.assertEqual(result.status, "ok")
        self.assertEqual(
            [record["id"] for record in result.records],
            [
                "topic:tutorials/2d/index",
                chunk_id,
                "entity:TestThing",
                "member:TestThing:method:move",
            ],
        )
        self.assertEqual(result.records[0]["snapshot_id"], manifest["snapshot_id"])
        self.assertIn("members", result.records[2]["metadata"])
        self.assertIn("Moves the fixture entity.", result.records[3]["content"])
        self.assertEqual(result.records[1]["metadata"]["heading_path"], [])

    def test_prompt_and_json_output_preserve_provenance(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        result = KnowledgeRetriever(output).retrieve(["topic:tutorials/2d/index"])
        prompt = result.to_prompt()
        payload = json.loads(result.to_json())

        self.assertIn("# Godot AI Context", prompt)
        self.assertIn(f"Snapshot: `{manifest['snapshot_id']}`", prompt)
        self.assertIn("BEGIN GODOT KNOWLEDGE RECORD", prompt)
        self.assertIn("tutorials/2d/index.rst", prompt)
        self.assertEqual(payload["snapshot_id"], manifest["snapshot_id"])
        self.assertEqual(payload["requested_ids"], ["topic:tutorials/2d/index"])
        self.assertEqual(
            payload["records"][0]["source_hash"],
            result.records[0]["source_hash"],
        )
        self.assertTrue(payload["records"][1]["content"])

    def test_budget_marks_truncation_and_bounds_prompt(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        result = KnowledgeRetriever(output).retrieve(
            ["topic:tutorials/2d/index", "entity:TestThing"],
            max_chars=800,
        )

        self.assertTrue(result.truncated)
        self.assertTrue(result.omitted_ids)
        self.assertLessEqual(len(result.to_prompt()), 800)
        self.assertIn("Notice: Context was truncated", result.to_prompt())
        self.assertEqual(result.as_dict()["truncated"], True)
        self.assertLessEqual(len(result.to_json()), 800)

    def test_invalid_ids_and_partial_retrieval(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)
        retriever = KnowledgeRetriever(output)

        strict = retriever.retrieve(["topic:missing", "source:tutorials/2d/movement.rst"])
        self.assertEqual(strict.status, "error")
        self.assertFalse(strict.records)
        self.assertEqual({error.code for error in strict.errors}, {"unknown_id", "unsupported_id"})

        partial = retriever.retrieve(
            ["entity:TestThing", "topic:missing"],
            allow_missing=True,
        )
        self.assertEqual(partial.status, "partial")
        self.assertEqual(partial.records[0]["id"], "entity:TestThing")
        self.assertEqual(partial.errors[0].record_id, "topic:missing")

        with self.assertRaises(ValueError):
            KnowledgeRetriever(output, expected_snapshot="godot-4.0@other")

    def test_mixed_snapshot_record_is_rejected(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)
        entities_path = output / "entities.jsonl"
        entities = [
            json.loads(line)
            for line in entities_path.read_text(encoding="utf-8").splitlines()
        ]
        entities[0]["snapshot_id"] = "godot-4.0@stale"
        entities_path.write_text(
            "\n".join(json.dumps(entity, ensure_ascii=False) for entity in entities) + "\n",
            encoding="utf-8",
        )

        result = KnowledgeRetriever(output).retrieve(["entity:@GlobalScope"])
        self.assertEqual(result.status, "error")
        self.assertEqual(result.errors[0].code, "snapshot_mismatch")

    def test_cli_retrieve_outputs_prompt_and_errors(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "retrieve",
                    "entity:TestThing",
                    "--index",
                    str(output),
                    "--max-chars",
                    "2000",
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertIn("API entity: TestThing", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "retrieve",
                    "entity:Missing",
                    "--index",
                    str(output),
                ]
            )
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ID is not present", stderr.getvalue())

    def test_real_snapshot_retrieval(self) -> None:
        repository_root = Path(__file__).resolve().parents[3]
        output = repository_root / "ai_knowledge"
        if not (output / "manifest.json").exists():
            self.skipTest("generated repository snapshot is not available")

        result = KnowledgeRetriever(output).retrieve(
            [
                "topic:tutorials/physics/physics_introduction",
                "member:CharacterBody2D:method:move_and_slide",
            ]
        )
        self.assertEqual(result.status, "ok")
        record_ids = [record["id"] for record in result.records]
        self.assertEqual(record_ids[0], "topic:tutorials/physics/physics_introduction")
        self.assertIn("chunk:topic:tutorials/physics/physics_introduction:0000", record_ids)
        self.assertIn("member:CharacterBody2D:method:move_and_slide", record_ids)


if __name__ == "__main__":
    unittest.main()

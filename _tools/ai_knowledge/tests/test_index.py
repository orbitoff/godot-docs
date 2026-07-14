from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _tools.ai_knowledge.index import generate
from _tools.ai_knowledge.query import KnowledgeIndex
from _tools.ai_knowledge.validate import validate


FIXTURES = Path(__file__).parent / "fixtures"
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def copy_fixture_tree(destination: Path) -> None:
    for source in FIXTURES.rglob("*"):
        relative = source.relative_to(FIXTURES)
        target = destination / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())


class KnowledgeIndexTests(unittest.TestCase):
    def build_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, Path, dict]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        copy_fixture_tree(root)
        output = root / "ai_knowledge"
        manifest = generate(root, output)
        return temporary, root, output, manifest

    def test_inventory_hierarchy_and_orphans(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        self.assertEqual(manifest["version"], "4.7")
        self.assertEqual(manifest["counts"]["source_files"], 8)
        self.assertEqual(manifest["counts"]["topics"], 5)
        taxonomy = json.loads((output / "taxonomy.json").read_text(encoding="utf-8"))
        orphan = next(page for page in taxonomy["pages"] if page["path"] == "orphan.rst")
        self.assertTrue(orphan["orphan"])
        movement = next(page for page in taxonomy["pages"] if page["path"].endswith("movement.rst"))
        self.assertIn("topic:tutorials/2d/index", movement["parent_ids"])

    def test_api_members_and_relations(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)

        entities = [
            json.loads(line)
            for line in (output / "entities.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        testthing = next(entity for entity in entities if entity.get("name") == "TestThing")
        kinds = {entity["kind"] for entity in entities if entity.get("owner") == testthing["id"]}
        self.assertTrue({"property", "method", "signal", "constant", "theme_icon"} <= kinds)
        self.assertTrue(any(entity.get("name") == "@GlobalScope" for entity in entities))
        relations = [
            json.loads(line)
            for line in (output / "relations.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(
            any(
                relation["relation_type"] == "inherits"
                and relation["source_id"] == "entity:TestThing"
                and relation["target_id"] == "entity:Object"
                for relation in relations
            )
        )
        self.assertTrue(
            any(
                relation["relation_type"] == "inherited_by"
                and relation["source_id"] == "entity:Object"
                and relation["target_id"] == "entity:TestThing"
                for relation in relations
            )
        )
        self.assertEqual(validate(output, root), [])

    def test_query_routing_and_no_match(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)
        index = KnowledgeIndex(output)

        movement = index.search("How do I handle 2D movement?", limit=5)
        self.assertIn(movement["status"], {"ok", "ambiguous"})
        self.assertEqual(movement["matches"][0]["id"], "topic:tutorials/2d/movement")

        class_result = index.search("TestThing", limit=5)
        self.assertEqual(class_result["matches"][0]["id"], "entity:TestThing")
        self.assertEqual(index.search("unknown engine concept")["status"], "no_match")
        with self.assertRaises(ValueError):
            KnowledgeIndex(output, expected_snapshot="godot-4.0@other")

    def test_real_snapshot_domain_queries(self) -> None:
        output = REPOSITORY_ROOT / "ai_knowledge"
        if not (output / "manifest.json").exists():
            self.skipTest("generated repository snapshot is not available")
        index = KnowledgeIndex(output)
        cases = {
            "How do I write GDScript?": {
                "entity:GDScript",
                "topic:tutorials/scripting/gdscript/index",
            },
            "How do I configure input actions?": {
                "entity:Input",
                "topic:tutorials/inputs/index",
            },
            "How do I make a multiplayer game?": {"topic:tutorials/networking/index"},
            "How do I improve rendering performance?": {
                "topic:tutorials/performance/index",
            },
            "How do I make a 2D game?": {
                "topic:getting_started/first_2d_game/index",
            },
            "How do I use Node?": {"entity:Node"},
        }
        for query, expected_ids in cases.items():
            result = index.search(query, limit=10)
            result_ids = {match["id"] for match in result["matches"]}
            self.assertTrue(expected_ids & result_ids, query)

    def test_incremental_change_detection(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)
        movement = root / "tutorials" / "2d" / "movement.rst"
        movement.write_text(movement.read_text(encoding="utf-8") + "\nChanged.\n", encoding="utf-8")
        refreshed = generate(root, output, incremental=True)
        self.assertIn("tutorials/2d/movement.rst", refreshed["change_summary"]["changed"])
        self.assertIn("index.rst", refreshed["change_summary"]["unchanged"])
        self.assertEqual(validate(output, root), [])

    def test_validation_detects_broken_relation(self) -> None:
        temporary, root, output, manifest = self.build_fixture()
        self.addCleanup(temporary.cleanup)
        relations_path = output / "relations.jsonl"
        relation = json.loads(relations_path.read_text(encoding="utf-8").splitlines()[0])
        relation["target_id"] = "entity:Missing"
        relations_path.write_text(json.dumps(relation) + "\n", encoding="utf-8")
        errors = validate(output, root)
        self.assertTrue(any("targets unknown id entity:Missing" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

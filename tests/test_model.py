"""Domain/persistence tests. These do not pretend to run Home Assistant."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from load_modules import model as m, storage as s


class ModelTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.saved = []
        self.notifications = 0
        async def save(doc):
            self.saved.append(deepcopy(doc))
        def notify():
            self.notifications += 1
        self.manager = m.TaskManager(m.initial_data(), save, notify)

    async def op(self, operation, **data):
        return await self.manager.execute(operation, data, "alice")

    def nodes(self, list_id="zakupy"):
        return self.manager.snapshot()["lists"][list_id]["nodes"]

    def assertCode(self, code):
        class Checker:
            def __enter__(inner):
                return inner
            def __exit__(inner, typ, err, tb):
                self.assertIsInstance(err, m.TaskError)
                self.assertEqual(err.code, code)
                return True
        return Checker()

    async def test_initial_tree_and_empty_category(self):
        self.assertEqual(m.aggregate(self.nodes(), "warzywniak"), {"total": 2, "done": 0, "checked": False, "indeterminate": False})
        await self.op("add_item", list_id="zakupy", kind="category", name="Empty", node_id="empty")
        self.assertEqual(m.aggregate(self.nodes(), "empty")["total"], 0)
        self.assertFalse(m.aggregate(self.nodes(), "empty")["checked"])

    async def test_task_drives_partial_then_full_category(self):
        await self.op("set_completed", list_id="zakupy", node_id="kapusta", completed=True)
        self.assertTrue(m.aggregate(self.nodes(), "warzywniak")["indeterminate"])
        await self.op("set_completed", list_id="zakupy", node_id="marchew", completed=True)
        self.assertTrue(m.aggregate(self.nodes(), "warzywniak")["checked"])
        self.assertFalse(self.nodes()["warzywniak"]["completed"])

    async def test_nested_bulk_operation_counts_tasks_once(self):
        await self.op("add_item", list_id="zakupy", kind="category", name="Nested", node_id="nested", parent_id="warzywniak")
        await self.op("add_item", list_id="zakupy", name="Nested task", node_id="nested_task", parent_id="nested")
        result = await self.op("set_completed", list_id="zakupy", node_id="warzywniak", completed=True)
        self.assertEqual(result["affected"], 3)
        self.assertTrue(m.aggregate(self.nodes(), "nested")["checked"])
        self.assertFalse(self.nodes()["chleb"]["completed"])
        result = await self.op("set_completed", list_id="zakupy", node_id="warzywniak", completed=False)
        self.assertEqual(result["affected"], 3)

    async def test_whole_list_completion(self):
        await self.op("set_completed", list_id="zakupy", completed=True)
        self.assertEqual(m.aggregate(self.nodes())["done"], 3)

    async def test_clear_completed_keeps_categories_and_pending(self):
        await self.op("set_completed", list_id="zakupy", node_id="kapusta", completed=True)
        await self.op("clear_completed", list_id="zakupy")
        self.assertNotIn("kapusta", self.nodes())
        self.assertIn("warzywniak", self.nodes())
        self.assertIn("marchew", self.nodes())
        self.assertEqual(self.nodes()["marchew"]["position"], 0)

    async def test_clear_scoped_to_subtree(self):
        await self.op("set_completed", list_id="zakupy", completed=True)
        await self.op("clear_completed", list_id="zakupy", node_id="warzywniak")
        self.assertIn("chleb", self.nodes())
        self.assertEqual(m.aggregate(self.nodes(), "warzywniak")["total"], 0)

    async def test_cycle_and_invalid_parent_do_not_modify_state(self):
        before = self.manager.snapshot()
        with self.assertCode("cycle"):
            await self.op("move_item", list_id="zakupy", node_id="warzywniak", parent_id="warzywniak")
        with self.assertCode("invalid_input"):
            await self.op("add_item", list_id="zakupy", name="No", parent_id="kapusta")
        self.assertEqual(before, self.manager.snapshot())
        self.assertFalse(self.saved)

    async def test_move_into_descendant_rejected(self):
        await self.op("add_item", list_id="zakupy", kind="category", name="Nested", parent_id="warzywniak", node_id="nested")
        with self.assertCode("cycle"):
            await self.op("move_item", list_id="zakupy", node_id="warzywniak", parent_id="nested")

    async def test_reorder_up_down_and_root(self):
        await self.op("move_item", list_id="zakupy", node_id="marchew", parent_id="warzywniak", position=0)
        self.assertEqual([n["id"] for n in m.children(self.nodes(), "warzywniak")], ["marchew", "kapusta"])
        await self.op("move_item", list_id="zakupy", node_id="marchew", parent_id="warzywniak", position=1)
        self.assertEqual([n["id"] for n in m.children(self.nodes(), "warzywniak")], ["kapusta", "marchew"])
        await self.op("move_item", list_id="zakupy", node_id="marchew", parent_id=None)
        self.assertIsNone(self.nodes()["marchew"]["parent_id"])

    async def test_move_category_between_lists_keeps_subtree(self):
        await self.op("create_list", name="Dom", list_id="dom")
        await self.op("move_item", list_id="zakupy", node_id="warzywniak", parent_id=None, target_list_id="dom")
        self.assertEqual(set(self.nodes("dom")), {"warzywniak", "kapusta", "marchew"})
        self.assertEqual(set(self.nodes()), {"piekarnia", "chleb"})
        self.assertEqual(self.nodes("dom")["kapusta"]["parent_id"], "warzywniak")

    async def test_cross_list_id_collision_does_not_lose_items(self):
        await self.op("create_list", name="Dom", list_id="dom")
        await self.op("add_item", list_id="dom", node_id="kapusta", name="Existing")
        before = self.manager.snapshot()
        with self.assertCode("already_exists"):
            await self.op("move_item", list_id="zakupy", node_id="warzywniak", parent_id=None, target_list_id="dom")
        self.assertEqual(before, self.manager.snapshot())

    async def test_delete_category_deletes_descendants(self):
        await self.op("delete_item", list_id="zakupy", node_id="warzywniak")
        self.assertEqual(set(self.nodes()), {"piekarnia", "chleb"})

    async def test_undo_is_own_last_change_only(self):
        before = self.manager.snapshot()
        await self.op("delete_item", list_id="zakupy", node_id="warzywniak")
        self.assertTrue(self.manager.can_undo("alice"))
        with self.assertCode("cannot_undo"):
            await self.manager.execute("undo", {}, "bob", 1)
        await self.manager.execute("undo", {}, "alice", 1)
        self.assertEqual(self.manager.snapshot()["lists"], before["lists"])
        self.assertEqual(self.manager.snapshot()["revision"], 2)
        self.assertFalse(self.manager.can_undo("alice"))

    async def test_other_actor_invalidates_previous_undo(self):
        await self.op("rename_list", list_id="zakupy", name="Groceries")
        await self.manager.execute("rename_list", {"list_id": "zakupy", "name": "Shared"}, "bob")
        self.assertFalse(self.manager.can_undo("alice"))
        self.assertTrue(self.manager.can_undo("bob"))

    async def test_noop_does_not_advance_revision_or_discard_undo(self):
        await self.op("set_completed", list_id="zakupy", node_id="kapusta", completed=True)
        count = len(self.saved)
        result = await self.op("set_completed", list_id="zakupy", node_id="kapusta", completed=True)
        self.assertFalse(result["changed"])
        self.assertEqual(result["revision"], 1)
        self.assertEqual(len(self.saved), count)
        self.assertTrue(self.manager.can_undo("alice"))

    async def test_two_clients_same_revision_one_conflict(self):
        async def add(name):
            return await self.manager.execute("add_item", {"list_id": "zakupy", "name": name}, name, 0)
        results = await asyncio.gather(add("A"), add("B"), return_exceptions=True)
        self.assertEqual(sum(isinstance(result, m.TaskError) and result.code == "conflict" for result in results), 1)
        self.assertEqual(len(self.nodes()), 6)
        self.assertEqual(self.notifications, 1)

    async def test_server_automations_without_revision_are_serialized(self):
        await asyncio.gather(*(self.manager.execute("add_item", {"list_id": "zakupy", "name": str(i)}, "system") for i in range(20)))
        self.assertEqual(len(self.nodes()), 25)
        self.assertEqual(self.manager.snapshot()["revision"], 20)

    async def test_save_failure_rolls_back_and_is_not_published(self):
        async def fail_save(data):
            raise OSError("disk full")
        self.manager._save = fail_save
        before = self.manager.snapshot()
        with self.assertRaises(OSError):
            await self.op("delete_list", list_id="zakupy")
        self.assertEqual(before, self.manager.snapshot())
        self.assertEqual(self.notifications, 0)
        self.assertFalse(self.manager.can_undo("alice"))

    async def test_cancel_waits_for_commit_before_releasing_lock(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def slow_save(data):
            entered.set()
            await release.wait()
        self.manager._save = slow_save
        first = asyncio.create_task(self.op("rename_list", list_id="zakupy", name="First"))
        await entered.wait()
        first.cancel()
        second = asyncio.create_task(self.op("rename_list", list_id="zakupy", name="Second"))
        await asyncio.sleep(0)
        self.assertFalse(second.done())
        release.set()
        with self.assertRaises(asyncio.CancelledError):
            await first
        await second
        self.assertEqual(self.manager.snapshot()["revision"], 2)
        self.assertEqual(self.manager.snapshot()["lists"]["zakupy"]["name"], "Second")

    async def test_import_is_validated_and_keeps_monotonic_revision(self):
        await self.op("rename_list", list_id="zakupy", name="Before import")
        imported = m.initial_data(False)
        imported["revision"] = 999
        await self.manager.execute("import_data", {"document": imported}, "alice", 1)
        self.assertEqual(self.manager.snapshot()["revision"], 2)
        self.assertEqual(self.nodes(), {})
        await self.manager.execute("undo", {}, "alice", 2)
        self.assertIn("kapusta", self.nodes())

    async def test_malformed_import_does_not_replace_data(self):
        bad = self.manager.snapshot()
        bad["lists"]["zakupy"]["nodes"]["warzywniak"]["parent_id"] = "warzywniak"
        before = self.manager.snapshot()
        with self.assertCode("invalid_input"):
            await self.manager.execute("import_data", {"document": bad}, "alice", 0)
        self.assertEqual(before, self.manager.snapshot())

    async def test_destructive_restore_requires_revision(self):
        with self.assertCode("invalid_input"):
            await self.manager.execute("import_data", {"document": m.initial_data()}, "alice")
        with self.assertCode("invalid_input"):
            await self.manager.execute("undo", {}, "alice")

    async def test_names_whitespace_and_unsafe_html_are_plain_data(self):
        await self.op("add_item", list_id="zakupy", name="  <img src=x onerror=alert(1)>  ", node_id="html")
        self.assertEqual(self.nodes()["html"]["name"], "<img src=x onerror=alert(1)>")
        for name in ("", "   ", "x" * 201, "line\nbreak", 123):
            with self.assertCode("invalid_input"):
                await self.op("add_item", list_id="zakupy", name=name)

    async def test_invalid_types_ids_unknown_fields_and_duplicate_ids(self):
        for value in ("true", 1, None):
            with self.assertCode("invalid_input"):
                await self.op("set_completed", list_id="zakupy", completed=value)
        for value in ("../x", "UpperCase", "", "a/b", True):
            with self.assertCode("invalid_input"):
                await self.op("create_list", list_id=value, name="Bad")
        with self.assertCode("invalid_input"):
            await self.op("add_item", list_id="zakupy", name="No", typo="x")
        with self.assertCode("already_exists"):
            await self.op("add_item", list_id="zakupy", name="Existing", node_id="kapusta")

    async def test_set_list_access_roundtrip_and_validation(self):
        result = await self.op("set_list_access", list_id="zakupy", access={"user-a": "read", "user-b": "write"})
        self.assertEqual(result["shared_users"], 2)
        self.assertEqual(self.manager.snapshot()["lists"]["zakupy"]["access"], {"user-a": "read", "user-b": "write"})
        with self.assertCode("invalid_input"):
            await self.op("set_list_access", list_id="zakupy", access={"user": "owner"})
        with self.assertCode("invalid_input"):
            await self.op("set_list_access", list_id="zakupy", access=[])

    async def test_legacy_schema_migrates_to_private_v2(self):
        legacy = m.initial_data()
        legacy["schema"] = 1
        for task_list in legacy["lists"].values():
            task_list.pop("access")
        migrated = m.validate_document(legacy)
        self.assertEqual(migrated["schema"], 2)
        self.assertEqual(migrated["lists"]["zakupy"]["access"], {})
        self.assertEqual(legacy["schema"], 1)
        self.assertNotIn("access", legacy["lists"]["zakupy"])

    async def test_depth_limit(self):
        parent = None
        for index in range(m.MAX_DEPTH):
            node_id = f"level{index}"
            await self.op("add_item", list_id="zakupy", name=node_id, node_id=node_id, kind="category", parent_id=parent)
            parent = node_id
        before = self.manager.snapshot()
        with self.assertCode("invalid_input"):
            await self.op("add_item", list_id="zakupy", name="Too deep", parent_id=parent)
        self.assertEqual(before, self.manager.snapshot())

    async def test_list_limit(self):
        with patch.object(m, "MAX_LISTS", 2):
            await self.op("create_list", name="Two")
            with self.assertCode("invalid_input"):
                await self.op("create_list", name="Three")

    async def test_item_limit(self):
        with patch.object(m, "MAX_NODES", 5):
            with self.assertCode("invalid_input"):
                await self.op("add_item", list_id="zakupy", name="Too many")

    async def test_snapshot_cannot_mutate_internal_data(self):
        snapshot = self.manager.snapshot()
        snapshot["lists"].clear()
        self.assertIn("zakupy", self.manager.snapshot()["lists"])

    async def test_unload_prevents_writes(self):
        await self.manager.close()
        with self.assertCode("not_ready"):
            await self.op("delete_list", list_id="zakupy")


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / ".storage" / "hierarchical_tasks.json"

    def test_missing_file(self):
        self.assertIsNone(s.read_document(self.path))

    def test_roundtrip_private_file(self):
        data = m.initial_data()
        s.write_document(self.path, data)
        self.assertEqual(s.read_document(self.path), data)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertFalse(list(self.path.parent.glob("*.tmp")))

    def test_invalid_json_is_not_overwritten(self):
        self.path.parent.mkdir()
        self.path.write_text("{broken")
        with self.assertRaises(m.TaskError):
            s.read_document(self.path)
        self.assertEqual(self.path.read_text(), "{broken")

    def test_future_schema_is_not_silently_accepted(self):
        self.path.parent.mkdir()
        data = m.initial_data(); data["schema"] = 99
        self.path.write_text(json.dumps(data))
        with self.assertRaises(m.TaskError):
            s.read_document(self.path)
        self.assertEqual(json.loads(self.path.read_text())["schema"], 99)

    def test_replace_failure_preserves_previous_file(self):
        first = m.initial_data()
        s.write_document(self.path, first)
        with patch.object(s.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                s.write_document(self.path, m.empty_data())
        self.assertEqual(s.read_document(self.path), first)
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_fsync_failure_preserves_previous_file(self):
        s.write_document(self.path, m.initial_data())
        with patch.object(s.os, "fsync", side_effect=OSError("fsync error")):
            with self.assertRaises(OSError):
                s.write_document(self.path, m.empty_data())
        self.assertEqual(s.read_document(self.path), m.initial_data())

    def test_file_limit(self):
        self.path.parent.mkdir()
        self.path.write_bytes(b"x" * 101)
        with patch.object(s, "MAX_FILE_BYTES", 100):
            with self.assertRaises(m.TaskError):
                s.read_document(self.path)


if __name__ == "__main__":
    unittest.main()

"""Per-list access policy tests with tiny HA type stubs, NOT a real HA runtime."""
import importlib
import sys
import types
import unittest
from unittest.mock import patch

from load_modules import model


def load_runtime():
    stubs = {name: types.ModuleType(name) for name in ("homeassistant", "homeassistant.core")}
    stubs["homeassistant.core"].HomeAssistant = object
    with patch.dict(sys.modules, stubs):
        return importlib.import_module("ht_test_package.runtime")


r = load_runtime()


def user(user_id="user", *, admin=False, active=True):
    return types.SimpleNamespace(id=user_id, is_admin=admin, is_active=active)


def make_runtime(*, zakupy=None, dom=None):
    async def save(data):
        pass

    data = model.initial_data()
    data["lists"]["zakupy"]["access"] = dict(zakupy or {})
    if dom is not None:
        model.apply_operation(data, "create_list", {"list_id": "dom", "name": "Dom"})
        data["lists"]["dom"]["access"] = dict(dom)
    return r.Runtime(model.TaskManager(data, save, lambda: None))


class AccessTests(unittest.TestCase):
    def test_admin_always_has_full_access(self):
        runtime = make_runtime()
        admin = user("admin", admin=True)
        self.assertEqual(r.list_role(runtime, admin, "zakupy"), "admin")
        out = r.payload(runtime, admin)
        self.assertIn("zakupy", out["data"]["lists"])
        self.assertTrue(out["permissions"]["lists"]["zakupy"]["manage"])
        self.assertIn("access", out["data"]["lists"]["zakupy"])

    def test_unshared_user_sees_no_lists(self):
        runtime = make_runtime()
        out = r.payload(runtime, user())
        self.assertEqual(out["data"]["lists"], {})
        self.assertEqual(out["permissions"]["lists"], {})
        self.assertFalse(out["permissions"]["write"])

    def test_write_share_allows_item_changes_but_hides_acl(self):
        runtime = make_runtime(zakupy={"user": "write"})
        regular = user()
        out = r.payload(runtime, regular)
        self.assertEqual(out["permissions"]["lists"]["zakupy"]["role"], "write")
        self.assertTrue(out["permissions"]["lists"]["zakupy"]["write"])
        self.assertNotIn("access", out["data"]["lists"]["zakupy"])
        r.authorize_operation(runtime, regular, "add_item", {"list_id": "zakupy", "name": "Mleko"})

    def test_read_share_is_visible_but_not_editable(self):
        runtime = make_runtime(zakupy={"user": "read"})
        regular = user()
        out = r.payload(runtime, regular)
        self.assertEqual(out["permissions"]["lists"]["zakupy"]["role"], "read")
        self.assertFalse(out["permissions"]["lists"]["zakupy"]["write"])
        with self.assertRaises(model.TaskError) as err:
            r.authorize_operation(runtime, regular, "add_item", {"list_id": "zakupy", "name": "Mleko"})
        self.assertEqual(err.exception.code, "forbidden")

    def test_inactive_and_missing_users_are_denied(self):
        runtime = make_runtime(zakupy={"user": "write"})
        with self.assertRaises(model.TaskError):
            r.payload(runtime, None)
        with self.assertRaises(model.TaskError):
            r.payload(runtime, user(active=False))

    def test_lists_are_filtered_independently(self):
        runtime = make_runtime(zakupy={"user": "write"}, dom={"other": "write"})
        self.assertEqual(set(r.payload(runtime, user())["data"]["lists"]), {"zakupy"})
        self.assertEqual(set(r.payload(runtime, user("other"))["data"]["lists"]), {"dom"})

    def test_list_management_and_sharing_are_admin_only(self):
        runtime = make_runtime(zakupy={"user": "write"})
        regular = user()
        for operation, data in (
            ("create_list", {"name": "Nowa"}),
            ("rename_list", {"list_id": "zakupy", "name": "Sklep"}),
            ("delete_list", {"list_id": "zakupy"}),
            ("set_list_access", {"list_id": "zakupy", "access": {"other": "read"}}),
            ("import_data", {"document": model.initial_data(False)}),
        ):
            with self.subTest(operation=operation):
                with self.assertRaises(model.TaskError) as err:
                    r.authorize_operation(runtime, regular, operation, data)
                self.assertEqual(err.exception.code, "forbidden")

    def test_move_requires_write_on_both_lists(self):
        runtime = make_runtime(zakupy={"user": "write"}, dom={"user": "read"})
        data = {"list_id": "zakupy", "node_id": "kapusta", "target_list_id": "dom", "parent_id": None}
        with self.assertRaises(model.TaskError):
            r.authorize_operation(runtime, user(), "move_item", data)
        runtime = make_runtime(zakupy={"user": "write"}, dom={"user": "write"})
        r.authorize_operation(runtime, user(), "move_item", data)


if __name__ == "__main__":
    unittest.main()

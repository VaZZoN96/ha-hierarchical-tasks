"""Access policy unit tests with tiny HA type stubs, NOT a real HA runtime."""
import importlib
import sys
import types
import unittest
from unittest.mock import patch

from load_modules import model


def load_runtime():
    stubs = {}
    for name in ("homeassistant", "homeassistant.auth", "homeassistant.auth.permissions", "homeassistant.auth.permissions.const", "homeassistant.core"):
        stubs[name] = types.ModuleType(name)
    stubs["homeassistant.auth.permissions.const"].POLICY_CONTROL = "control"
    stubs["homeassistant.auth.permissions.const"].POLICY_READ = "read"
    stubs["homeassistant.core"].HomeAssistant = object
    with patch.dict(sys.modules, stubs):
        return importlib.import_module("ht_test_package.runtime")


r = load_runtime()


class Permissions:
    def __init__(self, read=True, write=True):
        self.read = read
        self.write = write
    def access_all_entities(self, policy):
        return self.write if policy == "control" else self.read


def user(admin=False, active=True, read=True, write=True):
    return types.SimpleNamespace(id="user", is_admin=admin, is_active=active, permissions=Permissions(read, write))


class AccessTests(unittest.TestCase):
    def setUp(self):
        async def save(data):
            pass
        self.runtime = r.Runtime(model.TaskManager(model.initial_data(), save, lambda: None))

    def test_default_is_admin_only(self):
        self.assertTrue(r.has_access(self.runtime, user(admin=True), write=True))
        self.assertFalse(r.has_access(self.runtime, user()))

    def test_shared_regular_user_can_read_and_write(self):
        self.runtime.share_with_users = True
        self.assertTrue(r.has_access(self.runtime, user()))
        self.assertTrue(r.has_access(self.runtime, user(), write=True))

    def test_read_only_user_cannot_write(self):
        self.runtime.share_with_users = True
        readonly = user(write=False)
        self.assertTrue(r.has_access(self.runtime, readonly))
        self.assertFalse(r.has_access(self.runtime, readonly, write=True))
        self.assertFalse(r.payload(self.runtime, readonly)["permissions"]["write"])

    def test_restricted_custom_policy_is_denied(self):
        self.runtime.share_with_users = True
        self.assertFalse(r.has_access(self.runtime, user(read=False, write=False)))

    def test_inactive_and_missing_users_are_denied(self):
        self.runtime.share_with_users = True
        self.assertFalse(r.has_access(self.runtime, None))
        self.assertFalse(r.has_access(self.runtime, user(admin=True, active=False)))

    def test_import_requires_admin(self):
        self.runtime.share_with_users = True
        with self.assertRaises(model.TaskError):
            r.authorize(self.runtime, user(), write=True, admin=True)
        r.authorize(self.runtime, user(admin=True), write=True, admin=True)

    def test_payload_does_not_disclose_data_when_forbidden(self):
        with self.assertRaises(model.TaskError) as err:
            r.payload(self.runtime, user())
        self.assertEqual(err.exception.code, "forbidden")

    def test_sharing_revocation_takes_effect_on_next_check(self):
        self.runtime.share_with_users = True
        self.assertTrue(r.payload(self.runtime, user())["available"])
        self.runtime.share_with_users = False
        with self.assertRaises(model.TaskError):
            r.payload(self.runtime, user())


if __name__ == "__main__":
    unittest.main()

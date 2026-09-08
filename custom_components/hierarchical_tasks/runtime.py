"""Home Assistant runtime and explicit per-list access policy."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant

from .const import API_VERSION, DOMAIN
from .model import TaskError, TaskManager, check_fields


@dataclass
class Runtime:
    manager: TaskManager


def get_runtime(hass: HomeAssistant) -> Runtime:
    runtime = hass.data.get(DOMAIN, {}).get("runtime")
    if runtime is None or not runtime.manager.active:
        raise TaskError("not_ready", "Add/enable Hierarchical Tasks in Settings > Devices & services.")
    return runtime


def _active_user(user: Any) -> bool:
    return user is not None and bool(user.is_active)


def list_role(runtime: Runtime, user: Any, list_id: str) -> str | None:
    """Return the effective Hierarchical Tasks role: admin/write/read/None."""
    if not _active_user(user):
        return None
    task_list = runtime.manager.snapshot()["lists"].get(list_id)
    if task_list is None:
        return None
    if user.is_admin:
        return "admin"
    role = task_list.get("access", {}).get(user.id)
    return role if role in ("read", "write") else None


def has_list_access(runtime: Runtime, user: Any, list_id: str, *, write: bool = False) -> bool:
    role = list_role(runtime, user, list_id)
    return role in (("admin", "write") if write else ("admin", "write", "read"))


def authorize_operation(runtime: Runtime, user: Any, operation: str, data: dict) -> None:
    """Authorize one mutation without ever trusting frontend filtering."""
    if not _active_user(user):
        raise TaskError("forbidden", "Access denied.")
    check_fields(operation, data)

    if user.is_admin:
        return

    # List lifecycle, ACL and full import are administrative operations.
    if operation in {"create_list", "rename_list", "delete_list", "set_list_access", "import_data"}:
        raise TaskError("forbidden", "Only a Home Assistant administrator can manage lists or sharing.")

    if operation == "undo":
        if not runtime.manager.can_undo(user.id):
            raise TaskError("cannot_undo", "Only your own most recent change can be undone.")
        if not any(
            has_list_access(runtime, user, list_id, write=True)
            for list_id in runtime.manager.snapshot()["lists"]
        ):
            raise TaskError("forbidden", "You no longer have edit access to the affected lists.")
        return

    list_id = data.get("list_id")
    if not isinstance(list_id, str) or not has_list_access(runtime, user, list_id, write=True):
        raise TaskError("forbidden", "This list is not shared with you for editing.")

    if operation == "move_item":
        target_id = data.get("target_list_id", list_id)
        if not isinstance(target_id, str) or not has_list_access(runtime, user, target_id, write=True):
            raise TaskError("forbidden", "You need edit access to both the source and destination lists.")


def data_for_user(runtime: Runtime, user: Any) -> dict:
    """Return only lists visible to a user; strip ACL identities for non-admins."""
    if not _active_user(user):
        raise TaskError("forbidden", "Access denied.")
    snapshot = runtime.manager.snapshot()
    if user.is_admin:
        return snapshot

    visible: dict[str, dict] = {}
    for list_id, task_list in snapshot["lists"].items():
        if not has_list_access(runtime, user, list_id):
            continue
        clean = deepcopy(task_list)
        clean.pop("access", None)
        visible[list_id] = clean
    return {"schema": snapshot["schema"], "revision": snapshot["revision"], "lists": visible}


def payload(runtime: Runtime, user: Any) -> dict:
    data = data_for_user(runtime, user)
    list_permissions: dict[str, dict[str, bool | str]] = {}
    for list_id in data["lists"]:
        role = list_role(runtime, user, list_id)
        list_permissions[list_id] = {
            "read": role is not None,
            "write": role in ("admin", "write"),
            "manage": role == "admin",
            "role": role or "none",
        }
    can_write_any = any(item["write"] for item in list_permissions.values())
    is_admin = bool(user.is_admin)
    return {
        "api_version": API_VERSION,
        "available": True,
        "data": data,
        "permissions": {
            "admin": is_admin,
            "write": can_write_any,
            "create_list": is_admin,
            "import": is_admin,
            "undo": (is_admin or can_write_any) and runtime.manager.can_undo(user.id),
            "lists": list_permissions,
        },
    }

"""Home Assistant runtime and explicit access policy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.auth.permissions.const import POLICY_CONTROL, POLICY_READ
from homeassistant.core import HomeAssistant

from .const import API_VERSION, DOMAIN
from .model import TaskError, TaskManager


@dataclass
class Runtime:
    manager: TaskManager
    share_with_users: bool = False


def get_runtime(hass: HomeAssistant) -> Runtime:
    runtime = hass.data.get(DOMAIN, {}).get("runtime")
    if runtime is None or not runtime.manager.active:
        raise TaskError("not_ready", "Add/enable Hierarchical Tasks in Settings > Devices & services.")
    return runtime


def has_access(runtime: Runtime, user: Any, *, write: bool = False) -> bool:
    if user is None or not user.is_active:
        return False
    if user.is_admin:
        return True
    if not runtime.share_with_users:
        return False
    # Do not bypass Home Assistant's read-only user group. Restrictive custom
    # policies are refused because our data has no entity-based ACL mapping.
    return user.permissions.access_all_entities(POLICY_CONTROL if write else POLICY_READ)


def authorize(runtime: Runtime, user: Any, *, write: bool = False, admin: bool = False) -> None:
    if not has_access(runtime, user, write=write) or (admin and not user.is_admin):
        raise TaskError("forbidden", "Access denied. Check integration sharing settings and HA permissions.")


def payload(runtime: Runtime, user: Any) -> dict:
    authorize(runtime, user)
    can_write = has_access(runtime, user, write=True)
    return {
        "api_version": API_VERSION,
        "available": True,
        "data": runtime.manager.snapshot(),
        "permissions": {
            "write": can_write,
            "import": user.is_admin,
            "undo": can_write and runtime.manager.can_undo(user.id),
        },
    }

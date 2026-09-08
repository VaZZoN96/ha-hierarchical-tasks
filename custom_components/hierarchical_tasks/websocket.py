"""Authenticated custom WebSocket commands; no public data endpoints."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_UPDATED
from .model import TaskError
from .runtime import authorize_operation, get_runtime, payload

_LOGGER = logging.getLogger(__name__)
REVISION = vol.All(int, vol.Range(min=0))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/get"})
@callback
def ws_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        connection.send_result(msg["id"], payload(get_runtime(hass), connection.user))
    except TaskError as err:
        connection.send_error(msg["id"], err.code, str(err))


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/subscribe"})
@callback
def ws_subscribe(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        first = payload(get_runtime(hass), connection.user)
    except TaskError as err:
        connection.send_error(msg["id"], err.code, str(err))
        return

    @callback
    def updated() -> None:
        # Re-evaluate ACLs on every notification, including sharing changes.
        try:
            event = payload(get_runtime(hass), connection.user)
        except TaskError as err:
            event = {"available": False, "error": {"code": err.code, "message": str(err)}}
        connection.send_event(msg["id"], event)

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, SIGNAL_UPDATED, updated)
    connection.send_result(msg["id"])
    connection.send_event(msg["id"], first)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/users"})
@websocket_api.async_response
async def ws_users(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Return only the minimal user metadata needed by the ACL editor."""
    if not connection.user.is_active or not connection.user.is_admin:
        connection.send_error(msg["id"], "forbidden", "Only an administrator can manage sharing.")
        return
    users = await hass.auth.async_get_users()
    connection.send_result(
        msg["id"],
        [
            {
                "id": user.id,
                "name": user.name or user.id,
                "is_active": bool(user.is_active),
                "is_admin": bool(user.is_admin),
            }
            for user in users
            if not user.system_generated
        ],
    )


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/mutate",
    vol.Required("operation"): str,
    vol.Required("data"): dict,
    vol.Required("expected_revision"): REVISION,
})
@websocket_api.async_response
async def ws_mutate(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    try:
        runtime = get_runtime(hass)
        authorize_operation(runtime, connection.user, msg["operation"], msg["data"])
        result = await runtime.manager.execute(
            msg["operation"], msg["data"], connection.user.id, msg["expected_revision"]
        )
        connection.send_result(msg["id"], result)
    except TaskError as err:
        connection.send_error(msg["id"], err.code, str(err))
    except OSError:
        _LOGGER.exception("Could not persist Hierarchical Tasks data")
        connection.send_error(msg["id"], "storage_error", "Could not save data. Check disk space and HA logs.")
    except Exception:
        _LOGGER.exception("Unexpected Hierarchical Tasks command error")
        connection.send_error(msg["id"], "unknown_error", "Unexpected error. Check HA logs.")


@callback
def async_register(hass: HomeAssistant) -> None:
    for handler in (ws_get, ws_subscribe, ws_users, ws_mutate):
        websocket_api.async_register_command(hass, handler)

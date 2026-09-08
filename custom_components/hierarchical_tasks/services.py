"""Actions for automations; same validation and per-list permission checks."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .const import DOMAIN
from .model import FIELDS, TaskError
from .runtime import authorize_operation, data_for_user, get_runtime

_LOGGER = logging.getLogger(__name__)


def field_validator(key: str):
    if key in ("parent_id", "node_id"):
        return vol.Any(None, str)
    if key in ("position", "expected_revision"):
        return vol.All(int, vol.Range(min=0))
    if key == "completed":
        return bool
    if key in ("document", "access"):
        return dict
    return str


@callback
def async_register(hass: HomeAssistant) -> None:
    async def handle(call: ServiceCall):
        try:
            runtime = get_runtime(hass)
            user_id = call.context.user_id
            user = await hass.auth.async_get_user(user_id) if user_id is not None else None

            if call.service == "get_data":
                # Calls without user context are trusted HA automations/scripts.
                return runtime.manager.snapshot() if user is None else data_for_user(runtime, user)

            data = dict(call.data)
            revision = data.pop("expected_revision", None)
            if user is not None:
                authorize_operation(runtime, user, call.service, data)
            result = await runtime.manager.execute(call.service, data, user_id or "system", revision)
            return result if call.return_response else None
        except TaskError as err:
            raise ServiceValidationError(f"{err.code}: {err}") from err
        except OSError as err:
            _LOGGER.exception("Could not persist Hierarchical Tasks data")
            raise HomeAssistantError("Could not save tasks. Check disk space and HA logs.") from err

    hass.services.async_register(
        DOMAIN, "get_data", handle, schema=vol.Schema({}), supports_response=SupportsResponse.ONLY
    )
    for operation, (required, optional) in FIELDS.items():
        schema = {vol.Required(key): field_validator(key) for key in required}
        schema.update({vol.Optional(key): field_validator(key) for key in optional})
        revision_key = vol.Required if operation in ("undo", "import_data") else vol.Optional
        schema[revision_key("expected_revision")] = field_validator("expected_revision")
        hass.services.async_register(
            DOMAIN, operation, handle, schema=vol.Schema(schema), supports_response=SupportsResponse.OPTIONAL
        )

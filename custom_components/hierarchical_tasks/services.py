"""Actions for automations; the same domain validation and permission checks."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .const import DOMAIN
from .model import FIELDS, TaskError
from .runtime import authorize, get_runtime

_LOGGER = logging.getLogger(__name__)


def field_validator(key: str):
    if key in ("parent_id", "node_id"):
        return vol.Any(None, str)
    if key in ("position", "expected_revision"):
        return vol.All(int, vol.Range(min=0))
    if key == "completed":
        return bool
    if key == "document":
        return dict
    return str


@callback
def async_register(hass: HomeAssistant) -> None:
    async def handle(call: ServiceCall):
        try:
            runtime = get_runtime(hass)
            user_id = call.context.user_id
            if user_id is not None:
                user = await hass.auth.async_get_user(user_id)
                authorize(runtime, user, write=call.service != "get_data", admin=call.service == "import_data")
            # Calls without a user context are trusted HA automations/scripts.
            if call.service == "get_data":
                return runtime.manager.snapshot()
            data = dict(call.data)
            revision = data.pop("expected_revision", None)
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

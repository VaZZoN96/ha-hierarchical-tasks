"""Hierarchical Tasks: local task trees and a bundled Lovelace card."""
from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType

from . import services, websocket
from .const import CARD_URL, CONF_EXAMPLE, DOMAIN, SIGNAL_UPDATED, STORAGE_FILE, VERSION
from .model import TaskError, TaskManager, initial_data
from .runtime import Runtime
from .storage import read_document, write_document


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register actions, WebSocket commands and the bundled frontend card."""
    hass.data.setdefault(DOMAIN, {})
    await hass.http.async_register_static_paths([
        StaticPathConfig(
            CARD_URL,
            str(Path(__file__).parent / "frontend" / "hierarchical-tasks-card.js"),
            False,
        )
    ])
    # Load the bundled card globally. This removes the old manual Lovelace
    # Resources step that could lead to "Custom element doesn't exist".
    add_extra_js_url(hass, f"{CARD_URL}?v={VERSION}")
    services.async_register(hass)
    websocket.async_register(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    path = Path(hass.config.path(STORAGE_FILE))
    try:
        data = await hass.async_add_executor_job(read_document, path)
        if data is None:
            data = initial_data(entry.data.get(CONF_EXAMPLE, True))
            await hass.async_add_executor_job(write_document, path, data)
    except TaskError as err:
        raise ConfigEntryError(f"Invalid task storage: {err}. The original file was not modified.") from err
    except OSError as err:
        raise ConfigEntryNotReady(f"Could not access task storage: {err}") from err

    async def save(new_data: dict) -> None:
        await hass.async_add_executor_job(write_document, path, new_data)

    def notify() -> None:
        async_dispatcher_send(hass, SIGNAL_UPDATED)

    hass.data[DOMAIN]["runtime"] = Runtime(TaskManager(data, save, notify))
    notify()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    runtime = hass.data[DOMAIN].get("runtime")
    if runtime is not None:
        await runtime.manager.close()
        hass.data[DOMAIN].pop("runtime", None)
    async_dispatcher_send(hass, SIGNAL_UPDATED)
    # Removing the config entry deliberately DOES NOT delete the user's lists.
    return True

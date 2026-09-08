"""UI-only configuration with one shared storage instance."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import CONF_EXAMPLE, DOMAIN, NAME


class HierarchicalTasksConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title=NAME, data=user_input)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Optional(CONF_EXAMPLE, default=True): bool,
        }))

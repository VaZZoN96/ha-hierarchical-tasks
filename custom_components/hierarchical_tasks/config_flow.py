"""UI-only configuration with one shared storage instance."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_EXAMPLE, CONF_SHARE, DOMAIN, NAME


class HierarchicalTasksConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title=NAME, data=user_input)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Optional(CONF_EXAMPLE, default=True): bool,
            vol.Optional(CONF_SHARE, default=False): bool,
        }))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HierarchicalTasksOptionsFlow()


class HierarchicalTasksOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = self.config_entry.options.get(CONF_SHARE, self.config_entry.data.get(CONF_SHARE, False))
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Optional(CONF_SHARE, default=current): bool,
        }))

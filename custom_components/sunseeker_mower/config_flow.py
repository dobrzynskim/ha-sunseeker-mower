"""Config flow dla integracji Sunseeker / Bugull Mower."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SunseekerApiClient, SunseekerApiError, SunseekerAuthError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _async_validate_login(hass: HomeAssistant, email: str, password: str) -> None:
    """Probuje sie zalogowac - rzuca wyjatkiem, jesli sie nie uda."""
    session = async_get_clientsession(hass)
    client = SunseekerApiClient(session, email, password)
    await client.async_login()
    # sprawdzmy tez, czy w ogole widac jakies urzadzenia na koncie
    devices = await client.async_get_devices()
    if not devices:
        raise NoDevicesFound


class NoDevicesFound(Exception):
    """Zalogowano sie poprawnie, ale konto nie ma powiazanych kosiarek."""


class SunseekerMowerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow integracji."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_login(self.hass, email, password)
            except SunseekerAuthError:
                errors["base"] = "invalid_auth"
            except NoDevicesFound:
                errors["base"] = "no_devices_found"
            except SunseekerApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Nieoczekiwany blad podczas walidacji logowania")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Kosiarka ({email})",
                    data={CONF_EMAIL: email, CONF_PASSWORD: password},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Wywolywane automatycznie przez HA, gdy token/haslo przestana dzialac."""
        self._reauth_email = entry_data.get(CONF_EMAIL)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            try:
                await _async_validate_login(self.hass, self._reauth_email, password)
            except SunseekerAuthError:
                errors["base"] = "invalid_auth"
            except SunseekerApiError:
                errors["base"] = "cannot_connect"
            else:
                existing_entry = await self.async_set_unique_id(self._reauth_email.lower())
                if existing_entry:
                    self.hass.config_entries.async_update_entry(
                        existing_entry,
                        data={CONF_EMAIL: self._reauth_email, CONF_PASSWORD: password},
                    )
                    await self.hass.config_entries.async_reload(existing_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders={"email": self._reauth_email},
        )

"""Integracja Sunseeker / Bugull Mower dla Home Assistant."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SunseekerApiClient, SunseekerApiError, SunseekerAuthError
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


class MowerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Koordynator cyklicznie pobierajacy dane wszystkich kosiarek na koncie."""

    def __init__(self, hass: HomeAssistant, client: SunseekerApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            return await self.client.async_get_all_records()
        except SunseekerAuthError as err:
            # Zglaszamy do HA, ze potrzebny jest reauth flow (formularz logowania)
            raise ConfigEntryAuthFailed(str(err)) from err
        except SunseekerApiError as err:
            raise UpdateFailed(str(err)) from err


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguruje integracje na podstawie wpisu utworzonego przez config_flow."""
    session = async_get_clientsession(hass)
    # hass.config.language to np. "pl" albo "en" - przekazujemy jako Accept-Language,
    # serwer producenta wspiera lokalizacje tekstow statusu (widoczne w kodzie apki)
    language = hass.config.language or "en"
    client = SunseekerApiClient(
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        language=language,
    )

    coordinator = MowerDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usuwa integracje."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

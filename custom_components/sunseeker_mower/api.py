"""Klient API dla platformy Bugull / Sunseeker (server.sk-robot.com)."""
from __future__ import annotations

import logging
import time
from typing import Any

import aiohttp

from .const import BASE_URL, BASIC_AUTH_HEADER

_LOGGER = logging.getLogger(__name__)


class SunseekerApiError(Exception):
    """Blad komunikacji z API."""


class SunseekerAuthError(SunseekerApiError):
    """Bledny login/haslo lub wygasly refresh_token."""


class SunseekerApiClient:
    """Owija logowanie, odswiezanie tokena i zapytania o dane kosiarki."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        language: str = "en",
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        # Serwer wspiera Accept-Language (widoczne w zdekompilowanym kodzie apki) -
        # wysylamy je, zeby workStatusName/faultStatusName wracaly w naszym jezyku
        # zamiast domyslnego chinskiego. Jesli serwer nie wspiera danego jezyka,
        # i tak polegamy glownie na wlasnym mapowaniu kodow (STATUS_CODE_TO_KEY).
        self._language = language

        self._access_token: str | None = None
        self._token_type: str = "bearer"
        self._refresh_token: str | None = None
        self._expires_in: int = 0
        self._fetched_at: float = 0.0

    # ------------------------------------------------------------------
    # Autoryzacja
    # ------------------------------------------------------------------

    async def async_login(self) -> None:
        """Loguje sie od zera przy pomocy email/haslo."""
        data = {
            "username": self._email,
            "password": self._password,
            "grant_type": "password",
            "scope": "server",
        }
        await self._async_token_request(data)

    async def _async_refresh(self) -> None:
        """Odswieza token uzywajac refresh_token."""
        if not self._refresh_token:
            await self.async_login()
            return
        data = {
            "refresh_token": self._refresh_token,
            "grant_type": "refresh_token",
            "scope": "server",
        }
        try:
            await self._async_token_request(data)
        except SunseekerApiError:
            # refresh_token mogl wygasnac - sprobuj pelnego logowania
            await self.async_login()

    async def _async_token_request(self, form_data: dict[str, str]) -> None:
        headers = {
            "Authorization": BASIC_AUTH_HEADER,
            "Accept-Language": self._language,
        }
        url = BASE_URL + "auth/oauth/token"
        try:
            async with self._session.post(url, headers=headers, data=form_data) as resp:
                if resp.status == 401 or resp.status == 400:
                    raise SunseekerAuthError(f"Auth failed: HTTP {resp.status}")
                resp.raise_for_status()
                payload = await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise SunseekerApiError(f"Blad polaczenia przy logowaniu: {err}") from err

        if "access_token" not in payload:
            raise SunseekerAuthError(f"Brak access_token w odpowiedzi: {payload}")

        self._access_token = payload["access_token"]
        self._token_type = payload.get("token_type", "bearer")
        self._refresh_token = payload.get("refresh_token")
        self._expires_in = payload.get("expires_in", 0)
        self._fetched_at = time.time()

    async def _async_ensure_token(self) -> None:
        if self._access_token is None:
            await self.async_login()
            return
        age = time.time() - self._fetched_at
        # odswiez z wyprzedzeniem 1 dnia przed wygasnieciem
        if age >= max(self._expires_in - 86400, 0):
            await self._async_refresh()

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"{self._token_type} {self._access_token}",
            "Accept-Language": self._language,
        }

    # ------------------------------------------------------------------
    # Zapytania o dane
    # ------------------------------------------------------------------

    async def _async_get(self, path: str) -> Any:
        await self._async_ensure_token()
        url = BASE_URL + path
        try:
            async with self._session.get(url, headers=self._auth_headers()) as resp:
                if resp.status == 401:
                    # token odrzucony mimo lokalnego cache - wymus pelny relogin i powtorz raz
                    await self.async_login()
                    async with self._session.get(url, headers=self._auth_headers()) as resp2:
                        resp2.raise_for_status()
                        return await resp2.json(content_type=None)
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except aiohttp.ClientError as err:
            raise SunseekerApiError(f"Blad polaczenia: {err}") from err

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Zwraca liste urzadzen powiazanych z kontem."""
        payload = await self._async_get("app_mower/device-user/list")
        return payload.get("data") or []

    async def async_get_record(self, sn: str) -> dict[str, Any]:
        """Zwraca rekord statystyk (powierzchnia, godziny pracy, bateria...) dla danego SN."""
        payload = await self._async_get(f"app_mower/device-record/getRecord/{sn}")
        return payload.get("data") or {}

    async def async_get_all_records(self) -> dict[str, dict[str, Any]]:
        """Pobiera liste urzadzen i rekord danych dla kazdego z nich.

        Zwraca slownik {sn: {"name": ..., "record": {...}}}.
        """
        devices = await self.async_get_devices()
        result: dict[str, dict[str, Any]] = {}
        for dev in devices:
            sn = dev.get("deviceSn")
            if not sn:
                continue
            record = await self.async_get_record(sn)
            result[sn] = {
                "name": dev.get("deviceName") or "Kosiarka",
                "model": dev.get("deviceModelName") or dev.get("modelName"),
                "record": record,
            }
        return result

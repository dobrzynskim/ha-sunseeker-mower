"""Sensory dla integracji Sunseeker / Bugull Mower."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FAULT_CODE_TO_KEY,
    FAULT_UNKNOWN_KEY,
    KEY_AREA,
    KEY_BATTERY,
    KEY_BORDER_LENGTH_MM,
    KEY_FAULT_CODE,
    KEY_FAULT_NAME,
    KEY_GARDEN_AREA,
    KEY_ON_MIN,
    KEY_STATUS_CODE,
    KEY_STATUS_NAME,
    STATUS_CODE_TO_KEY,
    STATUS_UNKNOWN_KEY,
)


@dataclass(frozen=True, kw_only=True)
class MowerSensorDescription(SensorEntityDescription):
    """Opis sensora + funkcja wyciagajaca wartosc z rekordu danych."""

    value_fn: Callable[[dict[str, Any]], Any] = lambda record: None
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    options: tuple[str, ...] | None = None


def _status_value(record: dict[str, Any]) -> str:
    code = record.get(KEY_STATUS_CODE)
    return STATUS_CODE_TO_KEY.get(str(code), STATUS_UNKNOWN_KEY)


def _status_attrs(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_code": record.get(KEY_STATUS_CODE),
        "raw_text_from_server": record.get(KEY_STATUS_NAME),
    }


def _fault_value(record: dict[str, Any]) -> str:
    code = record.get(KEY_FAULT_CODE)
    return FAULT_CODE_TO_KEY.get(str(code), FAULT_UNKNOWN_KEY)


def _fault_attrs(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "raw_code": record.get(KEY_FAULT_CODE),
        "raw_text_from_server": record.get(KEY_FAULT_NAME),
    }


def _efficiency_value(record: dict[str, Any]) -> float | None:
    """Srednia wydajnosc koszenia OD POCZATKU (area / godziny pracy).

    UWAGA: to jest srednia za caly czas eksploatacji, nie tylko za czas
    aktywnego koszenia (serwer nie oddziela dotychczas czasu koszenia od
    czasu ladowania/postoju w danych, ktore mamy potwierdzone). Jesli w
    przyszlosci uda sie potwierdzic endpoint z historia sesji (cmdLogs /
    getLogRecords), mozna to zawezic do faktycznego czasu koszenia.
    """
    area = record.get(KEY_AREA)
    on_min = record.get(KEY_ON_MIN)
    if area is None or not on_min:
        return None
    hours = on_min / 60
    if hours <= 0:
        return None
    return round(area / hours, 1)


SENSOR_DESCRIPTIONS: tuple[MowerSensorDescription, ...] = (
    MowerSensorDescription(
        key="area_m2",
        translation_key="mowing_area",
        icon="mdi:texture-box",
        native_unit_of_measurement="m²",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda record: record.get(KEY_AREA),
    ),
    MowerSensorDescription(
        key="work_hours",
        translation_key="work_hours",
        icon="mdi:timer-outline",
        native_unit_of_measurement="h",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda record: (
            round(record[KEY_ON_MIN] / 60, 1) if record.get(KEY_ON_MIN) is not None else None
        ),
    ),
    MowerSensorDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda record: record.get(KEY_BATTERY),
    ),
    MowerSensorDescription(
        key="efficiency",
        translation_key="efficiency",
        icon="mdi:speedometer",
        native_unit_of_measurement="m²/h",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_efficiency_value,
    ),
    MowerSensorDescription(
        key="garden_area_total",
        translation_key="garden_area_total",
        icon="mdi:fence",
        native_unit_of_measurement="m²",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda record: record.get(KEY_GARDEN_AREA),
    ),
    MowerSensorDescription(
        key="border_length",
        translation_key="border_length",
        icon="mdi:vector-polyline",
        native_unit_of_measurement="m",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda record: (
            round(record[KEY_BORDER_LENGTH_MM] / 1000, 1)
            if record.get(KEY_BORDER_LENGTH_MM) is not None
            else None
        ),
    ),
    MowerSensorDescription(
        key="status",
        translation_key="mower_status",
        device_class=SensorDeviceClass.ENUM,
        options=("working", "unknown"),
        value_fn=_status_value,
        attrs_fn=_status_attrs,
    ),
    MowerSensorDescription(
        key="fault",
        translation_key="mower_fault",
        icon="mdi:alert-circle-outline",
        device_class=SensorDeviceClass.ENUM,
        options=("ok", "unknown"),
        value_fn=_fault_value,
        attrs_fn=_fault_attrs,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Tworzy encje sensorow dla kazdej kosiarki znalezionej na koncie."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[MowerSensor] = []
    for sn, device_data in coordinator.data.items():
        for description in SENSOR_DESCRIPTIONS:
            entities.append(MowerSensor(coordinator, sn, device_data, description))

    async_add_entities(entities)


class MowerSensor(CoordinatorEntity, SensorEntity):
    """Pojedynczy sensor kosiarki, oparty o dane z coordinatora."""

    entity_description: MowerSensorDescription

    def __init__(
        self,
        coordinator,
        sn: str,
        device_data: dict[str, Any],
        description: MowerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._sn = sn

        if description.options:
            self._attr_options = list(description.options)

        self._attr_unique_id = f"{sn}_{description.key}"
        self._attr_has_entity_name = True

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, sn)},
            name=device_data.get("name") or "Kosiarka",
            manufacturer="Sunseeker / Bugull",
            model=device_data.get("model"),
            serial_number=sn,
        )

    @property
    def native_value(self) -> Any:
        device_data = self.coordinator.data.get(self._sn)
        if not device_data:
            return None
        record = device_data.get("record", {})
        return self.entity_description.value_fn(record)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        device_data = self.coordinator.data.get(self._sn)
        if not device_data:
            return None
        record = device_data.get("record", {})
        return self.entity_description.attrs_fn(record)

    @property
    def available(self) -> bool:
        return super().available and self._sn in (self.coordinator.data or {})

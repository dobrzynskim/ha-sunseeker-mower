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
    KEY_AREA,
    KEY_BATTERY,
    KEY_FAULT,
    KEY_ON_MIN,
    KEY_STATUS,
)


@dataclass(frozen=True, kw_only=True)
class MowerSensorDescription(SensorEntityDescription):
    """Opis sensora + funkcja wyciagajaca wartosc z rekordu danych."""

    value_fn: Callable[[dict[str, Any]], Any] = lambda record: None


SENSOR_DESCRIPTIONS: tuple[MowerSensorDescription, ...] = (
    MowerSensorDescription(
        key="area_m2",
        translation_key="mowing_area",
        name="Powierzchnia koszenia",
        icon="mdi:texture-box",
        native_unit_of_measurement="m²",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda record: record.get(KEY_AREA),
    ),
    MowerSensorDescription(
        key="work_hours",
        translation_key="work_hours",
        name="Czas pracy",
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
        name="Bateria",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda record: record.get(KEY_BATTERY),
    ),
    MowerSensorDescription(
        key="status",
        translation_key="status",
        name="Status",
        icon="mdi:robot-mower-outline",
        value_fn=lambda record: record.get(KEY_STATUS),
    ),
    MowerSensorDescription(
        key="fault",
        translation_key="fault",
        name="Usterka",
        icon="mdi:alert-circle-outline",
        value_fn=lambda record: record.get(KEY_FAULT),
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
    def available(self) -> bool:
        return super().available and self._sn in (self.coordinator.data or {})

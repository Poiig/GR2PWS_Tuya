"""GR2PWS 数值平台。"""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUMBERS, GR2PWSNumberDescription
from .coordinator import GR2PWSCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置数值实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    async_add_entities([
        GR2PWSNumberEntity(coordinator, device_id, desc)
        for desc in NUMBERS.values()
    ])


class GR2PWSNumberEntity(CoordinatorEntity[GR2PWSCoordinator], NumberEntity):
    """GR2PWS 数值实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_mode = (
            NumberMode.SLIDER if description.mode == "slider" else NumberMode.BOX
        )
        self._scale = description.scale

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None

        if self._scale and isinstance(value, (int, float)):
            return value / (10**self._scale)

        return float(value) if isinstance(value, (int, float)) else None

    async def async_set_native_value(self, value: float) -> None:
        if self._scale:
            device_value = int(value * (10**self._scale))
        else:
            device_value = int(value)

        await self.coordinator.async_set_dp(
            self.entity_description.key, device_value
        )
        await self.coordinator.async_request_refresh()

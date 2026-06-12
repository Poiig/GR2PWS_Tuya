"""GR2PWS 选择器平台。"""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SELECTS, GR2PWSSelectDescription
from .coordinator import GR2PWSCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置选择器实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    async_add_entities([
        GR2PWSSelectEntity(coordinator, device_id, desc)
        for desc in SELECTS.values()
    ])


class GR2PWSSelectEntity(CoordinatorEntity[GR2PWSCoordinator], SelectEntity):
    """GR2PWS 选择器实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get(self.entity_description.key)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_dp(self.entity_description.key, option)
        await self.coordinator.async_request_refresh()

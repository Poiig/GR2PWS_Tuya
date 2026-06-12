"""GR2PWS 开关平台。

将设备的布尔控制点（开关状态、超限控制、系统声音、预付费、实时刷新）
映射为 Home Assistant 开关实体。
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SWITCHES, GR2PWSSwitchDescription
from .coordinator import GR2PWSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置开关实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    entities = [
        GR2PWSSwitchEntity(
            coordinator=coordinator,
            device_id=device_id,
            description=desc,
        )
        for desc in SWITCHES.values()
    ]

    async_add_entities(entities)


class GR2PWSSwitchEntity(CoordinatorEntity[GR2PWSCoordinator], SwitchEntity):
    """GR2PWS 开关实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSSwitchDescription,
    ) -> None:
        """初始化开关实体。"""
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description

        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_icon = description.icon

    @property
    def device_info(self) -> dict[str, Any]:
        """返回设备信息。"""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
        }

    @property
    def is_on(self) -> bool | None:
        """返回开关是否处于开启状态。"""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        return bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """开启开关。"""
        await self.coordinator.async_set_dp(self.entity_description.key, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭开关。"""
        await self.coordinator.async_set_dp(self.entity_description.key, False)
        await self.coordinator.async_request_refresh()

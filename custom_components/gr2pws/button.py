"""GR2PWS 按钮平台。

将设备的一次性触发操作（累计数据清零、WiFi重置、恢复出厂设置、
屏幕旋转、剩余电量清零）映射为 Home Assistant 按钮实体。
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BUTTONS, GR2PWSButtonDescription
from .coordinator import GR2PWSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置按钮实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    entities = [
        GR2PWSButtonEntity(
            coordinator=coordinator,
            device_id=device_id,
            description=desc,
        )
        for desc in BUTTONS.values()
    ]

    async_add_entities(entities)


class GR2PWSButtonEntity(CoordinatorEntity[GR2PWSCoordinator], ButtonEntity):
    """GR2PWS 按钮实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSButtonDescription,
    ) -> None:
        """初始化按钮实体。"""
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

    async def async_press(self) -> None:
        """按下按钮，发送 True 触发设备操作。"""
        await self.coordinator.async_set_dp(
            self.entity_description.key, True
        )
        await self.coordinator.async_request_refresh()

"""GR2PWS 选择器平台。

将设备的枚举控制点（设备语言、开关模式、待机画面、显示风格、计价模式）
映射为 Home Assistant 选择器实体。
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SELECTS, GR2PWSSelectDescription
from .coordinator import GR2PWSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置选择器实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    entities = [
        GR2PWSSelectEntity(
            coordinator=coordinator,
            device_id=device_id,
            description=desc,
        )
        for desc in SELECTS.values()
    ]

    async_add_entities(entities)


class GR2PWSSelectEntity(CoordinatorEntity[GR2PWSCoordinator], SelectEntity):
    """GR2PWS 选择器实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSSelectDescription,
    ) -> None:
        """初始化选择器实体。"""
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description

        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_icon = description.icon
        self._attr_options = description.options
        self._attr_current_option = None

    @property
    def device_info(self) -> dict[str, Any]:
        """返回设备信息。"""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
        }

    @property
    def current_option(self) -> str | None:
        """返回当前选项。"""
        return self.coordinator.data.get(self.entity_description.key)

    async def async_select_option(self, option: str) -> None:
        """设置选择项。"""
        await self.coordinator.async_set_dp(self.entity_description.key, option)
        await self.coordinator.async_request_refresh()

"""GR2PWS 数值平台。

将设备的数值控制点（过压值、过流值、过功率值、欠压值、漏电阀值、电费单价、
屏幕亮度、待机时间、恢复延时、倒计时、报警值、刷新间隔、电量充值等）
映射为 Home Assistant 数值实体。
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUMBERS, GR2PWSNumberDescription
from .coordinator import GR2PWSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置数值实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    entities = [
        GR2PWSNumberEntity(
            coordinator=coordinator,
            device_id=device_id,
            description=desc,
        )
        for desc in NUMBERS.values()
    ]

    async_add_entities(entities)


class GR2PWSNumberEntity(CoordinatorEntity[GR2PWSCoordinator], NumberEntity):
    """GR2PWS 数值实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSNumberDescription,
    ) -> None:
        """初始化数值实体。"""
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description

        self._attr_unique_id = f"{device_id}_{description.key}"
        self._attr_entity_category = description.entity_category
        self._attr_icon = description.icon
        self._attr_native_min_value = description.native_min_value
        self._attr_native_max_value = description.native_max_value
        self._attr_native_step = description.native_step
        self._attr_native_unit_of_measurement = description.native_unit
        self._attr_device_class = description.device_class
        self._attr_mode = (
            NumberMode.SLIDER if description.mode == "slider" else NumberMode.BOX
        )
        self._scale = description.scale

    @property
    def device_info(self) -> dict[str, Any]:
        """返回设备信息。"""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
        }

    @property
    def native_value(self) -> float | None:
        """返回当前值，根据 scale 缩放原始数据。"""
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None

        if self._scale and isinstance(value, (int, float)):
            return value / (10**self._scale)

        return float(value) if isinstance(value, (int, float)) else None

    async def async_set_native_value(self, value: float) -> None:
        """设置数值，将缩放后的值还原为设备原始格式发送。"""
        if self._scale:
            device_value = int(value * (10**self._scale))
        else:
            device_value = int(value)

        await self.coordinator.async_set_dp(
            self.entity_description.key, device_value
        )
        await self.coordinator.async_request_refresh()

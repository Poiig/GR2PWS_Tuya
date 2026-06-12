"""GR2PWS 传感器平台。

将设备的只读数据点映射为传感器实体，
并创建日/月/年用电量统计传感器（基于总电量差值累加，支持重置和手动校准）。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_IP_ADDRESS,
    DOMAIN,
    ENERGY_PERIODS,
    SENSORS,
    GR2PWSSensorDescription,
    WARNING_OPTIONS,
)
from .coordinator import GR2PWSCoordinator

_LOGGER = logging.getLogger(__name__)

ENERGY_PERIOD_NAMES = {
    "daily": "日用电量",
    "monthly": "月用电量",
    "yearly": "年用电量",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]
    ip_address: str = entry.data.get(CONF_IP_ADDRESS, "")

    entities: list[SensorEntity] = []

    # 基本传感器实体
    for desc in SENSORS.values():
        entities.append(
            GR2PWSSensorEntity(
                coordinator=coordinator,
                device_id=device_id,
                description=desc,
            )
        )

    # 设备内网 IP 传感器
    entities.append(
        GR2PWSIPAddressSensor(
            device_id=device_id,
            ip_address=ip_address,
        )
    )

    # 日/月/年用电量统计传感器
    for period in ENERGY_PERIODS:
        sensor = GR2PWSEnergyPeriodSensor(
            coordinator=coordinator,
            device_id=device_id,
            period=period,
        )
        entities.append(sensor)
        # 存储引用到 hass.data，供重置按钮和校准 number 使用
        data[f"energy_sensor_{period}"] = sensor

    async_add_entities(entities)


class GR2PWSSensorEntity(CoordinatorEntity[GR2PWSCoordinator], SensorEntity):
    """GR2PWS 传感器实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

        if description.key == "warning":
            self._attr_options = list(WARNING_OPTIONS.keys())

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def native_value(self) -> str | float | None:
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None

        if self.entity_description.key == "warning":
            return str(value)

        scale = self.entity_description.scale
        if scale and isinstance(value, (int, float)):
            return value / (10**scale)

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "warning":
            value = self.coordinator.data.get("warning")
            if value is not None:
                return {
                    "description": WARNING_OPTIONS.get(str(value), str(value)),
                }
        return None


class GR2PWSIPAddressSensor(SensorEntity):
    """设备内网 IP 地址传感器。"""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:ip-network"

    def __init__(self, device_id: str, ip_address: str) -> None:
        self._device_id = device_id
        self._ip_address = ip_address
        self._attr_unique_id = f"{device_id}_ip_address"
        self._attr_native_value = ip_address

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def translation_key(self) -> str:
        return "ip_address"

    @property
    def native_value(self) -> str:
        return self._ip_address


class GR2PWSEnergyPeriodSensor(CoordinatorEntity[GR2PWSCoordinator], SensorEntity):
    """日/月/年用电量统计传感器。

    基于设备总电量（ele）的变化量进行累加：
    - 每次 ele 增加时，将增量累加到当前周期的统计值
    - 每天 0:00 重置日用电量
    - 每月 1 日 0:00 重置月用电量
    - 每年 1 月 1 日 0:00 重置年用电量
    - 支持通过 native_value setter 手动校准数值
    """

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 3

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        period: str,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._period = period
        self._attr_unique_id = f"{device_id}_ele_{period}"
        self._attr_translation_key = f"ele_{period}"

        # 累计值和上一次总电量读数
        self._accumulated: float = 0.0
        self._last_ele: float | None = None

        period_icons = {
            "daily": "mdi:counter",
            "monthly": "mdi:calendar-month",
            "yearly": "mdi:calendar-clock",
        }
        self._attr_icon = period_icons.get(period, "mdi:counter")

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def native_value(self) -> float:
        return round(self._accumulated, 6)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """暴露可校准属性，让 HA UI 显示校准选项。"""
        return {
            "state_class": "total_increasing",
            "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
        }

    def set_value(self, value: float) -> None:
        """手动设置当前周期的累计值（校准/纠正）。

        Args:
            value: 新的累计用电量 (kWh)
        """
        _LOGGER.info(
            "手动校准 %s 用电量: %s -> %.3f kWh",
            ENERGY_PERIOD_NAMES.get(self._period, self._period),
            round(self._accumulated, 6),
            value,
        )
        self._accumulated = value
        self._last_ele = None  # 重置基线，避免重复计算
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """HA 添加实体时恢复上次数据并注册定时重置。"""
        await super().async_added_to_hass()

        # 从 HA recorder 恢复上次值
        last_data = await self.async_get_last_sensor_data()
        if last_data and last_data.native_value is not None:
            self._accumulated = float(last_data.native_value)
            _LOGGER.debug(
                "恢复 %s 用电量: %.3f kWh",
                ENERGY_PERIOD_NAMES.get(self._period, self._period),
                self._accumulated,
            )

        # 注册每日 0 点的重置任务
        self.async_on_remove(
            async_track_time_change(
                self.hass,
                self._async_reset_period,
                hour=0, minute=0, second=0,
            )
        )

    @callback
    def _async_reset_period(self, now: datetime) -> None:
        """定时检查并重置对应周期的统计数据。"""
        should_reset = False

        if self._period == "daily":
            should_reset = True
        elif self._period == "monthly" and now.day == 1:
            should_reset = True
        elif self._period == "yearly" and now.day == 1 and now.month == 1:
            should_reset = True

        if should_reset:
            _LOGGER.info(
                "重置 %s 用电量: %.3f -> 0",
                ENERGY_PERIOD_NAMES.get(self._period, self._period),
                self._accumulated,
            )
            self._accumulated = 0.0
            self._last_ele = None
            self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """coordinator 数据更新时，计算 ele 的增量并累加。"""
        raw_ele = self.coordinator.data.get("ele")
        if raw_ele is not None:
            # ele 的 scale 是 3（原始值 / 1000 = kWh）
            current_ele = raw_ele / 1000.0

            if self._last_ele is not None:
                delta = current_ele - self._last_ele
                # 只累加正增量（忽略设备重置导致的负值）
                if delta > 0:
                    self._accumulated += delta
                elif delta < 0:
                    # 总电量回退（设备被重置），重新设定基线
                    _LOGGER.debug(
                        "总电量回退 detected (%.3f -> %.3f)，重置基线",
                        self._last_ele, current_ele,
                    )

            self._last_ele = current_ele

        self.async_write_ha_state()

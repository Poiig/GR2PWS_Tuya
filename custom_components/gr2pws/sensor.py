"""GR2PWS 传感器平台。

将设备的只读数据点映射为传感器实体，并自动创建 Utility Meter 用于日/月/年用电量跟踪。
"""

from __future__ import annotations

import inspect
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.components.utility_meter import DEFAULT_OFFSET
from homeassistant.components.utility_meter.const import (
    DATA_TARIFF_SENSORS,
    DATA_UTILITY,
)
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_IP_ADDRESS, DOMAIN, SENSORS, GR2PWSSensorDescription, WARNING_OPTIONS
from .coordinator import GR2PWSCoordinator

_LOGGER = logging.getLogger(__name__)

METER_TYPES = ["daily", "monthly", "yearly"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置传感器实体，包括基本传感器、设备IP和 Utility Meter。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]
    ip_address: str = entry.data.get(CONF_IP_ADDRESS, "")

    entities: list[SensorEntity | UtilityMeterSensor] = []

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

    # Utility Meter 实体（日/月/年用电量跟踪，支持手动纠正）
    if DATA_UTILITY not in hass.data:
        hass.data[DATA_UTILITY] = {}

    source_entity_id = f"sensor.gr2pws_{device_id[:8]}_ele"

    meter_names = {
        "daily": "日用电量",
        "monthly": "月用电量",
        "yearly": "年用电量",
    }

    for meter_type in METER_TYPES:
        meter_entity_id = f"{source_entity_id}_{meter_type}"
        meter_unique_id = f"{device_id}_ele_{meter_type}"
        meter_name = meter_names[meter_type]

        params = {
            "hass": hass,
            "source_entity": source_entity_id,
            "name": meter_name,
            "meter_type": meter_type,
            "meter_offset": DEFAULT_OFFSET,
            "net_consumption": False,
            "tariff": None,
            "tariff_entity": None,
            "parent_meter": meter_entity_id,
            "delta_values": False,
            "cron_pattern": None,
            "periodically_resetting": True,
            "sensor_always_available": False,
            "unique_id": meter_unique_id,
        }

        signature = inspect.signature(UtilityMeterSensor.__init__)
        filtered_params = {
            k: v for k, v in params.items() if k in signature.parameters
        }

        meter = UtilityMeterSensor(**filtered_params)
        meter.entity_id = meter_entity_id
        entities.append(meter)

        hass.data[DATA_UTILITY][meter_entity_id] = {
            DATA_TARIFF_SENSORS: [meter]
        }

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
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_native_unit_of_measurement = description.native_unit
        self._attr_entity_category = description.entity_category
        self._attr_icon = description.icon

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
    """设备内网 IP 地址传感器。

    显示设备当前局域网 IP，属于诊断类别，方便用户查看设备网络信息。
    支持在 HA 服务中调用 sensor.gr2pws_xxx_ip_address 的 service 来更新 IP。
    """

    _attr_has_entity_name = True
    _attr_device_class = None
    _attr_state_class = None
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

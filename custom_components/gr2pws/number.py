"""GR2PWS 数值平台。

将设备的数值控制点映射为数值实体，
并添加日/月/年用电量校准实体（支持手动设置累计值）。
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NUMBERS, GR2PWSNumberDescription, ENERGY_PERIODS
from .coordinator import GR2PWSCoordinator

# 校准实体描述，按日/月/年顺序定义
# 最大值按实际用电量设定：日 1000 kWh，月 30000 kWh，年 999999 kWh
ENERGY_CALIBRATE_DESCRIPTIONS: list[tuple[str, NumberEntityDescription]] = [
    ("daily", NumberEntityDescription(
        key="calibrate_ele_daily",
        translation_key="calibrate_ele_daily",
        native_min_value=0.0,
        native_max_value=10000.0,
        native_step=0.01,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:pencil",
        entity_category=EntityCategory.CONFIG,
        mode="box",
    )),
    ("monthly", NumberEntityDescription(
        key="calibrate_ele_monthly",
        translation_key="calibrate_ele_monthly",
        native_min_value=0.0,
        native_max_value=100000.0,
        native_step=0.01,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:pencil",
        entity_category=EntityCategory.CONFIG,
        mode="box",
    )),
    ("yearly", NumberEntityDescription(
        key="calibrate_ele_yearly",
        translation_key="calibrate_ele_yearly",
        native_min_value=0.0,
        native_max_value=999999.0,
        native_step=0.01,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:pencil",
        entity_category=EntityCategory.CONFIG,
        mode="box",
    )),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置数值实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    entities: list[NumberEntity] = [
        GR2PWSNumberEntity(coordinator, device_id, desc)
        for desc in NUMBERS.values()
    ]

    # 按日/月/年顺序添加校准实体
    for period, desc in ENERGY_CALIBRATE_DESCRIPTIONS:
        entities.append(
            GR2PWSEnergyCalibrateNumber(hass, coordinator, device_id, desc, period)
        )

    async_add_entities(entities)


class GR2PWSNumberEntity(CoordinatorEntity[GR2PWSCoordinator], NumberEntity):
    """GR2PWS 设备数值实体。"""

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
        if not self.coordinator.data:
            return None
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


class GR2PWSEnergyCalibrateNumber(CoordinatorEntity[GR2PWSCoordinator], NumberEntity):
    """日/月/年用电量校准实体。

    设置此数值会直接覆盖对应周期的累计用电量。
    """

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: NumberEntityDescription,
        period: str,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._device_id = device_id
        self._period = period
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    @property
    def native_value(self) -> float | None:
        """显示当前周期的实际累计值。"""
        data = self._hass.data[DOMAIN]
        sensor_key = f"energy_sensor_{self._period}"
        for entry_id, entry_data in data.items():
            if isinstance(entry_data, dict) and sensor_key in entry_data:
                return entry_data[sensor_key].native_value
        return None

    async def async_set_native_value(self, value: float) -> None:
        """设置新值覆盖当前周期的累计用电量。"""
        data = self._hass.data[DOMAIN]
        sensor_key = f"energy_sensor_{self._period}"
        for entry_id, entry_data in data.items():
            if isinstance(entry_data, dict) and sensor_key in entry_data:
                entry_data[sensor_key].set_value(value)
                return

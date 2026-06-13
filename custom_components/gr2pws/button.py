"""GR2PWS 按钮平台。

将设备的一次性触发操作映射为按钮实体，
并添加日/月/年用电量重置按钮。
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BUTTONS, GR2PWSButtonDescription, ENERGY_PERIODS
from .coordinator import GR2PWSCoordinator

ENERGY_RESET_DESCRIPTIONS = {
    period: ButtonEntityDescription(
        key=f"reset_ele_{period}",
        translation_key=f"reset_ele_{period}",
        icon="mdi:counter",
        entity_category=EntityCategory.CONFIG,
    )
    for period in ENERGY_PERIODS
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置按钮实体。"""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: GR2PWSCoordinator = data["coordinator"]
    device_id: str = data["device_id"]

    entities: list[ButtonEntity] = [
        GR2PWSButtonEntity(coordinator, device_id, desc)
        for desc in BUTTONS.values()
    ]

    for period, desc in ENERGY_RESET_DESCRIPTIONS.items():
        entities.append(
            GR2PWSEnergyResetButton(hass, coordinator, device_id, desc, period)
        )

    async_add_entities(entities)


class GR2PWSButtonEntity(CoordinatorEntity[GR2PWSCoordinator], ButtonEntity):
    """GR2PWS 设备按钮实体。"""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: GR2PWSButtonDescription,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"gr2pws_{device_id}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    async def async_press(self) -> None:
        await self.coordinator.async_set_dp(self.entity_description.key, True)
        await self.coordinator.async_request_refresh()


class GR2PWSEnergyResetButton(CoordinatorEntity[GR2PWSCoordinator], ButtonEntity):
    """日/月/年用电量重置按钮。

    按下后将对应周期的累计用电量归零。
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: GR2PWSCoordinator,
        device_id: str,
        description: ButtonEntityDescription,
        period: str,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._device_id = device_id
        self._period = period
        self.entity_description = description
        self._attr_unique_id = f"gr2pws_{device_id}_{description.key}"

    @property
    def device_info(self) -> dict[str, Any]:
        return {"identifiers": {(DOMAIN, self._device_id)}}

    async def async_press(self) -> None:
        """重置对应周期的用电量统计。"""
        data = self._hass.data[DOMAIN]
        sensor_key = f"energy_sensor_{self._period}"
        for entry_id, entry_data in data.items():
            if isinstance(entry_data, dict) and sensor_key in entry_data:
                sensor = entry_data[sensor_key]
                sensor.set_value(0.0)
                return

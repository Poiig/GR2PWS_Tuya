"""GR2PWS Smart Energy Meter 集成入口。

该集成通过 tinytuya 库在本地局域网与 GR2PWS 智能电表通信，
将设备的所有功能点（传感器、开关、选择器、数值、按钮）映射为 Home Assistant 实体。
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_LOCAL_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import GR2PWSCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """设置配置入口。

    创建数据协调器并进行首次数据获取，
    然后转发设置到所有平台（sensor、switch、select、number、button）。
    """
    hass.data.setdefault(DOMAIN, {})

    device_id = entry.data[CONF_DEVICE_ID]
    ip_address = entry.data[CONF_IP_ADDRESS]
    local_key = entry.data[CONF_LOCAL_KEY]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = GR2PWSCoordinator(
        hass=hass,
        device_id=device_id,
        ip_address=ip_address,
        local_key=local_key,
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device_id": device_id,
    }

    # 注册设备到 HA 设备注册表
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=entry.title,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置入口。"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def _async_update_listener(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """选项更新时重新加载配置入口。"""
    await hass.config_entries.async_reload(entry.entry_id)

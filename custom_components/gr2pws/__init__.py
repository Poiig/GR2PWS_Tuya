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

    创建数据协调器并转发设置到所有平台，
    然后进行首次数据获取（不阻断实体创建）。
    """
    hass.data.setdefault(DOMAIN, {})

    device_id = entry.data[CONF_DEVICE_ID]
    ip_address = entry.data[CONF_IP_ADDRESS]
    local_key = entry.data[CONF_LOCAL_KEY]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    _LOGGER.info(
        "正在设置 GR2PWS 设备: id=%s, ip=%s, local_key=%s",
        device_id,
        ip_address,
        "***已设置" if local_key else "未设置",
    )

    coordinator = GR2PWSCoordinator(
        hass=hass,
        device_id=device_id,
        ip_address=ip_address,
        local_key=local_key,
        scan_interval=scan_interval,
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "device_id": device_id,
    }

    # 注册设备到 HA 设备注册表
    # 不设置 name，HA 默认使用 config entry title ("GR2PWS")
    # 用户可在 HA 界面中手动修改设备名为中文
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
    )

    # 先转发平台设置（创建所有实体），再做首次数据获取
    # 这样即使设备暂时不可达，实体也会被创建（显示为 unavailable）
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 首次数据获取，失败不阻断（coordinator 会自动重试）
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("首次数据获取失败（实体已创建，coordinator 将自动重试）: %s", err)

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

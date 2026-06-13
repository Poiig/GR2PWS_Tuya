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
from homeassistant.helpers import entity_registry as er

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
    """设置配置入口。"""
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

    short_name = f"GR2PWS {device_id[:8]}"
    cloud_device_name = entry.title

    device_registry = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    # 查找并清理旧的设备记录及其所有关联实体
    # 旧设备可能残留了中文 name_by_user，导致 entity_id 前缀是中文拼音
    old_device = device_registry.async_get_device(
        identifiers={(DOMAIN, device_id)},
    )
    if old_device is not None:
        # 检查旧设备名是否包含中文（slugify 后不以 gr2pws_ 开头）
        has_bad_name = (
            old_device.name_by_user is not None
            or (old_device.name is not None and not old_device.name.startswith("GR2PWS"))
        )
        if has_bad_name:
            # 删除旧设备关联的所有实体注册记录
            old_entities = er.async_entries_for_device(ent_reg, old_device.id)
            for entity_entry in old_entities:
                _LOGGER.info("清理旧实体: %s", entity_entry.entity_id)
                ent_reg.async_remove(entity_entry.entity_id)
            # 删除旧设备记录本身
            _LOGGER.info(
                "清理旧设备记录: name=%s, name_by_user=%s",
                old_device.name,
                old_device.name_by_user,
            )
            device_registry.async_remove_device(old_device.id)

    # 创建全新的设备记录
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=short_name,
    )
    _LOGGER.info(
        "设备注册完成: name=%s, name_by_user=%s, id=%s",
        device_entry.name,
        device_entry.name_by_user,
        device_entry.id,
    )

    # 创建所有实体
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 实体创建完成后，设置中文显示名
    if cloud_device_name:
        device_registry.async_update_device(
            device_id=device_entry.id,
            name_by_user=cloud_device_name,
        )

    # 首次数据获取，失败不阻断
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

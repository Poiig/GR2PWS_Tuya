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
    SENSORS,
    SWITCHES,
    SELECTS,
    NUMBERS,
    BUTTONS,
    ENERGY_PERIODS,
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


def _get_all_entity_keys() -> list[tuple[str, str]]:
    """返回所有实体的 (domain, key) 列表，用于清理旧注册记录。"""
    keys: list[tuple[str, str]] = []
    for key in SENSORS:
        keys.append(("sensor", key))
    # IP 传感器
    keys.append(("sensor", "ip_address"))
    # 日/月/年用电量传感器
    for period in ENERGY_PERIODS:
        keys.append(("sensor", f"ele_{period}"))
    for key in SWITCHES:
        keys.append(("switch", key))
    for key in SELECTS:
        keys.append(("select", key))
    for key in NUMBERS:
        keys.append(("number", key))
    # 校准数值实体
    for period in ENERGY_PERIODS:
        keys.append(("number", f"calibrate_ele_{period}"))
    for key in BUTTONS:
        keys.append(("button", key))
    # 重置按钮
    for period in ENERGY_PERIODS:
        keys.append(("button", f"reset_ele_{period}"))
    return keys


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

    # 注册设备到 HA 设备注册表
    # name 用英文短名控制 entity_id 前缀
    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device_id)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=short_name,
    )
    # 清除旧的中文 name_by_user
    if device_entry.name_by_user is not None:
        device_registry.async_update_device(
            device_id=device_entry.id,
            name_by_user=None,
        )

    # 通过 unique_id 逐个查找并清理旧的实体注册记录
    # unique_id 格式为 {device_id}_{key}，不受 config_entry 或 device 变化影响
    ent_reg = er.async_get(hass)
    removed = 0
    for domain, key in _get_all_entity_keys():
        unique_id = f"{device_id}_{key}"
        entity_id = ent_reg.async_get_entity_id(domain, DOMAIN, unique_id)
        if entity_id and not entity_id.startswith(f"{domain}.gr2pws_"):
            ent_reg.async_remove(entity_id)
            removed += 1
            _LOGGER.debug("清理旧实体: %s (unique_id=%s)", entity_id, unique_id)
    if removed:
        _LOGGER.info("清理了 %d 个旧实体注册记录（中文前缀 entity_id）", removed)

    # 创建所有实体，此时设备名是英文短名，entity_id 前缀为 gr2pws_xxxxxxxx
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 实体创建完成后，设置中文显示名（不影响已生成的 entity_id）
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

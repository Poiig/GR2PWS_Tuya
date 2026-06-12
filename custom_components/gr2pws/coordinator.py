"""GR2PWS 数据更新协调器，通过 tinytuya 轮询设备状态。"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import tinytuya
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_LOCAL_KEY,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# 连续失败次数达到此阈值后触发 IP 重新扫描
_IP_RESCAN_THRESHOLD = 3


class GR2PWSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """GR2PWS 数据更新协调器。

    通过 tinytuya 库以固定间隔轮询设备状态，获取所有 DP 点数据。
    当连续通信失败达到阈值时，自动扫描局域网重新发现设备 IP。
    """

    def __init__(
        self,
        hass: HomeAssistant,
        device_id: str,
        ip_address: str,
        local_key: str,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """初始化协调器。

        Args:
            hass: Home Assistant 实例
            device_id: Tuya 设备 ID
            ip_address: 设备局域网 IP 地址
            local_key: 设备本地密钥
            scan_interval: 轮询间隔（秒）
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_id}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.device_id = device_id
        self.ip_address = ip_address
        self.local_key = local_key
        self._consecutive_failures = 0

        self._device = tinytuya.Device(
            dev_id=device_id,
            address=ip_address,
            local_key=local_key,
            version=3.5,
        )
        self._device.set_socketTimeout(5)

    def _update_device_address(self, new_ip: str) -> None:
        """更新设备 IP 地址并重建 tinytuya 连接。

        Args:
            new_ip: 新发现的设备 IP 地址
        """
        _LOGGER.info("设备 IP 变更: %s -> %s", self.ip_address, new_ip)
        self.ip_address = new_ip
        self._device = tinytuya.Device(
            dev_id=self.device_id,
            address=new_ip,
            local_key=self.local_key,
            version=3.5,
        )
        self._device.set_socketTimeout(5)

    def _rescan_device_ip(self) -> str | None:
        """扫描局域网查找设备的当前 IP。

        Returns:
            找到的新 IP 地址，未找到则返回 None
        """
        _LOGGER.info("正在扫描局域网重新发现设备 %s 的 IP...", self.device_id)
        try:
            scanned = tinytuya.deviceScan()
            for ip, info in scanned.items():
                if info.get("gwId") == self.device_id:
                    return ip
        except Exception as err:
            _LOGGER.warning("局域网扫描失败: %s", err)
        return None

    async def _async_update_data(self) -> dict[str, Any]:
        """从设备获取最新状态数据。

        通信失败时会自动尝试重新扫描设备 IP。
        连续失败 _IP_RESCAN_THRESHOLD 次后触发 IP 重新发现。

        Returns:
            以 DP code 为键、DP 值为值的字典

        Raises:
            UpdateFailed: 当设备通信失败时抛出
        """
        try:
            status = await self.hass.async_add_executor_job(
                self._poll_device
            )
            self._consecutive_failures = 0
            return status
        except Exception as err:
            self._consecutive_failures += 1
            _LOGGER.debug(
                "设备通信失败 (连续第 %d 次): %s",
                self._consecutive_failures,
                err,
            )

            if self._consecutive_failures >= _IP_RESCAN_THRESHOLD:
                new_ip = await self.hass.async_add_executor_job(
                    self._rescan_device_ip
                )
                if new_ip and new_ip != self.ip_address:
                    self._update_device_address(new_ip)
                    # IP 更新后立即重试一次
                    try:
                        status = await self.hass.async_add_executor_job(
                            self._poll_device
                        )
                        self._consecutive_failures = 0
                        _LOGGER.info("IP 更新后通信恢复")
                        return status
                    except Exception as retry_err:
                        _LOGGER.error("IP 更新后仍然通信失败: %s", retry_err)

            raise UpdateFailed(f"设备通信失败: {err}") from err

    def _poll_device(self) -> dict[str, Any]:
        """同步轮询设备状态。

        通过 tinytuya 获取设备所有 DP 状态，返回解析后的字典。
        """
        try:
            response = self._device.status()
        except Exception as err:
            _LOGGER.error(
                "设备 %s (%s) 通信异常: %s",
                self.device_id, self.ip_address, err,
            )
            raise

        if not response:
            raise UpdateFailed("设备返回空数据")

        _LOGGER.debug("设备 %s 原始响应: %s", self.device_id, response)

        result: dict[str, Any] = {}
        dps = response.get("dps", {})

        if dps:
            result = self._parse_dps(dps)
        else:
            status_list = response.get("status", [])
            for item in status_list:
                code = item.get("code")
                value = item.get("value")
                if code is not None:
                    result[code] = value

        return result

    def _parse_dps(self, dps: dict[str, Any]) -> dict[str, Any]:
        """将 DPS ID 格式的数据转换为 DP code 格式。

        Args:
            dps: 以 DP ID 为键的原始数据字典，如 {'1': True, '20': 22678}

        Returns:
            以 DP code 为键的字典，如 {'switch_1': True, 'cur_voltage': 22678}
        """
        dp_id_to_code: dict[str, str] = {
            "1": "switch_1",
            "9": "countdown_1",
            "17": "add_ele",
            "18": "cur_current",
            "19": "cur_power",
            "20": "cur_voltage",
            "101": "price",
            "102": "cost",
            "103": "add_cost",
            "104": "ovp",
            "105": "ocp",
            "106": "opp",
            "107": "language",
            "108": "work_value",
            "109": "standby_value",
            "110": "standby_time",
            "111": "beep",
            "112": "sw_mode",
            "113": "data_reset",
            "114": "wifi_reset",
            "115": "factor_reset",
            "116": "screen_rotation",
            "117": "standby_screen",
            "118": "menu",
            "119": "lvp",
            "120": "control",
            "121": "olcp",
            "122": "leakage_ele",
            "123": "ele",
            "124": "leakage_current",
            "125": "reporting_interval",
            "126": "real_time_switch_5s_60s",
            "132": "warning",
            "133": "cur_frequency",
            "134": "power_factor",
            "135": "cpu_temp",
            "136": "price_mode",
            "137": "over_time",
            "138": "ttl",
            "139": "prepayment_switch",
            "140": "balance_energy",
            "141": "clear_energy",
            "142": "energy_charge",
            "143": "credit",
        }

        result: dict[str, Any] = {}
        for dp_id, value in dps.items():
            code = dp_id_to_code.get(dp_id)
            if code:
                result[code] = value
            else:
                result[dp_id] = value

        return result

    async def async_set_dp(self, dp_code: str, value: Any) -> None:
        """异步设置设备的 DP 值。

        Args:
            dp_code: DP 功能点代码，如 'switch_1'
            value: 要设置的值
        """
        code_to_id = {
            v: k for k, v in {
                "1": "switch_1",
                "9": "countdown_1",
                "17": "add_ele",
                "18": "cur_current",
                "19": "cur_power",
                "20": "cur_voltage",
                "101": "price",
                "102": "cost",
                "103": "add_cost",
                "104": "ovp",
                "105": "ocp",
                "106": "opp",
                "107": "language",
                "108": "work_value",
                "109": "standby_value",
                "110": "standby_time",
                "111": "beep",
                "112": "sw_mode",
                "113": "data_reset",
                "114": "wifi_reset",
                "115": "factor_reset",
                "116": "screen_rotation",
                "117": "standby_screen",
                "118": "menu",
                "119": "lvp",
                "120": "control",
                "121": "olcp",
                "122": "leakage_ele",
                "123": "ele",
                "124": "leakage_current",
                "125": "reporting_interval",
                "126": "real_time_switch_5s_60s",
                "132": "warning",
                "133": "cur_frequency",
                "134": "power_factor",
                "135": "cpu_temp",
                "136": "price_mode",
                "137": "over_time",
                "138": "ttl",
                "139": "prepayment_switch",
                "140": "balance_energy",
                "141": "clear_energy",
                "142": "energy_charge",
                "143": "credit",
            }.items()
        }

        dp_id = code_to_id.get(dp_code)
        if dp_id is None:
            _LOGGER.error("未知的 DP code: %s", dp_code)
            return

        await self.hass.async_add_executor_job(
            self._set_value, dp_id, value
        )

    def _set_value(self, dp_id: str, value: Any) -> None:
        """同步发送控制命令到设备。"""
        try:
            self._device.set_value(dp_id, value)
            _LOGGER.debug("设置 DP %s = %s 成功", dp_id, value)
        except Exception as err:
            _LOGGER.error("设置 DP %s = %s 失败: %s", dp_id, value, err)

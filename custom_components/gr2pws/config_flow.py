"""GR2PWS 集成配置流程。

流程：输入用户代码 -> 扫描二维码登录 -> 选择设备 -> 自动扫描局域网获取IP -> 完成
"""

from __future__ import annotations

import logging
from typing import Any

import tinytuya
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_LOCAL_KEY,
    CONF_TOKEN_INFO,
    CONF_USER_CODE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    TUYA_CLIENT_ID,
    TUYA_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

try:
    from tuya_sharing import LoginControl, Manager
    from tuya_sharing.customerapi import SharingTokenListener
    HAS_TUYA_SHARING = True
except ImportError:
    HAS_TUYA_SHARING = False

# OptionsFlowWithReload 是 HA 2025.7+ 提供的，自动在选项变更后重载集成
# 旧版本回退到 OptionsFlow，依赖 __init__.py 中的 update listener 重载
try:
    _OptionsFlowBase = config_entries.OptionsFlowWithReload
except AttributeError:
    _OptionsFlowBase = config_entries.OptionsFlow


class _ConfigFlowTokenListener(SharingTokenListener):
    """配置流程中的 Token 监听器，仅用于满足 Manager 初始化要求。"""

    def update_token(self, token_info: dict[str, Any]) -> None:
        """Token 更新回调（配置流程中无需处理）。"""


class GR2PWSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """GR2PWS 配置流程。

    直接进入扫码登录流程：
    async_step_user -> 输入用户代码
    async_step_qrcode -> 显示二维码等待扫码
    async_step_select_device -> 选择设备（自动扫描局域网获取IP）
    """

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_devices: dict[str, dict[str, Any]] = {}
        self._login_control = LoginControl() if HAS_TUYA_SHARING else None
        self._qr_code: str = ""
        self._user_code: str = ""
        self._token_info: dict[str, Any] = {}
        self._terminal_id: str = ""
        self._endpoint: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """第一步：输入 Smart Life APP 用户代码。"""
        if not HAS_TUYA_SHARING:
            return self.async_abort(reason="tuya_integration_required")

        errors: dict[str, str] = {}

        if user_input is not None:
            success, _ = await self.hass.async_add_executor_job(
                self._get_qr_code, user_input[CONF_USER_CODE]
            )
            if success:
                self._user_code = user_input[CONF_USER_CODE]
                return await self.async_step_qrcode()
            errors["base"] = "login_error"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USER_CODE): str,
            }),
            errors=errors,
        )

    async def async_step_qrcode(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """第二步：显示二维码等待用户扫码确认。"""
        if user_input is None:
            return self.async_show_form(
                step_id="qrcode",
                data_schema=vol.Schema({
                    vol.Optional("QR"): selector.QrCodeSelector(
                        config=selector.QrCodeSelectorConfig(
                            data=f"tuyaSmart--qrLogin?token={self._qr_code}",
                            scale=5,
                        )
                    )
                }),
            )

        ret, info = await self.hass.async_add_executor_job(
            self._login_control.login_result,
            self._qr_code,
            TUYA_CLIENT_ID,
            self._user_code,
        )

        if not ret:
            await self.hass.async_add_executor_job(
                self._get_qr_code, self._user_code
            )
            return self.async_show_form(
                step_id="qrcode",
                errors={"base": "login_error"},
                data_schema=vol.Schema({
                    vol.Optional("QR"): selector.QrCodeSelector(
                        config=selector.QrCodeSelectorConfig(
                            data=f"tuyaSmart--qrLogin?token={self._qr_code}",
                            scale=5,
                        )
                    )
                }),
            )

        # 扫码成功，保存登录信息
        self._token_info = {
            "t": info["t"],
            "uid": info["uid"],
            "expire_time": info["expire_time"],
            "access_token": info["access_token"],
            "refresh_token": info["refresh_token"],
        }
        self._terminal_id = info.get("terminal_id", "")
        self._endpoint = info.get("endpoint", "")

        return await self.async_step_select_device()

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """第三步：选择设备，自动扫描局域网获取IP。"""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input.get(CONF_DEVICE_ID)
            if device_id:
                device_info = self._discovered_devices.get(device_id, {})

                if device_info:
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()

                    ip_address = await self._scan_device_ip(device_id)

                    return self.async_create_entry(
                        title="GR2PWS",
                        data={
                            CONF_DEVICE_ID: device_id,
                            CONF_LOCAL_KEY: device_info.get("local_key", ""),
                            CONF_IP_ADDRESS: ip_address,
                            CONF_SCAN_INTERVAL: user_input.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                            CONF_TOKEN_INFO: self._token_info,
                            CONF_USER_CODE: self._user_code,
                            "terminal_id": self._terminal_id,
                            "endpoint": self._endpoint,
                        },
                    )
            errors["base"] = "device_not_found"

        # 从云端获取设备列表
        cloud_devices = await self._get_cloud_devices()
        if not cloud_devices:
            return self.async_show_form(
                step_id="select_device",
                errors={"base": "no_devices_found"},
            )

        self._discovered_devices = cloud_devices
        device_options = {
            dev_id: f"{info['name']} ({dev_id[:8]}...)"
            for dev_id, info in cloud_devices.items()
        }

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): vol.In(device_options),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): int,
            }),
            errors=errors,
        )

    # ========================================================================
    # 辅助方法
    # ========================================================================
    def _get_qr_code(self, user_code: str) -> tuple[bool, dict[str, Any]]:
        """生成二维码。"""
        response = self._login_control.qr_code(
            TUYA_CLIENT_ID, TUYA_SCHEMA, user_code
        )
        success = response.get("success", False)
        if success:
            self._qr_code = response["result"]["qrcode"]
        return success, response

    async def _get_cloud_devices(self) -> dict[str, dict[str, Any]]:
        """通过 tuya_sharing Manager 获取云端设备列表。

        使用与 HA 官方 Tuya 集成完全一致的 Manager 类来获取设备，
        确保 API 调用路径和签名方式正确。
        """
        try:
            token_listener = _ConfigFlowTokenListener()
            manager = Manager(
                TUYA_CLIENT_ID,
                self._user_code,
                self._terminal_id,
                self._endpoint,
                self._token_info,
                token_listener,
            )

            # Manager.update_device_cache() 会从云端拉取所有设备
            await self.hass.async_add_executor_job(manager.update_device_cache)

            devices: dict[str, dict[str, Any]] = {}
            for device_id, device in manager.device_map.items():
                devices[device_id] = {
                    "name": getattr(device, "name", ""),
                    "local_key": getattr(device, "local_key", ""),
                    "model": getattr(device, "model", ""),
                    "product_id": getattr(device, "product_id", ""),
                    "category": getattr(device, "category", ""),
                }

            _LOGGER.info("从云端获取到 %d 个设备", len(devices))
            return devices

        except Exception as err:
            _LOGGER.error("获取云端设备列表失败: %s", err, exc_info=True)
            return {}

    @staticmethod
    def _scan_network() -> dict[str, dict[str, Any]]:
        """扫描局域网中的 Tuya 设备。"""
        scanned = tinytuya.deviceScan()
        result: dict[str, dict[str, Any]] = {}
        for ip, info in scanned.items():
            device_id = info.get("gwId", "")
            result[device_id] = {
                "ip": ip,
                "version": info.get("version", "3.5"),
            }
        return result

    async def _scan_device_ip(self, device_id: str) -> str:
        """扫描局域网获取指定设备的 IP。"""
        scanned = await self.hass.async_add_executor_job(self._scan_network)
        ip = scanned.get(device_id, {}).get("ip", "")
        if not ip:
            _LOGGER.warning("未在局域网中找到设备 %s，可能需要手动配置 IP", device_id)
        return ip

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> GR2PWSOptionsFlow:
        return GR2PWSOptionsFlow()


class GR2PWSOptionsFlow(_OptionsFlowBase):
    """GR2PWS 选项配置流程。

    继承 OptionsFlowWithReload（如果可用），选项变更后自动重载集成。
    HA 2024.12+ 会自动注入 config_entry，不需要在 __init__ 中手动设置。
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """管理选项：轮询间隔。"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(int, vol.Range(min=1, max=300)),
            }),
        )

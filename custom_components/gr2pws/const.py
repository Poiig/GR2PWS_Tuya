"""GR2PWS Smart Energy Meter 常量定义。"""

from __future__ import annotations

from dataclasses import dataclass, field
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.number import NumberEntityDescription, NumberDeviceClass
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.const import (
    EntityCategory,
    UnitOfEnergy,
    UnitOfElectricPotential,
    UnitOfElectricCurrent,
    UnitOfPower,
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfTime,
)

DOMAIN = "gr2pws"

CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_IP_ADDRESS = "ip_address"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 5

# 日/月/年用电量统计周期
ENERGY_PERIODS = ["daily", "monthly", "yearly"]

# 设备型号
MODEL = "GR2PWS"
MANUFACTURER = "ATORCH"
DEVICE_NAME = "ATORCH Smart Energy Meter (GR2PWS)"

# Tuya 扫码登录相关常量
CONF_USER_CODE = "user_code"
CONF_TOKEN_INFO = "token_info"
TUYA_CLIENT_ID = "HA_3y9q4ak7g4ephrvke"
TUYA_SCHEMA = "haauthorize"


# ============================================================================
# 传感器定义
# ============================================================================
@dataclass(frozen=True)
class GR2PWSSensorDescription(SensorEntityDescription):
    """传感器实体描述，继承 HA 的 SensorEntityDescription。"""
    scale: int = 0


SENSORS: dict[str, GR2PWSSensorDescription] = {
    "cur_voltage": GR2PWSSensorDescription(
        key="cur_voltage",
        translation_key="cur_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        scale=2,
        icon="mdi:flash",
    ),
    "cur_current": GR2PWSSensorDescription(
        key="cur_current",
        translation_key="cur_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        scale=3,
        icon="mdi:current-ac",
    ),
    "cur_power": GR2PWSSensorDescription(
        key="cur_power",
        translation_key="cur_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        scale=2,
        icon="mdi:flash-outline",
    ),
    "cur_frequency": GR2PWSSensorDescription(
        key="cur_frequency",
        translation_key="cur_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        scale=2,
        icon="mdi:sine-wave",
    ),
    "power_factor": GR2PWSSensorDescription(
        key="power_factor",
        translation_key="power_factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=None,
        scale=2,
        icon="mdi:angle-acute",
    ),
    "cpu_temp": GR2PWSSensorDescription(
        key="cpu_temp",
        translation_key="cpu_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        scale=0,
        icon="mdi:thermometer",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "ele": GR2PWSSensorDescription(
        key="ele",
        translation_key="ele",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        scale=3,
        icon="mdi:lightning-bolt",
    ),
    "cost": GR2PWSSensorDescription(
        key="cost",
        translation_key="cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="CNY",
        scale=3,
        icon="mdi:currency-cny",
    ),
    "leakage_ele": GR2PWSSensorDescription(
        key="leakage_ele",
        translation_key="leakage_ele",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        scale=3,
        icon="mdi:flash-triangle-outline",
    ),
    "leakage_current": GR2PWSSensorDescription(
        key="leakage_current",
        translation_key="leakage_current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        scale=3,
        icon="mdi:current-ac",
    ),
    "warning": GR2PWSSensorDescription(
        key="warning",
        translation_key="warning",
        device_class=None,
        state_class=None,
        native_unit_of_measurement=None,
        scale=0,
        icon="mdi:alert-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    "add_ele": GR2PWSSensorDescription(
        key="add_ele",
        translation_key="add_ele",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        scale=2,
        icon="mdi:plus-circle-outline",
    ),
    "add_cost": GR2PWSSensorDescription(
        key="add_cost",
        translation_key="add_cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement="CNY",
        scale=2,
        icon="mdi:cash-plus",
    ),
    "balance_energy": GR2PWSSensorDescription(
        key="balance_energy",
        translation_key="balance_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        scale=2,
        icon="mdi:battery-charging",
    ),
}


# ============================================================================
# 开关定义
# ============================================================================
@dataclass(frozen=True)
class GR2PWSSwitchDescription(SwitchEntityDescription):
    """开关实体描述，继承 HA 的 SwitchEntityDescription。"""


SWITCHES: dict[str, GR2PWSSwitchDescription] = {
    "switch_1": GR2PWSSwitchDescription(
        key="switch_1",
        translation_key="switch_1",
        icon="mdi:power",
    ),
    "control": GR2PWSSwitchDescription(
        key="control",
        translation_key="control",
        icon="mdi:shield-check-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    "beep": GR2PWSSwitchDescription(
        key="beep",
        translation_key="beep",
        icon="mdi:volume-high",
        entity_category=EntityCategory.CONFIG,
    ),
    "prepayment_switch": GR2PWSSwitchDescription(
        key="prepayment_switch",
        translation_key="prepayment_switch",
        icon="mdi:cash-check",
        entity_category=EntityCategory.CONFIG,
    ),
    "real_time_switch_5s_60s": GR2PWSSwitchDescription(
        key="real_time_switch_5s_60s",
        translation_key="real_time_switch",
        icon="mdi:timer-outline",
        entity_category=EntityCategory.CONFIG,
    ),
}


# ============================================================================
# 选择器定义
# ============================================================================
@dataclass(frozen=True)
class GR2PWSSelectDescription(SelectEntityDescription):
    """选择器实体描述，继承 HA 的 SelectEntityDescription。"""


SELECTS: dict[str, GR2PWSSelectDescription] = {
    "language": GR2PWSSelectDescription(
        key="language",
        translation_key="language",
        options=["chinese", "english"],
        icon="mdi:translate",
        entity_category=EntityCategory.CONFIG,
    ),
    "sw_mode": GR2PWSSelectDescription(
        key="sw_mode",
        translation_key="sw_mode",
        options=["controlled", "normally_open"],
        icon="mdi:toggle-switch-variant",
        entity_category=EntityCategory.CONFIG,
    ),
    "standby_screen": GR2PWSSelectDescription(
        key="standby_screen",
        translation_key="standby_screen",
        options=["original", "measurement"],
        icon="mdi:monitor-screenshot",
        entity_category=EntityCategory.CONFIG,
    ),
    "menu": GR2PWSSelectDescription(
        key="menu",
        translation_key="menu",
        options=["front", "back", "display_off"],
        icon="mdi:monitor",
        entity_category=EntityCategory.CONFIG,
    ),
    "price_mode": GR2PWSSelectDescription(
        key="price_mode",
        translation_key="price_mode",
        options=["single_rate", "stair", "peak_valley_stair"],
        icon="mdi:cash-multiple",
        entity_category=EntityCategory.CONFIG,
    ),
}


# ============================================================================
# 数值定义
# ============================================================================
@dataclass(frozen=True)
class GR2PWSNumberDescription(NumberEntityDescription):
    """数值实体描述，继承 HA 的 NumberEntityDescription。"""
    scale: int = 0
    native_step: float = 1.0
    mode: str = "auto"


NUMBERS: dict[str, GR2PWSNumberDescription] = {
    "ovp": GR2PWSNumberDescription(
        key="ovp",
        translation_key="ovp",
        native_min_value=0.1,
        native_max_value=320.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        scale=1,
        device_class=NumberDeviceClass.VOLTAGE,
        icon="mdi:flash-alert",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "ocp": GR2PWSNumberDescription(
        key="ocp",
        translation_key="ocp",
        native_min_value=0.1,
        native_max_value=100.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        scale=1,
        device_class=NumberDeviceClass.CURRENT,
        icon="mdi:flash-alert-outline",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "opp": GR2PWSNumberDescription(
        key="opp",
        translation_key="opp",
        native_min_value=1,
        native_max_value=32000,
        native_step=1,
        native_unit_of_measurement=UnitOfPower.WATT,
        scale=0,
        device_class=NumberDeviceClass.POWER,
        icon="mdi:flash-red-eye",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "lvp": GR2PWSNumberDescription(
        key="lvp",
        translation_key="lvp",
        native_min_value=0.1,
        native_max_value=320.0,
        native_step=0.1,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        scale=1,
        device_class=NumberDeviceClass.VOLTAGE,
        icon="mdi:flash-outline",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "olcp": GR2PWSNumberDescription(
        key="olcp",
        translation_key="olcp",
        native_min_value=0.01,
        native_max_value=0.1,
        native_step=0.001,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        scale=3,
        device_class=NumberDeviceClass.CURRENT,
        icon="mdi:current-ac",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "price": GR2PWSNumberDescription(
        key="price",
        translation_key="price",
        native_min_value=0.0,
        native_max_value=999.99,
        native_step=0.01,
        native_unit_of_measurement="CNY/kWh",
        scale=2,
        icon="mdi:currency-cny",
        entity_category=EntityCategory.CONFIG,
        mode="box",
    ),
    "work_value": GR2PWSNumberDescription(
        key="work_value",
        translation_key="work_value",
        native_min_value=1,
        native_max_value=9,
        native_step=1,
        icon="mdi:brightness-7",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "standby_value": GR2PWSNumberDescription(
        key="standby_value",
        translation_key="standby_value",
        native_min_value=0,
        native_max_value=9,
        native_step=1,
        icon="mdi:brightness-4",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "standby_time": GR2PWSNumberDescription(
        key="standby_time",
        translation_key="standby_time",
        native_min_value=3,
        native_max_value=99,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer-sand",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "over_time": GR2PWSNumberDescription(
        key="over_time",
        translation_key="over_time",
        native_min_value=0,
        native_max_value=99,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        entity_category=EntityCategory.CONFIG,
        mode="slider",
    ),
    "countdown_1": GR2PWSNumberDescription(
        key="countdown_1",
        translation_key="countdown_1",
        native_min_value=0,
        native_max_value=360000,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:timer",
    ),
    "credit": GR2PWSNumberDescription(
        key="credit",
        translation_key="credit",
        native_min_value=10,
        native_max_value=500,
        native_step=1,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:battery-alert",
        entity_category=EntityCategory.CONFIG,
    ),
    "reporting_interval": GR2PWSNumberDescription(
        key="reporting_interval",
        translation_key="reporting_interval",
        native_min_value=1,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:update",
        entity_category=EntityCategory.CONFIG,
    ),
    "energy_charge": GR2PWSNumberDescription(
        key="energy_charge",
        translation_key="energy_charge",
        native_min_value=0.0,
        native_max_value=5000.0,
        native_step=0.01,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        scale=2,
        icon="mdi:cash-plus",
        entity_category=EntityCategory.CONFIG,
        mode="box",
    ),
    "add_ele_rw": GR2PWSNumberDescription(
        key="add_ele",
        translation_key="add_ele_rw",
        native_min_value=0.0,
        native_max_value=50000.0,
        native_step=0.01,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        scale=2,
        icon="mdi:plus-circle",
        entity_category=EntityCategory.CONFIG,
        mode="box",
    ),
}


# ============================================================================
# 按钮定义
# ============================================================================
@dataclass(frozen=True)
class GR2PWSButtonDescription(ButtonEntityDescription):
    """按钮实体描述，继承 HA 的 ButtonEntityDescription。"""


BUTTONS: dict[str, GR2PWSButtonDescription] = {
    "data_reset": GR2PWSButtonDescription(
        key="data_reset",
        translation_key="data_reset",
        icon="mdi:refresh",
        entity_category=EntityCategory.CONFIG,
    ),
    "wifi_reset": GR2PWSButtonDescription(
        key="wifi_reset",
        translation_key="wifi_reset",
        icon="mdi:wifi-off",
        entity_category=EntityCategory.CONFIG,
    ),
    "factor_reset": GR2PWSButtonDescription(
        key="factor_reset",
        translation_key="factor_reset",
        icon="mdi:restore",
        entity_category=EntityCategory.CONFIG,
    ),
    "screen_rotation": GR2PWSButtonDescription(
        key="screen_rotation",
        translation_key="screen_rotation",
        icon="mdi:screen-rotation",
        entity_category=EntityCategory.CONFIG,
    ),
    "clear_energy": GR2PWSButtonDescription(
        key="clear_energy",
        translation_key="clear_energy",
        icon="mdi:battery-off",
        entity_category=EntityCategory.CONFIG,
    ),
}


# ============================================================================
# 告警状态中文映射
# ============================================================================
WARNING_OPTIONS = {
    "off": "正常",
    "ovp": "过压告警",
    "ocp": "过流告警",
    "opp": "过功率告警",
    "lvp": "欠压告警",
    "le": "漏电告警",
    "olcp": "漏电阀值告警",
}

WARNING_OPTIONS_EN = {
    "off": "Normal",
    "ovp": "Over Voltage",
    "ocp": "Over Current",
    "opp": "Over Power",
    "lvp": "Under Voltage",
    "le": "Leakage",
    "olcp": "Over Leakage Current",
}

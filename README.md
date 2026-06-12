# ATORCH GR2PWS 智能电表

[![GitHub Release](https://img.shields.io/github/v/release/Poiig/GR2PWS_Tuya?style=flat-square)](https://github.com/Poiig/GR2PWS_Tuya/releases)
[![HACS Integration](https://img.shields.io/badge/HACS-Integration-blue?style=flat-square)](https://hacs.xyz/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green?style=flat-square)](LICENSE)

[中文](#中文) | [English](#english)

---

<a id="中文"></a>

专为 **ATORCH（炬为）GR2PWS** 智能电表设计的 Home Assistant 自定义集成。通过 [tinytuya](https://github.com/jasonacox/tinytuya) 库在本地局域网直接通信，无需云服务、无需 MQTT、无需注册涂鸦 IoT 平台账号。

## 功能特点

- **纯本地通信**：tinytuya 局域网直连，不依赖云端
- **完整实体映射**：设备 40+ 个数据点全部映射为 HA 实体
- **实时监控**：电压、电流、功率、频率、功率因数、CPU 温度（默认 5 秒轮询，可调）
- **用电统计**：总电量、总电费、日/月/年用电量（自动累加、定时重置、支持手动校准）
- **设备控制**：开关、超限控制、系统声音、预付费模式
- **参数配置**：屏幕亮度、待机设置、计价模式、保护阈值
- **完整中英文本地化**：所有实体名称和选项均有中文翻译
- **扫码配置**：通过 Smart Life APP 扫码自动获取设备信息
- **IP 自动发现**：自动扫描局域网获取设备 IP，IP 变化时自动重连
- **独立运行**：不影响 xtend_tuya 或其他涂鸦集成

## 安装

### 通过 HACS 安装（推荐）

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Poiig&repository=GR2PWS_Tuya&category=integration)

1. 点击上方按钮，通过 HACS 安装此集成
2. 重启 Home Assistant

### 手动安装

1. 下载或克隆此仓库
2. 将 `custom_components/gr2pws/` 文件夹复制到 Home Assistant 的 `custom_components/` 目录下
3. 重启 Home Assistant

## 配置

1. 在 HA 中进入 **设置 → 设备与服务 → 添加集成**
2. 搜索 "ATORCH GR2PWS" 或 "GR2PWS"
3. 输入 Smart Life APP 的用户代码（在 APP 的「设置 → 账户和安全」中找到）
4. 用 Smart Life APP 扫描 HA 显示的二维码
5. 从列表中选择 GR2PWS 设备
6. 系统自动扫描局域网获取设备 IP，完成配置

## 支持的实体

| 平台 | 数量 | 示例 |
|------|------|------|
| 传感器 | 17 | 当前电压、当前电流、当前功率、总电量、总电费、日/月/年用电量、设备 IP 等 |
| 开关 | 5 | 开关状态、超限控制使能、系统声音、预付费、实时刷新 |
| 选择器 | 5 | 设备语言、开关模式、待机画面、显示风格、计价模式 |
| 数值 | 18 | 过压值、过流值、欠压值、漏电阀值、电费单价、亮度、校准日/月/年用电量 |
| 按钮 | 8 | 累计数据清零、WiFi 重置、恢复出厂设置、重置日/月/年用电量 |

## 日/月/年用电量

集成自动创建日、月、年用电量统计传感器：

- **累加方式**：基于设备总电量（ele）的增量自动累加
- **自动重置**：日用电量每天 0:00 归零，月用电量每月 1 日归零，年用电量每年 1 月 1 日归零
- **手动校准**：通过"校准日/月/年用电量"数值实体直接设置累计值
- **手动重置**：通过"重置日/月/年用电量"按钮立即归零
- **数据恢复**：HA 重启后自动恢复上次累计值

## 轮询间隔

默认每 **5 秒** 轮询一次设备状态，可在 **设置 → 设备与服务 → ATORCH GR2PWS → 配置** 中调整（1-300 秒）。

## 网络建议

- **建议为设备分配静态 IP**：在路由器中绑定 GR2PWS 设备的 MAC 地址到固定 IP
- **自动 IP 重发现**：连续 3 次通信失败后，自动扫描局域网查找设备新 IP
- 设备长时间离线后重新上电，集成会自动恢复连接

## 与 xtend_tuya 的兼容性

此集成与 xtend_tuya **完全独立**，可以同时安装运行：

- 不同的集成域名（`gr2pws` vs `xtend_tuya`）
- 不同的通信方式（本地 tinytuya vs 云端 MQTT）
- 没有共享的 MQTT 订阅或主题
- 独立的设备注册条目

## 前置要求

- Home Assistant >= 2025.12.0
- tinytuya >= 1.17.0（自动安装）
- GR2PWS 设备与 Home Assistant 在同一局域网内
- Smart Life 或 Tuya Smart APP（用于扫码配置）

## 开源协议

本项目基于 [GPL-3.0](LICENSE) 协议开源。任何衍生作品必须以相同协议开源，不允许闭源商用。

---

<a id="english"></a>

A dedicated Home Assistant custom integration for the **ATORCH GR2PWS** smart energy meter. Communicates directly over your local network via [tinytuya](https://github.com/jasonacox/tinytuya) — no cloud, no MQTT, no Tuya IoT account needed.

## Features

- **Full Local Communication**: tinytuya direct LAN, no cloud dependency
- **Complete Entity Mapping**: 40+ data points mapped to HA entities
- **Real-time Monitoring**: Voltage, current, power, frequency, power factor, CPU temperature (5s default polling, adjustable)
- **Energy Statistics**: Total energy, cost, daily/monthly/yearly energy (auto-accumulate, auto-reset, manual calibration)
- **Device Control**: Switch, overlimit control, system sound, prepayment
- **Configuration**: Brightness, standby, price modes, protection thresholds
- **Full Localization**: Complete Chinese (zh-Hans) and English translations
- **QR Code Setup**: Auto-discover device via Smart Life APP scan
- **Auto IP Discovery**: Automatically scans LAN for device IP, reconnects on IP change
- **Independent**: Does not interfere with xtend_tuya

## Installation

### Via HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Poiig&repository=GR2PWS_Tuya&category=integration)

1. Click the button above, and install this integration via HACS
2. Restart Home Assistant

### Manual

1. Copy `custom_components/gr2pws/` to your HA `custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "ATORCH GR2PWS" or "GR2PWS"
3. Enter your Smart Life APP user code (Settings → Account and Security)
4. Scan the QR code with Smart Life APP
5. Select your GR2PWS device
6. Local IP is auto-discovered. Done.

## Supported Entities

| Platform | Count | Examples |
|----------|-------|---------|
| Sensor | 17 | Voltage, Current, Power, Energy, Cost, Daily/Monthly/Yearly Energy, Device IP |
| Switch | 5 | Main Switch, Overlimit Control, System Sound, Prepayment, Real-time Refresh |
| Select | 5 | Language, Switch Mode, Standby Screen, Display Style, Price Mode |
| Number | 18 | Over/Under Voltage, Over Current, Leakage Threshold, Price, Brightness, Calibrate Daily/Monthly/Yearly |
| Button | 8 | Reset Data, WiFi Reset, Factory Reset, Reset Daily/Monthly/Yearly Energy |

## Daily/Monthly/Yearly Energy

- **Accumulation**: Automatically accumulates based on total energy (ele) increments
- **Auto Reset**: Daily at 0:00, monthly on the 1st, yearly on Jan 1st
- **Manual Calibration**: Set accumulated value via "Calibrate Daily/Monthly/Yearly Energy" number entities
- **Manual Reset**: Reset to zero via "Reset Daily/Monthly/Yearly Energy" buttons
- **State Restore**: Values are preserved across HA restarts

## Polling Interval

Default: **5 seconds**. Adjustable in **Settings → Devices & Services → ATORCH GR2PWS → Configure** (1-300 seconds).

## Network

- **Static IP recommended**: Bind device MAC to a fixed IP in your router
- **Auto IP rediscovery**: After 3 consecutive failures, automatically scans LAN for new IP
- Auto-recovers when device comes back online

## xtend_tuya Compatibility

This integration is fully independent and can run alongside xtend_tuya simultaneously.

## Requirements

- Home Assistant >= 2025.12.0
- tinytuya >= 1.17.0 (auto-installed)
- GR2PWS device on the same local network
- Smart Life or Tuya Smart APP (for QR code setup)

## License

This project is licensed under [GPL-3.0](LICENSE). Any derivative work must also be open-sourced under the same license.

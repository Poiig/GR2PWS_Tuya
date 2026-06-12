# GR2PWS 智能电表 | GR2PWS Smart Energy Meter

[中文](#chinese) | [English](#english)

---

<a id="chinese"></a>

## GR2PWS 智能电表 - Home Assistant 集成

专为 **ATORCH GR2PWS** 智能电表设计的 Home Assistant 自定义集成。通过 [tinytuya](https://github.com/jasonacox/tinytuya) 库在本地局域网直接通信，无需云服务、无需 MQTT、无需注册涂鸦 IoT 平台账号。

### 功能特点

- **纯本地通信**：使用 tinytuya 直接在局域网内通信，不依赖云端
- **完整实体映射**：设备 40+ 个数据点全部映射为 HA 实体
- **实时监控**：电压、电流、功率、频率、功率因数、CPU 温度
- **用电追踪**：总电量、总电费、漏电电量、剩余可用电量、日/月/年用电量
- **设备控制**：开关控制、超限控制、系统声音、预付费模式
- **参数配置**：屏幕亮度、待机设置、计价模式、保护阈值
- **完整中文本地化**：所有实体名称和选项均有中文翻译
- **独立集成**：不影响 xtend_tuya 或其他涂鸦集成的安装和运行
- **扫码配置**：通过 Smart Life APP 扫码自动获取设备信息

### 配置流程

1. 在 HA 中进入 **设置 → 设备与服务 → 添加集成**
2. 搜索 "GR2PWS"
3. 输入 Smart Life APP 的用户代码（在 APP 的「设置 → 账户和安全」中找到）
4. 用 Smart Life APP 扫描 HA 显示的二维码
5. 从列表中选择 GR2PWS 设备
6. 系统自动扫描局域网获取设备 IP，完成配置

### 安装

#### 通过 HACS 安装（推荐）

1. 在 HACS 中，进入 **集成** 页面
2. 点击右上角三个点菜单 → **自定义仓库**
3. 添加此仓库的 URL，类别选择 **集成**
4. 搜索 "GR2PWS" 并安装
5. 重启 Home Assistant

#### 手动安装

1. 下载或克隆此仓库
2. 将 `custom_components/gr2pws/` 文件夹复制到 Home Assistant 的 `custom_components/` 目录下
3. 重启 Home Assistant

### 支持的实体

| 平台 | 数量 | 示例 |
|------|------|------|
| 传感器 | 18 | 当前电压、当前电流、当前功率、总电量、总电费、日/月/年用电量、设备IP等 |
| 开关 | 5 | 开关状态、超限控制使能、系统声音、预付费、实时刷新 |
| 选择器 | 5 | 设备语言、开关模式、待机画面、显示风格、计价模式 |
| 数值 | 15 | 过压值、过流值、欠压值、漏电阀值、电费单价、亮度等 |
| 按钮 | 5 | 累计数据清零、WiFi重置、恢复出厂设置、屏幕旋转、剩余电量清零 |

### 日/月/年用电量

集成自动创建日用电量、月用电量、年用电量三个 Utility Meter 实体。这些实体基于总电量传感器自动计算，支持在 HA 界面中手动纠正数值。

### 轮询间隔

默认每 **5 秒** 轮询一次设备状态。可在 HA 的 **设置 → 设备与服务 → GR2PWS → 配置** 中调整。

### IP 地址与网络

- **建议为设备分配静态 IP**：在路由器中将 GR2PWS 设备的 MAC 地址绑定固定 IP，避免设备重启后 IP 变化导致通信中断
- **自动 IP 重新发现**：当连续 3 次通信失败后，集成会自动扫描局域网重新查找设备 IP，无需手动干预
- 如果设备长时间离线（如断电），重新上电后集成会自动恢复连接

### 与 xtend_tuya 的兼容性

此集成与 xtend_tuya **完全独立**：

- 不同的集成域名（`gr2pws` vs `xtend_tuya`）
- 不同的通信方式（本地 tinytuya vs 云端 MQTT）
- 没有共享的 MQTT 订阅或主题
- 独立的设备注册条目
- 两者可以同时安装和运行，互不干扰

### 前置要求

- Home Assistant >= 2024.1.0
- tinytuya >= 1.17.0（自动安装）
- GR2PWS 设备与 Home Assistant 在同一局域网内
- Smart Life 或 Tuya Smart APP（用于扫码配置）

---

<a id="english"></a>

## GR2PWS Smart Energy Meter - Home Assistant Integration

A dedicated Home Assistant custom integration for the **ATORCH GR2PWS** smart energy meter. Communicates directly over your local network via [tinytuya](https://github.com/jasonacox/tinytuya) — no cloud, no MQTT, no Tuya IoT account needed.

### Features

- **Full Local Communication**: tinytuya direct LAN, no cloud dependency
- **Complete Entity Mapping**: 40+ data points mapped to HA entities
- **Real-time Monitoring**: Voltage, current, power, frequency, power factor, CPU temperature
- **Energy Tracking**: Total energy, cost, leakage, balance, daily/monthly/yearly
- **Device Control**: Switch, overlimit control, system sound, prepayment
- **Configuration**: Brightness, standby, price modes, protection thresholds
- **Full Chinese Localization**: Complete zh-Hans translations
- **Independent**: Does not interfere with xtend_tuya
- **QR Code Setup**: Auto-discover via Smart Life APP scan

### Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "GR2PWS"
3. Enter your Smart Life APP user code (Settings → Account and Security)
4. Scan the QR code with Smart Life APP
5. Select your GR2PWS device
6. Local IP is auto-discovered. Done.

### Installation

#### Via HACS (Recommended)

1. In HACS → **Integrations** → **Custom Repositories**
2. Add this repo URL, category: **Integration**
3. Install "GR2PWS" and restart Home Assistant

#### Manual

1. Copy `custom_components/gr2pws/` to your HA `custom_components/` directory
2. Restart Home Assistant

### Supported Entities

| Platform | Count | Examples |
|----------|-------|---------|
| Sensor | 18 | Voltage, Current, Power, Energy, Cost, Daily/Monthly/Yearly, Device IP |
| Switch | 5 | Main Switch, Overlimit Control, System Sound, Prepayment, Real-time Refresh |
| Select | 5 | Language, Switch Mode, Standby Screen, Display Style, Price Mode |
| Number | 15 | Over/Under Voltage, Over Current, Leakage Threshold, Price, Brightness, etc. |
| Button | 5 | Reset Data, WiFi Reset, Factory Reset, Screen Rotation, Clear Energy |

### Requirements

- Home Assistant >= 2024.1.0
- tinytuya >= 1.17.0 (auto-installed)
- GR2PWS device on the same local network
- Smart Life or Tuya Smart APP (for QR code setup)

### IP Address & Network

- **Static IP recommended**: Bind the GR2PWS device MAC to a fixed IP in your router to prevent connection loss after device reboot
- **Auto IP rediscovery**: After 3 consecutive communication failures, the integration automatically scans the LAN to find the device's new IP
- If the device goes offline (e.g. power loss), the integration will auto-recover when the device comes back online

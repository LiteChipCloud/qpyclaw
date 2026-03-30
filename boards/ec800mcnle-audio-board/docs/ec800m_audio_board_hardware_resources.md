# EC800M Audio Board V1.1 硬件资源整理

## 1. 资料来源

本整理基于板卡目录中的原始设计文件，而不是二手转述：

- `resource/EC800M AUDIO V1.1 SCH(1).pdf`
- `resource/EC800M AUDIO V1.1 SCH & PCB/EC800X.SchDoc`
- `resource/EC800M AUDIO V1.1 SCH & PCB/AUDIO.SchDoc`
- `resource/EC800M AUDIO V1.1 SCH & PCB/LCD.SchDoc`
- `resource/EC800M AUDIO V1.1 SCH & PCB/POWER.SchDoc`

## 2. 结论先看

这块板子本质上是一块围绕 `EC800M` 平台做的音频/显示/电池供电小板，硬件资源重点不是“通用 IO 全引出”，而是已经按 AI 语音终端的方向把几类资源配齐了：

- 蜂窝模组：`U1`，原理图库符号名是 `EC800G-CN`，但器件注释实际填的是 `EC800M-CN`
- 音频输入：板载麦克风 `MIC1`
- 音频输出：功放 `U5` + 外接扬声器座 `J3`
- 显示：SPI LCD 接口、复位/命令控制、TE 信号、背光控制
- 用户交互：`PWRKEY` 按键 `SW1`
- 外设接口：USB Type-C、SIM 卡座、天线座、电池座、LCD 接口座
- 供电：USB 供电、单节锂电充电、板载 3.3V LDO、电池直接给模组/功放供电

它更像是一个可直接拿来做语音对讲、AI 对话、带小屏交互终端的硬件底板。

这里要补一个自审后的型号口径：

- 本地原理图层面可直接看到的是 `EC800M-CN`
- 官方 QuecPython 方案和开发板口径应优先写成 `EC800MCNLE`

因此这份文档里更稳妥的结论是：

- 板级硬件属于 `EC800M` 家族音频开发板
- 研发目标平台按 `EC800MCNLE` 理解

## 3. 板级硬件资源总表

| 类别 | 资源 | 关键器件/信号 | 说明 |
| --- | --- | --- | --- |
| 核心模组 | 蜂窝通信主控 | `U1 = EC800M` 平台 | 原理图库符号名为 `EC800G-CN`，Comment 为 `EC800M-CN`；官方方案平台按 `EC800MCNLE` 理解 |
| USB | USB 2.0 + 供电输入 | `USBC1 = USB3.1C16PFSMT`，`USB_DP`，`USB_DM`，`USB_VBUS` | 用于供电、下载、调试 |
| SIM | USIM 卡接口 | `CARD1 = SMN-303`，`SIM_DATA/SIM_CLK/SIM_RST/SIM_VDD/SIM_DET` | 板载 SIM 卡座 |
| 天线 | 主天线接口 | `J1 = ANT`，`ANT_MAIN` | 板载天线座，旁边带 ESD 保护 |
| 音频输入 | 麦克风 | `MIC1 = B4013AM423-092`，`MIC_P/MIC_N` | 板载麦克风，走模组音频输入 |
| 音频输出 | 功放 + 扬声器接口 | `U5 = NS4160` 库符号，Comment 为 `NS4150C`；`J3` 扬声器座 | 模组音频输出进入功放后再驱动外部喇叭 |
| 显示 | SPI LCD 接口 | `LCD_SPI_CS`，`LCD_SPI_CLK`，`LCD_SPI_DOUT`，`LCD_RS`，`LCD_RST`，`LCD_TE` | 已单独做 LCD 子页，并有电平转换 |
| LCD 电平域 | 逻辑电平转换 | `TXS0104ERGYR` | 模组侧 `VDD_EXT` 到 LCD 侧 `VCC_3V3` 的电平转换 |
| 背光/辅助驱动 | LCD 背光或开关控制 | `MMBT3904T`，`HXY1012CI`，`BLK` | 用离散管做控制 |
| 电池 | 单节锂电接口 | `J2 = WAFER-MX1.25-2PWB` | 电池直接挂在 `VBAT` |
| 充电 | 线性充电 | `U2 = HX4057A` 库符号，Comment 为 `ME4055AM6G-N` | 带 `CHRG/STDBY` 状态脚 |
| 3.3V 电源 | 板载 LDO | `U3 = ME6203A50M3G` 库符号，Comment 为 `XC6206P332MR` | 生成 `VCC_3V3`，供 LCD 等外设 |
| 指示灯 | 状态/充电指示 | `D14` 绿灯，`D19` 蓝灯，配合 `Q3` | 至少有一组系统状态灯和一组充电相关指示 |

## 4. 核心模组资源

### 4.1 模组识别

- `U1` 的设计器件符号名是 `EC800G-CN`
- 但该器件的 `Comment` 实际写的是 `EC800M-CN`
- 制板目录、PDF 文件名、工程目录名也都明确写的是 `EC800M AUDIO`

因此更稳妥的判断是：

- 本地设计目标属于 `EC800M` 平台
- 原理图复用了 `EC800G-CN` 的符号封装资源
- 对应官方 QuecPython 项目时，研发应优先使用 `EC800MCNLE` 这个开发板型号

### 4.2 在原理图上明确可见的模组引脚资源

从 `EC800X.SchDoc` 中能直接提取到以下关键引脚名：

- 音频：`MIC_P`、`MIC_N`、`SPK_P`、`SPK_N`
- 控制：`PWRKEY`、`RESET_N`、`STATUS`、`NET_STATUS`、`USB_BOOT`
- USB：`USB_DP`、`USB_DM`、`USB_VBUS`
- SIM：`USIM_DATA`、`USIM_RST`、`USIM_CLK`、`USIM_VDD`、`USIM_DET`
- 串口：`MAIN_RXD`、`MAIN_TXD`、`AUX_RXD`、`AUX_TXD`、`DBG_RXD`、`DBG_TXD`
- 电源/逻辑：`VBAT1`、`VBAT2`、`VDD_EXT`
- 其他接口能力：`ADC0`、`I2C_SDA`、`I2C_SCL`、`PCM_CLK`、`PCM_SYNC`、`PCM_DIN`、`PCM_DOUT`
- 射频相关：`ANT_MAIN`、`ANT_GNSS`、`ANT_WIFI_SCAN`

注意：

- 以上是模组符号上可见能力，不等于所有引脚都被这块板子完整引出到外部接口
- 能明确确认已经在板级电路中被使用的，是 USB、SIM、天线、麦克风、功放/喇叭、LCD、PWRKEY、电池/充电这些资源

## 5. 各子系统详细记录

### 5.1 EC800X 主控页

主控页对应 `EC800X.SchDoc`，主要承担模组本体和基础外围：

- `U1`：`EC800M` 平台，研发口径优先按 `EC800MCNLE` 理解
- `CARD1`：`SMN-303` SIM 卡座
- `J1`：天线座 `ANT`
- `SW1`：轻触按键 `TS-1101VS-C-A-A`，用于 `PWRKEY`
- `D14`：绿灯 `XL-1608UGC-04`
- `Q3`：`DTC143ZE` 数字三极管，用于 LED/控制级
- `D9`：`LESD8LL5.0T5G` ESD 保护

板级明确能确认的对外资源：

- 蜂窝主天线
- SIM 卡
- USB
- PWRKEY 开机控制
- 状态指示灯

### 5.2 音频页

音频页对应 `AUDIO.SchDoc`，这是这块板子最核心的特色之一。

#### 输入部分

- `MIC1`：器件库名 `GMI6050P-66DB`
- 实际注释/BOM 型号：`B4013AM423-092`
- 连接到模组 `MIC_P/MIC_N`

说明：

- 这是板载麦克风方案，不需要额外再接模拟麦克风前端板
- 音频页中还布了磁珠和 ESD，说明这一路是按可实际量产的语音前端来处理的

#### 输出部分

- `U5`：器件库名 `NS4160`
- `Comment`：`NS4150C`
- 典型引脚：`INP`、`INN`、`VoP`、`VoN`、`VDD`、`GND`、`CTRL`
- `J3`：`WAFER-MX1.25-2PWB`，外接扬声器接口

说明：

- 模组的 `SPK_P/SPK_N` 没有直接裸接喇叭，而是先进功放
- 这意味着板子面向的是“可直接驱动外部喇叭”的应用，而不是只接耳机或只做线性音频输出

#### 音频保护/滤波

- `LESD8LL5.0T5G`：ESD 保护
- `PZ1005U121-1R0TF`：磁珠，100MHz 阻抗等级

结论：

- 这块板子的音频链路是完整的，具备“采音 + 放音”闭环能力，适合语音交互项目

### 5.3 LCD 页

LCD 页对应 `LCD.SchDoc`，证明这块板子并不只是“音频板”，而是明确考虑了小屏交互。

#### LCD 信号

在原理图中能直接提取到这些 LCD 相关信号名：

- `LCD_SPI_CS`
- `LCD_SPI_CLK`
- `LCD_SPI_DOUT`
- `LCD_RS`
- `LCD_RST`
- `LCD_TE`
- `BLK`

这些信号同时还出现了 `_3V3` 后缀版本，说明设计中做了电平域转换。

#### 关键器件

- `TXS0104ERGYR`：4bit 电平转换芯片
- `MMBT3904T`：小信号三极管
- `HXY1012CI`：NMOS
- `J6`：`Header 8`
- `J4`：`HC-1.25-3PWT`

设计意图基本可以判断为：

- 模组侧逻辑信号先从 `VDD_EXT` 电平域出来
- 经过 `TXS0104E` 转到 `VCC_3V3`
- 再送到 LCD/背光相关接口

也就是说，这块板子的显示接口不是“预留一下”，而是已经做到可用的 SPI LCD 小屏接口级别。

### 5.4 电源页

电源页对应 `POWER.SchDoc`。

#### USB 输入

- `USBC1`：`USB3.1C16PFSMT`
- 关键信号：`VBUS`、`DP1/DP2`、`DN1/DN2`、`CC1`、`CC2`

用途：

- USB 供电输入
- USB 数据下载/调试

#### 电池与充电

- `J2`：1.25mm 2Pin 电池座
- `U2`：库符号 `HX4057A`，Comment 为 `ME4055AM6G-N`
- 引脚：`VCC`、`BAT`、`PROG`、`CHRG`、`STDBY`、`GND`

说明：

- 这是典型单节锂电线性充电架构
- 板子支持 USB 供电 + 电池供电两种场景
- `CHRG/STDBY` 说明有充电状态指示电路

#### 板载 3.3V

- `U3`：库符号 `ME6203A50M3G`
- Comment：`XC6206P332MR`
- 引脚：`VIN`、`VOUT`、`VSS`
- 输出电源网：`VCC_3V3`

用途判断：

- 为 LCD 和其他 3.3V 外围提供供电
- 模组本体主供电仍走 `VBAT`

## 6. 对外连接器与可直接利用的板级资源

结合四张子页，板级可以直接利用的物理资源如下：

### 6.1 已确认的连接器/接口

- `USBC1`：USB Type-C
- `CARD1`：SIM 卡座
- `J1`：蜂窝主天线座
- `J2`：电池座
- `J3`：扬声器座
- `J4`：LCD/辅助 3Pin 接口
- `J6`：LCD 8Pin 接口

### 6.2 已确认的交互资源

- 板载麦克风
- 外接喇叭功放输出
- LCD 屏接口
- 电源按键
- 状态/充电指示灯

## 7. 这块板子适合做什么

从硬件组合看，这块板子最适合做以下类型项目：

- AI 语音助手
- 语音对讲/语音聊天终端
- 带小屏 UI 的语音盒子
- 蜂窝联网音频播报终端
- 带电池的便携式语音设备

它不太像传统“模组最小系统板”，而更像一块已经偏应用化的 AI 语音终端底板。

## 8. 设计文件里需要注意的 BOM/符号替换现象

这套工程里有几处“库符号”和“最终注释/BOM 型号”不完全一致的情况，后续做二次开发或复刻时要特别注意：

- `U1`：库符号 `EC800G-CN`，本地注释为 `EC800M-CN`，方案/研发口径优先按 `EC800MCNLE`
- `U5`：库符号 `NS4160`，实际注释 `NS4150C`
- `U2`：库符号 `HX4057A`，实际注释 `ME4055AM6G-N`
- `U3`：库符号 `ME6203A50M3G`，实际注释 `XC6206P332MR`

因此如果后续要做：

- BOM 导出
- 器件替换
- 采购校对
- 原理图转 PCB 再投板

最好以 `Comment / Manufacturer Part / Datasheet` 三项交叉核对，而不要只看 `LibReference`。

## 9. 最终判断

`EC800M AUDIO V1.1` 这块板子的板级资源已经足够支撑一个完整的 QuecPython AI 语音终端：

- 有模组
- 有 SIM
- 有 USB
- 有电池充电
- 有麦克风
- 有喇叭功放
- 有 LCD 接口
- 有按键和状态灯

从硬件形态上看，它和 QuecPython 官方那几套 AI 语音/小智/AIBox 类开源项目是高度同类的。

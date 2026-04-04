# EC800M Audio Board 软件资源映射

## 1. 这份文档的目标

这份文档不是重复硬件 BOM，而是从研发开发的角度，把这块 `EC800M AUDIO V1.1` 板子的资源整理成下面这种可直接对照的软件视图：

- 板上外设/连接器
- 板级网络名
- EC800M 模组引脚号
- 模组功能名
- 这是“固定功能脚”还是“可按 GPIO 理解的控制脚”
- QuecPython 开发时应该走哪一类接口/API

## 2. 一个先说清楚的判断

这块板子**不是通用 GPIO 扩展板**。

它更像一块已经按应用方向定过型的 AI 语音终端底板，所以很多外设并不是“随便找几个 GPIO 去 bitbang”：

- USB 是固定功能
- SIM 是固定功能
- MIC/SPK 是固定音频功能
- LCD 大概率走模组的专用 LCM 接口
- 主串口已经被转换后引出
- PWRKEY 是电源控制脚，不是普通 GPIO

所以真正适合研发使用的整理方式，不是只做一张 “GPIO 对照表”，而是做一张：

`外设 -> 网络名 -> 模组脚位 -> 功能类别 -> QuecPython 调用方式`

## 3. 资料来源

### 3.1 本地设计文件

- `resource/EC800M AUDIO V1.1 SCH(1).pdf`
- `resource/EC800M AUDIO V1.1 SCH & PCB/EC800X.SchDoc`
- `resource/EC800M AUDIO V1.1 SCH & PCB/AUDIO.SchDoc`
- `resource/EC800M AUDIO V1.1 SCH & PCB/LCD.SchDoc`
- `resource/EC800M AUDIO V1.1 SCH & PCB/POWER.SchDoc`

### 3.2 官方引脚资料

- `Quectel_EC800M-CN_QuecOpen_Hardware_Design_V1.1.pdf`
- QuecPython 官方方案文档：`xiaozhi_AI_mqtt`
- QuecPython 官方方案文档：`AIbox`

说明：

- 主控页里 `U1` 的库符号叫 `EC800G-CN`
- 但器件 Comment 明确写的是 `EC800M-CN`
- 官方方案文档里，目标开发板型号应按 `EC800MCNLE` 理解
- 本文采用两层口径：
  - 引脚功能映射：以 `EC800M-CN` 硬件设计文档作为依据
  - 方案/产品/开发板命名：以 `EC800MCNLE` 为主

### 3.3 本次使用的 Skills

这次整理使用的是 `quecpython-dev` skill。

实际采用了它的这几个工作思路：

- 用官方文档工作流核对 `xiaozhi_AI_mqtt` 和 `AIbox`
- 用项目/方案关系工作流判断主对应项目与参考项目
- 用 QuecPython 设备侧视角区分“固定功能脚”和“类 GPIO 控制脚”
- 用本地 QuecPython stubs 交叉确认 `machine.Pin`、`machine.UART`、`machine.LCD`、`audio`、`checkNet`、`dataCall`、`request`、`umqtt` 等 API 形态

### 3.4 这次自审后的型号结论

这里把口径统一：

- 说“官方方案、官方开发板、项目目标板”时，优先使用 `EC800MCNLE`
- 说“本地原理图里出现的模组家族命名、底层引脚资料”时，可使用 `EC800M-CN`

所以更稳妥的表达是：

- 研发目标平台：`EC800MCNLE`
- 底层引脚映射参考：`EC800M-CN`

## 4. 研发最该先记住的结论

### 4.1 这块板子的“软件资源核心”

对软件开发最重要的资源其实就 4 类：

1. 主串口
2. SIM/网络
3. 音频输入输出
4. LCD/LCM 接口

### 4.2 真正需要当成 GPIO 去研究的点并不多

当前能明确确认的板级资源里：

- `USB`
- `SIM`
- `MIC`
- `SPK`
- `PWRKEY`
- `MAIN_UART`
- `LCD_SPI_*`
- `LCD_TE`

这些都更像**专用功能脚**，不建议一上来就把它们当“普通 GPIO”处理。

从开发效率来看，更好的做法是：

- 固定功能接口按模块 API 驱动
- 只有无法走固定功能接口的控制点，再研究是否需要按 GPIO/Pin 使用

## 5. 外设到模组脚位的软件映射总表

| 板级资源 | 板级网络/连接器 | 模组引脚号 | 模组功能名 | 类别判断 | 软件侧建议 |
| --- | --- | --- | --- | --- | --- |
| 麦克风输入 | `MIC1` -> `MIC1P/MIC1N` | `3`, `4` | `MIC_P`, `MIC_N` | 固定音频接口 | 走音频采集/录音相关接口，不按 GPIO 使用 |
| 喇叭输出 | `SPK_P`, `SPK_N` -> 功放 `U5` -> `J3` | `5`, `6` | `SPK_P`, `SPK_N` | 固定音频接口 | 走音频播放/TTS/语音通话路径，不按 GPIO 使用 |
| 开机键 | `SW1` -> `PWRKEY` | `7` | `PWRKEY` | 电源控制脚 | 硬件开机键，不按普通 GPIO 驱动 |
| SIM 数据 | `SIM_DATA` | `11` | `USIM_DATA` | 固定 SIM 接口 | 由蜂窝协议栈管理，不按 GPIO 使用 |
| SIM 复位 | `SIM_RST` | `12` | `USIM_RST` | 固定 SIM 接口 | 同上 |
| SIM 时钟 | `SIM_CLK` | `13` | `USIM_CLK` | 固定 SIM 接口 | 同上 |
| SIM 供电 | `SIM_VDD` | `14` | `USIM_VDD` | 固定 SIM 接口 | 同上 |
| 网络状态 | 系统状态灯控制相关 | `16` | `NET_STATUS` | 专用状态脚 | 更适合作状态指示，不建议随意改作 GPIO |
| 主串口 RX | `MAIN_RXD` -> `RXD2` -> `J4` | `17` | `MAIN_RXD` | 固定 UART | 走 UART，不按 GPIO 使用 |
| 主串口 TX | `MAIN_TXD` -> `TXD2` -> `J4` | `18` | `MAIN_TXD` | 固定 UART | 走 UART，不按 GPIO 使用 |
| 外设逻辑电源 | `VDD_EXT` | `24` | `VDD_EXT` | 电源输出脚 | 这是 I/O 参考电源，不是 GPIO |
| 模组状态 | 板上状态控制相关 | `25` | `STATUS` | 专用状态脚 | 适合作状态检测，不建议先按 GPIO 理解 |
| 主天线 | `ANT_MAIN` -> `J1` | `27` | `ANT_MAIN` | 射频接口 | 硬件射频通道，无软件 GPIO 概念 |
| USB D+ | `USB_DP` -> `USBC1` | `59` | `USB_DP` | 固定 USB 接口 | 走 USB 下载/调试/数据功能 |
| USB D- | `USB_DM` -> `USBC1` | `60` | `USB_DM` | 固定 USB 接口 | 同上 |
| USB VBUS 检测/供电 | `USB_VBUS` -> `USBC1` | `61` | `USB_VBUS` | 固定 USB 接口 | 同上 |
| LCD 数据/命令 | `LCD_RS` | `51` | `LCD_SPI_RS` | 专用 LCM 接口 | 优先按 LCD/LCM 控制信号理解，不按普通 GPIO |
| LCD 片选 | `LCD_SPI_CS` | `52` | `LCD_SPI_CS` | 专用 LCM 接口 | 同上 |
| LCD 时钟 | `LCD_SPI_CLK` | `53` | `LCD_SPI_CLK` | 专用 LCM 接口 | 同上 |
| LCD 数据输出 | `LCD_SPI_DOUT` | `50` | `LCD_SPI_DOUT` | 专用 LCM 接口 | 同上 |
| LCD 复位 | `LCD_RST` | `49` | `LCD_RST` | 专用 LCM 接口 | 同上 |
| LCD TE | `LCD_TE` | `78` | `LCD_TE` | 专用 LCM 同步脚 | 若驱动需要 TE，同样按 LCD 专用脚处理 |
| SIM 检测 | `SIM_DET` | `79` | `USIM_DET` | 专用检测脚 | 可在软件中做卡插入状态判断，但不是通用 GPIO |
| USB_BOOT | `USB_BOOT` | `82` | `USB_BOOT` | 启动/下载相关脚 | 不建议在应用开发中挪作普通 GPIO |

## 6. 连接器级别的开发对照

## 6.1 J6：LCD 8Pin 接口

从 `LCD.SchDoc` 可以明确扣出 `J6` 的针脚和信号对应关系：

| J6 引脚 | 板级信号 | 说明 |
| --- | --- | --- |
| 1 | `GND` | 地 |
| 2 | `VCC_3V3` | LCD 3.3V 供电 |
| 3 | `LCD_SPI_CLK_3V3` | LCD SPI 时钟，来自模组 `LCD_SPI_CLK` 经电平转换 |
| 4 | `LCD_SPI_DOUT_3V3` | LCD SPI 数据输出，来自模组 `LCD_SPI_DOUT` 经电平转换 |
| 5 | `LCD_RST_3V3` | LCD 复位，来自模组 `LCD_RST` 经电平转换 |
| 6 | `LCD_RS_3V3` | LCD D/C 控制，来自模组 `LCD_SPI_RS` 经电平转换 |
| 7 | `BLK` | 背光相关信号，当前只确认是板级背光线，模组侧直连关系还需要二次核对 |
| 8 | `LCD_SPI_CS_3V3` | LCD 片选，来自模组 `LCD_SPI_CS` 经电平转换 |

补充说明：

- `TXS0104ERGYR` 负责至少一部分 LCD 控制线的电平转换
- 模组侧逻辑域是 `VDD_EXT`
- LCD 侧工作域是 `VCC_3V3`

这意味着：

- 如果后续做软件 bring-up，LCD 不只是“有 SPI 就行”
- 还必须考虑模组专用 LCM 引脚与外部 3.3V 屏之间的电平域关系

## 6.2 J4：3Pin 串口接口

从 `LCD.SchDoc` 里能扣出 `J4` 的 3 个针脚：

| J4 引脚 | 板级信号 | 推断来源 |
| --- | --- | --- |
| 1 | `RXD2` | 引脚纵坐标与网络名对应 |
| 2 | `TXD2` | 引脚纵坐标与网络名对应 |
| 3 | `GND` | 与 `GND` 网络对齐 |

同时在同一页还能看到：

- `MAIN_TXD`
- `MAIN_RXD`
- `TXD2`
- `RXD2`

以及一组电平/保护器件：

- `HXY1012CI`
- 上拉电阻
- 二极管/保护器件

因此可以高置信度判断：

- `J4` 是从模组主串口引出的板级串口接口
- `TXD2/RXD2` 是板外接口侧命名
- 模组侧对应 `MAIN_TXD/MAIN_RXD`

换句话说，研发调试时可以把 `J4` 看成一组对外串口：

- `J4-2`：模块 TX 输出
- `J4-1`：模块 RX 输入
- `J4-3`：GND

## 6.3 CARD1：SIM 卡座

`CARD1 = SMN-303` 的卡座管脚在原理图中可直接读到：

| CARD1 引脚 | 卡座功能 | 对应模组功能 |
| --- | --- | --- |
| C1 | `VCC` | `USIM_VDD` |
| C2 | `RST` | `USIM_RST` |
| C3 | `CLK` | `USIM_CLK` |
| C7 | `I/O` | `USIM_DATA` |
| CD | `CD` | `USIM_DET` |
| C5 | `GND` | GND |

这个接口完全按 SIM 固定功能理解，不需要做 GPIO 配置。

## 6.4 J1：天线座

`J1 = ANT`：

- 中心端是 `ANT_MAIN`
- 旁边两个端子是地

这是 RF 通道，不存在 GPIO 意义。

## 7. 从软件角度怎么分类这些资源

### 7.1 固定功能资源

这类资源不建议研发先按 GPIO 思维去碰：

- `USB_DP/USB_DM/USB_VBUS`
- `USIM_*`
- `MIC_P/MIC_N`
- `SPK_P/SPK_N`
- `MAIN_RXD/MAIN_TXD`
- `LCD_SPI_*`
- `LCD_TE`
- `PWRKEY`

它们更适合按以下路径使用：

- USB：下载、日志、串口、协议栈
- SIM/蜂窝：网络注册、拨号、云连接
- 音频：录音、播放、TTS、对讲、AI 语音
- 串口：调试口/外设串口
- LCD：LCM/LCD 驱动

### 7.2 类 GPIO/控制型资源

当前资料下，真正可能需要进一步按 Pin/GPIO 研究的，是这些点：

- `BLK`：LCD 背光控制线，当前只确认到板级，不确认最终直连到哪个模组脚
- `STATUS / NET_STATUS`：适合做状态读写/指示，但不建议在不核实启动和网络行为前就重定义
- `USB_BOOT`：涉及启动/下载流程，不建议直接拿来做应用 GPIO

## 8. 对 QuecPython 开发的直接建议

### 8.1 先不要把 LCD 口当普通 SPI + 普通 GPIO

从当前资料看，LCD 相关信号更像模组的专用 LCM 引脚：

- `LCD_RST`
- `LCD_SPI_DOUT`
- `LCD_SPI_RS`
- `LCD_SPI_CS`
- `LCD_SPI_CLK`
- `LCD_TE`

因此更合理的开发顺序是：

1. 先确认 EC800M 当前固件是否直接提供 LCD/LCM 驱动接口
2. 再确认这些接口在 QuecPython 里的模块/API 名称
3. 只有在官方驱动路径走不通时，再考虑退回到“GPIO + bitbang/自定义驱动”方案

### 8.2 音频链路优先按“应用功能”开发，不要按引脚开发

这块板子的音频已经闭环：

- 板载 MIC
- 模组音频输入
- 模组音频输出
- 外部功放
- 外接喇叭

所以研发应优先按：

- 录音
- 播放
- TTS
- 语音会话

这些能力去验证，而不是先纠结成“这两个脚是不是 GPIO”。

### 8.3 串口是最好先打通的“软件入口”

从开发效率上看，建议第一优先打通：

- `J4` 主串口

因为它可以直接用于：

- REPL/日志
- 初期驱动 bring-up
- 上层应用日志观察

## 9. 当前还需要二次确认的点

下面这些点我认为还能继续深挖，但已经不影响先开始研发：

### 9.1 BLK 最终来自哪个模组脚

当前能确认：

- `BLK` 在 `J6` 上输出
- LCD 页上存在背光相关管子/控制电路

当前还没完全扣实：

- `BLK` 是否直接由模组某个功能脚驱动
- 还是板上做了固定使能/半自动控制

### 9.2 LCD_TE 的物理引出路径

当前能确认：

- `LCD_TE` 网络在主控页与 LCD 页都出现
- 官方 EC800M 硬件设计中该信号对应模组专用脚位

当前还没完全扣实：

- 它是否进入某个未完全展开的连接点
- 还是只作为保留同步线存在

### 9.3 `TXD2/RXD2` 电平转换细节

当前高置信度判断：

- `J4` 对外就是主串口

但如果你后面要接 5V 转串口板、长线、或者其他 3.3V 外设，最好再根据 PDF 或 PCB 复核一下这一段的电平和保护方式。

## 10. 当前已经补齐的配套产物

围绕这块板子，当前已经补齐了几份能直接配合研发使用的资料：

- `docs/ec800m_audio_board_hardware_resources.md`
- `docs/ec800m_audio_board_board_map.md`
- `docs/ec800m_audio_board_quecpython_projects.md`
- `code/project/board_map.json`
- `code/project/board_map.py`

它们各自的定位是：

- `hardware_resources`：偏原理图/BOM/连接器视角
- `board_map`：偏板级信号与模组功能映射视角
- 当前这份 `software_resource_map`：偏研发联调、API、入口文件与仓库代码落点视角
- `board_map.json` / `board_map.py`：偏后续代码引用和自动化处理视角

## 11. 当前最实用的一句话总结

对这块 `EC800M AUDIO V1.1` 板子来说，研发最应该掌握的不是“GPIO 有多少个”，而是：

- 哪些资源本来就是模组专用功能
- 哪些连接器已经替你把这些专用功能引到板外
- 哪些控制点才值得继续往 GPIO 映射深挖

从当前资料看，这块板子最关键的软件资源已经足够支撑：

- 主串口调试
- SIM/蜂窝联网
- 录音与播音
- SPI LCD 显示 bring-up

这已经可以直接进入应用开发阶段了。

## 12. 结合 `AIChatbot-Xiaozhi-Mqtt` 仓库后的代码视图

### 12.1 已确认的主仓库

当前针对这块板子的主参考开源项目，已经统一为：

- 仓库名：`AIChatbot-Xiaozhi-Mqtt`
- 本地路径：`code/opensource/AIChatbot-Xiaozhi-Mqtt`
- README 中明确目标板：`EC800MCNLE`

这个仓库对当前板子最有价值的地方，不是“底层驱动源码”本身，而是：

- 它把板级资源已经组织成了可运行的 QuecPython 应用结构
- 它明确展示了音频、网络、LCD、MCP 在应用层的接入方式
- 它给出了几个已经写死的板级绑定点，能反向帮助我们整理联调资源

### 12.2 仓库内三个主要运行变体

| 变体 | 路径 | 主要用途 | 关键文件 |
| --- | --- | --- | --- |
| 基础语音版 | `code/opensource/AIChatbot-Xiaozhi-Mqtt/src` | 纯语音对话，最适合先跑通网络与音频 | `_main.py`、`protocol.py`、`utils.py`、`threading.py` |
| UI 版 | `code/opensource/AIChatbot-Xiaozhi-Mqtt/src(UI)` | 带 LCD/LVGL 表情显示 | `_main.py`、`protocol.py`、`utils.py`、`lcd.py`、`ui.py` |
| MCP 版 | `code/opensource/AIChatbot-Xiaozhi-Mqtt/src(mcp)` | 带 MCP 工具能力，但不带 LCD UI | `_main.py`、`protocol.py`、`utils.py` |

补充：

- 固件包位于 `code/opensource/AIChatbot-Xiaozhi-Mqtt/fw`
- 当前仓库自带固件名为 `EC800MCNLER06A03M08_OCPU_QPY_BETA1111.zip`

### 12.3 代码入口的实际职责

从研发联调角度，可以把这些文件理解成下面这样：

| 文件 | 职责 | 研发使用方式 |
| --- | --- | --- |
| `_main.py` | 应用入口、线程组织、唤醒后会话流程 | 先看这里确认主流程和板级初始化 |
| `utils.py` | 板级资源封装，包含音频、充电、网络管理 | 看这里确认外设怎么被应用层调用 |
| `protocol.py` | OTA 获取、MQTT、UDP、音频加密与消息分发 | 看这里确认云连接和音频上下行 |
| `lcd.py` | LCD 驱动初始化参数 | 带屏联调时先看这里 |
| `ui.py` | LVGL UI 逻辑与资源路径 | 带屏联调时看这里确认界面资源要求 |
| `threading.py` | 仓库自带线程/队列/事件封装 | 看线程模型、退出逻辑和阻塞点 |

### 12.4 运行主链路

仓库的主运行链路可以概括成：

1. `_main.py` 上电后先做板级初始化
2. `ChargeManager` 使能充电控制
3. `AudioManager` 打开音频、注册 KWS/VAD 回调
4. `NetManager` 负责网络状态监听和注册恢复
5. `MqttClient` 先通过 OTA 接口取云端配置，再建 MQTT 和 UDP 会话
6. 关键词唤醒后，应用进入“采音 -> VAD 判定 -> MQTT 控制 -> UDP 发 Opus 音频”的会话流程
7. 下行消息再根据类型进入：
   - 音频下发：播放
   - TTS/LLM 文本：日志或 UI 表情刷新
   - MCP 消息：工具调用响应

## 13. 外设 / GPIO / API / 代码入口对照表

这一节是给硬件、底层、应用一起对照用的。

### 13.1 总表

| 外设/功能 | 板级资源/网络 | 建议 QuecPython API | 仓库入口/落点 | 联调重点 |
| --- | --- | --- | --- | --- |
| 主串口调试 | `J4` / `MAIN_RXD` / `MAIN_TXD` | `machine.UART`、QPYcom、REPL | 仓库业务代码未直接使用，但它是首要下载/日志入口 | 先确认电平、串口线序、日志可读 |
| SIM 与网络注册 | `CARD1` / `SIM_*` / `SIM_DET` | `sim.getStatus()`、`checkNet.waitNetworkReady()`、`net.csqQueryPoll()`、`net.setModemFun()`、`dataCall.setCallback()`、`dataCall.getInfo()` | `src/utils.py`、`src(UI)/utils.py`、`src(mcp)/utils.py` 的 `NetManager` | 先确认卡、天线、信号、PDP 激活 |
| OTA 配置获取 | 无单独 GPIO，依赖蜂窝数据链路 | `request.post()` | 三个变体的 `protocol.py` 中 `ota_get()` | 能否成功拿到 MQTT endpoint、账号和 topic |
| MQTT 控制面 | 无单独 GPIO，依赖网络 | `umqtt.MQTTClient` 的 `connect()`、`subscribe()`、`publish()`、`wait_msg()`、`get_mqttsta()` | 三个变体的 `protocol.py` | 先看连接状态，再看 topic 是否正确 |
| UDP 音频通道 | 无单独 GPIO，依赖网络 | `usocket`、`ucryptolib` | 三个变体的 `protocol.py` | 看 `hello` 后是否建立 UDP、音频是否正常收发 |
| 麦克风采音与 Opus 编解码 | `MIC1` / `MIC_P` / `MIC_N` | `audio.Record`、`audio.Audio.PCM`、`Opus` | 三个变体的 `utils.py` 中 `AudioManager` | 麦克风硬件通路、增益、连续读流是否稳定 |
| KWS/VAD | 同音频输入通路 | 仓库实际使用 `ovkws_set_callback()`、`ovkws_start()`、`ovkws_stop()`、`vad_set_callback()`、`vad_start()`、`vad_stop()` | 三个变体的 `utils.py` 中 `AudioManager` | 这些接口是仓库实用路径，固件支持要与目标固件实测对齐 |
| 喇叭、功放、音量、PA 使能 | `SPK_P` / `SPK_N` -> `U5` -> `J3` | `audio.Audio`、`set_pa()`、`setVolume()`、`getVolume()`、`play()`、`stopAll()` | 三个变体的 `utils.py`；MCP 版/ UI 版还暴露音量工具 | 先确认喇叭与功放，再确认 PA 控制和音量范围 |
| 充电控制 | 板级充电控制点 | `machine.Pin` 的 `write()` | 三个变体的 `utils.py` 中 `ChargeManager` | 当前仓库把它作为简单 GPIO 输出控制 |
| 启动/辅助控制 | 仓库内一个额外控制点 | `machine.Pin` | 三个变体的 `_main.py` | 仓库上电即拉一个 GPIO，高度建议和硬件再核对用途 |
| LCD 面板初始化 | `J6` / `LCD_RST` / `LCD_SPI_*` / `LCD_TE` | `machine.LCD`、`lcd_init()`、`lcd_clear()`、`lcd_write()`、`lvgl` | `src(UI)/lcd.py`、`src(UI)/ui.py` | 先确认屏幕型号、供电、背光，再确认初始化序列 |
| LCD 背光 | `BLK` | 可能涉及 `machine.LCD` 亮度能力，也可能是板级单独控制 | 当前 UI 代码未直接显式操作 `BLK` | 必须和实际屏幕、板级背光电路一起确认 |
| UI 图形资源 | `U:/media/*.png` | `lvgl` 图像对象 | `src(UI)/ui.py` | 下载 UI 版时必须保证用户分区图片资源齐全 |
| MCP 工具 | 无单独 GPIO，走 MQTT 消息 | 仍然是 `umqtt` 消息收发 + 应用层 JSON 处理 | `src(UI)/protocol.py`、`src(mcp)/protocol.py` | 适合在网络和音频跑通后再接入 |

### 13.2 关于 KWS/VAD 接口的一条说明

从本地 `audio` stub 能确认标准 `audio.Audio` / `audio.Record` 能力，但仓库里实际还调用了：

- `ovkws_set_callback`
- `ovkws_start`
- `ovkws_stop`
- `vad_set_callback`
- `vad_start`
- `vad_stop`

这说明当前项目依赖的是目标固件上的扩展语音能力。

研发实践里应这样理解：

- 这些接口对当前项目是“必须能力”
- 它们是否可用，不应只靠文档名判断
- 最终以你当前板子实际烧录固件上的实测结果为准

## 14. 仓库里已经写死的板级绑定与注意事项

### 14.1 已经在代码中写死的绑定点

| 项目 | 当前仓库值 | 出现位置 | 当前解读 | 备注 |
| --- | --- | --- | --- | --- |
| 启动辅助 GPIO | `Pin.GPIO33` | 三个变体 `_main.py` | 上电后立即拉高的控制点 | 需要硬件复核它到底连到了什么 |
| 充电控制 GPIO | `GPIOn=3` | 三个变体 `utils.py` 的 `ChargeManager` | 作为充电控制/使能脚使用 | 需要硬件复核板级真实网络 |
| PA 控制 GPIO | `pa_number=29` | 三个变体 `utils.py` 的 `AudioManager` | 作为外部功放 PA 控制脚使用 | 需要硬件复核真实连接关系 |
| LCD 尺寸 | `240x240` | `src(UI)/lcd.py` | 当前 UI 版按 240x240 面板组织 | 与实际屏幕型号一致性要确认 |
| LCD 时钟 | `26000` | `src(UI)/lcd.py` | `26 MHz` LCM 时钟 | 是 UI bring-up 的关键参数 |
| LCD 总线配置 | `DATA_LINE=1`、`LINE_NUM=4`、`LCD_TYPE=0` | `src(UI)/lcd.py` | 当前按 1 data line、4-line、type 0 初始化 | 与屏幕驱动模型强相关 |
| LCD 亮度参数 | `LCD_SET_BRIGHTNESS = None` | `src(UI)/lcd.py` | 当前未传独立亮度命令表 | 按本地 `machine.LCD` stub，`None` 往往意味着亮度走 `LCD_BL_K` 侧逻辑 |
| UI 图片路径 | `U:/media/*.png` | `src(UI)/ui.py` | UI 资源放在用户分区 | 不只是 `/usr` 代码，还要同步 `U:/media` |
| 预留常量 | `CONTROL_PIN_NUMBER = 20`、`TE_PIN_NUMBER = 37` | `src(UI)/lcd.py` | 当前文件内定义了常量 | 但当前 `lcd_init()` 调用并未显式把这两个常量传进去 |

### 14.2 一个必须强调的映射风险

仓库里的这些写法：

- `Pin.GPIO33`
- `Pin.GPIO3`
- `audio.Audio(...).set_pa(29)`

都应该先理解成 **QuecPython 运行时 GPIO 标识**，而不是直接等同于本文件前面按照原理图整理出的“模组外部 pin 编号”。

也就是说，研发联调时不要直接做这种机械等号：

- `Pin.GPIO33 == 模组 pin 33`
- `Pin.GPIO3 == 模组 pin 3`
- `set_pa(29) == 模组 pin 29`

更稳妥的做法是：

1. 原理图层继续使用“模组外部 pin 编号 + 网络名”
2. 代码层继续使用“QuecPython Pin/GPIO 标识”
3. 真正冻结硬件适配前，再做一次 `Pin` 编号和物理 pad 的官方对照确认

这一步非常关键，否则很容易把“代码里看到的 GPIO 号”和“原理图上的模块 pin 号”误认为是同一个编号体系。

### 14.3 在“项目开发板 = 我们当前开发板”前提下的可复用结论

如果当前项目使用的官方开发板，和我们现在要用的开发板确认是同一块板，那么：

- `Pin.GPIO33`
- `GPIOn=3`
- `pa_number=29`

这几个值就应该优先理解为**当前板子的项目级默认配置**，可以直接作为 bring-up 和应用联调的复用起点。

也就是说，站在“项目复用”而不是“原理图 pin 编号解释”的角度，这几个值的置信度已经是高的。

但仍然保留一个边界：

- 可以直接复用到项目代码和联调流程里
- 不要直接把这些数字写成“模组物理 pin 号结论”
- 真要冻结成正式板级配置说明，最好再补一次官方 pin 映射或实机电气验证记录

## 15. 推荐联调方法

这一节按“先硬件 bring-up，再应用联调”的顺序写。

### 15.1 推荐先跑哪个变体

建议顺序：

1. 先跑 `src` 基础语音版
2. 再跑 `src(UI)` 带屏版
3. 最后再跑 `src(mcp)` 或 UI 版里的 MCP 能力

原因：

- 基础版最容易把问题收敛到“串口/网络/音频”
- UI 版会额外引入 LCD、图片资源、LVGL
- MCP 版会额外引入上层消息交互复杂度

### 15.2 联调阶段总表

| 阶段 | 硬件侧要确认什么 | 软件侧怎么做 | 通过标准 |
| --- | --- | --- | --- |
| 上电与串口 | USB、Type-C、PWRKEY、J4 线序与电平 | 先打通下载、REPL、日志 | 能稳定下载脚本并看到启动日志 |
| SIM 与网络 | SIM 卡插入、天线连接、信号环境 | 先验证 `sim.getStatus()`、`checkNet.waitNetworkReady()`、`net.csqQueryPoll()`、`dataCall.getInfo()` | SIM ready、网络 ready、能拿到 IP |
| 基础语音链路 | 麦克风、功放、喇叭、电源稳定 | 先运行 `src` 版本 | 能唤醒、能说话、能播报 |
| 云端会话 | 数据链路稳定、无弱信号问题 | 观察 OTA、MQTT、UDP 建链日志 | 能获取 OTA 配置、MQTT 建连、收到 `hello` |
| 带屏 UI | 屏幕型号、J6 接线、背光、供电 | 再运行 `src(UI)`，并同步 UI 图片资源 | 屏幕点亮、表情能切换 |
| MCP | 后端能力与 topic 路径 | 最后运行 `src(mcp)` 或 UI 版 | `tools/list`、音量查询/设置等可用 |

### 15.3 建议的最小联调顺序

#### A. 串口和基础运行环境

- 先通过 `J4` 或 USB 下载固件与脚本
- 确认 `src/_main.py` 能正常启动
- 确认日志链路可用

#### B. SIM/蜂窝网络

- 看 SIM 是否 ready
- 看网络是否 ready
- 看是否能取到 PDP/IP 信息

如果这一步不稳，不要急着看 MQTT/UDP，更不要急着看 UI。

#### C. 音频输出

- 先确认喇叭和功放电源
- 再确认 PA 控制是否真的被拉起
- 最后再看流式播放和会话中的下行音频

#### D. 音频输入、唤醒和 VAD

- 先确认麦克风焊接与通道通畅
- 再看关键词唤醒是否触发
- 再看 VAD 是否在讲话时进入发送态、停说后退出发送态

#### E. 屏幕

- 先确认 `J6` 供电和屏幕型号
- 再看初始化时序是否匹配
- 最后确认 `U:/media` 图片资源是否已经同步

### 15.4 UI 版额外注意

UI 版不是只拷贝 `src(UI)` 代码就够了，还要注意：

- `ui.py` 里图片路径写的是 `U:/media/*.png`
- 这意味着表情图片要进用户分区
- 如果图片没同步，UI 初始化可能成功，但图片显示会异常

## 16. 给硬件和应用团队的协同建议

### 16.1 硬件团队优先补实的点

最值得再补一轮闭环确认的是：

- `BLK` 最终来自哪个控制源
- 仓库中的 `GPIO33`、`GPIO3`、`29` 在这块板子的真实落点
- `J4` 的电平域和保护方式
- 当前 LCD 屏型号是否就是 UI 代码假设的 240x240 SPI 面板

### 16.2 应用团队优先复用的点

应用开发不要一上来就重写底层，把现成分层先用起来更划算：

- `utils.py` 当作板级资源封装层
- `protocol.py` 当作云连接和音频传输层
- `_main.py` 当作应用主流程入口
- `lcd.py` / `ui.py` 当作显示层入口

### 16.3 更适合当前项目的研发协作方式

对当前这块板子，更好的协作方式不是“先争论某个外设到底算不算 GPIO”，而是：

1. 先按固定功能通路把主链路跑通
2. 再把仓库里已经出现的 GPIO 控制点逐个回标到原理图
3. 最后再决定哪些点要封装成正式 `board_config` 或驱动层常量

## 17. 本轮迭代后的文档结论

到这一轮为止，这份文档已经不只是“板级资源整理”，而是可以直接给研发联调用的对照材料：

- 硬件可以看外设、网络名、连接器和待确认控制点
- 底层可以看建议 API、仓库入口和板级绑定
- 应用可以看推荐变体、运行主链路和联调顺序

当前还没有完全闭环的关键点，已经明确收敛到少数几个：

- `BLK`
- `GPIO33`
- `GPIO3`
- `PA gpio 29`
- LCD 面板与当前 UI 参数的一致性

这比单纯做一张 GPIO 表，更适合直接推进实际研发。

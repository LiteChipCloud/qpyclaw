# EC800MCNLE Audio Board Current State

## 日期

`2026-03-29`

## 目标

识别本机新接入的 `EC800MCNLE` 语音开发板当前处于什么状态，避免后续把它误判成
已经部署了 `qpyclaw-node` 的板子。

## 识别结果

串口分组实测可用：

| 角色 | 串口 |
| --- | --- |
| AT | `COM17` |
| REPL | `COM19` |

使用：

```powershell
python C:\Users\kingd\.codex\skills\quecpython-dev\scripts\qpy_device_info_probe.py --at-port COM17 --repl-port COM19 --json --include-raw
```

得到的关键事实：

| 项目 | 当前值 |
| --- | --- |
| 模组 | `EC800M` |
| 固件 | `EC800MCNLER06A03M08_AI_WS_OCPU_QPY_TEST0810` |
| SIM | `NOT INSERTED` |
| 驻网 | `false` |
| IPv4 | 无 |
| IPv6 | 无 |

## `/usr` 当前状态

板上当前 `/usr` 根目录并不是 `qpyclaw-node` 结构，而是现有语音/UI 工程。

实测：

```powershell
python C:\Users\kingd\.codex\skills\quecpython-dev\scripts\qpy_device_fs_cli.py --json --port COM19 --ls-via repl ls --path /usr
```

根目录包含：

```text
audio_gain.nvm
audio_ve.nvm
dev.py
lcd.py
logging.py
main.py
OTA_test.py
protocol.py
threading.py
ui.py
utils.py
uuid.py
media/
system_config.json
```

同时 `/usr/app` 不存在，这一点很关键：

它说明这块板子当前还没有 `qpyclaw-node` 的 `/usr/app/...` 运行时结构。

## `main.py` 头部特征

读取 `/usr/main.py` 前 600 字节后，能看到当前程序栈特征：

1. `from usr.protocol import WebSocketClient`
2. `from usr.utils import ChargeManager, AudioManager, NetManager, TaskManager`
3. `from usr.ui import *`
4. `from machine import ExtInt, Pin`

这说明当前板上跑的是一套音频/UI/按键/网络一体化应用，不是 `qpyclaw-node` 现有的
极简 `/usr/app` runtime。

## 当前结论

截至 `2026-03-29`，这块 `EC800MCNLE` 语音开发板的状态很明确：

1. 硬件已经接好，模组和 REPL/AT 都可访问
2. 当前固件是 AI/WS 方向测试固件
3. 当前没有插 SIM
4. 当前 `/usr` 上已有一套语音/UI 应用
5. 当前它不是 `qpyclaw-node` 板，不能直接拿 `COM11` 那套恢复/自检结论套过来

如果下一步要把它纳入 `qpyclaw` 开发，合理顺序应该是：

1. 决定是否保留当前语音/UI工程作为参考
2. 决定是并存目录，还是清板切到 `qpyclaw-node`
3. 再基于 `EC800MCNLE` 做音频板分层 bring-up

## 证据

[2026-03-29-ec800mcnle-audio-board-current-state.json](C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\docs\bringup\evidence\2026-03-29-ec800mcnle-audio-board-current-state.json)

# EC800MCNLE Audio Board

板级目录：

`boards/ec800mcnle-audio-board/`

这个目录只承载 `EC800MCNLE` 语音开发板相关的资料和板级代码，不承载通用
`qpyclaw-node` runtime。

## 目录职责

1. `code/`
   只放这块板子的专有代码，例如音频、屏幕、电源、UI、板级启动封装。
2. `README.md`
   记录这块板子的能力边界、目录约束、bring-up 约定。

## 和 qpyclaw-node 的关系

1. 通用单文件 runtime 在：
   `embed/qpyclaw-node/runtime/usr_mirror/qpyclaw_node.py`
2. 这块板子的组合示例在：
   `embed/qpyclaw-node/examples/ec800mcnle-audio-board/`
3. 板级代码同步到设备后，目标目录是：
   `/usr/board/`

## 当前已落地的板级能力

当前 `code/` 已经实现并接入 `qpyclaw-node` 扩展机制的能力包括：

1. 音频状态查询
2. 音量读取和设置
3. 本地音频流打开和关闭
4. 本地音频播放和停止
5. KWS 启停
6. VAD 启停
7. 充电控制引脚启停
8. 显示状态查询
9. UI 表情状态查询和切换
10. 运行态在线/离线状态联动屏幕表情

## 约束

1. 板级代码继续放在 `boards/ec800mcnle-audio-board/code/`，不要回灌到通用 runtime。
2. example 只负责说明“如何把通用 runtime 和板级代码拼起来”，不重复放驱动。
3. 当前仍以开发调试为主，默认不切到 `main.py` 上电自启动。

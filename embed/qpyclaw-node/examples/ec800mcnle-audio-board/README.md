# EC800MCNLE Audio Board Example

这个目录只放“如何组合使用”示例，不放板级驱动源码。

板级专有代码在：

`boards/ec800mcnle-audio-board/code/`

## 这个 example 解决什么问题

它负责把下面两部分拼起来：

1. 通用单文件 runtime：`/usr/qpyclaw_node.py`
2. EC800MCNLE 音频板专有代码：`/usr/board/*`

## 当前示例文件

1. `config_local.example.py`
   设备本地配置模板，目标是 `/usr/config_local.py`
2. `main.example.py`
   最直接的板级组合入口，单线程驱动 `runtime.step()`
3. `dispatch.example.py`
   供其他模块嵌入调用的轻量入口，会在子线程里拉起板级主循环

## 推荐设备目录

```text
/usr/
|-- qpyclaw_node.py
|-- _main.py
|-- config_local.py
|-- qpyclaw_board_main.py
|-- qpyclaw_board_dispatch.py
`-- board/
    |-- board_audio.py
    |-- board_display.py
    |-- board_power.py
    |-- board_ui.py
    `-- board_bootstrap.py
```

说明：

1. `config_local.py` 现在是唯一的正式配置入口。
2. 开发阶段可以保留 `_main.py`，暂时不切到 `main.py` 上电自启动。
3. `qpyclaw_board_main.py` 和 `qpyclaw_board_dispatch.py` 是板级组合入口，不属于通用 runtime。

## `main.example.py` 的职责

`main.example.py` 做三件事：

1. 把 `/usr` 和 `/usr/board` 加入导入路径
2. 创建 `EC800MCNLE` 板级扩展对象
3. 把扩展挂到 `qpyclaw_node.create_runtime()` 上，然后持续执行 `runtime.step()`

当前默认参数：

1. `enable_display=True`
2. `enable_charge=True`
3. `open_audio=False`

`open_audio` 现在默认关闭，是为了优先保证“联网 runtime + 屏幕/UI + 板级工具”这条链路稳定。
完整语音链路可以在后续单独打开和调优。

## 已接入的板级工具

当前扩展已经接入：

1. `qpy.board.status`
2. `qpy.audio.status`
3. `qpy.audio.volume.get`
4. `qpy.audio.volume.set`
5. `qpy.audio.play`
6. `qpy.audio.stop`
7. `qpy.audio.stream.open`
8. `qpy.audio.stream.close`
9. `qpy.audio.kws.start`
10. `qpy.audio.kws.stop`
11. `qpy.audio.vad.start`
12. `qpy.audio.vad.stop`
13. `qpy.power.status`
14. `qpy.power.charge.enable`
15. `qpy.power.charge.disable`
16. `qpy.display.status`
17. `qpy.ui.status`
18. `qpy.ui.emotion.show`

## Host 侧同步入口

板级代码同步入口：

1. `tools/host/qpy_board_code_sync.py --profile ec800mcnle-audio-board`
2. `tools/host/qpy_post_flash_recover.py --profile ec800mcnle-audio-board`

说明：

1. `qpy_post_flash_recover.py` 在识别到 `ec800mcnle-audio-board` manifest 后，会自动同步 `/usr/board`
2. 如果你只想恢复通用 runtime，不想同步板级代码，可以显式加 `--skip-board-sync`

对应 manifest：

`embed/qpyclaw-node/deploy/board-manifests/ec800mcnle-audio-board.json`

## UI 资源说明

当前 `board_ui.py` 默认从：

```text
U:/media/
```

读取表情图片。

如果要跑屏幕表情 UI，建议把参考素材从：

`embed/opensource/AIChatbot-Xiaozhi-Mqtt/src(UI)/media`

同步到设备的 `U:/media/`，或者在你自己的入口里改掉 `media_prefix`。

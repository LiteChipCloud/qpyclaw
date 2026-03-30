# 2026-03-29 EC800MCNLE 音频板上线会话补记

## 本轮意图

本轮不是继续空谈方案，而是把已经接好卡的 `EC800MCNLE` 音频板真正推到云端 `OpenClaw` 路径上，并确认：

1. 板级扩展已经和 `qpyclaw-node` 单文件 runtime 组合成功
2. 新板子的官方身份已经完成配对
3. 当前设备运行时确实在线
4. 板级命令面已经能直接执行

## 本轮关键决策

1. 不再继续依赖旧 REPL 环境里的热加载结果判断在线状态
2. 通过新入口 `/usr/qpyclaw_board_main.py` 拉起全新运行进程
3. 不切换到 `main.py` 自启动，仍保持开发态
4. 不把板级代码塞回通用 runtime 目录，继续保持：
   `qpyclaw_node.py` 单文件 runtime
   `boards/ec800mcnle-audio-board/code/` 板级代码
   `examples/ec800mcnle-audio-board/` 组合入口

## 本轮确认的事实

1. `COM19` 是当前活动 REPL 口
2. 板子已经 `SIM ready`
3. 板级目录 `/usr/board` 已在设备上
4. 设备侧 `debug_snapshot()` 已确认 `online = true`
5. 云端 `pending.json = {}`
6. 云端 `paired.json` 已包含
   `d88d71750471be40bc686de26ba3b4f77f3eb35f902c5e881ec009103b9916db`
7. `qpy.tools.catalog` 现在能返回 `20` 个工具
8. 板级工具 `qpy.board.status` / `qpy.audio.status` / `qpy.audio.volume.get` / `qpy.audio.volume.set` 已在本地执行通过

## 当前未闭环项

当前还没有闭环的，已经收敛为“官方 CLI 包装层”，不是设备或网关本体：

1. `nodes status`
2. `nodes invoke`

服务器本地 CLI 目前返回 `1006 abnormal closure`。但随后已经额外证明：

1. 服务器本机 raw websocket upgrade 正常
2. `connect.challenge` 正常
3. `connect` 正常
4. `node.list` 正常
5. `node.invoke` 也正常，只是当前 schema 需要 `idempotencyKey`

所以这条线的结论已经升级为：

1. 官方网关远程调用 `EC800MCNLE` 音频板是通的
2. 回归点是 CLI 层，不是节点层

## 本轮新增落地物

本轮还新增了一个可实际使用的 host 运维脚本：

`tools/host/qpy_openclaw_server_ops.py`

用途：

1. 在本机通过 SSH 发起
2. 在云服务器本机执行 raw operator RPC
3. 稳定完成 `node-list` / `node-invoke`

## 对应正式记录

本轮正式 bring-up 结果已写入：

`docs/bringup/2026-03-29-ec800mcnle-audio-cloud-online.md`

后续如果继续推进：

1. 先修 operator 调用链
2. 再做网关侧真实远程调用演示
3. 然后继续扩板级外设与示例

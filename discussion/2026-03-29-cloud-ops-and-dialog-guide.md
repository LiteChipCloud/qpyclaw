# 2026-03-29 云端运维与对话入口收敛记录

## 1. 背景

在 `2026-03-28` 已经完成了以下关键闭环：

1. `qpyclaw-node` 通过 Official OpenClaw Gateway 成功在线
2. 云端节点状态显示 `connected = true`
3. 云端已成功调用 `qpy.runtime.status`
4. 云端已成功调用 `qpy.device.status`

因此，项目状态从“证明能接上”进入到了“如何稳定运维和如何标准问设备”的阶段。

## 2. 用户新要求

用户明确选择同时推进两件事：

1. 整理“在 gateway 里怎么问 qpy 设备”的标准操作方式
2. 继续完善云端 `qpy设备运维` agent 的意义、常用问法和命令路由

## 3. 当前形成的判断

### 3.1 关于对话入口

最佳入口不是让用户直接记所有 `qpy.*` 命令，而是：

```mermaid
flowchart LR
  U["用户自然语言"] --> M["main"]
  M --> O["qpy设备运维"]
  O --> N["nodes.invoke / nodes.status"]
  N --> Q["qpyclaw-node"]
```

也就是说：

1. 用户仍然以自然语言说话
2. `main` 可以把设备类任务路由给 `qpy设备运维`
3. `qpy设备运维` 再把自然语言翻译成 `nodes` 调用

### 3.2 关于 `qpy设备运维` 的本质

它不是设备里的 agent。

它是：

`运行在云端 OpenClaw 内部、面向 qpyclaw-node 的专用设备运维 agent`

### 3.3 关于默认目标节点

当前已经明确：

| 项目 | 值 |
| --- | --- |
| 默认节点名 | `qpyclaw QuecPython Node` |
| 默认 node id | `09c41c83ee53ba08930ac6ca8d4815640382a77a13e08edfcc17646e66b8fc54` |

所以当前阶段可以把下面这些词默认映射到这台节点：

1. 设备
2. 板子
3. qpyclaw-node
4. 模组

## 4. 当前应支持的典型问法

### 4.1 状态巡检

1. `让 qpy设备运维 检查设备是否在线。`
2. `让 qpy设备运维 给我设备完整健康报告。`
3. `让 qpy设备运维 检查最近错误和 reconnect 情况。`

### 4.2 网络排查

1. `让 qpy设备运维 检查 SIM、驻网、信号和 PDP。`
2. `让 qpy设备运维 查询当前 IPv4、IPv6、DNS。`
3. `让 qpy设备运维 判断当前是模组没驻网、PDP 没起来，还是节点运行时问题。`

### 4.3 文件与配置

1. `让 qpy设备运维 读取 /usr/app/config_local.py。`
2. `让 qpy设备运维 列出 /usr/app/tools。`
3. `让 qpy设备运维 把 signer 配置写回 config_local.py。`

### 4.4 控制动作

1. `让 qpy设备运维 重启设备，并确认是否重新上线。`
2. `让 qpy设备运维 执行一段临时 Python，检查当前配置值。`

## 5. 当前产出

本轮新增两份正式文档：

1. `docs/bringup/2026-03-29-official-gateway-dialog-playbook.md`
2. `docs/architecture/06-qpy-device-ops-agent-and-routing.md`

它们分别承担：

| 文档 | 作用 |
| --- | --- |
| 对话与操作手册 | 告诉用户在网关里怎么问、怎么操作 |
| agent 定义与路由 | 把 `qpy设备运维` 的职责、路由和默认动作写清楚 |

## 6. 对云端 agent 的收敛方向

云端 `qpy设备运维` 需要具备以下最小规则：

1. 默认目标节点就是当前 `qpyclaw QuecPython Node`
2. 设备类问题优先走 `nodes`
3. 先读后写
4. 写完必须复核
5. 重启后必须回查在线状态
6. 回答要像运维，不要像闲聊

## 7. 当前意义

这一步非常关键，因为它把 `qpyclaw-node` 从“一个接入成功的 node”继续推进成了：

`一个已经开始具备真实远程运维入口的 OpenClaw 设备节点`

这会直接提升：

1. 可演示性
2. 可运维性
3. 可产品化程度
4. 对 OpenClaw 生态用户的可感知价值

## 8. 本轮额外落地结果

除了本地文档，本轮还直接更新了云端 `qpy设备运维` agent 的工作规则：

1. 默认目标节点
2. 默认 `nodes` 路由
3. 单目标运维问法模板
4. 文件操作与重启后的复核规则

并完成了真实 smoke：

1. agent 已能调用设备侧状态命令
2. agent 已能返回中文运维式结论
3. 当前更适合单目标运维问法
4. 多目标复合问法仍需后续继续强化

## 9. 标准回归补充

`2026-03-29` 又额外完成了一轮云端标准回归，覆盖：

1. `qpy.repl.run`
2. `qpy.fs.mkdir`
3. `qpy.fs.tree`
4. `qpy.fs.remove`
5. `qpy.device.reboot`

当前回归结论收敛为：

| 项目 | 结论 |
| --- | --- |
| `qpy.repl.run` | 通过 |
| `qpy.fs.mkdir/tree/remove` | 通过 |
| `qpy.device.reboot` 调用应答 | 通过 |
| `qpy.device.reboot` 自动恢复闭环 | 尚未闭环 |

这意味着当前最真实的状态不是“重启完全不可用”，而是：

1. 重启请求已经能下发到设备
2. 但当前开发板 bring-up 方式下，重启后还没有形成稳定的“自动回到在线节点”路径
3. 手工重新拉起 `/usr/_main.py` 后，节点会重新在线

## 10. 本轮新增文档

1. `docs/bringup/2026-03-29-cloud-node-standard-regression.md`
2. `docs/bringup/2026-03-29-qpy-device-ops-prompt-list.md`

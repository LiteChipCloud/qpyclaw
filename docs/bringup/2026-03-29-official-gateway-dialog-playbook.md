# Official OpenClaw Gateway 对话与操作手册

## 1. 目的

这份文档回答两个实际问题：

1. 现在在网关里到底该怎么问，才能和 `qpyclaw-node` 互动。
2. 哪些问法已经被当前链路真实验证过，哪些还只是已开放能力。

## 2. 当前可用链路

```mermaid
flowchart LR
  U["用户"] --> M["OpenClaw main"]
  M --> O["qpy设备运维"]
  O --> N["nodes.invoke"]
  N --> Q["qpyclaw-node"]
  Q --> D["EC800KCNLC 设备"]
```

当前已经验证成立的事实：

| 项目 | 当前状态 |
| --- | --- |
| 官方云网关 | 已连通 |
| `qpyclaw-node` | 已配对、已在线 |
| 远程节点调用 | 已成功 |
| 默认管理节点 | `qpyclaw QuecPython Node` |
| 默认 node id | `09c41c83ee53ba08930ac6ca8d4815640382a77a13e08edfcc17646e66b8fc54` |
| 当前接入模式 | `qpyclaw-node -> Official OpenClaw Gateway` |

## 3. 推荐对话入口

### 3.1 入口 A：在 `main` 里调用 `qpy设备运维`

这是当前最推荐的方式。

适合问法：

1. `让 qpy设备运维 检查 qpyclaw-node 当前是否在线。`
2. `让 qpy设备运维 查询设备完整状态，重点看网络、SIM、信号和 IP。`
3. `让 qpy设备运维 列出这台设备当前支持的 qpy 工具。`

### 3.2 入口 B：直接和 `qpy设备运维` 对话

如果前端支持直接切换 agent，可以直接问它。

适合问法：

1. `检查设备当前状态。`
2. `读取 /usr/app/config_local.py。`
3. `把设备重启一下，然后告诉我重连结果。`

## 4. 标准问法模板

### 4.1 在线与运行态

| 目的 | 推荐问法 | 典型底层命令 |
| --- | --- | --- |
| 看是否在线 | `让 qpy设备运维 检查设备是否在线，并汇报最近错误。` | `qpy.runtime.status` |
| 看运行态 | `让 qpy设备运维 查询运行时状态，重点看 online、connect_successes、last_error。` | `qpy.runtime.status` |
| 看签名链路 | `让 qpy设备运维 检查当前设备接入模式和 signer 信息。` | `qpy.runtime.status` |

### 4.2 设备全状态

| 目的 | 推荐问法 | 典型底层命令 |
| --- | --- | --- |
| 看整体健康 | `让 qpy设备运维 给我设备完整健康报告。` | `qpy.device.status` |
| 看模组信息 | `让 qpy设备运维 查询模组型号、固件版本、IMEI、序列号。` | `qpy.device.info` |
| 看 SIM 信息 | `让 qpy设备运维 查询 SIM 是否插入、是否 ready、ICCID、IMSI。` | `qpy.sim.info` |
| 看小区与信号 | `让 qpy设备运维 查询当前小区、信号、运营商。` | `qpy.cell.info` |
| 看网络诊断 | `让 qpy设备运维 做一次网络诊断，重点看驻网和 PDP。` | `qpy.net.diag` |
| 看 IP | `让 qpy设备运维 查询当前 IP、PDP、DNS。` | `qpy.net.ifconfig` 或 `qpy.device.status` |

### 4.3 工具与能力目录

| 目的 | 推荐问法 | 典型底层命令 |
| --- | --- | --- |
| 列支持工具 | `让 qpy设备运维 列出当前设备支持的全部 qpy 工具。` | `qpy.tools.catalog` |
| 看节点能力 | `让 qpy设备运维 说明这台设备现在暴露了哪些能力和命令。` | `nodes describe` + `qpy.tools.catalog` |

### 4.4 文件系统

| 目的 | 推荐问法 | 典型底层命令 |
| --- | --- | --- |
| 列目录 | `让 qpy设备运维 列出 /usr/app 目录。` | `qpy.fs.list` |
| 看树形目录 | `让 qpy设备运维 树形查看 /usr/app/tools。` | `qpy.fs.tree` |
| 读文件 | `让 qpy设备运维 读取 /usr/app/config_local.py。` | `qpy.fs.read` |
| 写文件 | `让 qpy设备运维 把 /usr/app/config_local.py 里的 signer 配置写进去。` | `qpy.fs.write` |
| 建目录 | `让 qpy设备运维 在 /usr 下创建 tmp 目录。` | `qpy.fs.mkdir` |
| 删除文件 | `让 qpy设备运维 删除 /usr/app/tmp.txt。` | `qpy.fs.remove` |

### 4.5 REPL 与重启

| 目的 | 推荐问法 | 典型底层命令 |
| --- | --- | --- |
| 临时代码执行 | `让 qpy设备运维 在设备上执行一段 Python，检查当前配置。` | `qpy.repl.run` |
| 模组重启 | `让 qpy设备运维 重启设备，并确认是否重新上线。` | `qpy.device.reboot` |

## 5. 当前已验证与已开放能力

### 5.1 已真实验证的闭环

| 能力 | 状态 |
| --- | --- |
| `qpy.runtime.status` | 已验证 |
| `qpy.device.status` | 已验证 |
| `qpy.tools.catalog` | 已验证 |
| `qpy.net.ifconfig` | 已验证 |
| `qpy.fs.list` | 已验证 |
| `qpy.fs.read` | 已验证 |
| `qpy.fs.write` | 已验证 |
| `qpy.fs.remove` | 已验证 |

### 5.2 已开放到网关，但建议继续分批回归

| 能力 | 当前结论 |
| --- | --- |
| `qpy.device.info` | 已开放，建议继续做云端回归 |
| `qpy.sim.info` | 已开放，建议继续做云端回归 |
| `qpy.cell.info` | 已开放，建议继续做云端回归 |
| `qpy.net.diag` | 已开放，建议继续做云端回归 |
| `qpy.device.reboot` | 已开放，建议做一次标准回归 |
| `qpy.repl.run` | 已开放，建议在网关侧做一次标准回归 |
| `qpy.fs.mkdir` | 已开放，建议做一次标准回归 |
| `qpy.fs.tree` | 已开放，建议做一次标准回归 |

## 6. 推荐问题集合

### 6.1 每日巡检

1. `让 qpy设备运维 检查设备是否在线。`
2. `让 qpy设备运维 给我设备完整健康报告。`
3. `让 qpy设备运维 汇报 SIM、驻网、信号、IP。`

### 6.2 故障排查

1. `让 qpy设备运维 检查最近错误、最近断线原因和 reconnect 情况。`
2. `让 qpy设备运维 执行网络诊断，判断是驻网问题、PDP 问题还是节点运行时问题。`
3. `让 qpy设备运维 读取 /usr/app/config_local.py，确认 ws、token、signer 配置。`

### 6.3 远程改配置

1. `让 qpy设备运维 先读取 /usr/app/config_local.py，再把 remote_signer_http 配置补齐。`
2. `让 qpy设备运维 修改完成后重启设备，并再次确认设备上线。`

### 6.4 能力盘点

1. `让 qpy设备运维 列出当前所有 qpy 工具。`
2. `让 qpy设备运维 说明哪些工具已经云端验证过，哪些还需要回归。`

## 7. 推荐输出格式

为了让对话更像设备运维，而不是闲聊，建议 `qpy设备运维` 的回答遵循这个结构：

```text
结论
关键指标
已执行命令
异常/风险
下一步建议
```

## 8. 当前实用建议

基于本轮对云端 `qpy设备运维` 的真实 smoke：

1. 单目标问题已经比较适合直接问
2. 复合问题可以问，但当前还不建议一次塞太多目标
3. 最稳妥的问法是“一次只问一个运维意图”

推荐这样问：

1. `让 qpy设备运维 检查设备是否在线，并汇报最近错误。`
2. `让 qpy设备运维 查询当前 IP、PDP 和 DNS。`
3. `让 qpy设备运维 检查 signer 和接入模式。`

不推荐当前阶段这样一次性混问太多：

1. `让 qpy设备运维 同时检查在线、最近错误、signer、IP、SIM、信号、小区和配置。`

## 9. 终端侧等价命令

如果你在云服务器终端而不是聊天窗口里操作，可以直接用：

```bash
openclaw nodes status --json
openclaw nodes invoke --node "qpyclaw QuecPython Node" --command qpy.runtime.status --json
openclaw nodes invoke --node "qpyclaw QuecPython Node" --command qpy.device.status --json
openclaw nodes invoke --node "qpyclaw QuecPython Node" --command qpy.tools.catalog --json
openclaw nodes invoke --node "qpyclaw QuecPython Node" --command qpy.fs.read --params '{"path":"/usr/app/config_local.py"}' --json
```

## 10. 当前结论

`qpyclaw-node` 已经不再是“只能证明能连上”的状态，而是已经进入“可以在 Official OpenClaw Gateway 中被真实运维”的状态。

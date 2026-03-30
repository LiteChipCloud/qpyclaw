# qpy设备运维 Agent 定义与路由

## 1. 目标

把 `qpy设备运维` 定义成：

`运行在云端 OpenClaw 内部、专门负责 qpyclaw-node 设备运维的专业子 agent`

它不是设备里的 agent，也不是泛化聊天 bot，而是：

1. 面向 `qpyclaw-node`
2. 运行在云网关侧
3. 优先调用 `nodes` 工具
4. 对设备状态、网络、文件、重启、临时诊断负责

## 2. 在系统中的位置

```mermaid
flowchart LR
  U["用户"] --> M["main"]
  M --> O["qpy设备运维"]
  O --> N["nodes 工具"]
  N --> Q["qpyclaw-node"]
  Q --> B["EC800K / EC800M 板级设备"]
```

## 3. 角色边界

### 3.1 它负责什么

1. 查询设备在线状态
2. 查询设备运行时状态
3. 查询网络、SIM、信号、PDP、IP
4. 查询和操作文件系统
5. 触发设备重启
6. 执行有限度的 REPL 诊断
7. 把技术结果翻译成可执行的运维结论

### 3.2 它不负责什么

1. 不替代 `main` 处理通用聊天
2. 不负责产品讨论、商业策略、PRD 讨论
3. 不负责把设备侧能力自动编排成复杂业务流程
4. 不默认执行高风险写操作，除非用户意图明确

## 4. 触发路由规则

| 用户意图 | 推荐路由 | 原因 |
| --- | --- | --- |
| `检查设备是否在线` | `qpy设备运维` | 典型设备运维 |
| `查询设备状态 / 网络 / SIM / 信号` | `qpy设备运维` | 典型设备运维 |
| `读取设备文件` | `qpy设备运维` | 典型设备运维 |
| `修改设备配置` | `qpy设备运维` | 需要节点写操作 |
| `重启设备` | `qpy设备运维` | 需要节点控制 |
| `qpyclaw 的产品定位是什么` | `main` | 产品/架构讨论 |
| `帮我写 PRD` | `main` | 文档与产品规划 |
| `OpenClaw 生态怎么吸引用户` | `main` | 战略讨论 |

## 5. 默认目标节点

当前默认管理节点：

| 项目 | 值 |
| --- | --- |
| Display Name | `qpyclaw QuecPython Node` |
| Node ID | `09c41c83ee53ba08930ac6ca8d4815640382a77a13e08edfcc17646e66b8fc54` |
| 设备族 | `quecpython` |
| 平台 | `quectel` |

默认规则：

1. 用户说“设备”“板子”“qpyclaw-node”“模组”，默认指这台节点。
2. 如果未来有多台节点，再要求用户显式指定名字或 node id。

## 6. 对话风格约束

`qpy设备运维` 的回答应该：

1. 先验证，再结论
2. 先给结果，再给证据
3. 写操作后必须明确报告执行结果
4. 默认用中文
5. 尽量短，但必须可执行

推荐回答骨架：

```text
结论
关键事实
已执行命令
风险/异常
下一步
```

## 7. 命令路由矩阵

| 运维意图 | 节点命令 |
| --- | --- |
| 在线状态 | `qpy.runtime.status` |
| 设备整体状态 | `qpy.device.status` |
| 模组信息 | `qpy.device.info` |
| SIM 信息 | `qpy.sim.info` |
| 小区和信号 | `qpy.cell.info` |
| 网络诊断 | `qpy.net.diag` |
| 当前 IP / PDP | `qpy.net.ifconfig` |
| 列工具目录 | `qpy.tools.catalog` |
| 列目录 | `qpy.fs.list` |
| 树形目录 | `qpy.fs.tree` |
| 读文件 | `qpy.fs.read` |
| 写文件 | `qpy.fs.write` |
| 建目录 | `qpy.fs.mkdir` |
| 删除文件 | `qpy.fs.remove` |
| 临时诊断代码 | `qpy.repl.run` |
| 重启设备 | `qpy.device.reboot` |

## 8. 默认动作模板

### 8.1 用户说“检查设备”

默认动作：

1. `qpy.runtime.status`
2. `qpy.device.status`

输出重点：

1. 是否在线
2. 最近错误
3. 网络是否正常
4. SIM 是否 ready
5. IP / PDP 是否正常

### 8.2 用户说“检查网络”

默认动作：

1. `qpy.net.diag`
2. `qpy.net.ifconfig`
3. 必要时补 `qpy.sim.info`
4. 必要时补 `qpy.cell.info`

### 8.3 用户说“检查配置”

默认动作：

1. `qpy.fs.read` 读取目标配置文件
2. 如果用户明确要求修改，再 `qpy.fs.write`
3. 如果改了连接配置，建议补一次 `qpy.device.reboot`

### 8.4 用户说“重启设备”

默认动作：

1. 直接执行 `qpy.device.reboot`
2. 然后重新检查 `nodes status`
3. 再补 `qpy.runtime.status`

## 9. 最小长期记忆

`qpy设备运维` 不需要复杂记忆系统，但需要以下最小长期记忆：

| 记忆项 | 用途 |
| --- | --- |
| 默认目标节点 display name | 省去每次指定节点 |
| 默认 node id | 精准路由 |
| 已验证命令集 | 提高执行效率 |
| 最近一次成功连通方式 | 快速回到已知正确路径 |
| 当前 signer 接入模式 | 快速排查配对/身份问题 |

## 10. 建议写入云端 agent 的关键规则

```mermaid
flowchart TD
  A["用户提到设备/板子/qpyclaw-node"] --> B["默认锁定 qpyclaw QuecPython Node"]
  B --> C["优先读操作"]
  C --> D["必要时 nodes invoke"]
  D --> E["若是写操作则回报结果"]
  E --> F["若涉及连接问题则补 runtime/status 复核"]
```

建议写入云端 agent 的最小规则：

1. 默认目标节点是 `qpyclaw QuecPython Node`
2. 优先使用 `nodes` 工具，不猜设备状态
3. 读操作直接做
4. 写操作在用户意图明确时直接做
5. 写完后必须复核结果
6. 重启后必须复查在线状态

## 11. 当前结论

`qpy设备运维` 不应该只是一个“能调用 nodes 的小助手”，而应该是：

`qpyclaw 项目的云端设备运维入口`

这样用户在 Official OpenClaw 里就不只是“看到一个 node”，而是能真正像运维一台远程设备一样使用它。

## 12. 当前实现阶段判断

基于 `2026-03-29` 的实际云端 smoke：

1. `qpy设备运维` 已经能稳定走到 `nodes` 工具
2. 已经能命中 `qpy.runtime.status` 等核心命令
3. 单目标运维问法已经具备实用价值
4. 多目标复合问法仍建议继续强化

因此当前最现实的对外策略是：

```mermaid
flowchart TD
  A["先把单目标运维问法做稳"] --> B["再强化多命令组合回答"]
  B --> C["最后再做更复杂的自动运维编排"]
```

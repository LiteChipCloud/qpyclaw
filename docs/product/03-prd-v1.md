# qpyclaw PRD v1

## 1. 文档目标

定义 `qpyclaw` 第一阶段产品需求。

当前 PRD 范围只覆盖：

1. `qpyclaw-node`
2. `qpyclaw-agent`
3. `EC800MCNLE` 首板验证

不覆盖：

1. `qpyclaw-fleet` 完整实现
2. 多租户后台
3. 商业版控制台

## 2. 产品目标

### 2.1 一级目标

1. 让 QuecPython 设备可以零改接入 OpenClaw Gateway
2. 让设备成为可调用的 OpenClaw node
3. 让设备具备语音、屏幕、设备状态、网络诊断等可展示能力
4. 让 `qpyclaw-agent` 成为 QuecPython 版 OpenClaw Gateway Core 的最小可运行骨架

### 2.2 二级目标

1. 提供第一版 `qpyclaw-agent` Gateway Core 运行时边界
2. 提供可解释、可审计、可扩展的工具面
3. 提供商业化演进的边界文档

## 3. 用户画像

| 用户 | 需求 | 为什么会用 |
| --- | --- | --- |
| OpenClaw 进阶用户 | 想接真实硬件、语音、屏幕 | 不想改 Gateway，但想获得设备能力 |
| Maker / IoT 开发者 | 想做 QuecPython 边缘智能节点 | 希望复用 OpenClaw 生态 |
| 集成商 | 想要可交付的硬件 agent 节点 | 需要更接近生产的设备 runtime |

## 4. 首版场景

### 场景 A：零改接入

用户把 EC800MCNLE 设备接入自己的 OpenClaw Gateway，在 Gateway 中看到在线 node，并可调用 `qpy.*` 命令。

### 场景 B：语音终端

用户把设备作为人机语音终端，用户说话，文本进入 OpenClaw，对端结果返回后由设备播报或显示。

### 场景 C：状态终端

用户把设备作为远程状态终端，可查看网络、SIM、设备运行时状态。

### 场景 D：Gateway-Lite

用户在更高资源 QuecPython 模组，或在单板简化模式下启用 `qpyclaw-agent`，让 `qpyclaw-node` 连接到它，完成本地事件、工具、记忆、规则和节点路由。

## 5. 功能范围

## 5.1 `qpyclaw-node` v1 Must Have

1. OpenClaw Gateway WebSocket 接入
2. challenge / connect / heartbeat / reconnect
3. pairing 兼容
4. `node.invoke.request / result`
5. 设备身份与权限声明
6. 只读工具集：
   - `qpy.device.info`
   - `qpy.device.status`
   - `qpy.net.diag`
   - `qpy.sim.info`
   - `qpy.cell.info`
   - `qpy.runtime.status`
   - `qpy.tools.catalog`

## 5.2 `qpyclaw-node` v1 Should Have

1. 语音输入上行接口
2. 语音输出播放接口
3. 屏幕状态展示接口
4. `agent.request` 主动上报
5. 基础安全白名单

## 5.3 `qpyclaw-agent` v1 Must Have

1. 下游 node 会话管理
2. 本地事件总线与路由
3. 工具注册与调度
4. 轻量会话状态与记忆系统
5. 本地规则 / 策略核心
6. 与 `qpyclaw-node` 共享协议与工具模型

## 5.4 `qpyclaw-agent` v1 Should Have

1. `gateway-lite mode`
2. `bridge mode` 到官方 OpenClaw Gateway
3. 设备级 prompt / profile
4. 离线 fallback

## 6. 非目标

1. 不做桌面 OpenClaw Gateway 的全量等价移植
2. 不做多租户控制台、后台管理面
3. 不做通用 shell / code agent
4. 不做“任意脚本远程执行”型 node
5. 不在 v1 引入高风险写操作工具

## 7. 首版成功标准

```mermaid
flowchart LR
  A["设备上电"] --> B["qpyclaw-node 或 qpyclaw-agent 完成 connect"]
  B --> C["上游看到在线 node 或下游 node"]
  C --> D["调用 qpy.device.status 成功"]
  D --> E["Gateway Core 能完成一条事件闭环"]
  E --> F["设备能作为语音 / 屏幕终端演示"]
```

满足以下 6 条即认为 v1 通过：

1. `qpyclaw-node` 可稳定连接官方 Gateway 或 `qpyclaw-agent`
2. 可稳定处理断线重连
3. 可稳定返回首批 `qpy.*` 命令
4. `qpyclaw-agent` 可完成至少一条“事件 -> 工具 -> 记忆 -> 回执”的闭环
5. 可完成一条“人说话 -> OpenClaw / qpyclaw-agent -> 设备播报 / 显示”的演示链路
6. 文档完整，可复现

## 8. 商业化前置信号

如果以下信号成立，说明项目已经具备商业化起点：

1. OpenClaw 生态用户愿意接设备
2. 有人愿意购买预配置板或适配服务
3. 有现场运维、语音面板、告警节点场景需求
4. 客户开始追问 OTA、日志、审计、配置管理

## 9. 首板验收重点

针对 `EC800MCNLE`，v1 验收重点不是“全功能”，而是：

1. 网关接入是否稳定
2. 音频链路是否稳定
3. 屏幕展示是否可用
4. `qpyclaw-agent` 的 Gateway Core 骨架是否能保持稳定会话
5. 板级资源是否能抽象为可复用 device profile

# qpyclaw-node Voice Dialog API Contract

## 1. 文档目标

这份文档继续承接：

1. [08-qpyclaw-node-voice-dialog-v1.md](08-qpyclaw-node-voice-dialog-v1.md)
2. [09-qpyclaw-node-voice-dialog-implementation-plan.md](09-qpyclaw-node-voice-dialog-implementation-plan.md)

它不再讨论“要不要做”，而是把 `V1` 编码前必须钉死的接口契约写清楚：

1. `qpyclaw-node` 作为 `operator` 连接 `OpenClaw Gateway` 时，到底依赖哪些官方接口
2. 哪些字段是官方文档已确认的事实，哪些字段只是 `qpyclaw` 设备侧自己的实现约定
3. `chat.send`、`chat.history`、`chat.subscribe` 在 `V1` 里怎么组合使用
4. `qpyclaw_node.py` 与板级扩展、ASR、TTS 之间使用什么最小数据结构

## 2. 证据边界

本文分两层：

### 2.1 官方事实层

下面这些点来自 OpenClaw 官方公开文档，已在 `2026-03-31` 核对：

1. [Gateway Protocol](https://docs.openclaw.ai/gateway/protocol)
2. [Talk Mode](https://docs.openclaw.ai/talk)
3. [Control UI](https://docs.openclaw.ai/web/control-ui)
4. [WebChat](https://docs.openclaw.ai/web/webchat)
5. [Session Tools](https://docs.openclaw.ai/session-tool)
6. [TypeBox / Protocol Source of Truth](https://docs.openclaw.ai/typebox)
7. [Android App](https://docs.openclaw.ai/platforms/android)

### 2.2 qpyclaw 约定层

下面这些内容不是 OpenClaw 文档逐字定义，而是 `qpyclaw-node V1` 为了稳妥落地所作的工程约定：

1. `operator` 会话的最小字段集
2. 回复收敛策略优先级
3. 设备侧 `voice turn` 数据结构
4. 板级 hook、ASR、TTS 的最小接口

凡是属于这一层，文中都会明确写为“`qpyclaw 约定`”或“工程推导”。

## 3. 官方协议面中，V1 真正依赖的最小集合

`V1` 并不需要吃下整个 Gateway API，只依赖下面这组最小能力：

| 能力 | 用途 | 官方状态 |
| --- | --- | --- |
| `connect` | 建立 `node` / `operator` 两类连接 | 已公开 |
| `role + scopes` | 区分能力宿主和控制面客户端 | 已公开 |
| `chat.send` | 把 transcript 送到 `main session` | 已公开 |
| `chat.history` | 拉取最终回复、做回补 | 已公开 |
| `chat.subscribe` | 订阅聊天更新，作为低延迟提示 | 已公开 |
| `chat.abort` | 语音中断或超时清理 | 已公开 |
| `event:"chat"` | 回复过程的推送事件 | 已公开 |

`V1` 不依赖：

1. 媒体流协议
2. 原始 `PCM / Opus` over Gateway
3. 服务端 VAD / TTS / ASR
4. Gateway 代设备管理本地声学状态

## 4. 官方已确认的协议事实

### 4.1 所有 WS 帧仍然是控制面 JSON

OpenClaw 官方文档明确说明 Gateway WS 使用：

1. `req`
2. `res`
3. `event`

三类帧，且都是 `WebSocket text frames with JSON payloads`。

这意味着 `qpyclaw-node V1` 继续走当前 `qpyclaw_node.py` 已有的 JSON 文本收发模型，不需要引入二进制媒体通道。

### 4.2 连接时必须声明 role + scopes

官方文档确认：

1. `role: "node"` 用于能力宿主
2. `role: "operator"` 用于控制面客户端
3. `operator` 常见 scopes 包括：
   - `operator.read`
   - `operator.write`
   - `operator.admin`
   - `operator.approvals`
   - `operator.pairing`

`qpyclaw-node V1` 只需要：

1. `node` 连接保持原样
2. 新增一条 `operator` 连接
3. `operator` 默认只申请最小读写权限

### 4.3 主会话 key 就是 `main`

官方文档在 `Talk Mode` 和 `Session Tools` 中都明确了：

1. 主会话使用字面量 `main`
2. `Talk Mode` 把 transcript 发到 `main session`

所以 `qpyclaw-node V1` 默认目标会话就是 `main`，不自己发明新的默认 session 规则。

### 4.4 `chat.send` 是非阻塞的

官方文档确认：

1. `chat.send` 立即 ack
2. ack 中包含 `{ runId, status: "started" }`
3. 相同 `idempotencyKey` 重发时，运行中返回 `{ status: "in_flight" }`
4. 运行完成后可返回 `{ status: "ok" }`
5. 回复过程通过 `event:"chat"` 流式推送

### 4.5 `chat.history` 和 `chat.subscribe` 都是公开路径

官方文档确认：

1. `WebChat` 使用 `chat.history`
2. Android Chat 使用 `chat.history`、`chat.send`
3. Android Chat 使用 `chat.subscribe -> event:"chat"` 做 best-effort 推送更新

这给了 `qpyclaw-node V1` 一个更稳妥的组合：

1. `chat.subscribe` 负责低延迟提示
2. `chat.history` 负责确定性回补

### 4.6 `chat.abort` 支持 session 级中止

官方文档确认：

1. `chat.abort` 可支持 `{ sessionKey }`
2. 可用于中止该 session 的活动 run

这对设备侧语音中断非常关键，因为它允许设备在本地检测到“用户打断”后主动停止服务端当前对话回合。

### 4.7 Talk Mode 回复可带 voice directive

官方 `Talk Mode` 文档明确给出：

1. 回复第一条非空行可以是单行 JSON
2. 这条 JSON 用来控制 voice
3. 该行在 TTS 播放前应被剥离

这说明 `qpyclaw-node V1` 需要具备“先解析首行 voice directive，再把正文送 TTS”的能力。

## 5. qpyclaw V1 的关键工程约定

## 5.1 双连接，但同一设备身份

`qpyclaw 约定`：

1. `node` 连接与 `operator` 连接共用同一个 `device.id`
2. 两条连接使用不同的 `client.id` / `client.mode` / `role`
3. 两条连接可以使用不同 token

这样做的原因是，官方文档说明 `system-presence` 会按设备身份聚合 `roles` 和 `scopes`。  
也就是说，同一台设备以 `node + operator` 两种角色同时在线，在 UI 上应能被视为一台设备，而不是两台无关客户端。

### 5.2 `operator` 只申请最小 scope

`qpyclaw 约定`：

`V1` 默认只使用：

1. `operator.read`
2. `operator.write`

不默认申请：

1. `operator.admin`
2. `operator.approvals`
3. `operator.pairing`

这是因为 `qpyclaw-node` 的语音链路只需要：

1. 发送聊天
2. 查看聊天历史
3. 订阅聊天更新
4. 必要时中止当前聊天

### 5.3 优先“文档保证字段”，少依赖未公开 event 细节

官方文档没有完整冻结 `event:"chat"` 的逐字段 payload 形状。  
因此 `qpyclaw-node V1` 采取保守策略：

1. 把 `event:"chat"` 当作“新回复可能已到”的提示
2. 把 `chat.history` 当作最终回复的权威回补来源

这意味着：

1. 即使 `chat` 事件结构未来有细节调整，`V1` 仍然能工作
2. 设备侧不需要绑定复杂的 delta 流 parser

## 6. 建议的连接契约

## 6.1 Node Session

这条连接继续沿用当前运行时已有字段：

```json
{
  "type": "req",
  "id": "req_node_connect_001",
  "method": "connect",
  "params": {
    "minProtocol": 3,
    "maxProtocol": 3,
    "client": {
      "id": "qpyclaw-node",
      "version": "0.1.0",
      "platform": "quectel",
      "mode": "node"
    },
    "role": "node",
    "scopes": [],
    "caps": ["audio", "display", "cellular"],
    "commands": ["qpy.device.info", "qpy.audio.play"],
    "permissions": {},
    "auth": { "token": "<node_token>" },
    "locale": "zh-CN",
    "userAgent": "qpyclaw-node/0.1.0",
    "device": {
      "id": "<stable_device_id>"
    }
  }
}
```

说明：

1. 这是基于官方 `connect` 结构和当前 `qpyclaw_node.py` 现有模式整理的示例
2. 真实 `caps/commands` 仍由当前 runtime + extension 汇总生成

## 6.2 Operator Session

`qpyclaw 约定` 的最小 `operator` 连接如下：

```json
{
  "type": "req",
  "id": "req_operator_connect_001",
  "method": "connect",
  "params": {
    "minProtocol": 3,
    "maxProtocol": 3,
    "client": {
      "id": "qpyclaw-voice",
      "version": "0.1.0",
      "platform": "quectel",
      "mode": "operator"
    },
    "role": "operator",
    "scopes": ["operator.read", "operator.write"],
    "caps": [],
    "commands": [],
    "permissions": {},
    "auth": { "token": "<operator_token>" },
    "locale": "zh-CN",
    "userAgent": "qpyclaw-node/0.1.0 voice",
    "device": {
      "id": "<stable_device_id>"
    }
  }
}
```

说明：

1. `device.id` 与 node 保持一致
2. `client.id` 与 node 区分开，便于日志和调试
3. `mode: "operator"`、`role: "operator"` 直接对应官方文档

## 7. qpyclaw V1 推荐的聊天收敛策略

这是本文最关键的部分。

### 7.1 不建议只靠 `event:"chat"` 拼完整回复

原因：

1. 官方文档确认了“有 `chat` 事件”
2. 但没有在高层文档里冻结 `chat` 事件逐字段结构
3. 设备侧如果直接绑定 delta payload，后续兼容风险更高

### 7.2 推荐的 V1 组合

`qpyclaw 约定`：

1. 建立 `operator` 连接
2. 调用 `chat.subscribe`
3. 发送 `chat.send`
4. 收到任意 `chat` 事件后，只把它当作“有更新”的提示
5. 周期性调用 `chat.history` 拉取最近消息
6. 用本地规则识别“本轮 turn 的最终 assistant 回复”

### 7.3 为什么这套组合更稳

| 路径 | 作用 |
| --- | --- |
| `chat.subscribe -> event:"chat"` | 降低等待延迟 |
| `chat.history` | 做最终一致性回补 |
| `runId` | 用于日志、超时、必要时 `abort` |
| `idempotencyKey` | 去重和断线重试保护 |

## 8. 推荐的 `chat.send` 调用约定

官方文档明确说明 `chat.send` 是有副作用的方法，且 `idempotencyKey` 参与幂等。

`qpyclaw 约定`：

`V1` 每次语音 turn 都生成一个稳定 `turn_id`，并将其映射为本轮 `idempotencyKey`。

### 8.1 建议参数

下面这组字段是 `qpyclaw-node V1` 依赖的最小字段集：

```json
{
  "type": "req",
  "id": "req_chat_send_turn_001",
  "method": "chat.send",
  "params": {
    "sessionKey": "main",
    "message": "今天天气怎么样",
    "idempotencyKey": "voice-turn-1743412345000-001"
  }
}
```

说明：

1. `sessionKey` 使用 `main`
2. `message` 是 ASR 得到的 transcript
3. `idempotencyKey` 由设备生成

关于这里的最小字段集，需要说明两点：

1. `sessionKey`、`message` 是基于官方 `Talk Mode` / `WebChat` / `Session Tools` 的公开行为推导
2. `idempotencyKey` 来自官方 `TypeBox` 文档对有副作用方法的约束，以及 `Control UI` 对 `chat.send` 幂等行为的说明

## 9. 推荐的回复识别规则

这是 `qpyclaw V1` 自己的实现约定，不是 OpenClaw 文档逐字定义。

### 9.1 Turn 基线快照

发送前先取一个基线：

1. 记录本地 `turn_id`
2. 记录本地 `started_ms`
3. 调用一次 `chat.history(limit=N)`
4. 记住“发送前最后一条消息”的位置或摘要

### 9.2 发送后等待规则

发送后进入循环：

1. 持续读 WS 帧
2. 若读到 `event:"chat"`，标记 `history_dirty = true`
3. 定时调用 `chat.history(limit=N)`
4. 在最近消息中查找“发送基线之后新增的 assistant 消息”
5. 找到后认定为本轮最终回复

### 9.3 超时回退

若在规定时间内未找到最终 assistant 消息：

1. 保留 `runId`
2. 可选择 `chat.abort`
3. 将本轮标记为 `CHAT_TIMEOUT`
4. 回到 `idle`

### 9.4 V1 先不做的复杂能力

`V1` 先不做：

1. 流式边说边播
2. 增量句子切块 TTS
3. 多条 assistant delta 合并
4. 并发多 turn

`V1` 只允许同一时间存在一个活跃 voice turn。

## 10. Voice Directive 契约

官方 Talk Mode 允许回复首行携带单行 JSON voice directive。  
`qpyclaw V1` 定义如下处理约定。

### 10.1 解析规则

1. 只检查第一条非空行
2. 若该行是合法 JSON object，则视为 voice directive
3. 该行从最终 TTS 文本中剥离
4. 其余正文继续作为回复文本

### 10.2 V1 支持策略

`qpyclaw 约定`：

`V1` 不要求设备把官方所有 voice key 都实现完全，只要求：

1. 能正确忽略未知字段
2. 能提取少量对设备有意义的字段

建议最小支持字段：

| 字段 | 处理方式 |
| --- | --- |
| `voice` / `voiceId` / `voice_id` | 映射到 TTS backend 的 voice 选择 |
| `lang` | 若 TTS backend 支持则透传 |
| `speed` / `rate` | 若后端支持则透传，不支持则忽略 |
| `once` | 只对本轮 reply 生效 |

其余字段一律允许忽略，但不得导致崩溃。

## 11. 设备侧最小数据结构

下面这些结构是 `qpyclaw_node.py` 内部约定，目的是减少后续编码歧义。

## 11.1 Voice Turn

```json
{
  "turn_id": "voice-turn-1743412345000-001",
  "session_key": "main",
  "state": "chatting",
  "started_ms": 1743412345000,
  "ended_ms": 0,
  "run_id": "",
  "transcript": "",
  "reply_text": "",
  "voice_directive": {},
  "error_code": "",
  "error_message": ""
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `turn_id` | 本轮唯一 ID，同时作为 `idempotencyKey` 来源 |
| `session_key` | `V1` 默认 `main` |
| `state` | `idle/wake_pending/listening/uploading/chatting/speaking/error` |
| `run_id` | `chat.send` ack 返回值 |
| `transcript` | ASR 结果 |
| `reply_text` | 最终 assistant 文本 |
| `voice_directive` | 解析出的首行 JSON |
| `error_code` | 标准化错误码 |

## 11.2 ASR 适配器输入输出

输入：

```json
{
  "turn_id": "voice-turn-1743412345000-001",
  "audio_format": "opus",
  "sample_rate": 16000,
  "frames": ["<opaque>"]
}
```

输出：

```json
{
  "ok": true,
  "text": "今天天气怎么样",
  "confidence": 0.93,
  "provider": "http_json",
  "latency_ms": 820,
  "error_code": "",
  "error_message": ""
}
```

### 11.3 TTS 适配器输入输出

输入：

```json
{
  "turn_id": "voice-turn-1743412345000-001",
  "text": "今天上海多云，气温二十度左右。",
  "voice_directive": {
    "voice": "default",
    "once": true
  }
}
```

输出：

```json
{
  "ok": true,
  "audio_format": "opus",
  "sample_rate": 16000,
  "payload": "<opaque>",
  "provider": "http_json",
  "latency_ms": 640,
  "error_code": "",
  "error_message": ""
}
```

## 12. 板级 hook 最小契约

这部分是 `qpyclaw_node.py` 与板级 extension 之间的接口，不直接暴露给 OpenClaw。

### 12.1 获取方式

`qpyclaw 约定`：

板级 extension 新增：

```python
get_voice_hooks() -> dict
```

### 12.2 字段定义

| key | 是否必需 | 说明 |
| --- | --- | --- |
| `open_stream` | 是 | 打开音频输入输出 |
| `close_stream` | 是 | 关闭音频输入输出 |
| `read_frame` | 是 | 读取一帧音频 |
| `write_frame` | 是 | 播放一帧音频或整段音频 |
| `start_kws` | 是 | 启动唤醒 |
| `stop_kws` | 是 | 停止唤醒 |
| `set_kws_callback` | 是 | 注册唤醒回调 |
| `start_vad` | 是 | 启动 VAD |
| `stop_vad` | 是 | 停止 VAD |
| `set_vad_callback` | 是 | 注册 VAD 回调 |
| `show_state` | 否 | 切换屏幕/UI 状态 |
| `set_volume` | 否 | 调节输出音量 |
| `snapshot` | 否 | 调试快照 |

### 12.3 `show_state` 的推荐枚举

`qpyclaw 约定`：

| 状态 | 含义 |
| --- | --- |
| `idle` | 待唤醒 |
| `listening` | 正在听音 |
| `thinking` | 已送出 transcript，等待回复 |
| `speaking` | 正在播报 |
| `error` | 本轮失败 |
| `offline` | 网络或 Gateway 不可用 |

## 13. 错误码约定

为了让板级 UI、日志和运维工具能统一处理，`V1` 推荐先统一下面这批错误码：

| 错误码 | 含义 |
| --- | --- |
| `VOICE_DISABLED` | 语音功能未启用 |
| `VOICE_BUSY` | 当前已有活跃 turn |
| `AUDIO_OPEN_FAILED` | 板级音频流打开失败 |
| `AUDIO_READ_FAILED` | 音频采集失败 |
| `ASR_FAILED` | ASR 调用失败 |
| `CHAT_SEND_FAILED` | `chat.send` 调用失败 |
| `CHAT_TIMEOUT` | 规定时间内未取到回复 |
| `CHAT_ABORTED` | 本地或远端中止 |
| `TTS_FAILED` | TTS 合成失败 |
| `PLAYBACK_FAILED` | 音频播放失败 |
| `VOICE_HOOK_MISSING` | 板级 hook 不完整 |

## 14. V1 编码落地顺序

如果按本文契约推进，建议编码顺序是：

1. 在 `qpyclaw_node.py` 内新增 `OperatorSessionClient`
2. 先打通 `chat.subscribe + chat.send + chat.history`
3. 再实现 `VoiceTurn` 状态机与错误码
4. 再实现 `voice directive` 解析
5. 最后把 `EC800MCNLE` 的 `get_voice_hooks()` 接上

## 15. 当前结论

到这里，`qpyclaw-node V1` 语音对话的协议面已经足够进入编码阶段：

1. 官方依赖面已经收缩到少数几个稳定 WS 方法
2. 回复收敛策略已经明确为“`chat` 事件提示 + `chat.history` 权威回补”
3. 设备侧 turn、ASR、TTS、板级 hook 的最小数据结构已经定型
4. `V1` 继续坚持“单文件通用 runtime + 板级目录承接专有能力”

下一步最合适的工作，不再是补概念文档，而是开始 `P0`：

1. 只做 `operator` 会话
2. 只做固定 transcript -> `main` -> 拉回文本
3. 跑通后再接真实 `KWS / VAD / ASR / TTS`

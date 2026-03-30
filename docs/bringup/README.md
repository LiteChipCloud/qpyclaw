# Bringup

这里放板级 bring-up、部署记录、首板联调结果、问题清单与 smoke 流程。

## 1. 当前优先板卡

1. `EC800KCNLC Dev Board`
2. `EC800MCNLE Audio Board`

## 2. 当前已完成的实测板卡

当前已经完成一次实机清板、部署和烟测的是：

```text
boards/ec800kcnlc-dev-board
```

## 3. EC800K 当前实测状态

| 项目 | 当前结果 |
| --- | --- |
| 实测日期 | `2026-03-27` |
| 板目录 | `boards/ec800kcnlc-dev-board/` |
| 模组识别 | `EC800K` |
| 固件版本 | `EC800KCNLCR07A03M04_OCPU_QPY` |
| AT 口 | `COM15` |
| REPL 口 | `COM14` |
| SIM 状态 | `NOT INSERTED` |
| `/usr` 旧应用 | 已清空 |
| `qpyclaw-node` runtime | 已部署到 `/usr` |
| 最小运行时烟测 | 已通过 |

## 4. 本次实测工作流

```mermaid
flowchart LR
  A["识别设备信息"] --> B["采集 /usr 旧树快照"]
  B --> C["清空旧 /usr 应用"]
  C --> D["部署 qpyclaw-node/usr_mirror"]
  D --> E["REPL 导入烟测"]
  E --> F["回写证据与文档"]
```

## 5. 当前证据文件

| 证据 | 文件 |
| --- | --- |
| 清板前 `/usr` 树快照 | `docs/bringup/evidence/ec800kcnlc-usr-before-reset.json` |
| 部署后 `/usr` 树快照 | `docs/bringup/evidence/ec800kcnlc-usr-after-qpyclaw-node-deploy.json` |
| 运行时最小烟测结果 | `docs/bringup/evidence/ec800kcnlc-runtime-smoke.json` |
| 插卡后设备基础探测 | `docs/bringup/evidence/ec800kcnlc-device-info-after-sim.json` |
| 插卡后底层网络 API 分段探测 | `docs/bringup/evidence/ec800kcnlc-net-api-step-probe.json` |
| 插卡后底层网络 API 补充探测 | `docs/bringup/evidence/ec800kcnlc-net-api-step-probe-2.json` |
| `qpy.net.ifconfig` 实测结果 | `docs/bringup/evidence/ec800kcnlc-qpy-ifconfig-long-wait.json` |
| `qpy.net.diag` 摘要结果 | `docs/bringup/evidence/ec800kcnlc-qpy-netdiag-summary.json` |
| 云端 operator `node.invoke` 闭环 | `docs/bringup/evidence/2026-03-28-cloud-node-operator-invoke.json` |

## 6. 当前已验证成立的事实

1. 这块开发板原有 `/usr` 应用已可安全清理，不再保留旧项目约束。
2. `qpyclaw-node/runtime/usr_mirror` 已能完整部署到设备 `/usr`。
3. 不启动 `_main.py` 主循环的情况下，`app` 包可正常导入。
4. `RuntimeState` 与 `ToolRunner` 可成功初始化。
5. 三个只读工具已经实测成功：
   `qpy.tools.catalog`、`qpy.runtime.status`、`qpy.device.info`
6. 当前实测结果表明，`EC800KCNLC` 已经可以作为 `qpyclaw-node` 的纯蜂窝开发板继续推进。

## 7. 当前未验证项

1. 真实蜂窝注册与 IP 获取
2. 与 Official OpenClaw Gateway 的真实 websocket 建链
3. 鉴权 token、设备身份与协议兼容性
4. 音频、显示、GPIO、摄像头等外设能力

当前主阻塞不是 runtime 骨架，而是：

```text
当前还没有真实 Gateway 地址和 token，因此还不能做 Official OpenClaw Gateway 建链验证。
```

## 8. 后续建议顺序

1. 先插入可用 SIM，验证驻网、PDP、IP 和 `qpy.net.diag`。
2. 再把 `app/config.py` 中的 Gateway 地址、token 和设备标识替换为真实值。
3. 然后做 `qpyclaw-node -> Official OpenClaw Gateway` 首次联通。
4. 最后再进入外设扩展、能力开放和产品化约束。

## 9. 插卡后的最新实测结论

`2026-03-27` 最新实测已经确认：

1. `CPIN=READY`
2. 已驻网成功
3. PDP 已激活
4. `qpy.net.ifconfig` 与 `qpy.net.diag` 都已实测成功

关键网络事实如下：

| 项目 | 实测值 |
| --- | --- |
| 运营商 | `CHN-CT / CT / 460-11` |
| IPv4 | `10.132.66.100` |
| IPv6 | `240e:46c:a602:79e3:1:1:b7aa:6f83` |
| IPv4 属性 | 运营商私网地址 |
| IPv6 属性 | 可路由全球 IPv6 地址 |
| `qpy.net.ifconfig` 耗时 | 约 `13.1s` |
| `qpy.net.diag` 耗时 | 约 `17.4s` |

这意味着：

1. `qpyclaw-node -> Official OpenClaw Gateway` 的出站建链条件已经基本具备。
2. 当前蜂窝 IPv4 不是公网直连地址，不适合假设“别人直接通过 IPv4 主动打进来”。
3. 但设备具备出站连接能力，而且同时拿到了 IPv6。

## 10. 当前新增风险提示

当前配置文件中的：

```text
MAX_CMD_EXEC_SEC = 12
```

而实测两个网络类工具耗时已经超过这个值：

1. `qpy.net.ifconfig` 约 `13.1s`
2. `qpy.net.diag` 约 `17.4s`

当前运行时本地并没有直接用这个值强杀工具，但它仍然是接入 Official Gateway 前必须重新评估的超时配置项。

## 11. 2026-03-28 最新云端节点状态

`2026-03-28` 这轮实测已经把 `EC800KCNLC -> Cloud OpenClaw Gateway` 的主链路打通到了
真实 operator 命令闭环。

当前成立的最新事实：

1. 当前串口映射是 `COM9=AT`、`COM11=REPL`、`COM10=diag/log`。
2. 板端当前处于 `online=true`，协议版本为 `3`。
3. 云端配对已经完成，当前 node id 为
   `09c41c83ee53ba08930ac6ca8d4815640382a77a13e08edfcc17646e66b8fc54`。
4. 云端 `gateway.nodes.allowCommands` 已放行
   `qpy.runtime.status`、`qpy.tools.catalog` 等 `qpy.*` 命令。
5. Host operator 已经真实调用成功：
   `qpy.runtime.status`、`qpy.tools.catalog`。
6. 设备端 `debug_snapshot()` 已能看到：
   `last_cmd_tool=qpy.tools.catalog`、
   `last_exec_status=succeeded`、
   `last_exec_result_code=OK`。

这意味着当前阻塞点已经从“能不能接上 Official Gateway”切换成了：

1. 是否继续扩展 `qpy.*` 指令面
2. 是否开始做长稳 soak
3. 是否切换到 `EC800M` 音频板推进语音/屏幕/外设能力

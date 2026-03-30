# embed/qpyclaw-node

这是当前 `qpyclaw` 项目最重要的目录。

当前主线目标：

```text
qpyclaw-node -> Official OpenClaw Gateway
```

当前子目录分工：

1. `runtime/`：设备端实际运行时，只放可部署到设备 `/usr` 的通用 runtime
2. `deploy/`：部署清单、bootstrap、recover、smoke 等下发与恢复工具
3. `examples/`：按板型组织的接入示例、样例配置、组合说明
4. `tests/`：设备端联调与回归验证
5. `docs/`：node 专项说明

## 当前边界

为避免后续目录再次混乱，当前统一按下面的原则收口：

1. `embed/qpyclaw-node/runtime/` 不再放板型示例，也不放板级专有驱动。
2. `boards/<board>/code/` 放该板独有的代码，例如音频、屏幕、按键、GPIO、摄像头、马达、板级引脚映射与初始化。
3. `embed/qpyclaw-node/examples/<board>/` 放“如何把通用 `qpyclaw_node.py` 与这块板的专有代码组合起来”的示例。
4. 也就是说：板级能力归 `boards`，通用 node runtime 归 `runtime`，组合方法归 `examples`。

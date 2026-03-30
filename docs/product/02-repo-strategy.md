# Repo Strategy And Project Layout

## 1. 当前结论

`qpyclaw` 现在按独立工程仓库组织，先承载三类内容：

1. `qpyclaw-node`
2. `qpyclaw`
3. `shared runtime contracts`

`qpyclaw-fleet` 仍然只保留产品边界和接口契约，不在当前仓库内实现完整平台。

## 2. 当前目录策略

### 2.1 代码目录

当前代码目录按“设备侧角色”拆分：

1. `embed/qpyclaw-node/`
2. `embed/qpyclaw/`
3. `embed/shared/`

其中：

1. 当前设备侧主业务代码放在 `embed/qpyclaw-node/`
2. 后续 QuecPython 侧 `qpyclaw` 本体能力放在 `embed/qpyclaw/`
3. 共享协议、通道、工具放在 `embed/shared/`

### 2.2 板级目录

`boards/` 放板级资料与板级专有代码，但不放通用 runtime。

内容包括：

1. 板级能力说明
2. 外设与接口定义
3. bring-up 记录
4. 板级调试注意事项
5. 板型专有驱动、适配层、板级初始化代码

### 2.3 板目录命名

板目录不再只写模组型号，而是统一按下面规则命名：

```text
<module>-<board-type-or-purpose>
```

当前正式板目录：

1. `boards/ec800kcnlc-dev-board/`
2. `boards/ec800mcnle-audio-board/`

## 3. 推荐目录结构

```text
qpyclaw/
├─ docs/
│  ├─ architecture/
│  ├─ public/
│  ├─ product/
│  └─ research/
├─ boards/
│  ├─ ec800kcnlc-dev-board/
│  └─ ec800mcnle-audio-board/
├─ embed/
│  ├─ qpyclaw/
│  ├─ qpyclaw-node/
│  └─ shared/
├─ desktop/
│  ├─ simulator/
│  ├─ bridge/
│  └─ tools/
├─ tools/
│  ├─ host/
│  ├─ flash/
│  └─ release/
└─ examples/
```

## 4. 每个目录的职责

| 路径 | 职责 |
| --- | --- |
| `docs/public/` | 存放面向开源用户的 Quickstart、配置样例与发布说明 |
| `docs/product/` | 存放产品定位、PRD、路线图、商业边界 |
| `docs/architecture/` | 存放系统架构、协议、数据结构 |
| `docs/research/` | 存放生态调研、竞品扫描、可行性记录 |
| `embed/qpyclaw-node/runtime/` | 当前设备侧通用 runtime 目录 |
| `embed/qpyclaw-node/examples/` | 按板型组织的组合示例、样例配置、接入说明 |
| `embed/qpyclaw/` | 后续 QuecPython 侧 qpyclaw 本体能力目录 |
| `embed/shared/` | qpyclaw 与 qpyclaw-node 共用的协议、通道、工具 |
| `boards/<board>/code/` | 放该板独有的驱动、适配层、板级初始化，不放通用 qpyclaw-node runtime |
| `tools/host/` | 部署、调试、验证、导出、板侧运维工具 |
| `examples/` | Demo、最小可运行示例、对接样例 |

## 5. 关于 `qpyclaw-fleet`

`qpyclaw-fleet` 当前仍建议作为未来独立产品线考虑，不混入本仓库的主实现。

当前仓库只保留与 `fleet` 有关的：

1. 边界说明
2. 契约文档
3. 接口草案

## 6. 当前建议

1. 继续开发时，以 `embed/qpyclaw-node/` 为设备端主目录。
2. 板级资料与板级专有代码统一收敛到 `boards/<board>/`。
3. 不再新增“纯模组型号”的板目录名。

# QuecPython 工具链与 Skill 审查

## 1. 审查目标

本次审查回答三个问题：

1. `quecpython-dev-skill-main` 到底提供了什么。
2. `qpy-vscode-extension-master` 到底提供了什么。
3. 当前已安装的 `quecpython-dev` skill 是否已经“功能齐全”。

## 2. 审查对象

| 对象 | 路径 | 角色判断 |
| --- | --- | --- |
| `quecpython-dev-skill-main` | `opensource/quecpython-dev-skill-main` | 本地 skill 源码仓库 |
| `qpy-vscode-extension-master` | `opensource/qpy-vscode-extension-master` | 官方 VS Code 插件主实现 |
| `vscode-extension-qpycom-issues-main` | `opensource/vscode-extension-qpycom-issues-main` | issue 跟踪仓库，不是功能实现仓库 |
| 已安装 `quecpython-dev` skill | `C:/Users/kingd/.codex/skills/quecpython-dev` | 当前实际被 Codex 调用的 skill |

## 3. 一句话结论

### 3.1 关于三个参考项目

1. `qpy-vscode-extension-master` 才是真正的主参考实现。
2. `quecpython-dev-skill-main` 是围绕 QuecPython 开发与运维流程做的 AI 化封装。
3. `vscode-extension-qpycom-issues-main` 几乎没有实现价值，只是 issue 入口。

### 3.2 关于当前已安装 skill

当前已安装的 `quecpython-dev` skill：

1. 不是空壳，已经相当能用。
2. 覆盖了大部分“设备开发 + 下载 + 调试 + 资料检索 + 项目管理”流程。
3. 但还不能叫“功能齐全”。
4. 最直接、最确定的缺口是：`query_module_capability.py` 依赖的数据文件缺失，功能实际是坏的。

## 4. `qpy-vscode-extension-master` 审查结果

## 4.1 具备的真实能力

| 能力 | 证据方向 | 结论 |
| --- | --- | --- |
| 串口连接 | `src/api/commands.ts` | 有 |
| REPL 交互 | `src/serial/*` | 有 |
| 文件下载 | `src/api/fileDownload.ts` + `scripts/QPYcom.exe` | 有 |
| 文件树浏览 | `src/deviceTree/moduleFileSystem.ts` | 有 |
| 脚本运行 | `src/api/commands.ts` 中 `runScript` | 有 |
| 固件下载 / 烧录 | `src/sidebar/*` + `scripts/QuecPythonDownload.exe` | 有 |
| 项目 / 组件管理 | `src/packagePanel/*` | 有 |
| 自动补全 / stubs | `snippets` / `resources` | 有 |

## 4.2 对本项目的价值

`qpy-vscode-extension-master` 的价值不在于它本身是 node runtime，而在于它证明了三件事：

1. 官方工具链已经覆盖了下载、运行、文件树、固件、项目管理这些核心宿主能力。
2. `EC800KCNLC` 确实在插件支持矩阵里。
3. 我们完全可以把这些能力拆成“可脚本化宿主工具链”，反向喂给 `quecpython-dev` skill。

## 4.3 对当前 skill 的启发

`quecpython-dev` skill 现在已经吸收了其中相当一部分能力：

1. 设备文件系统 CLI
2. 设备基础信息探测
3. 固件生命周期管理
4. Soak Runner
5. 项目 / 组件管理
6. 代码脚手架

但仍然没有做到和官方插件完全对齐。

## 5. `quecpython-dev-skill-main` 审查结果

## 5.1 优点

这个 skill 源码仓库最大的价值，是把“散落的 QuecPython 工具流程”整理成了明确的 AI 工作流：

```mermaid
flowchart LR
  A["Docs Search"] --> B["Capability Check"]
  B --> C["Compatibility Check"]
  C --> D["Device Ops"]
  D --> E["Probe / Smoke / Soak"]
  E --> F["Firmware / Project Manager"]
```

它不是简单堆几个脚本，而是已经形成了一套比较完整的流程地图。

## 5.2 已覆盖的主要能力

| 能力域 | 脚本 / 参考 | 结论 |
| --- | --- | --- |
| 兼容性检查 | `check_quecpython_compat.py` | 已覆盖 |
| 官方文档检索 | `query_official_docs.py` / `query_qpy_docs_online.py` | 已覆盖 |
| 模组能力查询 | `query_module_capability.py` | 设计有，但当前安装版不可用 |
| 固件管理 | `qpy_firmware_manager.py` | 已覆盖 |
| 文件系统操作 | `qpy_device_fs_cli.py` | 已覆盖 |
| 基础信息探测 | `qpy_device_info_probe.py` | 已覆盖 |
| 烟测 / 长稳 | `device_smoke_test.py` / `qpy_soak_runner.py` | 已覆盖 |
| 项目 / 组件管理 | `qpy_project_manager.py` | 已覆盖 |
| 脚手架生成 | 安装版额外含 `qpy_code_scaffold.py` | 已覆盖 |
| 宿主稳定性排查 | `qpy_crash_triage.py` | 已覆盖 |

## 6. 已安装 `quecpython-dev` skill 审查结果

## 6.1 比源码仓库更多的地方

当前安装版 skill 不只是源码仓库的原样复制，它额外多了：

1. `scripts/qpy_code_scaffold.py`
2. `scripts/qpy_event_window_check.py`
3. `references/code-scaffold-workflow.md`

这说明当前安装版实际上是一个“增强版”。

## 6.2 明确坏掉的地方

最明确的问题是：

```text
python C:\Users\kingd\.codex\skills\quecpython-dev\scripts\query_module_capability.py --module EC800KCNLC
```

返回：

```text
Data file not found: C:\Users\kingd\.codex\skills\quecpython-dev\data\modules_sheet03.normalized.json
```

这说明它的脚本在，但关键数据不在，因此这项能力是“假可用”。

## 6.3 为什么这很关键

`query_module_capability.py` 不是锦上添花，而是这个 skill 的核心判断基础之一。

因为我们后续要做：

1. 模组选型
2. 资源边界判断
3. 功能支持判断
4. 固件版本与能力匹配

如果这个数据链是断的，那么 skill 在“能力验证”这一环就不算完整。

## 6.4 当前完整性判断

| 维度 | 判断 |
| --- | --- |
| 日常开发可用性 | 高 |
| 设备运维可用性 | 高 |
| 文档检索能力 | 中高 |
| 官方插件能力映射度 | 中高 |
| 自包含程度 | 中 |
| 模组能力数据完整性 | 低 |
| 是否能称为“功能齐全” | 不能 |

## 7. 结论分层

### 7.1 可以确认已经做得不错的部分

1. 当前 skill 已经足够支撑 `qpyclaw-node` 的本地代码开发。
2. 当前 skill 已经能支撑设备下载、探测、烟测、文件系统管理。
3. 当前 skill 已经是“能打仗”的，不是演示性质。

### 7.2 当前还不能说功能齐全的原因

1. 关键能力查询链路存在缺失数据。
2. 与官方 VS Code 插件还不是完全同构。
3. 有些能力仍然依赖外部环境里恰好存在的工具或资源。

## 8. 对本项目的直接建议

### 8.1 结论

当前应该把 `quecpython-dev` skill 视为：

```text
足够支撑 qpyclaw 开发，但仍需要补齐数据资源和少量宿主工具链封装的“准生产级 skill”。
```

### 8.2 建议补齐项

1. 给已安装 skill 补上 `modules_sheet03.normalized.json` 数据链。
2. 把 `qpy-vscode-extension-master/scripts` 下的关键宿主工具发现逻辑再固化一层。
3. 为 `EC800KCNLC` 增加明确的模组 profile 与 bring-up workflow。
4. 后续补一个“从 skill 直接部署 qpyclaw-node 到 `/usr`”的专用流程。

## 9. 本次结论

1. `qpy-vscode-extension-master` 是主参考。
2. `vscode-extension-qpycom-issues-main` 不是实现仓库。
3. 当前安装的 `quecpython-dev` skill 很有价值，但还不能算真正功能齐全。
4. 当前最应优先修复的是模组能力数据缺口。

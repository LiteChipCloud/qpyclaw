# EC800KCNLC Dev Board Example

这个目录用于放 `EC800KCNLC` 开发板的 `qpyclaw-node` 组合示例。

当前这块板的定位是：

1. 无外设环境下验证 `qpyclaw-node -> Official OpenClaw Gateway`
2. 跑通网络、鉴权、文件系统、运维与恢复链路
3. 作为后续单文件 runtime 收敛和回归验证板

当前参考样例：

1. `config_local.example.py`

后续如需要，可以继续往这里补：

1. 示例 `main.py`
2. 开发态启动入口
3. 本板专用 smoke 场景

# embed/shared

这里放嵌入式侧共享基础层。

当前规划为：

1. `channels/`
2. `protocol/`
3. `utils/`

原则：

1. 共享层不承载产品角色语义。
2. `qpyclaw` 与 `qpyclaw-node` 都可以依赖这里。

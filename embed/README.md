# embed

这里是 `qpyclaw` 的嵌入式侧正式开发区。

## 正式开发目录

```text
embed/
├─ qpyclaw/
├─ qpyclaw-node/
└─ shared/
```

## 职责划分

1. `qpyclaw/`
   预留给后续 QuecPython 侧 `qpyclaw` 本体能力。
2. `qpyclaw-node/`
   当前设备侧主线目录，所有 node 业务代码都应优先收敛到这里。
3. `shared/`
   放共享协议、通道、工具和基础能力。

## 当前不要再用的旧占位目录

下面三个目录只是历史占位，不是正式落点：

1. `embed/channels/`
2. `embed/gateway/`
3. `embed/node/`

继续开发时，不要把新代码放进去。

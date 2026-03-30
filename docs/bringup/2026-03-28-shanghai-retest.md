# Shanghai Retest

## Purpose

Re-run the cloud OpenClaw transport checks after the board moved from Jinan to
Shanghai, in case the cellular routing behavior changed with location.

## Device State

| Item | Result |
| --- | --- |
| Date | `2026-03-28` |
| Module | `EC800K` |
| Firmware | `EC800KCNLCR07A03M04_OCPU_QPY` |
| AT port | `COM9` |
| REPL port | `COM11` |
| SIM | inserted / ready |
| Registration | OK |
| IPv4 | `10.87.171.69` |

## Probe Results

| Probe | Target | Result |
| --- | --- | --- |
| Plain HTTP baseline over gateway port | `124.70.221.88:18789` | `HTTP/1.1 302 Found` |
| Plain WS upgrade over gateway port | `ws://124.70.221.88:18789` | `HTTP/1.1 302 Found` |
| High-level HTTPS baseline | `https://www.baidu.com/` | `HTTPS USSL '[Errno 104] ECONNRESET'` |
| High-level plain WS connect | `ws://124.70.221.88:18789` | `b'HTTP/1.1 302 Found'` |

The `302` redirect target is still:

```text
http://service.sh.189.cn/service/jsp/recharge/greenRecharge/index.jsp
```

## Meaning

The move back to Shanghai did not clear either of the two known blockers:

1. Plain `ws://` traffic to the public cloud gateway is still rewritten by the
   cellular path.
2. Device-side HTTPS/TLS is still not usable from QuecPython on this EC800K
   firmware/SIM path.

This means the transport verdict did not change:

The current EC800K board still cannot connect directly as a public cloud
OpenClaw node from this network path.

## Evidence

```text
docs/bringup/evidence/2026-03-28-shanghai-retest.json
```

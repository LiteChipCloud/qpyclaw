# New SIM No Service

## Purpose

Verify whether switching to a new SIM card changes the EC800K transport result.

## Result

The new SIM is readable, but the module does not register to the cellular
network.

| Item | Result |
| --- | --- |
| Date | `2026-03-28` |
| Module | `EC800K` |
| Firmware | `EC800KCNLCR07A03M04_OCPU_QPY` |
| AT port | `COM9` |
| REPL port | `COM11` |
| SIM ICCID | `89861122060212026864` |
| SIM IMSI | `460115890331826` |
| CPIN | `READY` |
| CEREG | `3,0` |
| CGATT | `0` |
| CSQ | `99,99` |
| IPv4 | `0.0.0.0` |

## Recovery Attempt

A soft modem restart was triggered with:

```text
AT+CFUN=1,1
```

After reboot, the result did not improve:

1. still not registered
2. still not attached
3. still no IP address

## Meaning

This retest cannot reach the OpenClaw transport stage yet.

The blocker is now earlier than `ws://` or `wss://`:

1. the new SIM is present
2. the board currently has no usable radio/service state
3. therefore OpenClaw cloud connectivity cannot be validated on this SIM at this time

## Evidence

```text
docs/bringup/evidence/2026-03-28-new-sim-no-service.json
```

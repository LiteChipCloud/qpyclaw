import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const DEFAULT_PROTOCOL_VERSION = 3;
const DEFAULT_TIMEOUT_MS = 8000;
const DEFAULT_CANDIDATES = [
  "ws://127.0.0.1:18789",
  "ws://your-public-bridge.example.com:10503",
  "wss://your-public-bridge.example.com",
  "wss://your-public-bridge.example.com:10503",
];

function parseArgs(argv) {
  const args = {
    urls: [],
    timeoutMs: DEFAULT_TIMEOUT_MS,
    configPath: path.join(os.homedir(), ".openclaw", "openclaw.json"),
    json: false,
    insecure: false,
    skipConnect: false,
    role: "node",
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];
    if (arg === "--url" && next) {
      args.urls.push(next);
      i += 1;
      continue;
    }
    if (arg === "--timeout-ms" && next) {
      const parsed = Number.parseInt(next, 10);
      if (Number.isFinite(parsed) && parsed > 0) {
        args.timeoutMs = parsed;
      }
      i += 1;
      continue;
    }
    if (arg === "--config" && next) {
      args.configPath = next;
      i += 1;
      continue;
    }
    if (arg === "--role" && next) {
      args.role = next;
      i += 1;
      continue;
    }
    if (arg === "--json") {
      args.json = true;
      continue;
    }
    if (arg === "--insecure") {
      args.insecure = true;
      continue;
    }
    if (arg === "--skip-connect") {
      args.skipConnect = true;
      continue;
    }
  }

  if (args.urls.length === 0) {
    args.urls = DEFAULT_CANDIDATES.slice();
  }
  return args;
}

function maskSecret(value) {
  const text = typeof value === "string" ? value.trim() : "";
  if (!text) {
    return "";
  }
  if (text.length <= 8) {
    return `${text.slice(0, 2)}***${text.slice(-2)}`;
  }
  return `${text.slice(0, 4)}***${text.slice(-4)}`;
}

function loadGatewayToken(configPath) {
  const raw = fs.readFileSync(configPath, "utf8").replace(/^\uFEFF/, "");
  const parsed = JSON.parse(raw);
  const token = parsed?.gateway?.auth?.token;
  return typeof token === "string" ? token.trim() : "";
}

function toHttpProbeUrl(wsUrl) {
  const url = new URL(wsUrl);
  url.protocol = url.protocol === "wss:" ? "https:" : "http:";
  return url.toString();
}

async function httpProbe(wsUrl, timeoutMs) {
  const probeUrl = toHttpProbeUrl(wsUrl);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(probeUrl, {
      method: "GET",
      redirect: "manual",
      signal: controller.signal,
    });
    const text = await response.text();
    return {
      ok: true,
      url: probeUrl,
      status: response.status,
      location: response.headers.get("location") || "",
      contentType: response.headers.get("content-type") || "",
      bodyPreview: text.slice(0, 200),
    };
  } catch (error) {
    return {
      ok: false,
      url: probeUrl,
      error: error instanceof Error ? error.message : String(error),
    };
  } finally {
    clearTimeout(timer);
  }
}

function buildConnectParams(token, role) {
  return {
    minProtocol: DEFAULT_PROTOCOL_VERSION,
    maxProtocol: DEFAULT_PROTOCOL_VERSION,
    client: {
      id: "openclaw-probe",
      displayName: "qpyclaw Host Probe",
      version: "0.1.0",
      platform: process.platform,
      deviceFamily: "host-probe",
      mode: "probe",
    },
    role,
    caps: ["probe"],
    commands: ["qpy.help"],
    permissions: {},
    userAgent: "qpyclaw-host-probe/0.1.0",
    auth: token ? { token } : undefined,
  };
}

async function websocketProbe(wsUrl, params) {
  const result = {
    url: wsUrl,
    stage: "init",
    wsOpen: false,
    challengeSeen: false,
    connectResponseOk: false,
    closeCode: null,
    closeReason: "",
    error: "",
    frames: [],
  };

  return await new Promise((resolve) => {
    let settled = false;
    let connectRequestId = "host_probe_connect_1";
    let timeout = null;
    let ws = null;

    function finish(extra) {
      if (settled) {
        return;
      }
      settled = true;
      if (timeout) {
        clearTimeout(timeout);
      }
      if (ws && ws.readyState === WebSocket.OPEN) {
        try {
          ws.close(1000, "probe-done");
        } catch {
          // ignore
        }
      }
      resolve({ ...result, ...extra });
    }

    function pushFrame(frame) {
      if (result.frames.length >= 6) {
        return;
      }
      result.frames.push(frame);
    }

    try {
      ws = new WebSocket(wsUrl);
    } catch (error) {
      finish({
        stage: "construct_failed",
        error: error instanceof Error ? error.message : String(error),
      });
      return;
    }

    timeout = setTimeout(() => {
      finish({
        stage: result.stage === "init" ? "timeout_before_open" : "timeout_after_open",
        error: `timeout after ${params.timeoutMs}ms`,
      });
    }, params.timeoutMs);

    ws.addEventListener("open", () => {
      result.wsOpen = true;
      result.stage = "ws_open";
      if (params.skipConnect) {
        finish({});
      }
    });

    ws.addEventListener("error", (event) => {
      const message =
        event?.error instanceof Error
          ? event.error.message
          : event?.message || "websocket error";
      result.error = String(message);
    });

    ws.addEventListener("close", (event) => {
      result.closeCode = event.code;
      result.closeReason = event.reason || "";
      if (!settled) {
        finish({
          stage: result.stage,
          error: result.error || `closed(${event.code})`,
        });
      }
    });

    ws.addEventListener("message", (event) => {
      let text = "";
      if (typeof event.data === "string") {
        text = event.data;
      } else if (event.data instanceof Buffer) {
        text = event.data.toString("utf8");
      } else if (event.data && typeof event.data.text === "function") {
        event.data
          .text()
          .then((decoded) => {
            ws.dispatchEvent(new MessageEvent("message", { data: decoded }));
          })
          .catch(() => {});
        return;
      } else {
        text = String(event.data);
      }

      let frame = null;
      try {
        frame = JSON.parse(text);
      } catch {
        pushFrame({ type: "non_json", text: text.slice(0, 200) });
        return;
      }

      pushFrame(frame);

      if (frame?.type === "event" && frame?.event === "connect.challenge") {
        result.challengeSeen = true;
        result.stage = "challenge";
        if (params.skipConnect) {
          finish({});
          return;
        }
        const nonce = frame?.payload?.nonce;
        if (!nonce) {
          finish({
            stage: "challenge_missing_nonce",
            error: "connect.challenge missing nonce",
          });
          return;
        }
        const req = {
          type: "req",
          id: connectRequestId,
          method: "connect",
          params: buildConnectParams(params.token, params.role),
        };
        ws.send(JSON.stringify(req));
        result.stage = "connect_sent";
        return;
      }

      if (frame?.type === "res" && frame?.id === connectRequestId) {
        result.stage = "connect_response";
        result.connectResponseOk = Boolean(frame?.ok);
        if (frame?.ok) {
          finish({
            stage: "connect_ok",
            connectPayload: frame?.payload || null,
          });
        } else {
          const err = frame?.error || {};
          finish({
            stage: "connect_failed",
            errorCode: err?.code || "",
            error: err?.message || "connect rejected",
          });
        }
      }
    });
  });
}

function summarizeResult(item) {
  const http = item.httpProbe;
  const ws = item.wsProbe;
  return {
    url: item.url,
    httpStatus: http.ok ? http.status : null,
    httpLocation: http.ok ? http.location : "",
    wsStage: ws.stage,
    wsOpen: ws.wsOpen,
    challengeSeen: ws.challengeSeen,
    connectResponseOk: ws.connectResponseOk,
    error: ws.error || "",
    errorCode: ws.errorCode || "",
    closeCode: ws.closeCode,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.insecure) {
    process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";
  }

  const token = loadGatewayToken(args.configPath);
  const maskedToken = maskSecret(token);
  const results = [];

  for (const url of args.urls) {
    const httpResult = await httpProbe(url, args.timeoutMs);
    const wsResult = await websocketProbe(url, {
      token,
      role: args.role,
      timeoutMs: args.timeoutMs,
      skipConnect: args.skipConnect,
    });
    results.push({
      url,
      httpProbe: httpResult,
      wsProbe: wsResult,
      summary: summarizeResult({
        url,
        httpProbe: httpResult,
        wsProbe: wsResult,
      }),
    });
  }

  const payload = {
    configPath: args.configPath,
    tokenMasked: maskedToken,
    insecureTls: args.insecure,
    role: args.role,
    timeoutMs: args.timeoutMs,
    results,
  };

  if (args.json) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log(`Gateway token: ${maskedToken}`);
  console.log(`Role: ${args.role}`);
  console.log(`Timeout: ${args.timeoutMs}ms`);
  if (args.insecure) {
    console.log("TLS verify: disabled");
  }
  console.log("");

  for (const item of results) {
    const s = item.summary;
    console.log(`[${s.url}]`);
    console.log(`  http: ${s.httpStatus ?? "ERR"} ${s.httpLocation ? `location=${s.httpLocation}` : ""}`.trimEnd());
    console.log(`  ws_stage: ${s.wsStage}`);
    console.log(`  ws_open: ${s.wsOpen}`);
    console.log(`  challenge: ${s.challengeSeen}`);
    console.log(`  connect_ok: ${s.connectResponseOk}`);
    console.log(`  close_code: ${s.closeCode ?? ""}`);
    if (s.errorCode) {
      console.log(`  error_code: ${s.errorCode}`);
    }
    if (s.error) {
      console.log(`  error: ${s.error}`);
    }
    console.log("");
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exitCode = 1;
});

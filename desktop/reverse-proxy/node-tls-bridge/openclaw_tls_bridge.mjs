import fs from "node:fs";
import net from "node:net";
import tls from "node:tls";

function env(name, fallback = "") {
  const value = process.env[name];
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function intEnv(name, fallback) {
  const raw = env(name, "");
  if (!raw) {
    return fallback;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function buildTlsOptions() {
  const pfxFile = env("TLS_BRIDGE_PFX_FILE", "");
  const certFile = env("TLS_BRIDGE_CERT_FILE", "");
  const keyFile = env("TLS_BRIDGE_KEY_FILE", "");

  if (pfxFile) {
    return {
      pfx: fs.readFileSync(pfxFile),
      passphrase: env("TLS_BRIDGE_PFX_PASSPHRASE", ""),
    };
  }

  if (certFile && keyFile) {
    return {
      cert: fs.readFileSync(certFile),
      key: fs.readFileSync(keyFile),
    };
  }

  throw new Error(
    "Missing TLS material. Set TLS_BRIDGE_PFX_FILE or TLS_BRIDGE_CERT_FILE + TLS_BRIDGE_KEY_FILE.",
  );
}

const listenHost = env("TLS_BRIDGE_LISTEN_HOST", "127.0.0.1");
const listenPort = intEnv("TLS_BRIDGE_LISTEN_PORT", 18443);
const upstreamHost = env("TLS_BRIDGE_UPSTREAM_HOST", "127.0.0.1");
const upstreamPort = intEnv("TLS_BRIDGE_UPSTREAM_PORT", 18789);

const server = tls.createServer(buildTlsOptions(), (clientSocket) => {
  const peer = `${clientSocket.remoteAddress || "unknown"}:${clientSocket.remotePort || 0}`;
  console.log(`[tls-bridge] client connected ${peer}`);

  const upstreamSocket = net.connect({
    host: upstreamHost,
    port: upstreamPort,
  });

  clientSocket.on("error", (err) => {
    console.error(`[tls-bridge] client error ${peer}: ${err.message}`);
  });

  upstreamSocket.on("error", (err) => {
    console.error(`[tls-bridge] upstream error ${peer}: ${err.message}`);
    clientSocket.destroy(err);
  });

  clientSocket.on("close", () => {
    upstreamSocket.destroy();
    console.log(`[tls-bridge] client closed ${peer}`);
  });

  upstreamSocket.on("close", () => {
    clientSocket.destroy();
    console.log(`[tls-bridge] upstream closed ${peer}`);
  });

  clientSocket.pipe(upstreamSocket);
  upstreamSocket.pipe(clientSocket);
});

server.on("tlsClientError", (err, socket) => {
  const peer = socket ? `${socket.remoteAddress || "unknown"}:${socket.remotePort || 0}` : "unknown";
  console.error(`[tls-bridge] tls client error ${peer}: ${err.message}`);
});

server.listen(listenPort, listenHost, () => {
  console.log(
    `[tls-bridge] listening on ${listenHost}:${listenPort}, forwarding to ${upstreamHost}:${upstreamPort}`,
  );
});

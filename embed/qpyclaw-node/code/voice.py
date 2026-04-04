# voice.py — VoiceDialogClient for qpyclaw-node.
# Manages operator-role WebSocket connection for text chat via OpenClaw gateway.

import utime

try:
    import _thread
except Exception:
    _thread = None

from ws_client import WsClient, WsClosed, WsTimeout
from transport import (
    _string, _normalize_scopes, _request_remote_signature,
    dumps, loads,
)


class VoiceDialogClient(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self.ws = None
        self.online = False
        self._seq = 0
        self._lock = _thread.allocate_lock() if bool(_thread) and hasattr(_thread, "allocate_lock") else None
        self.connected_at_ms = 0
        self.last_connect_ms = 0
        self.last_disconnect_ms = 0
        self.last_close_reason = ""
        self.last_close_ms = 0
        self.last_error = ""
        self.last_error_code = ""
        self.last_error_ms = 0
        self.last_event = ""
        self.last_event_ms = 0
        self.last_run_id = ""
        self.last_turn_id = ""
        self.last_sent_message = ""
        self.last_sent_session_key = ""
        self.last_reply_text = ""
        self.last_reply_message_id = ""
        self.last_voice_directive = {}
        self.last_history_count = 0
        self.last_chat_status = ""
        self.last_history_poll_ms = 0
        self.last_subscribe_error = ""
        self.last_chat_duration_ms = 0
        self.last_chat_event_count = 0
        self.last_chat_history_polls = 0
        self.last_server_hello = None
        self.server_methods = []
        self.subscriptions = {}

    def _acquire(self):
        if self._lock is not None:
            self._lock.acquire()

    def _release(self):
        if self._lock is not None:
            self._lock.release()

    def _fail_locked(self, code, message, close=False):
        self.last_error_code = code or ""
        self.last_error = message or ""
        self.last_error_ms = utime.ticks_ms()
        if close:
            self._close_locked(code or "error")
        raise Exception((code or "VOICE_ERROR") + ": " + (message or "voice dialog failed"))

    def _bool_value(self, value, default):
        if value is None:
            return bool(default)
        if isinstance(value, bool):
            return value
        text = _string(value).strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off"):
            return False
        return bool(default)

    def _ws_url(self):
        text = _string(getattr(self.cfg, "VOICE_OPERATOR_WS_URL", "")).strip()
        if text:
            return text
        return _string(getattr(self.cfg, "OPENCLAW_WS_URL", "")).strip()

    def _session_key(self, session_key):
        text = _string(session_key).strip()
        if text:
            return text
        text = _string(getattr(self.cfg, "VOICE_MAIN_SESSION_KEY", "main")).strip()
        if text:
            return text
        return "main"

    def _connect_timeout_sec(self):
        value = getattr(self.cfg, "VOICE_OPERATOR_CONNECT_TIMEOUT_SEC", getattr(self.cfg, "CONNECT_TIMEOUT_SEC", 12))
        try:
            value = int(value)
        except Exception:
            value = 12
        if value <= 0:
            value = 12
        return value

    def _ack_timeout_ms(self):
        value = getattr(self.cfg, "ACK_TIMEOUT_MS", 10000)
        try:
            value = int(value)
        except Exception:
            value = 10000
        if value <= 0:
            value = 10000
        return value

    def _chat_timeout_ms(self, timeout_ms):
        value = timeout_ms
        if value in (None, ""):
            value = getattr(self.cfg, "VOICE_CHAT_TIMEOUT_MS", 45000)
        try:
            value = int(value)
        except Exception:
            value = 45000
        if value <= 0:
            value = 45000
        return value

    def _chat_poll_ms(self):
        value = getattr(self.cfg, "VOICE_CHAT_POLL_MS", 800)
        try:
            value = int(value)
        except Exception:
            value = 800
        if value <= 0:
            value = 800
        return value

    def _history_limit(self, history_limit):
        value = history_limit
        if value in (None, ""):
            value = getattr(self.cfg, "VOICE_CHAT_HISTORY_LIMIT", 12)
        try:
            value = int(value)
        except Exception:
            value = 12
        if value <= 0:
            value = 12
        return value

    def _operator_auth_token(self):
        token = _string(getattr(self.cfg, "VOICE_OPERATOR_AUTH_TOKEN", "")).strip()
        if token:
            return token
        if self._bool_value(getattr(self.cfg, "VOICE_OPERATOR_REUSE_NODE_TOKEN", False), False):
            return _string(getattr(self.cfg, "OPENCLAW_AUTH_TOKEN", "")).strip()
        return ""

    def _operator_client_id(self):
        return _string(getattr(self.cfg, "VOICE_OPERATOR_CLIENT_ID", "cli")).strip() or "cli"

    def _operator_client_mode(self):
        return _string(getattr(self.cfg, "VOICE_OPERATOR_CLIENT_MODE", "cli")).strip() or "cli"

    def _operator_role(self):
        return _string(getattr(self.cfg, "VOICE_OPERATOR_ROLE", "operator")).strip() or "operator"

    def _operator_scopes(self):
        return _normalize_scopes(getattr(self.cfg, "VOICE_OPERATOR_SCOPES", []))

    def _operator_logical_device_id(self):
        return _string(getattr(self.state, "logical_device_id", "")).strip() or _string(getattr(self.cfg, "DEVICE_ID", "")).strip()

    def _operator_device_id(self):
        return _string(self.state.node_id or getattr(self.cfg, "DEVICE_ID", "")).strip() or _string(getattr(self.cfg, "DEVICE_ID", "")).strip()

    def _resolve_connect_security_locked(self, token, nonce):
        auth = {"token": token}
        device = None
        device_auth_mode = _string(getattr(self.cfg, "VOICE_OPERATOR_DEVICE_AUTH_MODE", "")).strip()
        if not device_auth_mode:
            device_auth_mode = _string(getattr(self.cfg, "OPENCLAW_DEVICE_AUTH_MODE", "none")).strip() or "none"
        if device_auth_mode == "remote_signer_http":
            device = _request_remote_signature(
                self.cfg,
                self.state,
                token,
                nonce,
                client_id=self._operator_client_id(),
                client_mode=self._operator_client_mode(),
                role=self._operator_role(),
                scopes=self._operator_scopes(),
                logical_device_id=self._operator_logical_device_id(),
                device_name=_string(getattr(self.cfg, "DEVICE_NAME", "")).strip(),
            )
        elif device_auth_mode != "none":
            self._fail_locked("VOICE_CONFIG_ERROR", "unsupported voice device auth mode: " + device_auth_mode, False)
        return auth, device

    def _build_connect_params_locked(self, auth, device):
        client_id = self._operator_client_id()
        display_name = _string(getattr(self.cfg, "VOICE_OPERATOR_CLIENT_DISPLAY_NAME", "qpyclaw Voice Operator")).strip() or "qpyclaw Voice Operator"
        client_mode = self._operator_client_mode()
        role = self._operator_role()
        params = {
            "minProtocol": int(getattr(self.cfg, "OPENCLAW_MIN_PROTOCOL", 3)),
            "maxProtocol": int(getattr(self.cfg, "OPENCLAW_MAX_PROTOCOL", 3)),
            "client": {
                "id": client_id,
                "displayName": display_name,
                "version": _string(getattr(self.cfg, "FW_VERSION", "0.1.0")).strip() or "0.1.0",
                "platform": _string(getattr(self.cfg, "OPENCLAW_CLIENT_PLATFORM", "quectel")).strip() or "quectel",
                "deviceFamily": _string(getattr(self.cfg, "OPENCLAW_CLIENT_DEVICE_FAMILY", "quecpython")).strip() or "quecpython",
                "mode": client_mode,
            },
            "role": role,
            "scopes": self._operator_scopes(),
            "caps": list(getattr(self.cfg, "VOICE_OPERATOR_CAPS", []) or []),
            "commands": list(getattr(self.cfg, "VOICE_OPERATOR_COMMANDS", []) or []),
            "permissions": getattr(self.cfg, "VOICE_OPERATOR_PERMISSIONS", {}),
            "userAgent": _string(getattr(self.cfg, "VOICE_OPERATOR_USER_AGENT", "qpyclaw-node/0.1.0 voice")).strip() or "qpyclaw-node/0.1.0 voice",
            "device": device or {
                "id": self._operator_device_id(),
            },
        }
        if auth:
            params["auth"] = auth
        return params

    def _next_id_locked(self, prefix):
        self._seq += 1
        return str(prefix) + "_" + str(utime.ticks_ms()) + "_" + str(self._seq)

    def _close_locked(self, reason):
        self.last_close_reason = _string(reason).strip()
        self.last_close_ms = utime.ticks_ms()
        if self.online:
            self.last_disconnect_ms = self.last_close_ms
        self.online = False
        self.connected_at_ms = 0
        self.server_methods = []
        self.subscriptions = {}
        self.last_server_hello = None
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None

    def close(self, reason="manual-close"):
        self._acquire()
        try:
            self._close_locked(reason)
            return True
        finally:
            self._release()

    def _recv_frame_locked(self, timeout_ms):
        if self.ws is None:
            raise WsClosed("voice websocket closed")
        text = self.ws.recv_text(timeout_ms)
        return loads(text)

    def _send_frame_locked(self, frame):
        if self.ws is None:
            raise WsClosed("voice websocket closed")
        self.ws.send_text(dumps(frame))

    def _await_response_locked(self, request_id, timeout_ms):
        deadline = utime.ticks_add(utime.ticks_ms(), int(timeout_ms))
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            remaining = utime.ticks_diff(deadline, utime.ticks_ms())
            frame = self._recv_frame_locked(remaining)
            if not isinstance(frame, dict):
                continue
            if frame.get("type") == "res" and frame.get("id") == request_id:
                return frame
            self._handle_async_frame_locked(frame, "", "")
        raise Exception("voice ack timeout")

    def _request_locked(self, method, params, timeout_ms):
        request_id = self._next_id_locked(method)
        frame = {
            "type": "req",
            "id": request_id,
            "method": method,
            "params": params,
        }
        self._send_frame_locked(frame)
        return self._await_response_locked(request_id, timeout_ms)

    def _wait_connect_challenge_locked(self):
        deadline = utime.ticks_add(utime.ticks_ms(), int(self._connect_timeout_sec() * 1000))
        while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
            remaining = utime.ticks_diff(deadline, utime.ticks_ms())
            frame = self._recv_frame_locked(remaining)
            if not isinstance(frame, dict):
                continue
            if frame.get("type") == "event" and frame.get("event") == "connect.challenge":
                self.last_event = "connect.challenge"
                self.last_event_ms = utime.ticks_ms()
                return frame.get("payload") or {}
        raise Exception("voice connect challenge timeout")

    def _method_supported_locked(self, method):
        methods = self.server_methods
        if not isinstance(methods, list) or not methods:
            return True
        return method in methods

    def _ensure_connected_locked(self):
        if not self._bool_value(getattr(self.cfg, "VOICE_ENABLED", False), False):
            self._fail_locked("VOICE_DISABLED", "voice dialog is disabled", False)
        if self.online and self.ws is not None:
            return True
        url = self._ws_url()
        if not url:
            self._fail_locked("VOICE_CONFIG_ERROR", "voice operator websocket url missing", False)
        token = self._operator_auth_token()
        if not token:
            self._fail_locked("VOICE_CONFIG_ERROR", "voice operator token missing", False)

        self._close_locked("reconnect")
        ws = WsClient()
        try:
            ws.connect(url, self._connect_timeout_sec())
            self.ws = ws
            challenge = self._wait_connect_challenge_locked()
            nonce = challenge.get("nonce") if isinstance(challenge, dict) else None
            if not nonce:
                self._fail_locked("VOICE_CONNECT_FAILED", "connect challenge missing nonce", True)
            auth, device = self._resolve_connect_security_locked(token, nonce)
            response = self._request_locked(
                "connect",
                self._build_connect_params_locked(auth, device),
                self._ack_timeout_ms(),
            )
            if not response.get("ok"):
                error = response.get("error") or {}
                code = error.get("code") if isinstance(error, dict) else "VOICE_CONNECT_FAILED"
                message = error.get("message") if isinstance(error, dict) else str(error)
                self._fail_locked(_string(code).strip() or "VOICE_CONNECT_FAILED", _string(message).strip() or "voice connect failed", True)
            payload = response.get("payload") or {}
            self.online = True
            self.connected_at_ms = utime.ticks_ms()
            self.last_connect_ms = self.connected_at_ms
            self.last_error = ""
            self.last_error_code = ""
            self.last_server_hello = payload
            features = payload.get("features") or {}
            methods = features.get("methods") if isinstance(features, dict) else None
            if isinstance(methods, list):
                self.server_methods = methods
            else:
                self.server_methods = []
            return True
        except Exception as e:
            if self.last_error_code == "":
                self.last_error_code = "VOICE_CONNECT_FAILED"
                self.last_error = str(e)
                self.last_error_ms = utime.ticks_ms()
            self._close_locked("connect-failed")
            raise

    def _subscribe_locked(self, session_key):
        if session_key in self.subscriptions:
            return {
                "ok": True,
                "session_key": session_key,
                "status": "cached",
            }
        if not self._method_supported_locked("chat.subscribe"):
            return {
                "ok": False,
                "session_key": session_key,
                "status": "unsupported",
            }
        try:
            response = self._request_locked(
                "chat.subscribe",
                {"sessionKey": session_key},
                self._ack_timeout_ms(),
            )
            if bool(response.get("ok")):
                self.subscriptions[session_key] = utime.ticks_ms()
                self.last_subscribe_error = ""
                return {
                    "ok": True,
                    "session_key": session_key,
                    "status": "subscribed",
                    "payload": response.get("payload") or {},
                }
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_SUBSCRIBE_FAILED"
            message = error.get("message") if isinstance(error, dict) else str(error)
            self.last_subscribe_error = (_string(code).strip() or "CHAT_SUBSCRIBE_FAILED") + ": " + (_string(message).strip() or "subscribe failed")
            return {
                "ok": False,
                "session_key": session_key,
                "status": "failed",
                "error": self.last_subscribe_error,
            }
        except Exception as e:
            self.last_subscribe_error = str(e)
            return {
                "ok": False,
                "session_key": session_key,
                "status": "failed",
                "error": str(e),
            }

    def _history_locked(self, session_key, history_limit):
        if not self._method_supported_locked("chat.history"):
            self._fail_locked("VOICE_UNSUPPORTED", "chat.history not supported by gateway", False)
        params = {
            "sessionKey": session_key,
            "limit": int(history_limit),
        }
        response = self._request_locked("chat.history", params, self._ack_timeout_ms())
        if not response.get("ok"):
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_HISTORY_FAILED"
            message = error.get("message") if isinstance(error, dict) else str(error)
            self._fail_locked(_string(code).strip() or "CHAT_HISTORY_FAILED", _string(message).strip() or "chat history failed", False)
        payload = response.get("payload") or {}
        self.last_history_count = len(self._extract_history_messages_locked(payload))
        self.last_history_poll_ms = utime.ticks_ms()
        return payload

    def _send_chat_locked(self, message, session_key, idempotency_key):
        if not self._method_supported_locked("chat.send"):
            self._fail_locked("VOICE_UNSUPPORTED", "chat.send not supported by gateway", False)
        params = {
            "sessionKey": session_key,
            "message": message,
        }
        if idempotency_key:
            params["idempotencyKey"] = idempotency_key
        response = self._request_locked("chat.send", params, self._ack_timeout_ms())
        if not response.get("ok"):
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_SEND_FAILED"
            message_text = error.get("message") if isinstance(error, dict) else str(error)
            self._fail_locked(_string(code).strip() or "CHAT_SEND_FAILED", _string(message_text).strip() or "chat send failed", False)
        payload = response.get("payload") or {}
        self.last_run_id = _string(payload.get("runId")).strip()
        self.last_chat_status = _string(payload.get("status")).strip()
        self.last_sent_message = message
        self.last_sent_session_key = session_key
        self.last_turn_id = idempotency_key
        return payload

    def _abort_locked(self, session_key):
        if not self._method_supported_locked("chat.abort"):
            self._fail_locked("VOICE_UNSUPPORTED", "chat.abort not supported by gateway", False)
        response = self._request_locked(
            "chat.abort",
            {"sessionKey": session_key},
            self._ack_timeout_ms(),
        )
        if not response.get("ok"):
            error = response.get("error") or {}
            code = error.get("code") if isinstance(error, dict) else "CHAT_ABORT_FAILED"
            message = error.get("message") if isinstance(error, dict) else str(error)
            self._fail_locked(_string(code).strip() or "CHAT_ABORT_FAILED", _string(message).strip() or "chat abort failed", False)
        self.last_chat_status = "aborted"
        return response.get("payload") or {}

    def _event_matches_locked(self, payload, session_key, run_id):
        if not isinstance(payload, dict):
            return True
        session_value = payload.get("sessionKey")
        if session_value in (None, ""):
            session_value = payload.get("session_key")
        if session_value not in (None, "") and session_key and _string(session_value).strip() != session_key:
            return False
        run_value = payload.get("runId")
        if run_value in (None, ""):
            run_value = payload.get("run_id")
        if run_value not in (None, "") and run_id and _string(run_value).strip() != run_id:
            return False
        nested = payload.get("message")
        if nested is None:
            nested = payload.get("data")
        if nested is None:
            nested = payload.get("chat")
        if isinstance(nested, dict):
            return self._event_matches_locked(nested, session_key, run_id)
        return True

    def _handle_async_frame_locked(self, frame, session_key, run_id):
        if not isinstance(frame, dict):
            return False
        frame_type = frame.get("type")
        if frame_type == "event":
            event_name = _string(frame.get("event")).strip()
            self.last_event = event_name
            self.last_event_ms = utime.ticks_ms()
            if event_name == "chat":
                payload = frame.get("payload") or {}
                return self._event_matches_locked(payload, session_key, run_id)
        return False

    def _extract_history_messages_locked(self, payload):
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ("messages", "items", "history", "entries", "rows", "timeline"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for key in ("data", "session", "chat", "result", "payload"):
            value = payload.get(key)
            if isinstance(value, dict):
                items = self._extract_history_messages_locked(value)
                if items:
                    return items
        return []

    def _collect_text_locked(self, value, depth):
        if depth > 3 or value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, list):
            parts = []
            for item in value:
                text = self._collect_text_locked(item, depth + 1)
                text = _string(text).strip()
                if text:
                    parts.append(text)
            return "\n".join(parts)
        if isinstance(value, dict):
            for key in ("text", "message", "markdown", "body", "value", "contentText", "outputText"):
                if key in value:
                    text = self._collect_text_locked(value.get(key), depth + 1)
                    if _string(text).strip():
                        return text
            for key in ("content", "parts", "segments", "items"):
                if key in value:
                    text = self._collect_text_locked(value.get(key), depth + 1)
                    if _string(text).strip():
                        return text
        return ""

    def _message_role_locked(self, item):
        if not isinstance(item, dict):
            return ""
        for key in ("role", "authorRole", "senderRole", "messageRole"):
            value = item.get(key)
            if value not in (None, ""):
                return _string(value).strip().lower()
        for key in ("author", "sender", "meta"):
            value = item.get(key)
            if isinstance(value, dict):
                role = self._message_role_locked(value)
                if role:
                    return role
        return ""

    def _message_text_locked(self, item):
        if not isinstance(item, dict):
            return _string(item).strip()
        for key in ("text", "message", "content", "body", "value", "outputText"):
            if key in item:
                text = self._collect_text_locked(item.get(key), 0)
                if _string(text).strip():
                    return _string(text).strip()
        return ""

    def _message_id_locked(self, item):
        if not isinstance(item, dict):
            return ""
        for key in ("id", "messageId", "cid", "uuid"):
            value = item.get(key)
            if value not in (None, ""):
                return _string(value).strip()
        return ""

    def _message_fingerprint_locked(self, item):
        message_id = self._message_id_locked(item)
        text = self._message_text_locked(item)
        if len(text) > 160:
            text = text[:160]
        if message_id:
            return message_id + "|" + text
        role = self._message_role_locked(item)
        timestamp = ""
        if isinstance(item, dict):
            for key in ("ts", "createdAt", "createdAtMs", "timestamp", "time"):
                value = item.get(key)
                if value not in (None, ""):
                    timestamp = _string(value).strip()
                    break
        return role + "|" + timestamp + "|" + text

    def _assistant_role_locked(self, role):
        role_text = _string(role).strip().lower()
        return role_text in ("assistant", "agent", "model")

    def _text_lines_locked(self, text):
        raw = _string(text)
        if not raw:
            return []
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.split("\n")

    def _strip_voice_directive_locked(self, text):
        reply_text = _string(text)
        directive = {}
        lines = self._text_lines_locked(reply_text)
        first_index = -1
        index = 0
        while index < len(lines):
            if _string(lines[index]).strip():
                first_index = index
                break
            index += 1
        if first_index >= 0:
            first_line = _string(lines[first_index]).strip()
            if first_line[:1] == "{" and first_line[-1:] == "}":
                try:
                    maybe = loads(first_line)
                    if isinstance(maybe, dict):
                        directive = maybe
                        lines.pop(first_index)
                        reply_text = "\n".join(lines).strip()
                except Exception:
                    pass
        return reply_text, directive

    def _find_reply_locked(self, payload, seen):
        messages = self._extract_history_messages_locked(payload)
        self.last_history_count = len(messages)
        candidate = None
        for item in messages:
            fingerprint = self._message_fingerprint_locked(item)
            if fingerprint in seen:
                continue
            seen[fingerprint] = True
            text = self._message_text_locked(item)
            role = self._message_role_locked(item)
            if text and self._assistant_role_locked(role):
                candidate = {
                    "fingerprint": fingerprint,
                    "message_id": self._message_id_locked(item),
                    "role": role,
                    "text": text,
                    "raw": item,
                }
        return candidate

    def snapshot(self):
        self._acquire()
        try:
            return {
                "enabled": bool(getattr(self.cfg, "VOICE_ENABLED", False)),
                "online": self.online,
                "connected_at_ms": self.connected_at_ms,
                "last_connect_ms": self.last_connect_ms,
                "last_disconnect_ms": self.last_disconnect_ms,
                "last_close_reason": self.last_close_reason,
                "last_close_ms": self.last_close_ms,
                "last_error_code": self.last_error_code,
                "last_error": self.last_error,
                "last_error_ms": self.last_error_ms,
                "last_event": self.last_event,
                "last_event_ms": self.last_event_ms,
                "last_run_id": self.last_run_id,
                "last_turn_id": self.last_turn_id,
                "last_sent_session_key": self.last_sent_session_key,
                "last_reply_text": self.last_reply_text,
                "last_reply_message_id": self.last_reply_message_id,
                "last_voice_directive": self.last_voice_directive,
                "last_history_count": self.last_history_count,
                "last_chat_status": self.last_chat_status,
                "last_history_poll_ms": self.last_history_poll_ms,
                "last_subscribe_error": self.last_subscribe_error,
                "last_chat_duration_ms": self.last_chat_duration_ms,
                "last_chat_event_count": self.last_chat_event_count,
                "last_chat_history_polls": self.last_chat_history_polls,
                "main_session_key": self._session_key(""),
                "operator_ws_url": self._ws_url(),
                "operator_role": _string(getattr(self.cfg, "VOICE_OPERATOR_ROLE", "operator")).strip() or "operator",
                "operator_scopes": _normalize_scopes(getattr(self.cfg, "VOICE_OPERATOR_SCOPES", [])),
                "subscriptions": [name for name in self.subscriptions.keys()],
                "server_methods": self.server_methods,
            }
        finally:
            self._release()

    def chat(self, message, session_key="", timeout_ms=None, idempotency_key="", subscribe=None, history_limit=None):
        self._acquire()
        try:
            message_text = _string(message).strip()
            if not message_text:
                self._fail_locked("CHAT_SEND_FAILED", "message required", False)
            session_key_text = self._session_key(session_key)
            timeout_value = self._chat_timeout_ms(timeout_ms)
            poll_ms = self._chat_poll_ms()
            history_limit_value = self._history_limit(history_limit)
            subscribe_enabled = self._bool_value(subscribe, getattr(self.cfg, "VOICE_CHAT_SUBSCRIBE", True))
            turn_id = _string(idempotency_key).strip()
            if not turn_id:
                turn_id = self._next_id_locked("voice_turn")
            started = utime.ticks_ms()

            self._ensure_connected_locked()
            baseline = {}
            baseline_payload = self._history_locked(session_key_text, history_limit_value)
            baseline_messages = self._extract_history_messages_locked(baseline_payload)
            index = 0
            while index < len(baseline_messages):
                baseline[self._message_fingerprint_locked(baseline_messages[index])] = True
                index += 1

            subscribe_result = None
            if subscribe_enabled:
                subscribe_result = self._subscribe_locked(session_key_text)

            send_payload = self._send_chat_locked(message_text, session_key_text, turn_id)
            run_id = _string(send_payload.get("runId")).strip()
            history_polls = 0
            chat_events = 0
            deadline = utime.ticks_add(utime.ticks_ms(), timeout_value)

            while utime.ticks_diff(deadline, utime.ticks_ms()) > 0:
                remaining = utime.ticks_diff(deadline, utime.ticks_ms())
                wait_ms = remaining
                if wait_ms > poll_ms:
                    wait_ms = poll_ms
                if wait_ms <= 0:
                    wait_ms = 1
                try:
                    frame = self._recv_frame_locked(wait_ms)
                    if self._handle_async_frame_locked(frame, session_key_text, run_id):
                        chat_events += 1
                except WsTimeout:
                    pass
                payload = self._history_locked(session_key_text, history_limit_value)
                history_polls += 1
                candidate = self._find_reply_locked(payload, baseline)
                if candidate is not None:
                    reply_text, directive = self._strip_voice_directive_locked(candidate.get("text"))
                    self.last_reply_text = reply_text
                    self.last_reply_message_id = candidate.get("message_id") or ""
                    self.last_voice_directive = directive
                    self.last_chat_status = "ok"
                    self.last_chat_duration_ms = utime.ticks_diff(utime.ticks_ms(), started)
                    self.last_chat_event_count = chat_events
                    self.last_chat_history_polls = history_polls
                    return {
                        "ok": True,
                        "status": "ok",
                        "session_key": session_key_text,
                        "turn_id": turn_id,
                        "run_id": run_id,
                        "reply_text": reply_text,
                        "voice_directive": directive,
                        "assistant_message_id": self.last_reply_message_id,
                        "chat_events": chat_events,
                        "history_polls": history_polls,
                        "duration_ms": self.last_chat_duration_ms,
                        "subscribe": subscribe_result,
                    }

            self.last_chat_status = "timeout"
            self.last_chat_duration_ms = utime.ticks_diff(utime.ticks_ms(), started)
            self.last_chat_event_count = chat_events
            self.last_chat_history_polls = history_polls
            self._fail_locked("CHAT_TIMEOUT", "chat reply not received before timeout", False)
        finally:
            self._release()

    def abort(self, session_key=""):
        self._acquire()
        try:
            session_key_text = self._session_key(session_key)
            self._ensure_connected_locked()
            payload = self._abort_locked(session_key_text)
            return {
                "ok": True,
                "status": "aborted",
                "session_key": session_key_text,
                "run_id": self.last_run_id,
                "payload": payload,
            }
        finally:
            self._release()

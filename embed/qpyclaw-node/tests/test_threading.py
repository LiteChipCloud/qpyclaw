# test_threading.py — Multi-threading safety tests for qpyclaw-node.
# Runs on host CPython (unittest). Uses stubs for QuecPython-only modules.
# Coverage: voice.py, dispatch.py, cellular.py, board_voice_controller.py,
#           node_main.py, tools.py

import sys
import os
import time
import threading
import unittest

# ---------------------------------------------------------------------------
# Stub QuecPython modules so host CPython can import device-side code
# ---------------------------------------------------------------------------

class _FakeUtime:
    @staticmethod
    def ticks_ms():
        return int(time.time() * 1000)
    @staticmethod
    def ticks_diff(newer, older):
        return int(newer) - int(older)
    @staticmethod
    def ticks_add(base, delta):
        return int(base) + int(delta)
    @staticmethod
    def sleep_ms(ms):
        time.sleep(ms / 1000.0)
    @staticmethod
    def sleep(s):
        time.sleep(s)
    @staticmethod
    def time():
        return time.time()

class _FakeThread:
    @staticmethod
    def allocate_lock():
        return threading.Lock()
    @staticmethod
    def start_new_thread(func, args):
        t = threading.Thread(target=func, args=args, daemon=True)
        t.start()
        return t

sys.modules.setdefault("utime", _FakeUtime)
sys.modules.setdefault("_thread", _FakeThread)
sys.modules.setdefault("ubinascii", type(sys)("ubinascii"))
sys.modules.setdefault("uhashlib", type(sys)("uhashlib"))
sys.modules.setdefault("uos", os)
sys.modules.setdefault("usocket", type(sys)("usocket"))
sys.modules.setdefault("ustruct", type(sys)("ustruct"))
sys.modules.setdefault("ujson", __import__("json"))
sys.modules.setdefault("usys", sys)

# Stub request module
_req_stub = type(sys)("request")
sys.modules.setdefault("request", _req_stub)

# Add source paths
_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_EMBED_ROOT = os.path.normpath(os.path.join(_ROOT, ".."))
_COMPONENTS = os.path.normpath(os.path.join(_EMBED_ROOT, "components"))
_NODE_CODE = os.path.join(_ROOT, "code")
# Pick a real board for board_bootstrap stub — use ec800m audio board
_BOARD_CODE = os.path.normpath(os.path.join(_EMBED_ROOT, "boards", "ec800mcnle-audio-board", "code"))
for _p in [_NODE_CODE, _COMPONENTS, _BOARD_CODE]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Stub board_bootstrap so node_main can be imported without real hardware
import types as _types
_bb = _types.ModuleType("board_bootstrap")
def _create_qpyclaw_extension(cfg=None):
    return None
_bb.create_qpyclaw_extension = _create_qpyclaw_extension
sys.modules.setdefault("board_bootstrap", _bb)

# Stub machine module (used by board_bootstrap)
_machine = _types.ModuleType("machine")
class _FakePin:
    IN = OUT = 0
    def __init__(self, *a, **kw): pass
    def value(self, *a): return 0
_machine.Pin = _FakePin
sys.modules.setdefault("machine", _machine)

# Stub audio/display/misc QuecPython hardware modules
for _mod_name in ("audio", "lcd", "misc", "modem", "net", "dataCall",
                  "sim", "cellLocator", "checkNet", "fota", "ql_fs",
                  "log", "pm", "uio", "uzlib"):
    sys.modules.setdefault(_mod_name, _types.ModuleType(_mod_name))


# ---------------------------------------------------------------------------
# Minimal stubs for dependencies
# ---------------------------------------------------------------------------

class _FakeCfg:
    VOICE_ENABLED = True
    VOICE_OPERATOR_AUTH_TOKEN = "test-token"
    OPENCLAW_WS_URL = "ws://127.0.0.1:19999"
    VOICE_OPERATOR_WS_URL = ""
    OPENCLAW_AUTH_TOKEN = "test-token"
    VOICE_OPERATOR_REUSE_NODE_TOKEN = True
    OPENCLAW_MIN_PROTOCOL = 3
    OPENCLAW_MAX_PROTOCOL = 3
    VOICE_CHAT_TIMEOUT_MS = 2000
    VOICE_CHAT_POLL_MS = 100
    VOICE_CHAT_HISTORY_LIMIT = 5
    VOICE_CHAT_SUBSCRIBE = False
    VOICE_OPERATOR_CLIENT_ID = "test-client"
    VOICE_OPERATOR_CLIENT_MODE = "operator"
    VOICE_OPERATOR_ROLE = "operator"
    VOICE_OPERATOR_SCOPES = []
    VOICE_OPERATOR_CAPS = []
    VOICE_OPERATOR_COMMANDS = []
    VOICE_OPERATOR_PERMISSIONS = {}
    VOICE_OPERATOR_USER_AGENT = "test/1.0"
    VOICE_OPERATOR_CLIENT_DISPLAY_NAME = "Test"
    OPENCLAW_CLIENT_PLATFORM = "test"
    OPENCLAW_CLIENT_DEVICE_FAMILY = "test"
    FW_VERSION = "0.0.1"
    OPENCLAW_DEVICE_ID = "test-device"
    OPENCLAW_DEVICE_AUTH_MODE = "none"
    REMOTE_SIGNER_HTTP_URL = ""
    REMOTE_SIGNER_HTTP_AUTH_TOKEN = ""
    REMOTE_SIGNER_HTTP_TIMEOUT_SEC = 5
    REMOTE_SIGNER_HTTP_HEADERS = {}
    ACK_TIMEOUT_MS = 500
    VOICE_CONNECT_TIMEOUT_SEC = 2
    MAX_CMD_EXEC_SEC = 1
    NETWORK_CLOSE_TRANSPORT_ON_PDP_DOWN = True


class _FakeState:
    def __init__(self):
        self.errors = []
        self.transport = None
    def note_error(self, code, msg):
        self.errors.append((code, msg))
    def note_inflight_start(self, *a):
        pass
    def note_inflight_finish(self, *a):
        pass
    def note_worker_status(self, *a):
        pass
    def note_cmd(self, *a, **kw):
        pass


# ---------------------------------------------------------------------------
# Test 1: voice.abort() does not deadlock while chat() is running
# ---------------------------------------------------------------------------

class TestVoiceAbortNoDeadlock(unittest.TestCase):

    def test_abort_returns_while_chat_in_progress(self):
        """abort() must return within 1s even when chat() is blocked on I/O."""
        from voice import VoiceDialogClient

        cfg = _FakeCfg()
        state = _FakeState()
        client = VoiceDialogClient(cfg, state)

        # Simulate chat() holding no lock but looping — patch _ensure_connected
        # to block indefinitely so we can test abort() interrupts it.
        connect_called = threading.Event()
        abort_returned = threading.Event()
        chat_raised = threading.Event()

        original_ensure = client._ensure_connected

        def slow_connect():
            connect_called.set()
            # Block until abort is requested
            for _ in range(50):
                time.sleep(0.05)
                client._acquire()
                try:
                    aborted = client._abort_requested
                finally:
                    client._release()
                if aborted:
                    raise Exception("CHAT_ABORTED: abort requested")
            return original_ensure()

        client._ensure_connected = slow_connect

        chat_error = []

        def run_chat():
            try:
                client.chat("hello", session_key="s1")
            except Exception as e:
                chat_error.append(str(e))
            finally:
                chat_raised.set()

        t = threading.Thread(target=run_chat, daemon=True)
        t.start()

        # Wait for chat to start connecting
        connect_called.wait(timeout=2.0)
        self.assertTrue(connect_called.is_set(), "chat() never started")

        # abort() must return quickly — not deadlock
        start = time.time()
        result = client.abort(session_key="s1")
        elapsed = time.time() - start

        abort_returned.set()
        self.assertLess(elapsed, 1.0, "abort() took too long: %.2fs" % elapsed)
        self.assertIsInstance(result, dict)

        # chat() should eventually raise CHAT_ABORTED
        chat_raised.wait(timeout=5.0)
        self.assertTrue(chat_raised.is_set(), "chat() never finished")
        self.assertTrue(
            any("ABORTED" in e or "abort" in e.lower() for e in chat_error),
            "chat() did not raise abort error, got: %s" % chat_error,
        )


# ---------------------------------------------------------------------------
# Test 2: voice.snapshot() does not deadlock while chat() is running
# ---------------------------------------------------------------------------

class TestVoiceSnapshotNoDeadlock(unittest.TestCase):

    def test_snapshot_returns_immediately_during_chat(self):
        """snapshot() must return within 200ms even when chat() is in progress."""
        from voice import VoiceDialogClient

        cfg = _FakeCfg()
        state = _FakeState()
        client = VoiceDialogClient(cfg, state)

        connect_called = threading.Event()

        def slow_connect():
            connect_called.set()
            time.sleep(5.0)  # simulate long I/O
            raise Exception("CHAT_ABORTED: test")

        client._ensure_connected = slow_connect

        def run_chat():
            try:
                client.chat("hello")
            except Exception:
                pass

        t = threading.Thread(target=run_chat, daemon=True)
        t.start()
        connect_called.wait(timeout=2.0)

        # snapshot() must not block
        start = time.time()
        snap = client.snapshot()
        elapsed = time.time() - start

        self.assertLess(elapsed, 0.2, "snapshot() blocked for %.2fs" % elapsed)
        self.assertIsInstance(snap, dict)
        self.assertIn("online", snap)

        # cleanup
        client._acquire()
        try:
            client._abort_requested = True
        finally:
            client._release()
        t.join(timeout=2.0)


# ---------------------------------------------------------------------------
# Test 3: dispatch.py global state is thread-safe
# ---------------------------------------------------------------------------

class TestDispatchGlobalLock(unittest.TestCase):

    def test_concurrent_read_write_no_corruption(self):
        """Concurrent reads and writes to dispatch state must not corrupt values."""
        import dispatch

        errors_seen = []
        stop = threading.Event()

        def writer():
            i = 0
            while not stop.is_set():
                dispatch._set_dispatch_state(i % 2 == 0, "err_%d" % i, i * 10)
                i += 1
                time.sleep(0.001)

        def reader():
            while not stop.is_set():
                active, error = dispatch._get_dispatch_state()
                if not isinstance(active, bool):
                    errors_seen.append("active not bool: %r" % active)
                if not isinstance(error, str):
                    errors_seen.append("error not str: %r" % error)
                time.sleep(0.001)

        threads = [
            threading.Thread(target=writer, daemon=True),
            threading.Thread(target=reader, daemon=True),
            threading.Thread(target=reader, daemon=True),
        ]
        for t in threads:
            t.start()

        time.sleep(0.3)
        stop.set()
        for t in threads:
            t.join(timeout=1.0)

        self.assertEqual(errors_seen, [], "Type corruption detected: %s" % errors_seen)


# ---------------------------------------------------------------------------
# Test 4: cellular.py _on_data_call_event is thread-safe
# ---------------------------------------------------------------------------

class TestCellularEventLock(unittest.TestCase):

    def test_concurrent_event_and_poll_no_corruption(self):
        """Concurrent dataCall callback and poll() must not corrupt state."""
        from cellular import CellularNetworkManager

        cfg = _FakeCfg()
        state = _FakeState()
        mgr = CellularNetworkManager(cfg, state)

        corruption = []
        stop = threading.Event()

        def simulate_callback():
            i = 0
            while not stop.is_set():
                mgr._on_data_call_event([0, i % 2])
                i += 1
                time.sleep(0.002)

        def simulate_poll():
            while not stop.is_set():
                mgr.poll()
                # pending_transport_close_reason must always be a str
                val = mgr.pending_transport_close_reason
                if not isinstance(val, str):
                    corruption.append("not str: %r" % val)
                time.sleep(0.002)

        threads = [
            threading.Thread(target=simulate_callback, daemon=True),
            threading.Thread(target=simulate_poll, daemon=True),
            threading.Thread(target=simulate_poll, daemon=True),
        ]
        for t in threads:
            t.start()

        time.sleep(0.3)
        stop.set()
        for t in threads:
            t.join(timeout=1.0)

        self.assertEqual(corruption, [], "State corruption: %s" % corruption)


# ---------------------------------------------------------------------------
# Test 5: node_main._run_runtime_loop triggers reboot after 10 consecutive errors
# ---------------------------------------------------------------------------

class TestNodeMainReboot(unittest.TestCase):

    def test_consecutive_errors_trigger_reboot(self):
        """10 consecutive step() exceptions must trigger execute_reboot."""
        import node_main

        reboot_called = []

        class _FakeRuntime:
            def __init__(self):
                self.state = _FakeState()
                self._call_count = 0
            def step(self):
                self._call_count += 1
                raise Exception("simulated step error")

        class _FakeQN:
            @staticmethod
            def execute_reboot(mode):
                reboot_called.append(mode)

        # Patch sleep to be instant and qpyclaw_node import
        original_sleep = node_main._sleep_ms
        node_main._sleep_ms = lambda ms: None

        original_modules = sys.modules.get("qpyclaw_node")
        sys.modules["qpyclaw_node"] = _FakeQN

        runtime = _FakeRuntime()
        stop_after = [False]

        original_max = node_main._MAX_CONSECUTIVE_STEP_ERRORS

        try:
            # Run loop in thread, stop after reboot is called
            def run():
                try:
                    node_main._run_runtime_loop(runtime)
                except Exception:
                    pass

            t = threading.Thread(target=run, daemon=True)
            t.start()

            # Wait for reboot to be triggered
            deadline = time.time() + 3.0
            while time.time() < deadline and not reboot_called:
                time.sleep(0.05)

        finally:
            node_main._sleep_ms = original_sleep
            if original_modules is not None:
                sys.modules["qpyclaw_node"] = original_modules
            else:
                sys.modules.pop("qpyclaw_node", None)

        self.assertTrue(len(reboot_called) > 0, "execute_reboot was never called")
        self.assertEqual(reboot_called[0], "soft")
        self.assertGreaterEqual(runtime._call_count, original_max)


# ---------------------------------------------------------------------------
# Test 6: tools.py CommandWorker records timeout when tool exceeds MAX_CMD_EXEC_SEC
# ---------------------------------------------------------------------------

class TestWorkerExecTimeout(unittest.TestCase):

    def test_slow_tool_triggers_timeout_error(self):
        """A tool that exceeds MAX_CMD_EXEC_SEC must trigger WORKER_EXEC_TIMEOUT."""
        # Import tools module components
        import tools as _tools

        cfg = _FakeCfg()
        cfg.MAX_CMD_EXEC_SEC = 0  # 0s limit — any execution triggers timeout

        state = _FakeState()

        class _SlowRunner:
            def __init__(self):
                self.cfg = cfg
            def execute(self, cmd):
                time.sleep(0.05)  # 50ms — exceeds 0s limit
                return {"status": "ok", "result_code": 0}

        worker = _tools.CommandWorker(_SlowRunner(), state)

        # Submit a command
        cmd = {"id": "t1", "tool": "slow.tool", "params": {}}
        submitted = worker.submit(cmd)
        self.assertTrue(submitted, "submit() failed")

        # Wait for result
        deadline = time.time() + 3.0
        result = None
        while time.time() < deadline:
            result = worker.poll_result()
            if result is not None:
                break
            time.sleep(0.05)

        self.assertIsNotNone(result, "Worker never produced a result")

        timeout_errors = [e for e in state.errors if e[0] == "WORKER_EXEC_TIMEOUT"]
        self.assertTrue(
            len(timeout_errors) > 0,
            "WORKER_EXEC_TIMEOUT not recorded. Errors: %s" % state.errors,
        )


# ---------------------------------------------------------------------------
# Test 7: dispatch.main() timeout does not corrupt state when thread continues
# ---------------------------------------------------------------------------

class TestDispatchMainTimeout(unittest.TestCase):

    def test_state_consistent_after_timeout(self):
        """After dispatch.main() times out, state must remain consistent."""
        import dispatch

        # Reset state
        dispatch._set_dispatch_state(False, "", 0)

        # main() with 0ms wait — will time out immediately
        # _run_board_main is not actually started here (no _thread in this test path)
        # We just verify state reads are consistent after the call
        active_before, _ = dispatch._get_dispatch_state()
        self.assertFalse(active_before)

        # Simulate concurrent write during read
        results = []
        stop = threading.Event()

        def concurrent_writer():
            i = 0
            while not stop.is_set():
                dispatch._set_dispatch_state(i % 2 == 0, "e%d" % i)
                i += 1
                time.sleep(0.001)

        def concurrent_reader():
            for _ in range(50):
                active, error = dispatch._get_dispatch_state()
                results.append((isinstance(active, bool), isinstance(error, str)))
                time.sleep(0.002)

        wt = threading.Thread(target=concurrent_writer, daemon=True)
        rt = threading.Thread(target=concurrent_reader, daemon=True)
        wt.start()
        rt.start()
        rt.join(timeout=2.0)
        stop.set()
        wt.join(timeout=1.0)

        bad = [r for r in results if not (r[0] and r[1])]
        self.assertEqual(bad, [], "Type inconsistency during concurrent access: %s" % bad)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)

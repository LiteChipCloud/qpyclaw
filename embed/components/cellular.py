# cellular.py — Cellular network management for QuecPython devices.
# Extracted from qpyclaw_node.py as a reusable component.

import utime


# ---------------------------------------------------------------------------
# Inline utilities (duplicated to avoid extra import on constrained devices)
# ---------------------------------------------------------------------------

def safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


def safe_call(func, *args):
    if not func:
        return None
    try:
        return func(*args)
    except Exception:
        return None


def ok_value(value):
    return value not in (None, -1, "")


def mask_value(value, enabled):
    if (not enabled) or (not ok_value(value)):
        return value
    text = str(value)
    if len(text) <= 8:
        return text
    return text[:4] + ("*" * (len(text) - 8)) + text[-4:]


def wall_time_ms():
    try:
        return int(utime.time() * 1000)
    except Exception:
        return 0


def _sleep_ms(delay_ms):
    value = int(delay_ms or 0)
    if value <= 0:
        return
    if hasattr(utime, "sleep_ms"):
        utime.sleep_ms(value)
        return
    utime.sleep(value / 1000.0)


def safe_attr_call(module, names, *args):
    if not module:
        return None, ""
    for name in names:
        if hasattr(module, name):
            return safe_call(getattr(module, name), *args), name
    return None, ""


def measure_step(step_name, timings, func, *args):
    started = utime.ticks_ms()
    result = func(*args)
    if isinstance(timings, dict):
        timings[step_name] = utime.ticks_diff(utime.ticks_ms(), started)
    return result


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_reg_entry(entry):
    if (not isinstance(entry, (list, tuple))) or len(entry) < 6:
        return None
    return {
        "state": entry[0],
        "lac": entry[1],
        "cid": entry[2],
        "rat": entry[3],
        "reject_cause": entry[4],
        "psc": entry[5],
    }


def parse_operator_info(raw):
    if (not isinstance(raw, (list, tuple))) or len(raw) < 4:
        return None
    return {
        "long_name": raw[0],
        "short_name": raw[1],
        "mcc": raw[2],
        "mnc": raw[3],
    }


def parse_pdp_context(raw, ip_type):
    if (not isinstance(raw, (list, tuple))) or len(raw) < 5:
        return None
    return {
        "ip_type": ip_type,
        "state": raw[0],
        "reconnect": raw[1],
        "ip_address": raw[2],
        "dns_primary": raw[3],
        "dns_secondary": raw[4],
    }


def parse_data_context(raw):
    if (not isinstance(raw, (list, tuple))) or len(raw) < 3:
        return None
    ctx = {
        "profile_id": raw[0],
        "ip_type_code": raw[1],
        "contexts": [],
    }
    if raw[1] == 2 and len(raw) >= 4:
        ipv4 = parse_pdp_context(raw[2], "IP")
        ipv6 = parse_pdp_context(raw[3], "IPV6")
        if ipv4:
            ctx["contexts"].append(ipv4)
        if ipv6:
            ctx["contexts"].append(ipv6)
    else:
        ip_type = "IPV6" if raw[1] == 1 else "IP"
        parsed = parse_pdp_context(raw[2], ip_type)
        if parsed:
            ctx["contexts"].append(parsed)

    preferred = None
    for item in ctx["contexts"]:
        if item.get("state") == 1:
            preferred = item
            break
    if preferred is None and ctx["contexts"]:
        preferred = ctx["contexts"][0]

    if preferred:
        ctx["cid_preferred"] = ctx["profile_id"]
        ctx["ip_type"] = preferred.get("ip_type")
        ctx["ip_address"] = preferred.get("ip_address")
        ctx["cid"] = ctx["profile_id"]
        ctx["state"] = preferred.get("state")
        ctx["source"] = "dataCall.getInfo"
    return ctx


def _signal_quality(csq):
    if not isinstance(csq, int) or csq < 0:
        return "unknown"
    if csq >= 20:
        return "good"
    if csq >= 10:
        return "fair"
    return "weak"


# ---------------------------------------------------------------------------
# Gather functions — probe hardware and return structured dicts
# ---------------------------------------------------------------------------

def gather_modem_info(cfg, mask_sensitive):
    modem = safe_import("modem")
    info = {
        "device_id": cfg.DEVICE_ID,
        "device_name": getattr(cfg, "DEVICE_NAME", ""),
        "device_model_hint": getattr(cfg, "DEVICE_MODEL_HINT", ""),
        "board_profile": getattr(cfg, "BOARD_PROFILE", ""),
        "tenant_id": cfg.TENANT_ID,
        "access_mode": cfg.ACCESS_MODE,
        "fw_version_config": cfg.FW_VERSION,
        "ts": wall_time_ms(),
    }
    if modem:
        model = safe_call(getattr(modem, "getDevModel", None))
        imei = safe_call(getattr(modem, "getDevImei", None))
        fw_version = safe_call(getattr(modem, "getDevFwVersion", None))
        sn = safe_call(getattr(modem, "getDevSN", None))
        product_id = safe_call(getattr(modem, "getDevProductId", None))
        mac = safe_call(getattr(modem, "getDevMAC", None))
        if ok_value(model):
            info["module_model"] = model
        if ok_value(imei):
            info["imei"] = mask_value(imei, mask_sensitive)
        if ok_value(fw_version):
            info["firmware_version"] = fw_version
        if ok_value(sn):
            info["serial_number"] = mask_value(sn, mask_sensitive)
        if ok_value(product_id):
            info["product_id"] = product_id
        if ok_value(mac):
            info["mac_address"] = mask_value(mac, mask_sensitive)
    return info


def gather_sim_info(mask_sensitive):
    sim = safe_import("sim")
    data = {
        "available": bool(sim),
        "ready": False,
    }
    if not sim:
        return data

    status = safe_call(getattr(sim, "getStatus", None))
    data["status"] = status
    data["ready"] = status == 1
    data["inserted"] = status not in (None, 0, -1)

    iccid = safe_call(getattr(sim, "getIccid", None))
    imsi = safe_call(getattr(sim, "getImsi", None))
    phone_number = safe_call(getattr(sim, "getPhoneNumber", None))
    cur_simid = safe_call(getattr(sim, "getCurSimid", None)) if hasattr(sim, "getCurSimid") else None

    if ok_value(iccid):
        data["iccid"] = mask_value(iccid, mask_sensitive)
    if ok_value(imsi):
        data["imsi"] = mask_value(imsi, mask_sensitive)
    if ok_value(phone_number):
        data["phone_number"] = mask_value(phone_number, mask_sensitive)
    if ok_value(cur_simid) or cur_simid == 0:
        data["current_sim_id"] = cur_simid
    return data


def gather_network_info():
    net = safe_import("net")
    check_net = safe_import("checkNet")
    data = {
        "available": bool(net),
    }
    if not net:
        return data

    reg_raw, reg_source = safe_attr_call(net, ["getState"])
    voice = None
    data_reg = None
    if isinstance(reg_raw, (list, tuple)) and len(reg_raw) >= 2:
        voice = parse_reg_entry(reg_raw[0])
        data_reg = parse_reg_entry(reg_raw[1])
        data["registration_raw"] = reg_raw
        data["registration_source"] = reg_source

    operator_raw, operator_source = safe_attr_call(net, ["getOperatorName", "operatorName"])
    operator_info = parse_operator_info(operator_raw)
    serving_ci, _ = safe_attr_call(net, ["getServingCi"])
    serving_lac, _ = safe_attr_call(net, ["getServingLac"])
    serving_mcc, _ = safe_attr_call(net, ["getServingMcc"])
    serving_mnc, _ = safe_attr_call(net, ["getServingMnc"])
    csq, _ = safe_attr_call(net, ["csqQueryPoll"])
    signal_detail, signal_source = safe_attr_call(net, ["getSignal"], 1)
    nitz, nitz_source = safe_attr_call(net, ["nitzTime"])
    cells, cells_source = safe_attr_call(net, ["getCellInfo", "currentCellInfo"])

    if voice:
        data["voice_registration"] = voice
    if data_reg:
        data["data_registration"] = data_reg
        state = data_reg.get("state")
        data["registered"] = state in (1, 5, 8)
        data["registration"] = {
            "registered": data["registered"],
            "source": "net.getState",
            "stat": state,
        }
    if operator_info:
        operator_info["source"] = operator_source
        data["operator"] = operator_info

    signal = {}
    if ok_value(serving_ci):
        signal["serving_ci"] = serving_ci
    if ok_value(serving_lac):
        signal["serving_lac"] = serving_lac
    if ok_value(serving_mcc):
        signal["serving_mcc"] = serving_mcc
    if ok_value(serving_mnc):
        signal["serving_mnc"] = serving_mnc
    if ok_value(csq):
        signal["csq"] = csq
        signal["quality"] = _signal_quality(csq)
    if ok_value(signal_detail):
        signal["detail"] = signal_detail
        signal["detail_source"] = signal_source
    if signal:
        data["signal"] = signal

    if ok_value(nitz):
        data["nitz_time"] = {
            "raw": nitz,
            "source": nitz_source,
        }
    if ok_value(cells):
        data["cell_scan"] = {
            "raw": cells,
            "source": cells_source,
        }

    if check_net and hasattr(check_net, "waitNetworkReady"):
        ready = safe_call(check_net.waitNetworkReady, 1)
        if isinstance(ready, (list, tuple)) and len(ready) >= 2:
            data["network_ready"] = {
                "stage": ready[0],
                "state": ready[1],
            }
    return data


def gather_data_context():
    data_call = safe_import("dataCall")
    data = {
        "available": bool(data_call),
    }
    if not data_call:
        return data

    raw = safe_call(getattr(data_call, "getInfo", None), 1, 2)
    if raw in (None, -1):
        raw = safe_call(getattr(data_call, "getInfo", None), 1, 0)
    parsed = parse_data_context(raw)
    if parsed:
        data.update(parsed)
        data["raw"] = raw
    return data


def quick_network_status(cfg):
    network_info = gather_network_info()
    data_context = gather_data_context()
    sim_info = gather_sim_info(False)
    registration = network_info.get("registration") or {}
    registered = bool(registration.get("registered"))
    sim_ready = bool(sim_info.get("ready"))
    ip_address = data_context.get("ip_address")
    pdp_active = bool(
        data_context.get("available")
        and data_context.get("state") == 1
        and ok_value(ip_address)
        and str(ip_address) not in ("0.0.0.0", "::", "0:0:0:0:0:0:0:0")
    )
    stage = 3
    state = 1 if pdp_active else 0
    if not sim_ready:
        stage = 1
        state = sim_info.get("status")
        if state in (None, ""):
            state = 0
    elif not registered:
        stage = 2
        state = registration.get("stat")
        if state in (None, ""):
            state = 0
    return {
        "ready": bool(sim_ready and registered and pdp_active),
        "stage": stage,
        "state": state,
        "sim_ready": sim_ready,
        "registered": registered,
        "pdp_active": pdp_active,
        "ip_address": ip_address or "",
        "cid": data_context.get("cid"),
        "sim": sim_info,
        "registration": registration,
        "data_context": data_context,
        "target_gateway": getattr(cfg, "OPENCLAW_WS_URL", ""),
        "ts": wall_time_ms(),
    }


def wait_network_ready_status(cfg, timeout_sec):
    seconds = int(timeout_sec or 0)
    if seconds <= 0:
        seconds = 1
    check_net = safe_import("checkNet")
    if check_net and hasattr(check_net, "waitNetworkReady"):
        ready = safe_call(getattr(check_net, "waitNetworkReady"), seconds)
        if isinstance(ready, (list, tuple)) and len(ready) >= 2:
            try:
                return {
                    "stage": int(ready[0]),
                    "state": int(ready[1]),
                    "source": "checkNet.waitNetworkReady",
                    "ready": int(ready[0]) == 3 and int(ready[1]) == 1,
                }
            except Exception:
                return {
                    "stage": ready[0],
                    "state": ready[1],
                    "source": "checkNet.waitNetworkReady",
                    "ready": ready[0] == 3 and ready[1] == 1,
                }
    quick = quick_network_status(cfg)
    return {
        "stage": quick.get("stage"),
        "state": quick.get("state"),
        "source": "quick_network_status",
        "ready": bool(quick.get("ready")),
    }


# ---------------------------------------------------------------------------
# Cell info helpers
# ---------------------------------------------------------------------------

def _fill_cell_serving_from_signal(data, signal):
    if not isinstance(signal, dict):
        return
    for source_key, target_key in (
        ("serving_ci", "ci"),
        ("serving_lac", "lac"),
        ("serving_mcc", "mcc"),
        ("serving_mnc", "mnc"),
    ):
        value = signal.get(source_key)
        if ok_value(value):
            data["serving"][target_key] = value


def _fill_cell_serving_from_raw(data):
    raw = data.get("raw")
    if not (isinstance(raw, (list, tuple)) and len(raw) >= 3):
        return
    rows = raw[2]
    if not (isinstance(rows, (list, tuple)) and rows):
        return
    row = rows[0]
    if not isinstance(row, (list, tuple)):
        return
    mapping = (
        (1, "ci"),
        (2, "mcc"),
        (3, "mnc"),
        (5, "lac"),
    )
    for index, key in mapping:
        if len(row) > index and ok_value(row[index]):
            data["serving"][key] = row[index]


def _fill_cell_neighbors_from_raw(data):
    raw = data.get("raw")
    if not (isinstance(raw, (list, tuple)) and len(raw) >= 3):
        return
    rows = raw[2]
    if not isinstance(rows, (list, tuple)):
        return
    collected = {
        "ci": [],
        "mcc": [],
        "mnc": [],
        "lac": [],
    }
    mapping = (
        (1, "ci"),
        (2, "mcc"),
        (3, "mnc"),
        (5, "lac"),
    )
    for row in rows:
        if not isinstance(row, (list, tuple)):
            continue
        for index, key in mapping:
            if len(row) > index and ok_value(row[index]):
                collected[key].append(row[index])
    for key in ("ci", "mcc", "mnc", "lac"):
        if collected[key] and key not in data["neighbors"]:
            data["neighbors"][key] = collected[key]


def gather_cell_info(network_info=None):
    net = safe_import("net")
    if not net and not isinstance(network_info, dict):
        return {"available": False}

    data = {
        "available": True,
        "serving": {},
        "neighbors": {},
    }

    if isinstance(network_info, dict):
        _fill_cell_serving_from_signal(data, network_info.get("signal"))
        cell_scan = network_info.get("cell_scan")
        if isinstance(cell_scan, dict):
            raw = cell_scan.get("raw")
            if ok_value(raw):
                data["raw"] = raw
                data["raw_source"] = cell_scan.get("source") or "reused.cell_scan"
                _fill_cell_serving_from_raw(data)
                _fill_cell_neighbors_from_raw(data)

    if net:
        if not data["serving"]:
            for method_name, key in (
                ("getServingCi", "ci"),
                ("getServingLac", "lac"),
                ("getServingMcc", "mcc"),
                ("getServingMnc", "mnc"),
            ):
                if hasattr(net, method_name):
                    value = safe_call(getattr(net, method_name))
                    if ok_value(value):
                        data["serving"][key] = value

        if "raw" not in data:
            cells, source = safe_attr_call(net, ["getCellInfo", "currentCellInfo"])
            if ok_value(cells):
                data["raw"] = cells
                data["raw_source"] = source
                _fill_cell_serving_from_raw(data)
                _fill_cell_neighbors_from_raw(data)
    return data


# ---------------------------------------------------------------------------
# CellularNetworkManager
# ---------------------------------------------------------------------------

class CellularNetworkManager(object):

    def __init__(self, cfg, state):
        self.cfg = cfg
        self.state = state
        self.runtime = None
        self.bootstrapped = False
        self.callback_registered = False
        self.last_ready = False
        self.last_stage = -1
        self.last_state = -1
        self.last_reason = ""
        self.last_check_ms = 0
        self.last_recover_ms = 0
        self.last_cfun_ms = 0
        self.last_event_ms = 0
        self.last_event_profile = -1
        self.last_event_state = -1
        self.last_recovery_action = ""
        self.last_recovery_result = ""
        self.last_ip_address = ""
        self.pending_transport_close_reason = ""

    def attach_runtime(self, runtime):
        self.runtime = runtime
        return True

    def snapshot(self):
        return {
            "bootstrapped": self.bootstrapped,
            "callback_registered": self.callback_registered,
            "last_ready": self.last_ready,
            "last_stage": self.last_stage,
            "last_state": self.last_state,
            "last_reason": self.last_reason,
            "last_check_ms": self.last_check_ms,
            "last_recover_ms": self.last_recover_ms,
            "last_cfun_ms": self.last_cfun_ms,
            "last_event_ms": self.last_event_ms,
            "last_event_profile": self.last_event_profile,
            "last_event_state": self.last_event_state,
            "last_recovery_action": self.last_recovery_action,
            "last_recovery_result": self.last_recovery_result,
            "last_ip_address": self.last_ip_address,
            "pending_transport_close_reason": self.pending_transport_close_reason,
        }

    def bootstrap(self):
        if self.bootstrapped:
            return True
        data_call = safe_import("dataCall")
        profile_id = int(getattr(self.cfg, "NETWORK_PROFILE_ID", 1))
        ip_type = int(getattr(self.cfg, "NETWORK_IPTYPE", 2))
        if data_call:
            apn = str(getattr(self.cfg, "NETWORK_APN", "") or "")
            username = str(getattr(self.cfg, "NETWORK_APN_USERNAME", "") or "")
            password = str(getattr(self.cfg, "NETWORK_APN_PASSWORD", "") or "")
            auth_type = int(getattr(self.cfg, "NETWORK_APN_AUTH_TYPE", 0))
            if apn and hasattr(data_call, "setPDPContext"):
                safe_call(
                    getattr(data_call, "setPDPContext"),
                    profile_id,
                    ip_type,
                    apn,
                    username,
                    password,
                    auth_type,
                )
            if bool(getattr(self.cfg, "NETWORK_ENFORCE_AUTO_ACTIVATE", True)) and hasattr(data_call, "setAutoActivate"):
                safe_call(getattr(data_call, "setAutoActivate"), profile_id, 1)
            if bool(getattr(self.cfg, "NETWORK_ENFORCE_AUTO_CONNECT", True)) and hasattr(data_call, "setAutoConnect"):
                safe_call(getattr(data_call, "setAutoConnect"), profile_id, 1)
            if hasattr(data_call, "setCallback"):
                safe_call(getattr(data_call, "setCallback"), self._on_data_call_event)
                self.callback_registered = True
        self.bootstrapped = True
        return True

    def poll(self):
        reason = self.pending_transport_close_reason
        if not reason:
            return False
        self.pending_transport_close_reason = ""
        runtime = self.runtime
        if runtime is None or runtime.transport is None:
            return False
        if not getattr(runtime.transport, "online", False):
            return False
        runtime.transport.close(reason)
        return True

    def ensure_ready(self, reason):
        self.bootstrap()
        if not bool(getattr(self.cfg, "NETWORK_AUTO_RECOVER", True)):
            self._remember_quick(quick_network_status(self.cfg), reason or "disabled")
            return True

        quick = quick_network_status(self.cfg)
        force_recover = self._should_force_recover(quick)
        if self._remember_quick(quick, reason or "quick") and (not force_recover):
            return True

        now = utime.ticks_ms()
        min_interval_ms = int(getattr(self.cfg, "NETWORK_RECOVER_RETRY_INTERVAL_SEC", 15) * 1000)
        if self.last_recover_ms and utime.ticks_diff(now, self.last_recover_ms) < min_interval_ms:
            return False
        self.last_recover_ms = now

        quick_wait = wait_network_ready_status(
            self.cfg, int(getattr(self.cfg, "NETWORK_READY_QUICK_TIMEOUT_SEC", 1))
        )
        if self._remember_stage(quick_wait, "checknet.quick") and (not force_recover):
            return True

        stage = quick_wait.get("stage")
        state = quick_wait.get("state")
        if stage == 3 and state != 1 and bool(getattr(self.cfg, "NETWORK_ACTIVATE_ON_STAGE3", True)):
            if self._activate_pdp():
                activate_wait = wait_network_ready_status(self.cfg, 3)
                if self._remember_stage(activate_wait, "pdp.activate"):
                    return True
                stage = activate_wait.get("stage")
                state = activate_wait.get("state")

        allow_cfun = False
        if force_recover:
            allow_cfun = True
        elif stage == 2 and bool(getattr(self.cfg, "NETWORK_CFUN_ON_STAGE2", True)):
            allow_cfun = True
        elif stage == 3 and bool(getattr(self.cfg, "NETWORK_CFUN_ON_STAGE3", True)):
            allow_cfun = True

        if allow_cfun and self._cfun_recover():
            return True

        return self._remember_quick(quick_network_status(self.cfg), "quick.final")

    def _on_data_call_event(self, args):
        self.last_event_ms = utime.ticks_ms()
        try:
            self.last_event_profile = int(args[0])
        except Exception:
            self.last_event_profile = -1
        try:
            self.last_event_state = int(args[1])
        except Exception:
            self.last_event_state = -1

        if self.last_event_state == 1:
            self.last_ready = True
            self.last_stage = 3
            self.last_state = 1
            self.last_reason = "pdp.connected"
            self.pending_transport_close_reason = ""
            return

        if self.last_event_state == 0:
            self.last_ready = False
            self.last_stage = 3
            self.last_state = 0
            self.last_reason = "pdp.disconnected"
            self.state.note_error("NETWORK_LINK_DOWN", "dataCall callback: disconnected")
            if bool(getattr(self.cfg, "NETWORK_CLOSE_TRANSPORT_ON_PDP_DOWN", True)):
                self.pending_transport_close_reason = "network-disconnected"

    def _should_force_recover(self, quick):
        threshold = int(getattr(self.cfg, "NETWORK_FORCE_RECOVER_AFTER_CONNECT_FAILURES", 0))
        if threshold <= 0:
            return False
        if not bool(quick.get("ready")):
            return False
        return int(getattr(self.state, "consecutive_failures", 0)) >= threshold

    def _remember_quick(self, quick, reason):
        self.last_check_ms = utime.ticks_ms()
        self.last_ready = bool(quick.get("ready"))
        self.last_stage = quick.get("stage")
        self.last_state = quick.get("state")
        self.last_reason = str(reason or "")
        self.last_ip_address = str(quick.get("ip_address") or "")
        return self.last_ready

    def _remember_stage(self, status, reason):
        self.last_check_ms = utime.ticks_ms()
        self.last_stage = status.get("stage")
        self.last_state = status.get("state")
        self.last_reason = str(reason or "")
        self.last_ready = bool(status.get("ready"))
        return self.last_ready

    def _activate_pdp(self):
        data_call = safe_import("dataCall")
        if not data_call:
            self.last_recovery_action = "pdp.activate"
            self.last_recovery_result = "dataCall unavailable"
            return False

        profile_id = int(getattr(self.cfg, "NETWORK_PROFILE_ID", 1))
        ip_type = int(getattr(self.cfg, "NETWORK_IPTYPE", 2))
        apn = str(getattr(self.cfg, "NETWORK_APN", "") or "")
        username = str(getattr(self.cfg, "NETWORK_APN_USERNAME", "") or "")
        password = str(getattr(self.cfg, "NETWORK_APN_PASSWORD", "") or "")
        auth_type = int(getattr(self.cfg, "NETWORK_APN_AUTH_TYPE", 0))
        result = None
        if apn and hasattr(data_call, "setPDPContext"):
            safe_call(
                getattr(data_call, "setPDPContext"),
                profile_id,
                ip_type,
                apn,
                username,
                password,
                auth_type,
            )
        if hasattr(data_call, "activate"):
            result = safe_call(getattr(data_call, "activate"), profile_id)
        if result not in (0, True, None) and hasattr(data_call, "start"):
            result = safe_call(
                getattr(data_call, "start"),
                profile_id,
                ip_type,
                apn,
                username,
                password,
                auth_type,
            )
        self.last_recovery_action = "pdp.activate"
        self.last_recovery_result = str(result)
        return result in (0, True, None)

    def _cfun_recover(self):
        net = safe_import("net")
        if not net or (not hasattr(net, "setModemFun")):
            self.last_recovery_action = "cfun"
            self.last_recovery_result = "net.setModemFun unavailable"
            return False

        now = utime.ticks_ms()
        cooldown_ms = int(getattr(self.cfg, "NETWORK_CFUN_COOLDOWN_SEC", 90) * 1000)
        if self.last_cfun_ms and utime.ticks_diff(now, self.last_cfun_ms) < cooldown_ms:
            self.last_recovery_action = "cfun"
            self.last_recovery_result = "cooldown"
            return False

        off_result = safe_call(getattr(net, "setModemFun"), 0, 0)
        _sleep_ms(int(getattr(self.cfg, "NETWORK_CFUN_OFF_MS", 1200)))
        on_result = safe_call(getattr(net, "setModemFun"), 1, 0)
        self.last_cfun_ms = utime.ticks_ms()
        self.last_recovery_action = "cfun"
        self.last_recovery_result = str((off_result, on_result))
        wait_status = wait_network_ready_status(
            self.cfg, int(getattr(self.cfg, "NETWORK_POST_CFUN_WAIT_SEC", 15))
        )
        return self._remember_stage(wait_status, "cfun.wait")

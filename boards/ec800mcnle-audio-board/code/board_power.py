def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


class BoardPower(object):

    def __init__(self, charge_gpio=3, system_gpio=33):
        self.charge_gpio = charge_gpio
        self.system_gpio = system_gpio
        self.machine = _safe_import("machine")
        self.supported = bool(self.machine and hasattr(self.machine, "Pin"))
        self.init_error = ""
        self.charge_pin = None
        self.system_pin = None
        self.charge_enabled = False
        self.system_pin_prepared = False

        if not self.supported:
            self.init_error = "machine.Pin unavailable"
            return

        try:
            pin_cls = getattr(self.machine, "Pin")
            charge_attr = getattr(pin_cls, "GPIO" + str(charge_gpio))
            self.charge_pin = pin_cls(charge_attr, pin_cls.OUT, pin_cls.PULL_PU)
        except Exception as e:
            self.init_error = str(e)
            self.supported = False
            self.charge_pin = None

    def _require_supported(self):
        if not self.supported:
            raise Exception(self.init_error or "board power unsupported")

    def prepare_boot_pins(self):
        self._require_supported()
        if self.system_pin_prepared:
            return True
        pin_cls = getattr(self.machine, "Pin")
        system_attr = getattr(pin_cls, "GPIO" + str(self.system_gpio))
        self.system_pin = pin_cls(system_attr, pin_cls.OUT, pin_cls.PULL_PD, 1)
        self.system_pin_prepared = True
        return True

    def enable_charge(self):
        self._require_supported()
        if self.charge_pin is not None:
            self.charge_pin.write(1)
            self.charge_enabled = True
        return True

    def disable_charge(self):
        self._require_supported()
        if self.charge_pin is not None:
            self.charge_pin.write(0)
            self.charge_enabled = False
        return True

    def snapshot(self):
        return {
            "supported": bool(self.supported),
            "init_error": self.init_error,
            "charge_gpio": self.charge_gpio,
            "system_gpio": self.system_gpio,
            "charge_enabled": bool(self.charge_enabled),
            "system_pin_prepared": bool(self.system_pin_prepared),
        }

INIT_480X854_LOCAL = (
    0x11, 0, 0,
    0xFF, 120, 5, 0x77, 0x01, 0x00, 0x00, 0x10,
    0xC0, 0, 2, 0xE9, 0x03,
    0xC1, 0, 2, 0x11, 0x02,
    0xC2, 0, 2, 0x31, 0x08,
    0xCC, 0, 1, 0x10,
    0xB0, 0, 16, 0x00, 0x0D, 0x14, 0x0D, 0x10, 0x05, 0x02, 0x08, 0x08, 0x1E, 0x05, 0x13, 0x11, 0xA3, 0x29, 0x18,
    0xB1, 0, 16, 0x00, 0x0C, 0x14, 0x0C, 0x10, 0x05, 0x03, 0x08, 0x07, 0x20, 0x05, 0x13, 0x11, 0xA4, 0x29, 0x18,
    0xFF, 0, 5, 0x77, 0x01, 0x00, 0x00, 0x11,
    0xB0, 0, 1, 0x6C,
    0xB1, 0, 1, 0x43,
    0xB2, 0, 1, 0x07,
    0xB3, 0, 1, 0x80,
    0xB5, 0, 1, 0x47,
    0xB7, 0, 1, 0x85,
    0xB8, 0, 1, 0x20,
    0xB9, 0, 1, 0x10,
    0xC1, 0, 1, 0x78,
    0xC2, 0, 1, 0x78,
    0xD0, 0, 1, 0x88,
    0xE0, 100, 3, 0x00, 0x00, 0x02,
    0xE1, 0, 11, 0x08, 0x00, 0x0A, 0x00, 0x07, 0x00, 0x09, 0x00, 0x00, 0x33, 0x33,
    0xE2, 0, 13, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xE3, 0, 4, 0x00, 0x00, 0x33, 0x33,
    0xE4, 0, 2, 0x44, 0x44,
    0xE5, 0, 16, 0x0E, 0x60, 0xA0, 0xA0, 0x10, 0x60, 0xA0, 0xA0, 0x0A, 0x60, 0xA0, 0xA0, 0x0C, 0x60, 0xA0, 0xA0,
    0xE6, 0, 4, 0x00, 0x00, 0x33, 0x33,
    0xE7, 0, 2, 0x44, 0x44,
    0xE8, 0, 16, 0x0D, 0x60, 0xA0, 0xA0, 0x0F, 0x60, 0xA0, 0xA0, 0x09, 0x60, 0xA0, 0xA0, 0x0B, 0x60, 0xA0, 0xA0,
    0xEB, 0, 7, 0x02, 0x01, 0xE4, 0xE4, 0x44, 0x00, 0x40,
    0xEC, 0, 2, 0x02, 0x01,
    0xED, 0, 16, 0xAB, 0x89, 0x76, 0x54, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x10, 0x45, 0x67, 0x98, 0xBA,
    0xFF, 0, 5, 0x77, 0x01, 0x00, 0x00, 0x00,
    0x3A, 0, 1, 0x77,
    0x36, 0, 1, 0x00,
    0x35, 0, 1, 0x00,
    0x29, 0, 0,
)


def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


class BoardDisplay(object):

    def __init__(self, width=854, height=480, panel_width=480, panel_height=854):
        self.width = int(width)
        self.height = int(height)
        self.panel_width = int(panel_width)
        self.panel_height = int(panel_height)
        self.machine = _safe_import("machine")
        self.lv = _safe_import("lvgl")
        self.gc = _safe_import("gc")
        self.utime = _safe_import("utime")
        self.thread = _safe_import("_thread")
        self.tp_module = _safe_import("tp")
        self.supported = bool(self.machine and self.lv and hasattr(self.machine, "LCD"))
        self.init_error = ""
        self.ready = False
        self.touch_supported = False
        self.touch_ready = False
        self.touch_error = ""
        self.lcd = None
        self.disp_buf = None
        self.buf1 = None
        self.buf_bytes = 0
        self.buf_pixels = 0
        self.buf_lines = 0
        self.disp_drv = None
        self.indev_drv = None
        self.touch = None
        self.tick_ms = 20
        self.auto_pump_running = False
        self.auto_pump_started = False
        self.auto_pump_error = ""
        self.pump_hook = None
        self.pump_hook_error = ""
        self.init_attempt_count = 0
        self.last_init_attempt_ms = 0
        self.next_retry_ms = 0
        self._lv_lock = None
        if self.thread is not None and hasattr(self.thread, "allocate_lock"):
            try:
                self._lv_lock = self.thread.allocate_lock()
            except Exception:
                self._lv_lock = None

    def _require_supported(self):
        if not self.supported:
            raise Exception(self.init_error or "display unsupported")

    def acquire(self):
        if self._lv_lock is not None:
            self._lv_lock.acquire()

    def release(self):
        if self._lv_lock is not None:
            self._lv_lock.release()

    def _set_boot_pins(self):
        if self.machine is None or not hasattr(self.machine, "Pin"):
            return False
        pin_cls = self.machine.Pin
        rows = (
            (getattr(pin_cls, "GPIO27", 27), 1),
            (getattr(pin_cls, "GPIO8", 8), 1),
            (getattr(pin_cls, "GPIO11", 11), 1),
        )
        index = 0
        while index < len(rows):
            try:
                pin_cls(rows[index][0], pin_cls.OUT, pin_cls.PULL_PU, rows[index][1])
            except Exception:
                pass
            index += 1
        return True

    def _alloc_draw_buffer(self):
        line_candidates = (40, 24, 16, 12, 8, 4)
        # The panel controller is brought up in its native portrait geometry.
        # LVGL rotation then maps the AIRI scene into landscape coordinates.
        width = int(self.panel_width or self.width or 0)
        if width <= 0:
            width = 480
        last_error = "unknown"
        index = 0
        while index < len(line_candidates):
            lines = int(line_candidates[index])
            pixels = width * lines
            buf_bytes = pixels * 2
            try:
                if self.gc is not None:
                    try:
                        self.gc.collect()
                    except Exception:
                        pass
                return bytearray(buf_bytes), buf_bytes, pixels, lines
            except Exception as e:
                last_error = str(e)
            index += 1
        raise Exception("draw buffer allocation failed: " + last_error)

    def _ticks_ms(self):
        if self.utime is None:
            return 0
        try:
            return int(self.utime.ticks_ms())
        except Exception:
            return 0

    def _set_retry_backoff(self, delay_ms):
        self.next_retry_ms = 0
        if self.utime is None:
            return False
        try:
            self.next_retry_ms = int(self.utime.ticks_add(self.utime.ticks_ms(), int(delay_ms or 0)))
            return True
        except Exception:
            self.next_retry_ms = 0
            return False

    def _retry_pending(self):
        if int(self.next_retry_ms or 0) <= 0 or self.utime is None:
            return False
        try:
            return self.utime.ticks_diff(self.next_retry_ms, self.utime.ticks_ms()) > 0
        except Exception:
            return False

    def _init_mipi_locked(self):
        delay_plan = (1200, 400, 800)
        last_error = "mipi init fail"
        index = 0
        while index < len(delay_plan):
            self.init_attempt_count += 1
            self.last_init_attempt_ms = self._ticks_ms()
            self._set_boot_pins()
            self._sleep_ms(delay_plan[index])
            if self.gc is not None:
                try:
                    self.gc.collect()
                except Exception:
                    pass
            try:
                self.lcd = self.machine.LCD()
                self.lcd.mipi_init(
                    initbuf=bytearray(INIT_480X854_LOCAL),
                    width=self.panel_width,
                    hight=self.panel_height,
                    DataLane=2,
                    TransMode=1,
                )
                self.init_error = ""
                self.next_retry_ms = 0
                return True
            except Exception as e:
                self.lcd = None
                last_error = str(e) or "mipi init fail"
            index += 1
        self._set_retry_backoff(8000)
        raise Exception(last_error)

    def ensure_ready(self):
        if self.ready:
            return True
        self._require_supported()
        if self.init_error and self._retry_pending():
            raise Exception(self.init_error)
        self.acquire()
        try:
            if self.ready:
                return True
            self._init_mipi_locked()
            self.lv.init()
            self.disp_buf = self.lv.disp_draw_buf_t()
            self.buf1, self.buf_bytes, self.buf_pixels, self.buf_lines = self._alloc_draw_buffer()
            self.disp_buf.init(self.buf1, None, self.buf_pixels)
            self.disp_drv = self.lv.disp_drv_t()
            self.disp_drv.init()
            self.disp_drv.draw_buf = self.disp_buf
            self.disp_drv.flush_cb = self.lcd.lcd_write
            self.disp_drv.hor_res = self.panel_width
            self.disp_drv.ver_res = self.panel_height
            self.disp_drv.sw_rotate = 1
            try:
                self.disp_drv.rotated = self.lv.DISP_ROT._270
            except Exception:
                pass
            self.disp_drv.register()
            self._init_touch_locked()
            self._finalize_boot_pins()
            self.ready = True
            self._pump_locked()
            return True
        except Exception as e:
            self.init_error = str(e)
            self.ready = False
            if not self._retry_pending():
                self._set_retry_backoff(8000)
            raise
        finally:
            self.release()

    def _init_touch_locked(self):
        self.touch_supported = False
        self.touch_ready = False
        self.touch_error = ""
        if self.tp_module is None or not hasattr(self.tp_module, "gt9xx"):
            return False
        try:
            self.touch = self.tp_module.gt9xx(irq=40, reset=20)
            self.touch.activate()
            self.touch.init()
            self.indev_drv = self.lv.indev_drv_t()
            self.indev_drv.init()
            self.indev_drv.type = self.lv.INDEV_TYPE.POINTER
            self.indev_drv.read_cb = self.touch.read
            self.indev_drv.register()
            self.touch_supported = True
            self.touch_ready = True
            return True
        except Exception as e:
            self.touch_supported = True
            self.touch_ready = False
            self.touch_error = str(e)
            return False

    def _finalize_boot_pins(self):
        if self.machine is None or not hasattr(self.machine, "Pin"):
            return False
        pin_cls = self.machine.Pin
        try:
            pin_cls(getattr(pin_cls, "GPIO40", 40), pin_cls.OUT, pin_cls.PULL_PU, 0)
            return True
        except Exception:
            return False

    def _sleep_ms(self, delay_ms):
        if self.utime is None:
            return
        try:
            self.utime.sleep_ms(int(delay_ms))
        except Exception:
            try:
                self.utime.sleep(int(delay_ms / 1000))
            except Exception:
                pass

    def _pump_locked(self):
        if not self.ready:
            return False
        self.lv.tick_inc(self.tick_ms)
        self.lv.task_handler()
        if self.pump_hook is not None:
            try:
                self.pump_hook()
                self.pump_hook_error = ""
            except Exception as e:
                self.pump_hook_error = str(e)
        return True

    def set_pump_hook(self, callback):
        self.pump_hook = callback
        self.pump_hook_error = ""
        return True

    def pump(self):
        if not self.ready:
            return False
        self.acquire()
        try:
            return self._pump_locked()
        finally:
            self.release()

    def start_auto_pump(self, tick_ms=20):
        self.ensure_ready()
        self.tick_ms = int(tick_ms or 20)
        if self.tick_ms < 10:
            self.tick_ms = 10
        if self.auto_pump_started:
            self.auto_pump_running = True
            return True
        if self.thread is None or not hasattr(self.thread, "start_new_thread"):
            self.auto_pump_error = "thread unavailable"
            self.auto_pump_started = False
            self.auto_pump_running = False
            return False
        self.auto_pump_running = True
        self.auto_pump_started = True
        try:
            self.thread.start_new_thread(self._auto_pump_loop, ())
            return True
        except Exception as e:
            self.auto_pump_error = str(e)
            self.auto_pump_running = False
            self.auto_pump_started = False
            return False

    def _auto_pump_loop(self):
        while self.auto_pump_running:
            try:
                self.pump()
            except Exception as e:
                self.auto_pump_error = str(e)
            self._sleep_ms(self.tick_ms)

    def stop_auto_pump(self):
        self.auto_pump_running = False
        return True

    def clear(self, color=0x0000):
        self.ensure_ready()
        self.acquire()
        try:
            self.lcd.lcd_clear(int(color) & 0xFFFF)
            return True
        finally:
            self.release()

    def snapshot(self):
        return {
            "supported": bool(self.supported),
            "init_error": self.init_error,
            "ready": bool(self.ready),
            "width": self.width,
            "height": self.height,
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
            "buf_bytes": self.buf_bytes,
            "buf_pixels": self.buf_pixels,
            "buf_lines": self.buf_lines,
            "touch_supported": bool(self.touch_supported),
            "touch_ready": bool(self.touch_ready),
            "touch_error": self.touch_error,
            "auto_pump_started": bool(self.auto_pump_started),
            "auto_pump_running": bool(self.auto_pump_running),
            "auto_pump_error": self.auto_pump_error,
            "pump_hook_error": self.pump_hook_error,
            "tick_ms": self.tick_ms,
            "init_attempt_count": self.init_attempt_count,
            "last_init_attempt_ms": self.last_init_attempt_ms,
        }

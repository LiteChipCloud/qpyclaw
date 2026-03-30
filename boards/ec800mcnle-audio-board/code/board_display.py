INIT_RAW_DATA = (
    2, 0, 120,
    0, 0, 0x11,
    0, 1, 0x36,
    1, 1, 0x00,
    0, 1, 0x3A,
    1, 1, 0x05,
    0, 0, 0x21,
    0, 5, 0xB2,
    1, 1, 0x05,
    1, 1, 0x05,
    1, 1, 0x00,
    1, 1, 0x33,
    1, 1, 0x33,
    0, 1, 0xB7,
    1, 1, 0x23,
    0, 1, 0xBB,
    1, 1, 0x22,
    0, 1, 0xC0,
    1, 1, 0x2C,
    0, 1, 0xC2,
    1, 1, 0x01,
    0, 1, 0xC3,
    1, 1, 0x13,
    0, 1, 0xC4,
    1, 1, 0x20,
    0, 1, 0xC6,
    1, 1, 0x0F,
    0, 2, 0xD0,
    1, 1, 0xA4,
    1, 1, 0xA1,
    0, 1, 0xD6,
    1, 1, 0xA1,
    0, 14, 0xE0,
    1, 1, 0x70,
    1, 1, 0x06,
    1, 1, 0x0C,
    1, 1, 0x08,
    1, 1, 0x09,
    1, 1, 0x27,
    1, 1, 0x2E,
    1, 1, 0x34,
    1, 1, 0x46,
    1, 1, 0x37,
    1, 1, 0x13,
    1, 1, 0x13,
    1, 1, 0x25,
    1, 1, 0x2A,
    0, 14, 0xE1,
    1, 1, 0x70,
    1, 1, 0x04,
    1, 1, 0x08,
    1, 1, 0x09,
    1, 1, 0x07,
    1, 1, 0x03,
    1, 1, 0x2C,
    1, 1, 0x42,
    1, 1, 0x42,
    1, 1, 0x38,
    1, 1, 0x14,
    1, 1, 0x14,
    1, 1, 0x27,
    1, 1, 0x2C,
    0, 0, 0x29,
    0, 4, 0x2A,
    1, 1, 0x00,
    1, 1, 0x00,
    1, 1, 0x00,
    1, 1, 0xEF,
    0, 4, 0x2B,
    1, 1, 0x00,
    1, 1, 0x00,
    1, 1, 0x01,
    1, 1, 0x3F,
    0, 0, 0x2C,
)

XSTART_H = 0xF0
XSTART_L = 0xF1
YSTART_H = 0xF2
YSTART_L = 0xF3
XEND_H = 0xE0
XEND_L = 0xE1
YEND_H = 0xE2
YEND_L = 0xE3


def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


class BoardDisplay(object):

    def __init__(self, width=240, height=240, buffer_lines=None):
        self.width = width
        self.height = height
        self.buffer_lines = buffer_lines
        self.machine = _safe_import("machine")
        self.lv = _safe_import("lvgl")
        self.gc = _safe_import("gc")
        self.supported = bool(self.machine and self.lv and hasattr(self.machine, "LCD"))
        self.init_error = ""
        self.ready = False
        self.lcd = None
        self.disp_buf = None
        self.buf1 = None
        self.buf_bytes = 0
        self.buffer_mode = ""
        self.disp_drv = None
        self.display_on_result = None
        self.brightness_result = None

    def _require_supported(self):
        if not self.supported:
            raise Exception(self.init_error or "display unsupported")

    def ensure_ready(self):
        if self.ready:
            return True
        self._require_supported()

        try:
            buffer_lines = self.buffer_lines
            if buffer_lines is None:
                buffer_lines = self.height
            buffer_lines = int(buffer_lines)
            if buffer_lines < 4:
                buffer_lines = 4
            if buffer_lines >= self.height:
                buffer_lines = self.height
                self.buffer_mode = "full"
            else:
                self.buffer_mode = "partial"
            self.buffer_lines = buffer_lines
            lcd_init_data = bytearray(INIT_RAW_DATA)
            lcd_invalid = bytearray((
                0, 4, 0x2A,
                1, 1, XSTART_H,
                1, 1, XSTART_L,
                1, 1, XEND_H,
                1, 1, XEND_L,
                0, 4, 0x2B,
                1, 1, YSTART_H,
                1, 1, YSTART_L,
                1, 1, YEND_H,
                1, 1, YEND_L,
                0, 0, 0x2C,
            ))
            lcd_display_off = bytearray((
                0, 0, 0x28,
                2, 0, 120,
                0, 0, 0x10,
            ))
            lcd_display_on = bytearray((
                0, 0, 0x11,
                2, 0, 20,
                0, 0, 0x29,
            ))

            self.lcd = self.machine.LCD()
            self.lcd.lcd_init(
                lcd_init_data,
                self.width,
                self.height,
                26000,
                1,
                4,
                0,
                lcd_invalid,
                lcd_display_on,
                lcd_display_off,
                None,
            )
            self._wake_panel()
            self.lcd.lcd_clear(0x0000)

            self.lv.init()
            self.disp_buf = self.lv.disp_draw_buf_t()
            self.buf_bytes = self.width * self.buffer_lines * 2
            if self.gc is not None:
                try:
                    self.gc.collect()
                except Exception:
                    pass
            self.buf1 = bytearray(self.buf_bytes)
            self.disp_buf.init(self.buf1, None, len(self.buf1))
            self.disp_drv = self.lv.disp_drv_t()
            self.disp_drv.init()
            self.disp_drv.draw_buf = self.disp_buf
            self.disp_drv.flush_cb = self.lcd.lcd_write
            self.disp_drv.hor_res = self.width
            self.disp_drv.ver_res = self.height
            self.disp_drv.sw_rotate = 1
            self.disp_drv.rotated = self.lv.DISP_ROT._180
            self.disp_drv.register()

            self.lv.img.cache_invalidate_src(None)
            self.lv.img.cache_set_size(16)
            self.lv.tick_inc(5)
            self.lv.task_handler()
            self.ready = True
            return True
        except Exception as e:
            self.init_error = str(e)
            self.supported = False
            self.ready = False
            raise

    def _wake_panel(self):
        if self.lcd is None:
            return False
        display_on = getattr(self.lcd, "lcd_display_on", None)
        brightness = getattr(self.lcd, "lcd_brightness", None)
        try:
            if display_on is not None:
                self.display_on_result = display_on()
        except Exception as e:
            self.display_on_result = str(e)
        try:
            if brightness is not None:
                self.brightness_result = brightness(1)
        except Exception as e:
            self.brightness_result = str(e)
        return True

    def clear(self, color=0x0000):
        self.ensure_ready()
        self._wake_panel()
        self.lcd.lcd_clear(color)
        return True

    def pump(self):
        if not self.ready:
            return False
        self._wake_panel()
        self.lv.tick_inc(5)
        self.lv.task_handler()
        return True

    def snapshot(self):
        return {
            "supported": bool(self.supported),
            "init_error": self.init_error,
            "ready": bool(self.ready),
            "width": self.width,
            "height": self.height,
            "buffer_lines": self.buffer_lines,
            "buffer_bytes": self.buf_bytes,
            "buffer_mode": self.buffer_mode,
            "display_on_result": self.display_on_result,
            "brightness_result": self.brightness_result,
        }

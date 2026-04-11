from board_airi_data import GLOW_SWING, MODE_KEYS, MODE_PROFILES, PRESENCE_SWING
from board_airi_expression_data import AIRI_EXPRESSION_MANIFEST_CANDIDATES, resolve_expression_for_scene
from board_airi_frame_player import AiriFramePlayer
from board_gif_player import AiriGifPlayer
from board_miaoban_player import MiaobanPlayer


PROFILE_MAP = {}
_profile_index = 0
while _profile_index < len(MODE_PROFILES):
    _profile = MODE_PROFILES[_profile_index]
    PROFILE_MAP[_profile.get("key")] = _profile
    _profile_index += 1


EMOTE_ALIASES = {
    "wake": "neutral",
    "idle": "neutral",
    "neutral": "neutral",
    "standby": "neutral",
    "listen": "listen",
    "listening": "listen",
    "asking": "listen",
    "talk": "happy",
    "speak": "happy",
    "speaking": "happy",
    "happy": "happy",
    "laughing": "happy",
    "loving": "happy",
    "cool": "happy",
    "relaxed": "neutral",
    "sleep": "sleep",
    "sleepy": "sleep",
    "sad": "sad",
    "cry": "cry",
    "crying": "cry",
    "angry": "angry",
    "anger": "angry",
    "thinking": "confused",
    "confused": "confused",
    "shocked": "shocked",
    "surprised": "shocked",
    "panic": "shocked",
    "winking": "winking",
    "blink": "winking",
    "error": "shocked",
}


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _first_item(rows, default_text):
    if not isinstance(rows, (list, tuple)) or not rows:
        return default_text
    try:
        return _string(rows[0])
    except Exception:
        return default_text


def _profile_for_mode(mode_key):
    key = _string(mode_key).strip().lower()
    if key in PROFILE_MAP:
        return PROFILE_MAP.get(key)
    return PROFILE_MAP.get("idle") or MODE_PROFILES[0]


def _rgb_tuple_to_hex(row, default_color):
    if not isinstance(row, (list, tuple)) or len(row) < 3:
        return int(default_color) & 0xFFFFFF
    try:
        return ((int(row[0]) & 0xFF) << 16) | ((int(row[1]) & 0xFF) << 8) | (int(row[2]) & 0xFF)
    except Exception:
        return int(default_color) & 0xFFFFFF


def _normalize_emote_name(value, default_name):
    text = _string(value).strip().lower()
    if text in EMOTE_ALIASES:
        return EMOTE_ALIASES.get(text)
    return default_name


def _rgb565_hex(value):
    color = int(value or 0) & 0xFFFFFF
    red = (color >> 16) & 0xFF
    green = (color >> 8) & 0xFF
    blue = color & 0xFF
    return (((red & 0xF8) << 8) | ((green & 0xFC) << 3) | ((blue & 0xF8) >> 3)) & 0xFFFF


def _file_exists(path):
    if not path:
        return False
    try:
        fp = open(path, "rb")
        fp.close()
        return True
    except Exception:
        return False


class AiriScene(object):

    def __init__(self, display):
        self.display = display
        self.lv = getattr(display, "lv", None)
        self.utime = getattr(display, "utime", None)
        self.ready = False
        self.mode_key = "idle"
        self.fill_only = False
        self.scene_visible = True
        self.overlay_status = ""
        self.overlay_message = ""
        self.overlay_footer = ""
        self.overlay_mood = ""
        self.avatar_src = ""
        self.avatar_exists = True
        self.avatar_error = ""
        self.avatar_candidates = []
        self.current_emote = "neutral"
        self._anim_tick = 0
        self._last_anim_ms = 0
        self._screen_width = int(getattr(display, "width", 854) or 854)
        self._screen_height = int(getattr(display, "height", 480) or 480)
        self._avatar_stage_base_y = 0
        self._halo_base_x = 26
        self._halo_base_y = 18
        self._halo_base_size = 186
        self._ring_base_x = 46
        self._ring_base_y = 38
        self._ring_base_size = 148
        self.screen = None
        self.backdrop_glow = None
        self.corner_glow = None
        self.shell = None
        self.brand_mark = None
        self.brand_label = None
        self.brand_sub = None
        self.avatar_panel = None
        self.avatar_stage = None
        self.avatar_image = None
        self.avatar_canvas = None
        self.avatar_canvas_buf = None
        self.avatar_canvas_width = 0
        self.avatar_canvas_height = 0
        self.avatar_floor_glow = None
        self.avatar_halo = None
        self.avatar_ring = None
        self.avatar_fallback = None
        self.status_panel = None
        self.status_overline = None
        self.status_title = None
        self.status_copy = None
        self.chat_panel = None
        self.chat_overline = None
        self.chat_line = None
        self.chat_support = None
        self.chat_divider = None
        self.action_hint = None
        self.action_button = None
        self.action_label = None
        self.expression_player = None
        self.expression_ready = False
        self.gif_player = None
        self.gif_ready = False
        self.expression_animimg = None
        self.animimg_ready = False
        self.expression_engine = "frame"
        self.miaoban = None
        self.miaoban_ready = False
        self.avatar_render_mode = "fallback"
        self.avatar_static_src = ""
        self.current_expression = ""

    def _static_avatar_rgb565_candidates(self):
        return [
            {"path": "/usr/media/airi-avatar-176.rgb565", "width": 176, "height": 176, "zoom": 320},
            {"path": "U:/media/airi-avatar-176.rgb565", "width": 176, "height": 176, "zoom": 320},
        ]

    def _static_avatar_candidates(self):
        return [
            "/usr/media/airi-avatar-240.jpg",
            "/usr/media/airi-avatar-240.png",
            "/usr/media/airi-preview.png",
            "U:/media/airi-avatar-240.jpg",
            "U:/media/airi-avatar-240.png",
            "U:/media/airi-preview.png",
            "U:/img/airi-avatar-240.jpg",
        ]

    def _resolve_static_avatar(self):
        raw_rows = self._static_avatar_rgb565_candidates()
        index = 0
        while index < len(raw_rows):
            path = raw_rows[index].get("path")
            if _file_exists(path):
                return path
            index += 1
        rows = self._static_avatar_candidates()
        index = 0
        while index < len(rows):
            if _file_exists(rows[index]):
                return rows[index]
            index += 1
        return ""

    def _ensure_avatar_canvas_locked(self, width, height):
        if self.avatar_canvas is None:
            return False
        width = int(width or 0)
        height = int(height or 0)
        if width <= 0 or height <= 0:
            return False
        if (
            self.avatar_canvas_buf is not None
            and self.avatar_canvas_width == width
            and self.avatar_canvas_height == height
        ):
            return True
        self.avatar_canvas_width = width
        self.avatar_canvas_height = height
        self.avatar_canvas_buf = bytearray(width * height * 2)
        self.avatar_canvas.set_buffer(self.avatar_canvas_buf, width, height, self.lv.img.CF.TRUE_COLOR)
        self._set_hidden(self.avatar_canvas, True)
        return True

    def _copy_avatar_canvas_locked(self, data):
        if self.avatar_canvas_buf is None:
            return False
        try:
            self.avatar_canvas_buf[:] = data
            return True
        except Exception:
            index = 0
            size = len(data)
            while index < size:
                self.avatar_canvas_buf[index] = data[index]
                index += 1
            return True

    def _set_static_avatar_layout_locked(self, width, height, zoom):
        if self.avatar_image is None:
            return False
        width = int(width or 0)
        height = int(height or 0)
        zoom = int(zoom or 256)
        draw_w = int((width * zoom) / 256)
        draw_h = int((height * zoom) / 256)
        stage_w = 258
        stage_h = 225
        if self.avatar_stage is not None:
            try:
                value = int(self.avatar_stage.get_width())
                if value > 0:
                    stage_w = value
            except Exception:
                pass
            try:
                value = int(self.avatar_stage.get_height())
                if value > 0:
                    stage_h = value
            except Exception:
                pass
        x = int((stage_w - draw_w) / 2)
        y = int((stage_h - draw_h) / 2)
        self.avatar_image.set_pos(x, y)
        try:
            self.avatar_image.set_zoom(zoom)
        except Exception:
            pass
        return True

    def _apply_rgb565_avatar_source_locked(self, path, width, height, zoom):
        if self.avatar_canvas is None or self.avatar_image is None:
            return False
        width = int(width or 0)
        height = int(height or 0)
        zoom = int(zoom or 256)
        fp = open(path, "rb")
        try:
            data = fp.read()
        finally:
            fp.close()
        expected = width * height * 2
        if len(data) != expected:
            raise Exception("rgb565 size mismatch")
        self._ensure_avatar_canvas_locked(width, height)
        self._copy_avatar_canvas_locked(data)
        self.avatar_image.set_src(self.avatar_canvas.get_img())
        self._set_static_avatar_layout_locked(width, height, zoom)
        self.avatar_static_src = path
        self.avatar_error = ""
        return True

    def _apply_file_avatar_source_locked(self, path):
        if self.avatar_image is None:
            return False
        self.avatar_image.set_src(path)
        self._set_static_avatar_layout_locked(240, 240, 272)
        width = 0
        height = 0
        try:
            width = int(self.avatar_image.get_width())
        except Exception:
            pass
        try:
            height = int(self.avatar_image.get_height())
        except Exception:
            pass
        if width <= 0 or height <= 0:
            raise Exception("lvgl file decoder returned empty size")
        self.avatar_static_src = path
        self.avatar_error = ""
        return True

    def _apply_static_avatar_source_locked(self):
        raw_rows = self._static_avatar_rgb565_candidates()
        index = 0
        while index < len(raw_rows):
            candidate = raw_rows[index]
            path = candidate.get("path")
            if _file_exists(path) and self.avatar_image is not None:
                try:
                    if self._apply_rgb565_avatar_source_locked(
                        path,
                        candidate.get("width"),
                        candidate.get("height"),
                        candidate.get("zoom"),
                    ):
                        return True
                except Exception as e:
                    self.avatar_error = _string(e)
            index += 1
        rows = self._static_avatar_candidates()
        index = 0
        while index < len(rows):
            path = rows[index]
            if _file_exists(path) and self.avatar_image is not None:
                try:
                    if self._apply_file_avatar_source_locked(path):
                        return True
                except Exception as e:
                    self.avatar_error = _string(e)
            index += 1
        self.avatar_static_src = ""
        return False

    def _friendly_status_copy(self):
        if self.mode_key == "talk":
            return "AIRI is currently responding and the conversation becomes the visual center."
        if self.mode_key == "listen":
            return "AIRI is awake and quietly waiting for your next input."
        if self.mode_key == "sleep":
            return "AIRI is in low-power rest mode and can be brought back with one simple action."
        return "AIRI is in companion mode, holding a gentle presence without asking for attention."

    def _color(self, value):
        try:
            color = int(value)
            if color <= 0xFFFF:
                red = ((color >> 11) & 0x1F) * 255 // 31
                green = ((color >> 5) & 0x3F) * 255 // 63
                blue = (color & 0x1F) * 255 // 31
                color = (red << 16) | (green << 8) | blue
            return self.lv.color_hex(color & 0xFFFFFF)
        except Exception:
            return self.lv.color_hex(0x000000)

    def _font(self, size_candidates):
        index = 0
        while index < len(size_candidates):
            font = getattr(self.lv, "font_montserrat_%s" % int(size_candidates[index]), None)
            if font is not None:
                return font
            index += 1
        return None

    def _disable_scroll(self, obj):
        try:
            obj.clear_flag(self.lv.obj.FLAG.SCROLLABLE)
        except Exception:
            pass
        try:
            obj.set_scrollbar_mode(self.lv.SCROLLBAR_MODE.OFF)
        except Exception:
            pass

    def _style_box(self, obj, bg, opa, radius, border_width, border_color):
        obj.set_style_bg_color(self._color(bg), 0)
        obj.set_style_bg_opa(int(opa), 0)
        obj.set_style_radius(int(radius), 0)
        obj.set_style_border_width(int(border_width), 0)
        obj.set_style_border_color(self._color(border_color), 0)
        try:
            obj.set_style_outline_width(0, 0)
        except Exception:
            pass
        try:
            obj.set_style_pad_all(0, 0)
        except Exception:
            pass

    def _make_box(self, parent, x, y, width, height, bg, opa, radius, border_width, border_color):
        obj = self.lv.obj(parent)
        self._disable_scroll(obj)
        self._style_box(obj, bg, opa, radius, border_width, border_color)
        obj.set_pos(int(x), int(y))
        obj.set_size(int(width), int(height))
        return obj

    def _make_label(self, parent, x, y, width, text, color, font_sizes, opacity):
        label = self.lv.label(parent)
        label.set_pos(int(x), int(y))
        label.set_width(int(width))
        label.set_text(_string(text))
        label.set_style_text_color(self._color(color), 0)
        label.set_style_text_opa(int(opacity), 0)
        font = self._font(font_sizes)
        if font is not None:
            try:
                label.set_style_text_font(font, 0)
            except Exception:
                pass
        try:
            label.set_long_mode(self.lv.label.LONG.WRAP)
        except Exception:
            pass
        return label

    def _set_hidden(self, obj, hidden):
        try:
            if hidden:
                obj.add_flag(self.lv.obj.FLAG.HIDDEN)
            else:
                obj.clear_flag(self.lv.obj.FLAG.HIDDEN)
            return True
        except Exception:
            return False

    def _ticks_ms(self):
        if self.utime is None:
            return 0
        try:
            return int(self.utime.ticks_ms())
        except Exception:
            return 0

    def _obj_flag_hidden(self, obj):
        if obj is None:
            return None
        try:
            return bool(obj.has_flag(self.lv.obj.FLAG.HIDDEN))
        except Exception:
            return None

    def _obj_metric(self, obj, method_name):
        if obj is None:
            return None
        try:
            method = getattr(obj, method_name)
        except Exception:
            return None
        try:
            return int(method())
        except Exception:
            return None

    def _obj_snapshot(self, obj, include_zoom=False):
        if obj is None:
            return None
        data = {
            "x": self._obj_metric(obj, "get_x"),
            "y": self._obj_metric(obj, "get_y"),
            "w": self._obj_metric(obj, "get_width"),
            "h": self._obj_metric(obj, "get_height"),
        }
        hidden = self._obj_flag_hidden(obj)
        if hidden is not None:
            data["hidden"] = bool(hidden)
        if include_zoom:
            try:
                data["zoom"] = int(obj.get_zoom())
            except Exception:
                pass
        return data

    def _action_text_for_mode(self):
        if self.mode_key == "talk":
            return "Interrupt reply"
        if self.mode_key == "listen":
            return "Tap to speak"
        if self.mode_key == "sleep":
            return "Wake system"
        return "Wake AIRI"

    def _resolve_active_emote(self):
        default_name = "neutral"
        if self.mode_key == "listen":
            default_name = "listen"
        elif self.mode_key == "talk":
            default_name = "happy"
        return _normalize_emote_name(self.overlay_mood, default_name)

    def _resolved_overlay(self):
        profile = _profile_for_mode(self.mode_key)
        message = _string(profile.get("headline")).replace("\n", " ").strip()
        footer = _first_item(profile.get("footer"), "AIRI holds the scene on the board.")
        status_copy = self._friendly_status_copy()
        status_override = _string(self.overlay_status).strip()
        if status_override and ("//" not in status_override) and len(status_override) <= 96:
            status_copy = status_override
        return {
            "status_copy": status_copy,
            "message": self.overlay_message or message or "AIRI is here on the board.",
            "footer": self.overlay_footer or footer,
        }

    def _apply_scene_visibility_locked(self):
        hidden = bool(self.fill_only or (not self.scene_visible))
        rows = (
            self.backdrop_glow,
            self.corner_glow,
            self.shell,
        )
        index = 0
        while index < len(rows):
            item = rows[index]
            if item is not None:
                self._set_hidden(item, hidden)
            index += 1

    def _ensure_expression_animimg_locked(self):
        if self.expression_animimg is not None and self.animimg_ready:
            return self.expression_animimg
        if self.avatar_stage is None:
            return None
        try:
            from board_airi_animimg_player import AiriAnimImgPlayer

            self.expression_animimg = AiriAnimImgPlayer(self.display, self.avatar_stage)
            self.animimg_ready = bool(self.expression_animimg.available())
            if self.animimg_ready:
                self.expression_animimg.set_layout(zoom=328)
                if self.expression_animimg.manifest_path:
                    self.avatar_candidates.append(self.expression_animimg.manifest_path)
            return self.expression_animimg
        except Exception as e:
            self.expression_animimg = None
            self.animimg_ready = False
            self.avatar_error = _string(e)
            return None

    def _ensure_gif_player_locked(self):
        if self.gif_player is not None and self.gif_ready:
            return self.gif_player
        if self.avatar_stage is None:
            return None
        try:
            self.gif_player = AiriGifPlayer(self.display, self.avatar_stage)
            self.gif_ready = bool(self.gif_player.available())
            if self.gif_ready:
                self.gif_player.set_layout(zoom=240)
                rows = self.gif_player.catalog_paths()
                index = 0
                while index < len(rows):
                    self.avatar_candidates.append(rows[index])
                    index += 1
            return self.gif_player
        except Exception as e:
            self.gif_player = None
            self.gif_ready = False
            self.avatar_error = _string(e)
            return None

    def _apply_avatar_locked(self):
        self.current_emote = self._resolve_active_emote()
        self.current_expression = resolve_expression_for_scene(
            self.mode_key,
            self.overlay_mood,
            self.current_emote,
            "idle_blink",
        )
        prefer_gif = self.expression_engine == "gif"
        prefer_animimg = self.expression_engine == "animimg"
        if prefer_gif:
            gif_player = self._ensure_gif_player_locked()
            if self.gif_ready and gif_player is not None:
                try:
                    if self.avatar_image is not None:
                        self._set_hidden(self.avatar_image, True)
                    if self.expression_player is not None:
                        try:
                            self.expression_player.hide()
                        except Exception:
                            pass
                    if self.expression_animimg is not None:
                        try:
                            self.expression_animimg.hide()
                        except Exception:
                            pass
                    if self.miaoban is not None:
                        try:
                            self.miaoban.hide()
                        except Exception:
                            pass
                    if gif_player.set_expression(self.current_expression, self.current_emote):
                        gif_player.show()
                        self.avatar_src = gif_player.current_src
                        self.avatar_exists = True
                        self.avatar_error = ""
                        self.avatar_render_mode = "gif"
                        self._set_hidden(self.avatar_fallback, True)
                        return True
                except Exception as e:
                    self.avatar_error = _string(e)
            if not self.gif_ready:
                prefer_animimg = True
        if prefer_animimg:
            animimg = self._ensure_expression_animimg_locked()
            if self.animimg_ready and animimg is not None:
                try:
                    if self.avatar_image is not None:
                        self._set_hidden(self.avatar_image, True)
                    if self.gif_player is not None:
                        try:
                            self.gif_player.hide()
                        except Exception:
                            pass
                    if self.expression_player is not None:
                        try:
                            self.expression_player.hide()
                        except Exception:
                            pass
                    if self.miaoban is not None:
                        try:
                            self.miaoban.hide()
                        except Exception:
                            pass
                    if animimg.set_expression(self.current_expression):
                        animimg.show()
                        self.avatar_src = animimg.current_src or animimg.manifest_path
                        self.avatar_exists = True
                        self.avatar_error = ""
                        self.avatar_render_mode = "airi-animimg"
                        self._set_hidden(self.avatar_fallback, True)
                        return True
                except Exception as e:
                    self.avatar_error = _string(e)
        if self.expression_ready and self.expression_player is not None:
            try:
                if self.avatar_image is not None:
                    self._set_hidden(self.avatar_image, True)
                if self.gif_player is not None:
                    try:
                        self.gif_player.hide()
                    except Exception:
                        pass
                if self.expression_animimg is not None:
                    try:
                        self.expression_animimg.hide()
                    except Exception:
                        pass
                if self.miaoban is not None:
                    try:
                        self.miaoban.hide()
                    except Exception:
                        pass
                if self.expression_player.set_expression(self.current_expression):
                    self.expression_player.show()
                    self.avatar_src = self.expression_player.current_src or self.expression_player.manifest_path
                    self.avatar_exists = True
                    self.avatar_error = ""
                    self.avatar_render_mode = "airi-frame"
                    self._set_hidden(self.avatar_fallback, True)
                    return True
            except Exception as e:
                self.avatar_error = _string(e)
        if self.avatar_static_src and self.avatar_image is not None:
            try:
                if self.avatar_src != self.avatar_static_src:
                    self._apply_static_avatar_source_locked()
            except Exception as e:
                self.avatar_error = _string(e)
            if self.expression_player is not None:
                try:
                    self.expression_player.hide()
                except Exception:
                    pass
            if self.gif_player is not None:
                try:
                    self.gif_player.hide()
                except Exception:
                    pass
            if self.expression_animimg is not None:
                try:
                    self.expression_animimg.hide()
                except Exception:
                    pass
            if self.miaoban is not None:
                try:
                    self.miaoban.hide()
                except Exception:
                    pass
            self._set_hidden(self.avatar_image, False)
            self._set_hidden(self.avatar_fallback, True)
            self.avatar_src = self.avatar_static_src
            self.avatar_exists = True
            self.avatar_error = ""
            self.avatar_render_mode = "static"
            self.current_expression = ""
            return True
        if self.miaoban_ready and self.miaoban is not None:
            try:
                if self.avatar_image is not None:
                    self._set_hidden(self.avatar_image, True)
                if self.gif_player is not None:
                    try:
                        self.gif_player.hide()
                    except Exception:
                        pass
                if self.expression_player is not None:
                    try:
                        self.expression_player.hide()
                    except Exception:
                        pass
                if self.expression_animimg is not None:
                    try:
                        self.expression_animimg.hide()
                    except Exception:
                        pass
                self.miaoban.set_backdrop565(_rgb565_hex(0xF5F8FF))
                self.miaoban.set_emote(self.current_emote)
                self.miaoban.show()
                self.avatar_src = self.miaoban._asset_path(self.current_emote)
                self.avatar_exists = True
                self.avatar_error = ""
                self.avatar_render_mode = "miaoban"
                self.current_expression = ""
                self._set_hidden(self.avatar_fallback, True)
                return True
            except Exception as e:
                self.avatar_error = _string(e)
        if self.expression_player is not None:
            try:
                self.expression_player.hide()
            except Exception:
                pass
        if self.gif_player is not None:
            try:
                self.gif_player.hide()
            except Exception:
                pass
        if self.expression_animimg is not None:
            try:
                self.expression_animimg.hide()
            except Exception:
                pass
        if self.avatar_image is not None:
            self._set_hidden(self.avatar_image, True)
        self.avatar_exists = False
        self.avatar_render_mode = "fallback"
        self.current_expression = ""
        self._set_hidden(self.avatar_fallback, False)
        return False

    def _apply_mode_locked(self):
        profile = _profile_for_mode(self.mode_key)
        accent = _rgb_tuple_to_hex(profile.get("accent"), 0x6AA7FF)
        accent_alt = _rgb_tuple_to_hex(profile.get("accent_alt"), 0x79E9FF)
        soft_accent = accent_alt
        self._style_box(self.backdrop_glow, accent, 58, 999, 0, accent)
        self._style_box(self.corner_glow, 0x101A32, 220, 120, 0, 0x101A32)
        self._style_box(self.shell, 0x091327, 248, 34, 1, 0x1B3157)
        self._style_box(self.brand_mark, accent, 255, 16, 0, accent)
        self._style_box(self.avatar_panel, 0x0A1429, 214, 28, 1, 0x203455)
        self._style_box(self.status_panel, 0x141E34, 228, 28, 1, 0x22365A)
        self._style_box(self.chat_panel, 0x0B162D, 234, 28, 1, 0x203455)
        self._style_box(self.chat_divider, 0x203455, 120, 0, 0, 0x203455)
        self._style_box(self.action_button, 0x1C3858, 210, 18, 1, soft_accent)
        self._style_box(self.avatar_stage, 0x000000, 255, 24, 0, 0x000000)
        self._set_hidden(self.avatar_floor_glow, True)
        self._set_hidden(self.avatar_halo, True)
        self._set_hidden(self.avatar_ring, True)
        try:
            self.brand_mark.set_style_bg_grad_color(self._color(accent_alt), 0)
            self.brand_mark.set_style_bg_grad_dir(self.lv.GRAD_DIR.VER, 0)
        except Exception:
            pass
        try:
            self.action_button.set_style_bg_grad_color(self._color(0x274765), 0)
            self.action_button.set_style_bg_grad_dir(self.lv.GRAD_DIR.HOR, 0)
        except Exception:
            pass
        self.brand_label.set_style_text_color(self._color(0xF3F8FF), 0)
        self.brand_sub.set_style_text_color(self._color(0x7E93BC), 0)
        self.status_overline.set_style_text_color(self._color(0x889ABB), 0)
        self.chat_overline.set_style_text_color(self._color(0x889ABB), 0)
        self.action_hint.set_style_text_color(self._color(0x889ABB), 0)
        self.status_title.set_style_text_color(self._color(0xF4F8FF), 0)
        self.status_copy.set_style_text_color(self._color(0xD2DDF0), 0)
        self.chat_line.set_style_text_color(self._color(0xF4F8FF), 0)
        self.chat_support.set_style_text_color(self._color(0xD2DDF0), 0)
        self.action_label.set_style_text_color(self._color(0xF7FBFF), 0)
        self.status_title.set_text(self.mode_key.upper())
        self.action_label.set_text(self._action_text_for_mode())
        self._apply_avatar_locked()

    def _apply_overlay_locked(self):
        payload = self._resolved_overlay()
        self.status_title.set_text(self.mode_key.upper())
        self.status_copy.set_text(_string(payload.get("status_copy")) or "AIRI is here.")
        self.chat_line.set_text(_string(payload.get("message")) or "AIRI is visible on the board.")
        self.chat_support.set_text(_string(payload.get("footer")) or "Only the main message stays on screen.")
        self.action_label.set_text(self._action_text_for_mode())
        self._apply_avatar_locked()

    def _build_screen_locked(self):
        self.screen = self.lv.obj()
        self._disable_scroll(self.screen)
        self._style_box(self.screen, 0x050914, 255, 0, 0, 0x050914)
        self.screen.set_size(self._screen_width, self._screen_height)
        self.backdrop_glow = self._make_box(self.screen, 38, 118, 220, 220, 0x6AA7FF, 58, 999, 0, 0x6AA7FF)
        self.corner_glow = self._make_box(self.screen, 664, 18, 164, 112, 0x121A33, 208, 80, 0, 0x121A33)
        self.shell = self._make_box(self.screen, 0, 0, 854, 480, 0x091327, 248, 34, 1, 0x1B3157)
        self.brand_mark = self._make_box(self.shell, 24, 24, 42, 42, 0x6AA7FF, 255, 16, 0, 0x6AA7FF)
        self.brand_label = self._make_label(self.shell, 84, 26, 160, "AIRI", 0xF4F8FF, (18, 16, 14), 255)
        self.brand_sub = self._make_label(self.shell, 84, 52, 240, "conversation-first stage", 0x8194BC, (12, 10), 220)
        self.avatar_panel = self._make_box(self.shell, 24, 86, 258, 225, 0x0A1429, 214, 28, 1, 0x203455)
        self.avatar_stage = self._make_box(self.avatar_panel, 16, 0, 225, 225, 0x000000, 255, 24, 0, 0x000000)
        try:
            self.avatar_stage.add_flag(self.lv.obj.FLAG.CLIP_CORNER)
        except Exception:
            pass
        self.avatar_floor_glow = self._make_box(self.avatar_panel, 34, 168, 190, 42, 0x6AA7FF, 52, 999, 0, 0x6AA7FF)
        self._halo_base_x = 10
        self._halo_base_y = -8
        self._halo_base_size = 238
        self._ring_base_x = 30
        self._ring_base_y = 12
        self._ring_base_size = 198
        self.avatar_halo = self._make_box(self.avatar_panel, self._halo_base_x, self._halo_base_y, self._halo_base_size, self._halo_base_size, 0x6AA7FF, 42, 999, 0, 0x6AA7FF)
        self.avatar_ring = self._make_box(self.avatar_panel, self._ring_base_x, self._ring_base_y, self._ring_base_size, self._ring_base_size, 0x000000, 0, 999, 1, 0x79E9FF)
        self.avatar_canvas = self.lv.canvas(self.avatar_stage)
        self._set_hidden(self.avatar_canvas, True)
        self.avatar_image = self.lv.img(self.avatar_stage)
        self._set_hidden(self.avatar_image, True)
        self.avatar_static_src = self._resolve_static_avatar()
        self.avatar_fallback = self._make_label(self.avatar_panel, 82, 96, 100, "AIRI", 0xF4F8FF, (24, 22, 20), 220)
        try:
            self.avatar_stage.move_foreground()
        except Exception:
            pass
        try:
            self.avatar_image.move_foreground()
        except Exception:
            pass
        try:
            self.avatar_fallback.move_foreground()
        except Exception:
            pass
        self.status_panel = self._make_box(self.shell, 24, 325, 258, 131, 0x141E34, 228, 28, 1, 0x22365A)
        self.status_overline = self._make_label(self.status_panel, 22, 18, 132, "current state", 0x889ABB, (12, 10), 180)
        self.status_title = self._make_label(self.status_panel, 22, 46, 150, "IDLE", 0xF4F8FF, (34, 32, 30), 255)
        self.status_copy = self._make_label(self.status_panel, 22, 94, 214, "AIRI is here.", 0xD2DDF0, (14, 12), 255)
        self.chat_panel = self._make_box(self.shell, 300, 86, 530, 370, 0x0B162D, 234, 28, 1, 0x203455)
        self.chat_overline = self._make_label(self.chat_panel, 30, 24, 160, "dialog space", 0x889ABB, (12, 10), 180)
        self.chat_line = self._make_label(self.chat_panel, 30, 68, 452, "AIRI is here. Say the wake word when you want to start.", 0xF4F8FF, (48, 44, 40, 36), 255)
        self.chat_support = self._make_label(self.chat_panel, 30, 232, 470, "The main message should own the screen. Everything else steps back.", 0xD2DDF0, (14, 12), 255)
        self.chat_divider = self._make_box(self.chat_panel, 30, 296, 470, 1, 0x203455, 120, 0, 0, 0x203455)
        self.action_hint = self._make_label(self.chat_panel, 30, 312, 140, "next action", 0x889ABB, (12, 10), 180)
        self.action_button = self._make_box(self.chat_panel, 328, 306, 172, 46, 0x1C3858, 210, 18, 1, 0x79E9FF)
        self.action_label = self._make_label(self.action_button, 0, 13, 172, "Tap to speak", 0xF7FBFF, (16, 14, 12), 255)
        try:
            self.action_label.set_style_text_align(self.lv.TEXT_ALIGN.CENTER, 0)
        except Exception:
            pass
        self.avatar_candidates = []
        raw_rows = self._static_avatar_rgb565_candidates()
        index = 0
        while index < len(raw_rows):
            self.avatar_candidates.append(raw_rows[index].get("path"))
            index += 1
        self.avatar_candidates.extend(self._static_avatar_candidates())
        index = 0
        while index < len(AIRI_EXPRESSION_MANIFEST_CANDIDATES):
            self.avatar_candidates.append(AIRI_EXPRESSION_MANIFEST_CANDIDATES[index])
            index += 1
        self._ensure_gif_player_locked()
        self._ensure_expression_animimg_locked()
        try:
            self.expression_player = AiriFramePlayer(self.display, self.avatar_stage)
            self.expression_ready = bool(self.expression_player.available())
            if self.expression_ready:
                self.expression_player.set_layout(zoom=328)
                if self.expression_player.manifest_path:
                    self.avatar_candidates.append(self.expression_player.manifest_path)
            elif self.avatar_static_src:
                self._apply_static_avatar_source_locked()
        except Exception as e:
            self.expression_player = None
            self.expression_ready = False
            if self.avatar_static_src:
                try:
                    self._apply_static_avatar_source_locked()
                except Exception:
                    pass
            else:
                self.avatar_error = _string(e)
        try:
            self.miaoban = MiaobanPlayer(self.display, self.avatar_stage)
            self.miaoban_ready = bool(self.miaoban.available())
            if self.miaoban_ready:
                self.miaoban.set_layout(zoom=292)
                self.avatar_candidates.extend(
                    [
                        self.miaoban._asset_path("neutral"),
                        self.miaoban._asset_path("listen"),
                        self.miaoban._asset_path("happy"),
                    ]
                )
        except Exception as e:
            self.miaoban = None
            self.miaoban_ready = False
            if not self.avatar_static_src:
                self.avatar_exists = False
                self.avatar_error = _string(e)
        self.lv.scr_load(self.screen)
        try:
            if hasattr(self.display, "set_pump_hook"):
                self.display.set_pump_hook(self._pump_anim)
        except Exception as e:
            self.avatar_error = _string(e)
        self._apply_scene_visibility_locked()
        self._apply_mode_locked()
        self._apply_overlay_locked()

    def ensure_ready(self):
        if self.ready:
            return True
        self.display.ensure_ready()
        self.lv = getattr(self.display, "lv", None)
        self.display.acquire()
        try:
            if self.ready:
                return True
            self._build_screen_locked()
            self.ready = True
        finally:
            self.display.release()
        return True

    def _advance_anim_locked(self):
        if not self.ready:
            return False
        self._anim_tick += 1
        if self.avatar_stage is not None:
            offset = 0
            if self.avatar_render_mode == "miaoban":
                offset = PRESENCE_SWING[self._anim_tick % len(PRESENCE_SWING)]
            self.avatar_stage.set_y(self._avatar_stage_base_y + int(offset))
        if self.avatar_render_mode == "airi-frame" and self.expression_ready and self.expression_player is not None:
            try:
                self.expression_player.tick()
            except Exception as e:
                self.avatar_error = _string(e)
        if self.avatar_render_mode == "miaoban" and self.miaoban_ready and self.miaoban is not None:
            try:
                self.miaoban.tick()
            except Exception as e:
                self.avatar_error = _string(e)
        return True

    def _pump_anim(self):
        now = self._ticks_ms()
        if self._last_anim_ms > 0 and now > 0 and self.utime is not None:
            try:
                if self.utime.ticks_diff(now, self._last_anim_ms) < 90:
                    return False
            except Exception:
                pass
        self._last_anim_ms = now
        return self._advance_anim_locked()

    def show_booting(self):
        self.ensure_ready()
        return self.render_runtime_state(
            "idle",
            "BOOT // AIRI",
            "AIRI is booting on this board now.",
            "Display and scene are being prepared for runtime.",
            mood="wake"
        )

    def show_ready(self):
        self.ensure_ready()
        return self.render_runtime_state(
            "talk",
            "AIRI is currently responding and the conversation becomes the visual center.",
            "I am answering you now. This line should become the strongest message on screen.",
            "When AIRI speaks, the dialogue area should dominate attention naturally.",
            mood="happy"
        )

    def show_waiting(self):
        self.ensure_ready()
        return self.render_runtime_state(
            "listen",
            "AIRI is awake and quietly waiting for your next input.",
            "AIRI is here. Say the wake word when you want to start.",
            "The main message should own the screen. Everything else steps back.",
            mood="listen"
        )

    def show_error(self, message=None):
        self.ensure_ready()
        return self.render_runtime_state(
            "listen",
            "ERROR // AIRI",
            _string(message) or "Board UI raised an error.",
            "The scene stays visible for debugging.",
            mood="shocked"
        )

    def set_expression_engine(self, engine):
        self.ensure_ready()
        self.display.acquire()
        try:
            target = _string(engine).strip().lower()
            if target not in ("gif", "frame", "animimg"):
                target = "frame"
            if target == "gif":
                self._ensure_gif_player_locked()
            if target == "animimg":
                self._ensure_expression_animimg_locked()
            self.expression_engine = target
            self.fill_only = False
            self.scene_visible = True
            self._apply_scene_visibility_locked()
            self._apply_mode_locked()
            self._apply_overlay_locked()
            self.lv.scr_load(self.screen)
            return {
                "engine": self.expression_engine,
                "gif_ready": bool(self.gif_ready),
                "animimg_ready": bool(self.animimg_ready),
                "expression_ready": bool(self.expression_ready),
                "avatar_render_mode": self.avatar_render_mode,
            }
        finally:
            self.display.release()

    def render_runtime_state(self, mode_key, status, message, footer, mood=""):
        self.ensure_ready()
        self.display.acquire()
        try:
            self.fill_only = False
            self.scene_visible = True
            self.mode_key = _string(mode_key).strip().lower()
            if self.mode_key not in MODE_KEYS:
                self.mode_key = "idle"
            self.overlay_status = _string(status)
            self.overlay_message = _string(message)
            self.overlay_footer = _string(footer)
            self.overlay_mood = _string(mood)
            self._style_box(self.screen, 0x050914, 255, 0, 0, 0x050914)
            self._apply_scene_visibility_locked()
            self._apply_mode_locked()
            self._apply_overlay_locked()
            self.lv.scr_load(self.screen)
            return True
        finally:
            self.display.release()

    def set_mode(self, mode_key):
        self.ensure_ready()
        self.display.acquire()
        try:
            key = _string(mode_key).strip().lower()
            if key not in MODE_KEYS:
                key = "idle"
            self.mode_key = key
            self.fill_only = False
            self.scene_visible = True
            self._style_box(self.screen, 0x050914, 255, 0, 0, 0x050914)
            self._apply_scene_visibility_locked()
            self._apply_mode_locked()
            self._apply_overlay_locked()
            self.lv.scr_load(self.screen)
            return True
        finally:
            self.display.release()

    def set_overlay(self, status=None, message=None, footer=None, mood=None):
        self.ensure_ready()
        self.display.acquire()
        try:
            if status is not None:
                self.overlay_status = _string(status)
            if message is not None:
                self.overlay_message = _string(message)
            if footer is not None:
                self.overlay_footer = _string(footer)
            if mood is not None:
                self.overlay_mood = _string(mood)
            self.fill_only = False
            self.scene_visible = True
            self._apply_scene_visibility_locked()
            self._apply_overlay_locked()
            self.lv.scr_load(self.screen)
            return True
        finally:
            self.display.release()

    def clear_overlay(self):
        self.overlay_status = ""
        self.overlay_message = ""
        self.overlay_footer = ""
        self.overlay_mood = ""
        if self.ready:
            self.display.acquire()
            try:
                self._apply_overlay_locked()
            finally:
                self.display.release()
        return True

    def show_fill(self, color):
        self.ensure_ready()
        self.display.acquire()
        try:
            self.fill_only = True
            self.scene_visible = False
            self._style_box(self.screen, int(color) & 0xFFFFFF, 255, 0, 0, int(color) & 0xFFFFFF)
            self._apply_scene_visibility_locked()
            self.lv.scr_load(self.screen)
            return True
        finally:
            self.display.release()

    def show_scene(self):
        self.ensure_ready()
        self.display.acquire()
        try:
            self.fill_only = False
            self.scene_visible = True
            self._style_box(self.screen, 0x050914, 255, 0, 0, 0x050914)
            self._apply_scene_visibility_locked()
            self._apply_mode_locked()
            self._apply_overlay_locked()
            self.lv.scr_load(self.screen)
            return True
        finally:
            self.display.release()

    def snapshot(self):
        return {
            "ready": bool(self.ready),
            "mode_key": self.mode_key,
            "fill_only": bool(self.fill_only),
            "scene_visible": bool(self.scene_visible),
            "overlay_status": self.overlay_status,
            "overlay_message": self.overlay_message,
            "overlay_footer": self.overlay_footer,
            "overlay_mood": self.overlay_mood,
            "avatar_src": self.avatar_src,
            "avatar_exists": bool(self.avatar_exists),
            "avatar_error": self.avatar_error,
            "avatar_candidates": list(self.avatar_candidates),
            "avatar_render_mode": self.avatar_render_mode,
            "avatar_static_src": self.avatar_static_src,
            "current_emote": self.current_emote,
            "current_expression": self.current_expression,
            "expression_engine": self.expression_engine,
            "gif_ready": bool(self.gif_ready),
            "gif_player": self.gif_player.snapshot() if self.gif_player is not None else None,
            "expression_ready": bool(self.expression_ready),
            "expression_player": self.expression_player.snapshot() if self.expression_player is not None else None,
            "animimg_ready": bool(self.animimg_ready),
            "expression_animimg": self.expression_animimg.snapshot() if self.expression_animimg is not None else None,
            "screen_width": self._screen_width,
            "screen_height": self._screen_height,
            "avatar_canvas_width": self.avatar_canvas_width,
            "avatar_canvas_height": self.avatar_canvas_height,
            "avatar_panel": self._obj_snapshot(self.avatar_panel),
            "avatar_stage": self._obj_snapshot(self.avatar_stage),
            "avatar_image": self._obj_snapshot(self.avatar_image, True),
            "avatar_fallback": self._obj_snapshot(self.avatar_fallback),
            "status_panel": self._obj_snapshot(self.status_panel),
            "chat_panel": self._obj_snapshot(self.chat_panel),
            "action_button": self._obj_snapshot(self.action_button),
            "anim_tick": self._anim_tick,
        }

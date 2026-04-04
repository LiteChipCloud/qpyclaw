def _safe_import(name):
    try:
        return __import__(name)
    except Exception:
        return None


class BoardEmojiUi(object):

    def __init__(self, display, media_prefix="U:/media"):
        self.display = display
        self.media_prefix = media_prefix
        self.uos = _safe_import("uos")
        self.utime = _safe_import("utime")
        self.lv = None
        self.screen = None
        self.screen_img = None
        self.overlay = None
        self.overlay_status_label = None
        self.overlay_message_label = None
        self.overlay_status_text = ""
        self.overlay_message_text = ""
        self.current_emoji = ""
        self.current_src = ""
        self.current_src_candidates = []
        self.ready = False
        self.passive_mode = ""
        self.passive_color = None
        self.supported_emojis = [
            "angry",
            "confident",
            "cool",
            "crying",
            "delicious",
            "funny",
            "happy",
            "kissy",
            "laughing",
            "loving",
            "neutral",
            "sleepy",
            "sad",
            "surprised",
            "winking",
            "thinking",
            "relaxed",
            "shocked",
            "embarrassed",
            "confused",
        ]

    def _string(self, value):
        if value is None:
            return ""
        try:
            return str(value)
        except Exception:
            return ""

    def _normalize_overlay_text(self, value, limit=0):
        text = self._string(value).replace("\r", "\n")
        rows = []
        for row in text.split("\n"):
            line = row.strip()
            if line:
                rows.append(line)
        text = "\n".join(rows).strip()
        if limit and len(text) > limit:
            text = text[: max(0, int(limit) - 3)].rstrip() + "..."
        return text

    def _media_prefixes(self):
        rows = []
        for prefix in [self.media_prefix, "U:/media", "/usr/media", "usr/media"]:
            text = str(prefix or "").strip()
            if (not text) or text in rows:
                continue
            rows.append(text)
        return rows

    def resolved_media_prefix(self):
        for prefix in self._media_prefixes():
            if self._path_exists(prefix + "/neutral.png"):
                return prefix
        return self.media_prefix

    def _lvgl_media_prefixes(self):
        rows = []
        for prefix in self._media_prefixes():
            text = str(prefix or "").strip().rstrip("/")
            if not text:
                continue
            if text not in rows:
                rows.append(text)
            if text.startswith("/"):
                relative = text[1:]
                if relative and relative not in rows:
                    rows.append(relative)
        return rows

    def ensure_ready(self):
        if self.ready:
            return True
        self.display.ensure_ready()
        self.lv = self.display.lv
        self.screen = self.lv.obj()
        self.screen.set_size(self.display.width, self.display.height)
        self.screen.set_scrollbar_mode(self.lv.SCROLLBAR_MODE.OFF)
        self.screen.set_style_bg_opa(255, self.lv.PART.MAIN | self.lv.STATE.DEFAULT)
        self.screen.set_style_bg_color(self.lv.color_hex(0x000000), self.lv.PART.MAIN | self.lv.STATE.DEFAULT)
        self.screen.set_style_bg_grad_dir(self.lv.GRAD_DIR.NONE, self.lv.PART.MAIN | self.lv.STATE.DEFAULT)
        self.screen.center()
        self.screen.set_flex_align(
            self.lv.FLEX_ALIGN.SPACE_EVENLY,
            self.lv.FLEX_ALIGN.CENTER,
            self.lv.FLEX_ALIGN.CENTER,
        )
        self.screen.set_flex_flow(self.lv.FLEX_FLOW.COLUMN)
        self.screen_img = self.lv.img(self.screen)
        self.screen_img.set_style_bg_color(self.lv.color_hex(0x000000), 0)
        self.screen_img.set_style_bg_opa(self.lv.OPA.COVER, 0)
        self.screen_img.set_size(self.display.width, self.display.height)
        self._ensure_overlay()
        self.lv.scr_load(self.screen)
        self.ready = True
        self.show_emotion("neutral")
        return True

    def _ensure_overlay(self):
        if self.overlay is not None:
            return True
        self.overlay = self.lv.obj(self.screen)
        self.overlay.set_size(self.display.width - 12, 76)
        self.overlay.align(self.lv.ALIGN.BOTTOM_MID, 0, -6)
        self.overlay.set_scrollbar_mode(self.lv.SCROLLBAR_MODE.OFF)
        try:
            self.overlay.clear_flag(self.lv.obj.FLAG.SCROLLABLE)
        except Exception:
            pass
        try:
            self.overlay.set_style_radius(10, 0)
        except Exception:
            pass
        try:
            self.overlay.set_style_border_width(0, 0)
        except Exception:
            pass
        self.overlay.set_style_bg_color(self.lv.color_hex(0x101010), 0)
        self.overlay.set_style_bg_opa(168, 0)
        try:
            self.overlay.set_style_pad_all(0, 0)
        except Exception:
            pass

        self.overlay_status_label = self.lv.label(self.overlay)
        self.overlay_status_label.set_width(self.display.width - 28)
        self.overlay_status_label.set_long_mode(self.lv.label.LONG.CLIP)
        self.overlay_status_label.align(self.lv.ALIGN.TOP_LEFT, 8, 6)
        try:
            self.overlay_status_label.set_style_text_color(self.lv.color_hex(0xFFFFFF), 0)
        except Exception:
            pass
        try:
            self.overlay_status_label.set_style_text_font(self.lv.font_montserrat_14, 0)
        except Exception:
            pass
        self.overlay_status_label.set_text("")

        self.overlay_message_label = self.lv.label(self.overlay)
        self.overlay_message_label.set_size(self.display.width - 28, 42)
        self.overlay_message_label.set_long_mode(self.lv.label.LONG.WRAP)
        self.overlay_message_label.align(self.lv.ALIGN.TOP_LEFT, 8, 26)
        try:
            self.overlay_message_label.set_style_text_color(self.lv.color_hex(0xE8E8E8), 0)
        except Exception:
            pass
        try:
            self.overlay_message_label.set_style_text_font(self.lv.font_montserrat_14, 0)
        except Exception:
            pass
        self.overlay_message_label.set_text("")
        try:
            self.overlay.add_flag(self.lv.obj.FLAG.HIDDEN)
        except Exception:
            pass
        return True

    def _emotion_path(self, emotion):
        media_prefix = self.resolved_media_prefix()
        if emotion in self.supported_emojis:
            return media_prefix + "/" + emotion + ".png"
        return media_prefix + "/neutral.png"

    def _lvgl_src_candidates(self, emotion):
        rows = []
        if emotion not in self.supported_emojis:
            emotion = "neutral"
        for prefix in self._lvgl_media_prefixes():
            path = prefix + "/" + emotion + ".png"
            text = str(path or "").strip()
            if (not text) or text in rows:
                continue
            rows.append(text)
        return rows

    def _path_exists(self, path):
        if self.uos is None:
            return None
        try:
            self.uos.stat(path)
            return True
        except Exception:
            return False

    def available_emojis(self):
        rows = []
        for emotion in self.supported_emojis:
            if self._path_exists(self._emotion_path(emotion)):
                rows.append(emotion)
        return rows

    def catalog(self):
        available = self.available_emojis()
        return {
            "media_prefix": self.media_prefix,
            "resolved_media_prefix": self.resolved_media_prefix(),
            "media_prefix_candidates": self._media_prefixes(),
            "supported_emojis": self.supported_emojis[:],
            "supported_emoji_count": len(self.supported_emojis),
            "available_emojis": available,
            "available_emoji_count": len(available),
        }

    def show_emotion(self, emotion):
        self.ensure_ready()
        if emotion == self.current_emoji and (not self.passive_mode):
            self._refresh()
            return True
        if emotion not in self.supported_emojis:
            emotion = "neutral"
        chosen_src = ""
        self.current_src_candidates = self._lvgl_src_candidates(emotion)
        try:
            self.lv.img.cache_invalidate_src(None)
        except Exception:
            pass
        for src in self.current_src_candidates:
            chosen_src = src
            try:
                self.screen_img.set_src(src)
                break
            except Exception:
                chosen_src = ""
        self.current_emoji = emotion
        self.current_src = chosen_src
        self.passive_mode = ""
        self.passive_color = None
        self._refresh()
        return True

    def show_overlay(self, status=None, message=None):
        self.ensure_ready()
        self._ensure_overlay()
        if status is not None:
            self.overlay_status_text = self._normalize_overlay_text(status, limit=28)
        if message is not None:
            self.overlay_message_text = self._normalize_overlay_text(message, limit=120)
        if (not self.overlay_status_text) and (not self.overlay_message_text):
            return self.clear_overlay()
        try:
            self.overlay.clear_flag(self.lv.obj.FLAG.HIDDEN)
        except Exception:
            pass
        try:
            self.overlay_status_label.set_text(self.overlay_status_text)
        except Exception:
            pass
        try:
            self.overlay_message_label.set_text(self.overlay_message_text)
        except Exception:
            pass
        self._refresh()
        return True

    def show_status(self, status):
        return self.show_overlay(status=status, message=None)

    def show_message(self, message):
        return self.show_overlay(status=None, message=message)

    def clear_overlay(self):
        self.ensure_ready()
        self._ensure_overlay()
        self.overlay_status_text = ""
        self.overlay_message_text = ""
        try:
            self.overlay_status_label.set_text("")
        except Exception:
            pass
        try:
            self.overlay_message_label.set_text("")
        except Exception:
            pass
        try:
            self.overlay.add_flag(self.lv.obj.FLAG.HIDDEN)
        except Exception:
            pass
        self._refresh()
        return True

    def show_fill(self, color):
        self.display.ensure_ready()
        self.passive_mode = "fill"
        self.passive_color = int(color) & 0xFFFF
        self.current_emoji = ""
        self.current_src = ""
        self.current_src_candidates = []
        self.display.clear(self.passive_color)
        return True

    def _refresh(self):
        if not self.ready:
            return False
        for obj in [self.screen_img, self.overlay, self.overlay_status_label, self.overlay_message_label]:
            if obj is None:
                continue
            try:
                obj.invalidate()
            except Exception:
                pass
        count = 0
        while count < 3:
            self.display.pump()
            if self.utime is not None:
                try:
                    self.utime.sleep_ms(20)
                except Exception:
                    pass
            count += 1
        return True

    def show_booting(self):
        self.show_overlay(status="BOOTING", message="")
        return self.show_emotion("thinking")

    def show_ready(self):
        self.show_overlay(status="READY", message=None)
        return self.show_emotion("neutral")

    def show_waiting(self):
        self.show_overlay(status="WAITING", message=None)
        return self.show_emotion("sleepy")

    def show_error(self):
        self.show_overlay(status="ERROR", message=None)
        return self.show_emotion("confused")

    def tick(self):
        if self.passive_mode == "fill":
            return True
        return self.display.pump()

    def snapshot(self):
        current_path = ""
        current_exists = None
        if not self.passive_mode:
            current_emoji = self.current_emoji or "neutral"
            current_path = self._emotion_path(current_emoji)
            current_exists = self._path_exists(current_path)
        catalog = self.catalog()
        return {
            "ready": bool(self.ready),
            "passive_mode": self.passive_mode,
            "passive_color": self.passive_color,
            "current_emoji": self.current_emoji,
            "current_src": self.current_src,
            "current_src_candidates": self.current_src_candidates,
            "current_path": current_path,
            "current_asset_exists": current_exists,
            "overlay_status_text": self.overlay_status_text,
            "overlay_message_text": self.overlay_message_text,
            "overlay_visible": bool(self.overlay_status_text or self.overlay_message_text),
            "media_prefix": self.media_prefix,
            "resolved_media_prefix": catalog["resolved_media_prefix"],
            "media_prefix_candidates": catalog["media_prefix_candidates"],
            "lvgl_media_prefix_candidates": self._lvgl_media_prefixes(),
            "supported_emojis": catalog["supported_emojis"],
            "supported_emoji_count": catalog["supported_emoji_count"],
            "available_emojis": catalog["available_emojis"],
            "available_emoji_count": catalog["available_emoji_count"],
        }

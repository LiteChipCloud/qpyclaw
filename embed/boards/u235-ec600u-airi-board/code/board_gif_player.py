GIF_EMOTES = (
    "angry",
    "confident",
    "confused",
    "cool",
    "crying",
    "delicious",
    "embarrassed",
    "funny",
    "happy",
    "kissy",
    "laughing",
    "loving",
    "neutral",
    "relaxed",
    "sad",
    "silly",
    "sleep",
    "surprised",
    "thinking",
    "winking",
)


GIF_ALIASES = {
    "wake": "neutral",
    "idle": "neutral",
    "standby": "neutral",
    "idle_blink": "neutral",
    "listen": "thinking",
    "listening": "thinking",
    "asking": "thinking",
    "listen_focus": "thinking",
    "thinking": "thinking",
    "talk": "happy",
    "speak": "happy",
    "speaking": "happy",
    "talk_smile": "happy",
    "talk_open": "happy",
    "happy_pop": "happy",
    "sleepy": "sleep",
    "sleep_breath": "sleep",
    "sad_soft": "sad",
    "cry": "crying",
    "angry_fire": "angry",
    "anger": "angry",
    "shock_hold": "surprised",
    "shocked": "surprised",
    "panic": "surprised",
    "error": "surprised",
    "wink_ping": "winking",
    "blink": "winking",
}


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _file_exists(path):
    if not path:
        return False
    try:
        fp = open(path, "rb")
        fp.close()
        return True
    except Exception:
        return False


def _normalize_name(value):
    text = _string(value).strip().lower().replace("-", "_").replace(" ", "_")
    if not text:
        return ""
    if text in GIF_EMOTES:
        return text
    if text in GIF_ALIASES:
        return GIF_ALIASES.get(text)
    return text


def _normalize_path(path):
    return _string(path).replace("\\", "/")


def _join_path(base, child):
    left = _normalize_path(base)
    right = _normalize_path(child)
    if not left:
        return right
    if not right:
        return left
    if right.startswith("/") or (":/" in right):
        return right
    if left.endswith("/"):
        return left + right
    return left + "/" + right


class AiriGifPlayer(object):

    def __init__(self, display, parent, search_roots=None):
        self.display = display
        self.lv = getattr(display, "lv", None)
        self.parent = parent
        self.search_roots = search_roots or ("/usr/media", "U:/media")
        self.ready = False
        self.supported = bool(self.lv is not None and hasattr(self.lv, "gif"))
        self.available_flag = False
        self.widget = None
        self.current_name = ""
        self.current_src = ""
        self.width = 240
        self.height = 240
        self.zoom = 240
        self.layout_x = None
        self.layout_y = None
        self.layout_zoom = None
        self.last_error = ""
        if not self.supported:
            self.last_error = "lv.gif unavailable"

    def _set_hidden(self, obj, hidden):
        if obj is None:
            return False
        try:
            if hidden:
                obj.add_flag(self.lv.obj.FLAG.HIDDEN)
            else:
                obj.clear_flag(self.lv.obj.FLAG.HIDDEN)
            return True
        except Exception:
            return False

    def _asset_path(self, name):
        resolved = _normalize_name(name)
        if not resolved:
            return ""
        index = 0
        while index < len(self.search_roots):
            path = _join_path(self.search_roots[index], resolved + ".gif")
            if _file_exists(path):
                return path
            index += 1
        return ""

    def _resolve_asset(self, primary_name, fallback_name):
        resolved = _normalize_name(primary_name)
        path = self._asset_path(resolved)
        if path:
            return resolved, path
        resolved = _normalize_name(fallback_name)
        path = self._asset_path(resolved)
        if path:
            return resolved, path
        path = self._asset_path("neutral")
        if path:
            return "neutral", path
        return "", ""

    def _ensure_widget(self):
        if not self.supported:
            return False
        if self.widget is not None:
            return True
        self.widget = self.lv.gif(self.parent)
        self._set_hidden(self.widget, True)
        try:
            self.widget.set_size(int(self.width or 240), int(self.height or 240))
        except Exception:
            pass
        return True

    def _query_size(self):
        if self.widget is None:
            return False
        width = 0
        height = 0
        try:
            width = int(self.widget.get_width())
        except Exception:
            width = 0
        try:
            height = int(self.widget.get_height())
        except Exception:
            height = 0
        if width > 0:
            self.width = width
        if height > 0:
            self.height = height
        return True

    def _apply_zoom(self):
        if self.widget is None:
            return False
        zoom = int(self.layout_zoom or self.zoom or 256)
        self.zoom = zoom
        try:
            self.widget.set_style_transform_pivot_x(int(self.width / 2), 0)
            self.widget.set_style_transform_pivot_y(int(self.height / 2), 0)
        except Exception:
            pass
        try:
            self.widget.set_style_transform_zoom(zoom, 0)
            return True
        except Exception:
            pass
        try:
            self.widget.set_zoom(zoom)
            return True
        except Exception:
            return False

    def _layout_widget(self):
        if self.widget is None:
            return False
        parent_w = 225
        parent_h = 225
        try:
            value = int(self.parent.get_width())
            if value > 0:
                parent_w = value
        except Exception:
            pass
        try:
            value = int(self.parent.get_height())
            if value > 0:
                parent_h = value
        except Exception:
            pass
        zoom = int(self.layout_zoom or self.zoom or 256)
        draw_w = int((int(self.width or 0) * zoom) / 256)
        draw_h = int((int(self.height or 0) * zoom) / 256)
        if self.layout_x is None:
            x = int((parent_w - draw_w) / 2)
        else:
            x = int(self.layout_x)
        if self.layout_y is None:
            y = int((parent_h - draw_h) / 2)
        else:
            y = int(self.layout_y)
        try:
            self.widget.set_size(int(self.width or 240), int(self.height or 240))
        except Exception:
            pass
        self.widget.set_pos(x, y)
        self._apply_zoom()
        return True

    def available(self):
        if not self.supported:
            return False
        if self.available_flag:
            return True
        index = 0
        while index < len(GIF_EMOTES):
            if self._asset_path(GIF_EMOTES[index]):
                self.available_flag = True
                self.last_error = ""
                return True
            index += 1
        self.last_error = "gif assets missing"
        return False

    def catalog(self):
        rows = []
        index = 0
        while index < len(GIF_EMOTES):
            if self._asset_path(GIF_EMOTES[index]):
                rows.append(GIF_EMOTES[index])
            index += 1
        return rows

    def catalog_paths(self):
        rows = []
        names = self.catalog()
        index = 0
        while index < len(names):
            path = self._asset_path(names[index])
            if path:
                rows.append(path)
            index += 1
        return rows

    def set_layout(self, x=None, y=None, zoom=None):
        if x is not None:
            self.layout_x = int(x)
        if y is not None:
            self.layout_y = int(y)
        if zoom is not None:
            self.layout_zoom = int(zoom)
            self.zoom = int(zoom)
        if self.widget is not None:
            self._layout_widget()
        return True

    def set_expression(self, expression_name, fallback_name=""):
        if not self.available():
            return False
        name, path = self._resolve_asset(expression_name, fallback_name)
        if not path:
            self.last_error = "gif missing for " + _string(expression_name)
            return False
        self._ensure_widget()
        self.widget.set_src(path)
        self.current_name = name
        self.current_src = path
        self._query_size()
        self._layout_widget()
        self._set_hidden(self.widget, False)
        try:
            self.widget.invalidate()
        except Exception:
            pass
        self.ready = True
        self.available_flag = True
        self.last_error = ""
        return True

    def tick(self):
        return True

    def show(self):
        self._set_hidden(self.widget, False)
        return True

    def hide(self):
        self._set_hidden(self.widget, True)
        return True

    def snapshot(self):
        return {
            "ready": bool(self.ready),
            "supported": bool(self.supported),
            "available": bool(self.available()),
            "current_name": self.current_name,
            "current_src": self.current_src,
            "width": self.width,
            "height": self.height,
            "zoom": self.zoom,
            "catalog": self.catalog(),
            "last_error": self.last_error,
        }

try:
    import ujson as _json
except Exception:
    _json = None

from board_airi_expression_data import AIRI_EXPRESSION_MANIFEST_CANDIDATES, resolve_expression_key


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


def _normalize_path(path):
    return _string(path).replace("\\", "/")


def _dirname(path):
    text = _normalize_path(path)
    slash = text.rfind("/")
    if slash < 0:
        return ""
    if slash == 0:
        return "/"
    return text[:slash]


def _join_path(base, child):
    right = _normalize_path(child)
    if not right:
        return _normalize_path(base)
    if right.startswith("/") or (":/" in right):
        return right
    left = _normalize_path(base)
    if not left:
        return right
    if left.endswith("/"):
        return left + right
    return left + "/" + right


class AiriFramePlayer(object):

    def __init__(self, display, parent, manifest_candidates=None):
        self.display = display
        self.lv = getattr(display, "lv", None)
        self.parent = parent
        self.manifest_candidates = manifest_candidates or AIRI_EXPRESSION_MANIFEST_CANDIDATES
        self.ready = False
        self.available_flag = False
        self.manifest_loaded = False
        self.manifest_path = ""
        self.manifest_dir = ""
        self.manifest = {}
        self.expressions = {}
        self.default_key = "idle_blink"
        self.canvas = None
        self.image = None
        self.canvas_buf = None
        self.width = 0
        self.height = 0
        self.zoom = 256
        self.layout_x = None
        self.layout_y = None
        self.layout_zoom = None
        self.current_key = ""
        self.current_entry = None
        self.current_src = ""
        self.current_tick_step = 1
        self.frame_index = 0
        self.frame_hold = 0
        self.last_error = ""
        self.current_frame_format = ""
        self.frame_cache = {}
        self.frame_cache_bytes = 0
        self.max_cache_bytes = 384 * 1024

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

    def _ensure_manifest(self):
        if self.manifest_loaded:
            return bool(self.available_flag)
        self.manifest_loaded = True
        index = 0
        while index < len(self.manifest_candidates):
            path = self.manifest_candidates[index]
            if _file_exists(path):
                try:
                    if _json is None:
                        raise Exception("ujson unavailable")
                    fp = open(path, "r")
                    try:
                        text = fp.read()
                    finally:
                        fp.close()
                    data = _json.loads(text)
                    if not isinstance(data, dict):
                        raise Exception("manifest must be dict")
                    self.manifest_path = path
                    self.manifest_dir = _dirname(path)
                    self.manifest = data
                    rows = data.get("expressions") or {}
                    if isinstance(rows, dict):
                        self.expressions = rows
                    else:
                        self.expressions = {}
                    self.default_key = resolve_expression_key(data.get("default"), "idle_blink")
                    self.last_error = ""
                    self.available_flag = False
                    if self._has_expression(self.default_key):
                        self.available_flag = True
                    else:
                        for item_key in self.expressions:
                            if self._has_expression(item_key):
                                self.available_flag = True
                                break
                    return self.available_flag
                except Exception as e:
                    self.last_error = _string(e)
            index += 1
        self.available_flag = False
        if not self.last_error:
            self.last_error = "manifest missing"
        return False

    def _entry_for_key(self, key):
        if not self.manifest_loaded:
            self._ensure_manifest()
        if not self.manifest_loaded:
            return None
        if not isinstance(self.expressions, dict) or not self.expressions:
            return None
        resolved = resolve_expression_key(key, self.default_key)
        if resolved in self.expressions:
            return self.expressions.get(resolved)
        if self.default_key in self.expressions:
            return self.expressions.get(self.default_key)
        for item_key in self.expressions:
            return self.expressions.get(item_key)
        return None

    def _frame_path(self, frame_row):
        if isinstance(frame_row, dict):
            path = frame_row.get("path")
        else:
            path = frame_row
        return _join_path(self.manifest_dir, path)

    def _has_expression(self, key):
        entry = self._entry_for_key(key)
        if not isinstance(entry, dict):
            return False
        frames = entry.get("frames") or []
        if not isinstance(frames, list) or not frames:
            return False
        frame_path = self._frame_path(frames[0])
        if not _file_exists(frame_path):
            return False
        return True

    def available(self):
        return self._ensure_manifest()

    def catalog(self):
        if not self.manifest_loaded:
            self._ensure_manifest()
        if not isinstance(self.expressions, dict) or not self.expressions:
            return []
        rows = []
        for key in self.expressions:
            rows.append(key)
        rows.sort()
        return rows

    def set_layout(self, x=None, y=None, zoom=None):
        if x is not None:
            self.layout_x = int(x)
        if y is not None:
            self.layout_y = int(y)
        if zoom is not None:
            self.layout_zoom = int(zoom)
        if self.image is not None:
            self._layout_image()
        return True

    def _ensure_canvas(self, width, height, zoom):
        width = int(width or 0)
        height = int(height or 0)
        zoom = int(zoom or 256)
        if width <= 0 or height <= 0:
            raise Exception("invalid frame size")
        if self.canvas is None:
            self.canvas = self.lv.canvas(self.parent)
            self._set_hidden(self.canvas, True)
        if self.image is None:
            self.image = self.lv.img(self.parent)
            self._set_hidden(self.image, True)
        if self.canvas_buf is None or self.width != width or self.height != height:
            self.canvas_buf = bytearray(width * height * 2)
            self.canvas.set_buffer(self.canvas_buf, width, height, self.lv.img.CF.TRUE_COLOR)
        self.width = width
        self.height = height
        self.zoom = int(self.layout_zoom or zoom or 256)
        self.image.set_src(self.canvas.get_img())
        try:
            self.image.set_zoom(self.zoom)
        except Exception:
            pass
        self._layout_image()
        self.ready = True
        return True

    def _ensure_image(self, width, height, zoom):
        width = int(width or 0)
        height = int(height or 0)
        zoom = int(zoom or 256)
        if self.image is None:
            self.image = self.lv.img(self.parent)
            self._set_hidden(self.image, True)
        self.width = width
        self.height = height
        self.zoom = int(self.layout_zoom or zoom or 256)
        try:
            self.image.set_zoom(self.zoom)
        except Exception:
            pass
        self._layout_image()
        self.ready = True
        return True

    def _layout_image(self):
        if self.image is None:
            return False
        zoom = int(self.zoom or 256)
        draw_w = int((self.width * zoom) / 256)
        draw_h = int((self.height * zoom) / 256)
        parent_w = 258
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
        if self.layout_x is None:
            x = int((parent_w - draw_w) / 2)
        else:
            x = int(self.layout_x)
        if self.layout_y is None:
            y = int((parent_h - draw_h) / 2)
        else:
            y = int(self.layout_y)
        self.image.set_pos(x, y)
        return True

    def _copy_frame(self, data):
        if self.canvas_buf is None:
            return False
        try:
            self.canvas_buf[:] = data
            return True
        except Exception:
            index = 0
            size = len(data)
            while index < size:
                self.canvas_buf[index] = data[index]
                index += 1
            return True

    def _frame_bytes(self, path, width, height):
        fp = open(path, "rb")
        try:
            data = fp.read()
        finally:
            fp.close()
        expected = int(width or 0) * int(height or 0) * 2
        if len(data) != expected:
            raise Exception("frame rgb565 size mismatch")
        return data

    def _frame_format(self, entry, frame_path):
        format_name = _string(entry.get("frame_format")).strip().lower()
        if format_name:
            return format_name
        if _normalize_path(frame_path).lower().endswith(".rgb565"):
            return "rgb565"
        return "file"

    def _prepare_frame_cache(self, entry):
        self.frame_cache = {}
        self.frame_cache_bytes = 0
        frames = entry.get("frames") or []
        if not isinstance(frames, list) or not frames:
            return False
        width = int(entry.get("width") or 0)
        height = int(entry.get("height") or 0)
        total_bytes = 0
        index = 0
        while index < len(frames):
            frame_path = self._frame_path(frames[index])
            if self._frame_format(entry, frame_path) != "rgb565":
                index += 1
                continue
            if frame_path in self.frame_cache:
                index += 1
                continue
            data = self._frame_bytes(frame_path, width, height)
            total_bytes += len(data)
            if total_bytes > int(self.max_cache_bytes or 0):
                self.frame_cache = {}
                self.frame_cache_bytes = 0
                return False
            self.frame_cache[frame_path] = data
            index += 1
        self.frame_cache_bytes = total_bytes
        return bool(self.frame_cache)

    def _apply_frame(self, entry, frame_index):
        frames = entry.get("frames") or []
        if not frames:
            raise Exception("expression has no frames")
        if frame_index < 0 or frame_index >= len(frames):
            frame_index = 0
        width = int(entry.get("width") or 0)
        height = int(entry.get("height") or 0)
        zoom = int(entry.get("zoom") or 256)
        frame_path = self._frame_path(frames[frame_index])
        frame_format = self._frame_format(entry, frame_path)
        if frame_path == self.current_src and frame_format == self.current_frame_format:
            return True
        self.current_frame_format = frame_format
        if frame_format == "rgb565":
            data = self.frame_cache.get(frame_path)
            if data is None:
                data = self._frame_bytes(frame_path, width, height)
            self._ensure_canvas(width, height, zoom)
            self._copy_frame(data)
            self.image.set_src(self.canvas.get_img())
            try:
                self.canvas.invalidate()
            except Exception:
                pass
        else:
            self._ensure_image(width, height, zoom)
            self.image.set_src(frame_path)
            try:
                actual_width = int(self.image.get_width())
                if actual_width > 0:
                    self.width = actual_width
            except Exception:
                pass
            try:
                actual_height = int(self.image.get_height())
                if actual_height > 0:
                    self.height = actual_height
            except Exception:
                pass
            self._layout_image()
        self._set_hidden(self.image, False)
        try:
            self.image.invalidate()
        except Exception:
            pass
        self.current_src = frame_path
        return True

    def set_expression(self, expression_key):
        if not self._ensure_manifest():
            return False
        key = resolve_expression_key(expression_key, self.default_key)
        entry = self._entry_for_key(key)
        if entry is None:
            return False
        if self.current_key != key:
            self.current_key = key
            self.current_entry = entry
            self.frame_index = 0
            self.frame_hold = 0
            self.current_tick_step = int(entry.get("tick_step") or 1)
            if self.current_tick_step <= 0:
                self.current_tick_step = 1
            self._prepare_frame_cache(entry)
            self._apply_frame(entry, 0)
        return True

    def tick(self):
        if self.current_entry is None:
            return False
        frames = self.current_entry.get("frames") or []
        if len(frames) <= 1:
            return True
        self.frame_hold += 1
        if self.frame_hold < int(self.current_tick_step or 1):
            return True
        self.frame_hold = 0
        self.frame_index += 1
        if self.frame_index >= len(frames):
            if bool(self.current_entry.get("loop", True)):
                self.frame_index = 0
            else:
                self.frame_index = len(frames) - 1
        self._apply_frame(self.current_entry, self.frame_index)
        return True

    def show(self):
        self._set_hidden(self.image, False)
        return True

    def hide(self):
        self._set_hidden(self.image, True)
        return True

    def snapshot(self):
        return {
            "ready": bool(self.ready),
            "available": bool(self.available_flag),
            "manifest_path": self.manifest_path,
            "current_key": self.current_key,
            "current_src": self.current_src,
            "frame_index": self.frame_index,
            "frame_hold": self.frame_hold,
            "width": self.width,
            "height": self.height,
            "zoom": self.zoom,
            "frame_format": self.current_frame_format,
            "frame_cache_bytes": self.frame_cache_bytes,
            "catalog": self.catalog(),
            "last_error": self.last_error,
        }

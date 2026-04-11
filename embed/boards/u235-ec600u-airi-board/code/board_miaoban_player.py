import ustruct as _struct


EMOTE_FILES = {
    "neutral": "neutral.eaf",
    "idle": "neutral.eaf",
    "listen": "listen.eaf",
    "happy": "Happy.eaf",
    "sad": "Sad.eaf",
    "cry": "cry.eaf",
    "sleep": "sleep.eaf",
    "angry": "angry.eaf",
    "confused": "confused.eaf",
    "shocked": "shocked.eaf",
    "winking": "winking.eaf",
}


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def _u16le(data, offset):
    return (data[offset] & 0xFF) | ((data[offset + 1] & 0xFF) << 8)


def _u32le(data, offset):
    return (
        (data[offset] & 0xFF)
        | ((data[offset + 1] & 0xFF) << 8)
        | ((data[offset + 2] & 0xFF) << 16)
        | ((data[offset + 3] & 0xFF) << 24)
    )


def _file_exists(path):
    if not path:
        return False
    try:
        fp = open(path, "rb")
        fp.close()
        return True
    except Exception:
        return False


def _replace_ext(path, new_ext):
    dot = path.rfind(".")
    if dot < 0:
        return path + new_ext
    return path[:dot] + new_ext


class MiaobanPlayer(object):

    def __init__(self, display, parent, asset_dir="/usr/media/miaoban"):
        self.display = display
        self.lv = getattr(display, "lv", None)
        self.parent = parent
        self.asset_dir = asset_dir
        self.ready = False
        self.available_flag = False
        self.canvas = None
        self.image = None
        self.canvas_buf = None
        self.asset_cache = {}
        self.current_key = ""
        self.current_meta = None
        self.frame_index = 0
        self.width = 0
        self.height = 0
        self.zoom = 256
        self.backdrop565 = 0xF7DF
        self.layout_x = None
        self.layout_y = None
        self.layout_zoom = None
        self.last_error = ""

    def _write_bytes(self, offset, data):
        if self.canvas_buf is None:
            return False
        size = len(data)
        if size <= 0:
            return True
        offset = int(offset or 0)
        try:
            _struct.pack_into("%ds" % size, self.canvas_buf, offset, data)
            return True
        except Exception:
            index = 0
            while index < size:
                _struct.pack_into("B", self.canvas_buf, offset + index, data[index])
                index += 1
            return True

    def _write_u16(self, offset, value):
        if self.canvas_buf is None:
            return False
        _struct.pack_into("<H", self.canvas_buf, int(offset or 0), int(value or 0) & 0xFFFF)
        return True

    def available(self):
        if self.available_flag:
            return True
        path = self._asset_path("neutral")
        try:
            if not _file_exists(path):
                raise Exception("neutral asset missing")
            self.available_flag = True
            self.last_error = ""
        except Exception:
            self.available_flag = False
            self.last_error = path
        return self.available_flag

    def set_backdrop565(self, value):
        self.backdrop565 = int(value or 0) & 0xFFFF
        return True

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

    def _asset_path(self, emote_name):
        key = _string(emote_name).strip().lower()
        file_name = EMOTE_FILES.get(key) or EMOTE_FILES.get("neutral")
        neutral_name = EMOTE_FILES.get("neutral")
        path = self.asset_dir + "/" + file_name
        candidates = [
            _replace_ext(path, ".mbp"),
            _replace_ext(path, ".mbp") + ".tmp",
            path,
            path + ".tmp",
        ]
        if file_name != neutral_name:
            neutral_path = self.asset_dir + "/" + neutral_name
            candidates.extend(
                [
                    _replace_ext(neutral_path, ".mbp"),
                    _replace_ext(neutral_path, ".mbp") + ".tmp",
                    neutral_path,
                    neutral_path + ".tmp",
                ]
            )
        index = 0
        while index < len(candidates):
            if _file_exists(candidates[index]):
                return candidates[index]
            index += 1
        return candidates[0]

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

    def _load_meta(self, emote_name):
        key = _string(emote_name).strip().lower()
        if key in self.asset_cache:
            return self.asset_cache.get(key)
        path = self._asset_path(key)
        fp = open(path, "rb")
        try:
            head = fp.read(16)
            if len(head) < 16:
                raise Exception("invalid miaoban asset")
            if head[0:4] == b"MBP1":
                meta = self._load_mbp_meta(key, path, head, fp)
            elif head[0:4] == b"\x89EAF":
                meta = self._load_eaf_meta(key, path, head, fp)
            else:
                raise Exception("unsupported miaoban asset")
            self.asset_cache[key] = meta
            self.last_error = ""
            return meta
        finally:
            fp.close()

    def _load_mbp_meta(self, key, path, head, fp):
        frame_count = _u16le(head, 8)
        data_base = _u32le(head, 12)
        width = _u16le(head, 4)
        height = _u16le(head, 6)
        table_raw = fp.read(frame_count * 4)
        frames = []
        index = 0
        while index < frame_count:
            frames.append(_u32le(table_raw, index * 4))
            index += 1
        fp.seek(0, 2)
        file_size = fp.tell()
        return {
            "key": key,
            "path": path,
            "format": "mbp",
            "frame_count": frame_count,
            "data_base": data_base,
            "frames": frames,
            "width": width,
            "height": height,
            "file_size": file_size,
        }

    def _load_eaf_meta(self, key, path, head, fp):
        frame_count = _u32le(head, 4)
        data_base = 16 + (frame_count * 8)
        table_raw = fp.read(frame_count * 8)
        frames = []
        index = 0
        while index < frame_count:
            base = index * 8
            size = _u32le(table_raw, base)
            offset = _u32le(table_raw, base + 4)
            frames.append((size, offset))
            index += 1
        width = 0
        height = 0
        if frames:
            fp.seek(data_base + frames[0][1])
            chunk_head = fp.read(20)
            if len(chunk_head) >= 16 and chunk_head[0:4] == b"ZZ_S":
                width = _u16le(chunk_head, 12)
                height = _u16le(chunk_head, 14)
        return {
            "key": key,
            "path": path,
            "format": "eaf",
            "frame_count": frame_count,
            "data_base": data_base,
            "frames": frames,
            "width": width,
            "height": height,
        }

    def _ensure_canvas(self, width, height):
        width = int(width or 0)
        height = int(height or 0)
        if width <= 0 or height <= 0:
            raise Exception("invalid canvas size")
        if self.ready and self.width == width and self.height == height:
            return True
        self.width = width
        self.height = height
        self.zoom = int(self.layout_zoom or (1024 if height <= 64 else 512))
        self.canvas_buf = bytearray(width * height * 2)
        self.canvas = self.lv.canvas(self.parent)
        self.canvas.set_buffer(self.canvas_buf, width, height, self.lv.img.CF.TRUE_COLOR)
        self._set_hidden(self.canvas, True)
        self.image = self.lv.img(self.parent)
        self.image.set_src(self.canvas.get_img())
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
        parent_w = 440
        parent_h = 430
        try:
            parent_w = int(self.parent.get_width())
        except Exception:
            pass
        try:
            parent_h = int(self.parent.get_height())
        except Exception:
            pass
        if self.layout_x is None:
            x = int((parent_w - draw_w) / 2)
        else:
            x = int(self.layout_x)
        if self.layout_y is None:
            y = int((parent_h - draw_h) / 2)
            if self.height <= 64:
                y = int((parent_h - draw_h) / 2) - 10
        else:
            y = int(self.layout_y)
        self.image.set_pos(x, y)
        return True

    def _decode_chunk(self, chunk, target_width, target_height):
        block_count = _u16le(chunk, 16)
        block_height = _u16le(chunk, 18)
        palette_base = 20 + (block_count * 4)
        palette = chunk[palette_base:palette_base + 1024]
        data_offset = palette_base + 1024
        pixels = bytearray()
        block_index = 0
        while block_index < block_count:
            size = _u32le(chunk, 20 + (block_index * 4))
            block = chunk[data_offset:data_offset + size]
            if (not block) or block[0] != 0:
                raise Exception("unsupported zz_s block")
            run_bytes = block[1:]
            run_index = 0
            while run_index < len(run_bytes):
                count = run_bytes[run_index]
                value = run_bytes[run_index + 1]
                if count > 0:
                    pixels.extend(bytes([value]) * count)
                run_index += 2
            data_offset += size
            block_index += 1
        if len(pixels) != (int(target_width) * int(target_height)):
            raise Exception("pixel size mismatch")
        return palette, pixels

    def _clear_canvas(self):
        if self.canvas_buf is None:
            return False
        length = len(self.canvas_buf)
        fill_pair = _struct.pack("<H", int(self.backdrop565 or 0) & 0xFFFF)
        fill_chunk = fill_pair * 64
        index = 0
        while index < length:
            remain = length - index
            if remain >= 128:
                self._write_bytes(index, fill_chunk)
                index += 128
            else:
                self._write_bytes(index, fill_chunk[:remain])
                index += remain
        return True

    def _rgb565(self, r, g, b):
        value = ((int(r) & 0xF8) << 8) | ((int(g) & 0xFC) << 3) | ((int(b) & 0xF8) >> 3)
        return value & 0xFFFF

    def _draw_eaf_frame(self, meta, frame_index):
        path = meta.get("path")
        frames = meta.get("frames") or []
        if (not path) or (not frames):
            return False
        if frame_index < 0 or frame_index >= len(frames):
            frame_index = 0
        size, offset = frames[frame_index]
        fp = open(path, "rb")
        try:
            fp.seek(int(meta.get("data_base") or 0) + int(offset))
            chunk = fp.read(int(size))
        finally:
            fp.close()
        palette, pixels = self._decode_chunk(chunk, meta.get("width"), meta.get("height"))
        self._ensure_canvas(meta.get("width"), meta.get("height"))
        if int(frame_index) <= 0:
            self._clear_canvas()
        color_lut = bytearray(512)
        alpha_lut = bytearray(256)
        color_index = 0
        while color_index < 256:
            base = color_index * 4
            alpha_lut[color_index] = palette[base + 3]
            color = self._rgb565(palette[base], palette[base + 1], palette[base + 2])
            color_lut[color_index * 2] = color & 0xFF
            color_lut[(color_index * 2) + 1] = (color >> 8) & 0xFF
            color_index += 1
        pixel_index = 0
        write_index = 0
        while pixel_index < len(pixels):
            palette_index = pixels[pixel_index]
            if alpha_lut[palette_index] != 0:
                lut_index = palette_index * 2
                self._write_u16(write_index, _u16le(color_lut, lut_index))
            write_index += 2
            pixel_index += 1
        return True

    def _draw_mbp_frame(self, meta, frame_index):
        path = meta.get("path")
        frames = meta.get("frames") or []
        if (not path) or (not frames):
            return False
        if frame_index < 0 or frame_index >= len(frames):
            frame_index = 0
        width = meta.get("width")
        height = meta.get("height")
        self._ensure_canvas(width, height)
        frame_offset = int(frames[frame_index])
        if frame_index + 1 < len(frames):
            next_offset = int(frames[frame_index + 1])
        else:
            next_offset = int(meta.get("file_size") or 0) - int(meta.get("data_base") or 0)
        frame_size = next_offset - frame_offset
        fp = open(path, "rb")
        try:
            fp.seek(int(meta.get("data_base") or 0) + frame_offset)
            frame_head = fp.read(4)
            if len(frame_head) < 4:
                raise Exception("invalid mbp frame")
            flags = _u16le(frame_head, 0)
            run_count = _u16le(frame_head, 2)
            if (flags & 1) != 0 or frame_index <= 0:
                self._clear_canvas()
            run_index = 0
            while run_index < run_count:
                run_head = fp.read(4)
                if len(run_head) < 4:
                    raise Exception("invalid mbp run")
                start = _u16le(run_head, 0)
                length = _u16le(run_head, 2)
                data = fp.read(int(length) * 2)
                byte_index = int(start) * 2
                self._write_bytes(byte_index, data)
                run_index += 1
        finally:
            fp.close()
        _ = frame_size
        return True

    def _draw_frame(self, meta, frame_index):
        fmt = _string(meta.get("format")).lower()
        if fmt == "mbp":
            ok = self._draw_mbp_frame(meta, frame_index)
        else:
            ok = self._draw_eaf_frame(meta, frame_index)
        try:
            self.image.invalidate()
        except Exception:
            pass
        self._set_hidden(self.image, False)
        return ok

    def set_emote(self, emote_name):
        key = _string(emote_name).strip().lower()
        if not key:
            key = "neutral"
        meta = self._load_meta(key)
        if meta is None:
            return False
        if self.current_key != key:
            self.current_key = key
            self.current_meta = meta
            self.frame_index = 0
            self._draw_frame(meta, self.frame_index)
        return True

    def tick(self):
        if self.current_meta is None:
            return False
        frames = self.current_meta.get("frames") or []
        if len(frames) <= 1:
            return True
        self.frame_index += 1
        if self.frame_index >= len(frames):
            self.frame_index = 0
        self._draw_frame(self.current_meta, self.frame_index)
        return True

    def show(self):
        self._set_hidden(self.image, False)
        return True

    def hide(self):
        self._set_hidden(self.image, True)
        return True

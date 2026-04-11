from board_airi_data import EMOTION_MODE_MAP, MODE_KEYS
from board_airi_scene import AiriScene


class BoardAiriUi(object):

    def __init__(self, display):
        self.display = display
        self.scene = AiriScene(display)
        self.ready = False

    def ensure_ready(self):
        if self.ready:
            return True
        self.display.ensure_ready()
        self.scene.ensure_ready()
        self.ready = True
        return True

    def show_booting(self):
        self.ensure_ready()
        return self.scene.show_booting()

    def show_ready(self):
        self.ensure_ready()
        return self.scene.show_ready()

    def show_waiting(self):
        self.ensure_ready()
        return self.scene.show_waiting()

    def show_error(self, message=None):
        self.ensure_ready()
        return self.scene.show_error(message)

    def show_fill(self, color):
        self.ensure_ready()
        return self.scene.show_fill(color)

    def show_overlay(self, status=None, message=None, footer=None, mood=None):
        self.ensure_ready()
        return self.scene.set_overlay(status=status, message=message, footer=footer, mood=mood)

    def clear_overlay(self):
        self.ensure_ready()
        return self.scene.clear_overlay()

    def show_mode(self, mode_key, status=None, message=None, footer=None, mood=None):
        self.ensure_ready()
        if mode_key not in MODE_KEYS:
            mode_key = "idle"
        self.scene.set_mode(mode_key)
        return self.scene.set_overlay(status=status, message=message, footer=footer, mood=mood)

    def render_runtime_state(self, mode_key, status, message, footer, mood=""):
        self.ensure_ready()
        return self.scene.render_runtime_state(mode_key, status, message, footer, mood=mood)

    def show_emotion(self, emotion):
        self.ensure_ready()
        mode_key = EMOTION_MODE_MAP.get(str(emotion or "").strip().lower(), "idle")
        return self.show_mode(mode_key)

    def catalog(self):
        return {
            "modes": list(MODE_KEYS),
            "emotion_aliases": dict(EMOTION_MODE_MAP),
        }

    def tick(self):
        if self.display.auto_pump_started:
            return True
        return self.display.pump()

    def snapshot(self):
        return {
            "ready": bool(self.ready),
            "display": self.display.snapshot(),
            "scene": self.scene.snapshot(),
            "catalog": self.catalog(),
        }

MODE_KEYS = ("idle", "listen", "talk")
MODE_NAMES = ("IDLE", "LISTEN", "TALK")

WAVE_FRAMES = (
    (-5, 1, 4, -2, 2, 5),
    (-2, 4, 1, 3, -1, 2),
    (0, 6, -2, 5, 1, -1),
    (3, 2, 5, 1, 4, 2),
    (1, -2, 3, 6, 0, 4),
    (-3, 1, 0, 4, 5, -2),
)

PULSE_SWING = (0, 1, 3, 4, 2, 0, -1, 1)
LINK_SWING = (0, 1, 2, 1, 0, -1, 0, 1)
PRESENCE_SWING = (0, 2, 4, 3, 1, -1, 1, 2)
GLOW_SWING = (0, 8, 16, 10, 4, 12, 18, 9)

MODE_PROFILES = (
    {
        "key": "idle",
        "mode_line": "MODE // IDLE",
        "status": "CALM // STANDBY",
        "scene": "SOFT SYNC",
        "avatar": "AIRI // IDLE PORTRAIT",
        "headline": "AIRI is resting\non the board.",
        "description": "Board-native portrait page.\nqpyclaw keeps the stage alive.",
        "waves": (14, 28, 18, 24, 16, 30),
        "pulse": 72,
        "link": 96,
        "presence": 84,
        "accent": (0x4C, 0xC9, 0xF0),
        "accent_alt": (0xFF, 0x7B, 0xC6),
        "footer": (
            "AIRI is pinned to the qpyclaw node.",
            "Idle aura keeps the panel breathing.",
            "Board room is holding a clean signal.",
        ),
        "messages": (
            ("HELLO, I'M AIRI.", "qpyclaw node stage online."),
            ("This board is now my room.", "Node runtime and AIRI UI are merged."),
            ("The old screen was cleared for me.", "Only the AIRI layer stays visible."),
        ),
    },
    {
        "key": "listen",
        "mode_line": "MODE // LISTEN",
        "status": "SENSOR // ATTENTIVE",
        "scene": "OPEN LOOP",
        "avatar": "AIRI // LISTEN MODE",
        "headline": "AIRI is listening\nfor the next input.",
        "description": "Waiting for network, host text,\nor a runtime event from qpyclaw.",
        "waves": (24, 42, 30, 46, 28, 38),
        "pulse": 79,
        "link": 98,
        "presence": 91,
        "accent": (0xB2, 0x9A, 0xFF),
        "accent_alt": (0x6F, 0xF0, 0xFF),
        "footer": (
            "Listening shell is open on the node.",
            "The next bridge step can inject live lines.",
            "AIRI is ready for host-side text.",
        ),
        "messages": (
            ("I'm listening.", "Waiting for the next command."),
            ("Input can come from runtime or host.", "Board-side shell is ready."),
            ("This mode holds the next transition.", "Cloud chat can be wired in next."),
        ),
    },
    {
        "key": "talk",
        "mode_line": "MODE // TALK",
        "status": "VOICE // SPEAKING",
        "scene": "VOICE BURST",
        "avatar": "AIRI // TALK MODE",
        "headline": "AIRI is replying\nfrom the stage.",
        "description": "Active runtime work pushes her into\nan on-stage talking pose.",
        "waves": (38, 56, 44, 60, 40, 50),
        "pulse": 93,
        "link": 99,
        "presence": 95,
        "accent": (0xFF, 0x93, 0xD1),
        "accent_alt": (0x89, 0xFC, 0xD9),
        "footer": (
            "Wave rail is now running hot.",
            "The speaking pose is active for live work.",
            "Small runtime, strong AIRI identity.",
        ),
        "messages": (
            ("I can answer on this display.", "Dialogue shell is visible now."),
            ("My board voice already has rhythm.", "The stage is brighter in TALK mode."),
            ("qpyclaw is now driving my scene.", "Runtime actions can be seen directly."),
        ),
    },
)

EMOTION_MODE_MAP = {
    "neutral": "idle",
    "sleepy": "idle",
    "relaxed": "idle",
    "confident": "idle",
    "thinking": "listen",
    "confused": "listen",
    "surprised": "listen",
    "winking": "listen",
    "happy": "talk",
    "loving": "talk",
    "cool": "talk",
    "laughing": "talk",
    "kissy": "talk",
}

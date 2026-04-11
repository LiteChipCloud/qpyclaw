AIRI_EXPRESSION_KEYS = (
    "idle_blink",
    "listen_focus",
    "talk_smile",
    "talk_open",
    "happy_pop",
    "sad_soft",
    "angry_fire",
    "sleep_breath",
    "shock_hold",
    "wink_ping",
    "neutral",
    "relaxed",
    "thinking",
    "confused",
    "happy",
    "laughing",
    "loving",
    "cool",
    "confident",
    "delicious",
    "funny",
    "sad",
    "crying",
    "angry",
    "sleep",
    "surprised",
    "winking",
    "embarrassed",
    "kissy",
    "silly",
)


AIRI_EXPRESSION_MANIFEST_CANDIDATES = (
    "/usr/media/expressions/manifest.json",
    "/usr/media/airi/expressions/manifest.json",
    "U:/media/expressions/manifest.json",
    "U:/media/airi/expressions/manifest.json",
)


AIRI_EXPRESSION_ALIASES = {
    "wake": "idle_blink",
    "idle": "idle_blink",
    "neutral": "idle_blink",
    "standby": "idle_blink",
    "relaxed": "idle_blink",
    "listen": "listen_focus",
    "listening": "listen_focus",
    "asking": "listen_focus",
    "thinking": "listen_focus",
    "confused": "listen_focus",
    "talk": "talk_smile",
    "speak": "talk_open",
    "speaking": "talk_open",
    "happy": "happy_pop",
    "laughing": "happy_pop",
    "loving": "happy_pop",
    "cool": "happy_pop",
    "confident": "happy_pop",
    "delicious": "happy_pop",
    "funny": "talk_smile",
    "kissy": "wink_ping",
    "embarrassed": "wink_ping",
    "silly": "talk_smile",
    "sad": "sad_soft",
    "cry": "crying",
    "crying": "sad_soft",
    "angry": "angry_fire",
    "anger": "angry_fire",
    "sleep": "sleep_breath",
    "sleepy": "sleep_breath",
    "shocked": "surprised",
    "surprised": "shock_hold",
    "panic": "surprised",
    "error": "shock_hold",
    "winking": "wink_ping",
    "blink": "winking",
}


AIRI_EXPRESSION_PROFILES = (
    {
        "key": "idle_blink",
        "label": "Idle Blink",
        "tick_step": 3,
        "loop": True,
        "note": "Default breathing expression for calm standby.",
    },
    {
        "key": "listen_focus",
        "label": "Listen Focus",
        "tick_step": 2,
        "loop": True,
        "note": "Eyes stay attentive while waiting for user input.",
    },
    {
        "key": "talk_smile",
        "label": "Talk Smile",
        "tick_step": 1,
        "loop": True,
        "note": "Closed-mouth speaking loop for soft replies.",
    },
    {
        "key": "talk_open",
        "label": "Talk Open",
        "tick_step": 1,
        "loop": True,
        "note": "Open-mouth speaking loop for active voice replies.",
    },
    {
        "key": "happy_pop",
        "label": "Happy Pop",
        "tick_step": 2,
        "loop": False,
        "note": "Short positive accent that can land back on talk or idle.",
    },
    {
        "key": "sad_soft",
        "label": "Sad Soft",
        "tick_step": 3,
        "loop": False,
        "note": "Low-energy sad response.",
    },
    {
        "key": "angry_fire",
        "label": "Angry Fire",
        "tick_step": 2,
        "loop": False,
        "note": "Short sharp emphasis.",
    },
    {
        "key": "sleep_breath",
        "label": "Sleep Breath",
        "tick_step": 4,
        "loop": True,
        "note": "Slow loop for low-power rest state.",
    },
    {
        "key": "shock_hold",
        "label": "Shock Hold",
        "tick_step": 2,
        "loop": False,
        "note": "Alert pose for errors or surprise.",
    },
    {
        "key": "wink_ping",
        "label": "Wink Ping",
        "tick_step": 2,
        "loop": False,
        "note": "Small charm accent.",
    },
    {
        "key": "neutral",
        "label": "Neutral",
        "tick_step": 4,
        "loop": True,
        "note": "Alias for the imported neutral XiaoZhi face.",
    },
    {
        "key": "relaxed",
        "label": "Relaxed",
        "tick_step": 4,
        "loop": True,
        "note": "Alias for the imported relaxed XiaoZhi face.",
    },
    {
        "key": "thinking",
        "label": "Thinking",
        "tick_step": 3,
        "loop": True,
        "note": "Alias for the imported thinking XiaoZhi face.",
    },
    {
        "key": "confused",
        "label": "Confused",
        "tick_step": 3,
        "loop": True,
        "note": "Alias for the imported confused XiaoZhi face.",
    },
    {
        "key": "happy",
        "label": "Happy",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported happy XiaoZhi face.",
    },
    {
        "key": "laughing",
        "label": "Laughing",
        "tick_step": 2,
        "loop": True,
        "note": "Alias for the imported laughing XiaoZhi face.",
    },
    {
        "key": "loving",
        "label": "Loving",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported loving XiaoZhi face.",
    },
    {
        "key": "cool",
        "label": "Cool",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported cool XiaoZhi face.",
    },
    {
        "key": "confident",
        "label": "Confident",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported confident XiaoZhi face.",
    },
    {
        "key": "delicious",
        "label": "Delicious",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported delicious XiaoZhi face.",
    },
    {
        "key": "funny",
        "label": "Funny",
        "tick_step": 2,
        "loop": True,
        "note": "Alias for the imported funny XiaoZhi face.",
    },
    {
        "key": "sad",
        "label": "Sad",
        "tick_step": 3,
        "loop": False,
        "note": "Alias for the imported sad XiaoZhi face.",
    },
    {
        "key": "crying",
        "label": "Crying",
        "tick_step": 3,
        "loop": False,
        "note": "Alias for the imported crying XiaoZhi face.",
    },
    {
        "key": "angry",
        "label": "Angry",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported angry XiaoZhi face.",
    },
    {
        "key": "sleep",
        "label": "Sleep",
        "tick_step": 4,
        "loop": True,
        "note": "Alias for the imported sleep XiaoZhi face.",
    },
    {
        "key": "surprised",
        "label": "Surprised",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported surprised XiaoZhi face.",
    },
    {
        "key": "winking",
        "label": "Winking",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported winking XiaoZhi face.",
    },
    {
        "key": "embarrassed",
        "label": "Embarrassed",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported embarrassed XiaoZhi face.",
    },
    {
        "key": "kissy",
        "label": "Kissy",
        "tick_step": 2,
        "loop": False,
        "note": "Alias for the imported kissy XiaoZhi face.",
    },
    {
        "key": "silly",
        "label": "Silly",
        "tick_step": 2,
        "loop": True,
        "note": "Alias for the imported silly XiaoZhi face.",
    },
)


PROFILE_MAP = {}
_index = 0
while _index < len(AIRI_EXPRESSION_PROFILES):
    _profile = AIRI_EXPRESSION_PROFILES[_index]
    PROFILE_MAP[_profile.get("key")] = _profile
    _index += 1


def _string(value):
    if value is None:
        return ""
    try:
        return str(value)
    except Exception:
        return ""


def resolve_expression_key(value, default_key="idle_blink"):
    key = _string(value).strip().lower()
    if key in PROFILE_MAP:
        return key
    if key in AIRI_EXPRESSION_ALIASES:
        return AIRI_EXPRESSION_ALIASES.get(key)
    return default_key


def expression_profile(value, default_key="idle_blink"):
    key = resolve_expression_key(value, default_key)
    return PROFILE_MAP.get(key) or PROFILE_MAP.get(default_key)


def resolve_expression_for_scene(mode_key, mood="", emote_name="", default_key="idle_blink"):
    mode = _string(mode_key).strip().lower()
    mood_key = resolve_expression_key(mood, "")
    emote_key = resolve_expression_key(emote_name, "")

    if mode == "talk":
        if mood_key and mood_key not in ("idle_blink", "listen_focus"):
            return mood_key
        if emote_key and emote_key not in ("idle_blink", "listen_focus"):
            return emote_key
        return "talk_open"

    if mode == "listen":
        if mood_key and mood_key not in ("talk_smile", "talk_open"):
            return mood_key
        if emote_key and emote_key not in ("talk_smile", "talk_open"):
            return emote_key
        return "listen_focus"

    if mode == "sleep":
        return "sleep_breath"

    if mood_key:
        return mood_key
    if emote_key:
        return emote_key
    return resolve_expression_key(mode, default_key)

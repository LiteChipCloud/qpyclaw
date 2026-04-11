DIRS = (
    "/usr/media/expressions/angry",
    "/usr/media/expressions/confident",
    "/usr/media/expressions/cool",
    "/usr/media/expressions/crying",
    "/usr/media/expressions/delicious",
    "/usr/media/expressions/embarrassed",
    "/usr/media/expressions/funny",
    "/usr/media/expressions/happy",
    "/usr/media/expressions/kissy",
    "/usr/media/expressions/laughing",
    "/usr/media/expressions/loving",
    "/usr/media/expressions/relaxed",
    "/usr/media/expressions/sad",
    "/usr/media/expressions/silly",
    "/usr/media/expressions/sleep",
    "/usr/media/expressions/surprised",
    "/usr/media/expressions/winking",
)

try:
    import uos
except Exception:
    uos = None

removed = 0
if uos is not None:
    index = 0
    while index < len(DIRS):
        base = DIRS[index]
        try:
            names = uos.listdir(base)
        except Exception:
            names = []
        inner = 0
        while inner < len(names):
            path = base + "/" + names[inner]
            try:
                st = uos.stat(path)
            except Exception:
                st = None
            if st is not None and (int(st[0]) & 0x4000):
                inner += 1
                continue
            try:
                uos.remove(path)
                removed += 1
            except Exception:
                pass
            inner += 1
        index += 1

print("PURGE_OK %d" % removed)

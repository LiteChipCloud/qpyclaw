import gc
import ujson
import uos
import usys

PREFIX = 'codex_memprobe_20260329'


def safe_remove(path):
    try:
        uos.remove(path)
    except Exception:
        pass


def snapshot(label):
    gc.collect()
    return {
        'label': label,
        'mem_free': gc.mem_free(),
        'mem_alloc': gc.mem_alloc() if hasattr(gc, 'mem_alloc') else None,
        'modules': len(usys.modules),
    }

for i in range(12):
    safe_remove('/usr/%s_%d.py' % (PREFIX, i))
    try:
        name = '%s_%d' % (PREFIX, i)
        if name in usys.modules:
            del usys.modules[name]
    except Exception:
        pass

after_cleanup = snapshot('after_cleanup')
rows = [after_cleanup]

for i in range(12):
    path = '/usr/%s_%d.py' % (PREFIX, i)
    f = open(path, 'w')
    f.write('')
    f.close()
rows.append(snapshot('after_create_12_empty_files'))

import_rows = []
for i in range(12):
    name = '%s_%d' % (PREFIX, i)
    before = snapshot('before_import_%d' % i)
    __import__(name)
    after = snapshot('after_import_%d' % i)
    import_rows.append({
        'import_index': i,
        'module': name,
        'delta_mem_free': before['mem_free'] - after['mem_free'],
        'delta_modules': after['modules'] - before['modules'],
        'before_mem_free': before['mem_free'],
        'after_mem_free': after['mem_free'],
    })

summary = {
    'rows': rows,
    'import_rows': import_rows,
    'avg_import_delta_mem_free': sum([r['delta_mem_free'] for r in import_rows]) / len(import_rows),
    'max_import_delta_mem_free': max([r['delta_mem_free'] for r in import_rows]),
    'min_import_delta_mem_free': min([r['delta_mem_free'] for r in import_rows]),
}
print(ujson.dumps(summary))

for i in range(12):
    safe_remove('/usr/%s_%d.py' % (PREFIX, i))
    try:
        name = '%s_%d' % (PREFIX, i)
        if name in usys.modules:
            del usys.modules[name]
    except Exception:
        pass

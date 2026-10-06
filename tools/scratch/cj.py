"""Load and save the game's content JSON exactly as it is written (one-space
indent, UTF-8, CRLF), so a patch changes only what it means to."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/godot/data/content/'

def load(name):
    return json.loads(open(ROOT + name, 'rb').read().decode('utf-8'))

def save(name, d):
    out = json.dumps(d, indent=1, ensure_ascii=False).replace('\n', '\r\n') + '\r\n'
    open(ROOT + name, 'wb').write(out.encode('utf-8'))

def insert_after(d, after_key, key, value):
    """A new key in an ordered dict, placed after another."""
    items = list(d.items())
    out = {}
    for k, v in items:
        if k == key:
            continue
        out[k] = v
        if k == after_key:
            out[key] = value
    if key not in out:
        out[key] = value
    d.clear()
    d.update(out)

def node(d, convo, nid):
    return d[convo]['nodes'][nid]

def choice(d, convo, nid, fragment):
    """The one choice in a node whose first text contains fragment."""
    n = node(d, convo, nid)
    hits = []
    for c in n.get('choices') or []:
        t = c['text'] if isinstance(c['text'], str) else c['text'][0]['text']
        if fragment in t:
            hits.append(c)
    if len(hits) != 1:
        raise KeyError(f'{convo}.{nid}: {len(hits)} choices match {fragment!r}')
    return hits[0]

def choices(d, convo, fragment):
    """Every choice in a conversation whose first text contains fragment."""
    out = []
    for nid, n in d[convo]['nodes'].items():
        for c in n.get('choices') or []:
            t = c['text'] if isinstance(c['text'], str) else c['text'][0]['text']
            if fragment in t:
                out.append((nid, c))
    return out

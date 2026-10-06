import json, sys, os

ROOT = sys.argv[1]
OUT = sys.argv[2]
d = json.load(open(os.path.join(ROOT, 'dialogue.json'), encoding='utf-8'))


def cond(c):
    if c is None:
        return ''
    return json.dumps(c, ensure_ascii=False, separators=(',', ':'))


def text(t):
    if isinstance(t, str):
        return [('', t)]
    out = []
    for v in t:
        pre = ('+' if v.get('add') else '') + ('[' + cond(v.get('when')) + '] ' if v.get('when') else '')
        out.append((pre, v['text']))
    return out


os.makedirs(OUT, exist_ok=True)
for cid, c in d.items():
    lines = []
    lines.append(f'### {cid} (npc {c["npc"]})')
    lines.append('ENTRY:')
    for e in c['entry']:
        lines.append(f'  {e["node"]}  <- {cond(e.get("when"))}')
    if c.get('marker'):
        lines.append('MARKER:')
        for m in c['marker']:
            lines.append(f'  {m.get("mark")} <- {cond(m.get("when"))}')
    for nid, n in c['nodes'].items():
        lines.append('')
        lines.append(f'== {nid}' + (f' (speaker {n["speaker"]})' if n.get('speaker') else '') + (f' next->{n["next"]}' if n.get('next') else ''))
        if n.get('effects'):
            lines.append(f'   EFFECTS {cond(n["effects"])}')
        for pre, t in text(n['text']):
            lines.append(f'   {pre}{t}')
        for i, ch in enumerate(n.get('choices') or []):
            bits = []
            if ch.get('show'): bits.append('SHOW ' + cond(ch['show']))
            if ch.get('when'): bits.append('WHEN ' + cond(ch['when']))
            if ch.get('locked'): bits.append('LOCKED "' + ch['locked'] + '"')
            if ch.get('badge'): bits.append('BADGE ' + ch['badge'])
            if ch.get('once'): bits.append('ONCE ' + ch['once'])
            if ch.get('action'): bits.append('ACTION ' + ch['action'])
            if ch.get('goto'): bits.append('-> ' + ch['goto'])
            if ch.get('end'): bits.append('END')
            tt = text(ch['text'])
            lines.append(f'  [{i}] ' + ' / '.join(p + t for p, t in tt))
            if bits: lines.append('       ' + ' | '.join(bits))
            if ch.get('effects'): lines.append('       FX ' + cond(ch['effects']))
    open(os.path.join(OUT, cid + '.txt'), 'w', encoding='utf-8').write('\n'.join(lines))
print('ok')

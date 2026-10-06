"""Every choice or node that pays gold, gives an item or moves a feeling, and
what stops it being taken twice (once, a take, a condition on a fact it sets)."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/godot/'
d = json.load(open(G + 'data/content/dialogue.json', encoding='utf-8'))

def flat(effects):
    out = []
    for e in effects or []:
        if 'if' in e:
            t = e.get('then'); el = e.get('else')
            out += flat(t if isinstance(t, list) else [t] if t else [])
            out += flat(el if isinstance(el, list) else [el] if el else [])
        else:
            out.append(e)
    return out

def rewards(effects):
    r = []
    for e in flat(effects):
        if 'gold' in e and e['gold'] > 0: r.append(f"gold {e['gold']}")
        if 'give' in e: r.append(f"give {e['give']}")
        if 'rel' in e and any((e['rel'].get(k) or 0) > 0 for k in ('trust', 'affection', 'respect')): r.append(f"rel+ {e['rel']['npc']}")
    return r

def sets(effects):
    s = set()
    for e in flat(effects):
        if 'set' in e: s.update(e['set'].keys())
        if 'npcFlag' in e: s.add('flag:' + e['npcFlag']['key'])
        if 'take' in e: s.add('take:' + e['take'])
        if 'quest' in e and e['quest'].get('entry'): s.add('entry:' + e['quest']['entry'])
    return s

# Which nodes lead to which: a reward on a node is guarded by the choice that leads there.
for cid, c in d.items():
    nodes = c['nodes']
    into = {}
    for nid, n in nodes.items():
        for ch in n.get('choices') or []:
            if ch.get('goto'): into.setdefault(ch['goto'], []).append((nid, ch))
        if n.get('next'): into.setdefault(n['next'], []).append((nid, None))
    for e in c['entry']:
        into.setdefault(e['node'], []).append(('ENTRY', {'when': e.get('when')}))
    for nid, n in nodes.items():
        r = rewards(n.get('effects'))
        if r:
            guards = []
            for src, ch in into.get(nid, []):
                if ch is None: guards.append(f'next from {src}'); continue
                g = []
                if ch.get('once'): g.append('once')
                if ch.get('when') or ch.get('show'): g.append('cond')
                if sets(ch.get('effects')): g.append('sets')
                guards.append(f"{src}:{'+'.join(g) or 'UNGUARDED'}")
            print(f"{cid}.{nid} NODE {r} sets={sorted(sets(n.get('effects')))} via {guards}")
        for ch in n.get('choices') or []:
            r = rewards(ch.get('effects'))
            if r:
                g = []
                if ch.get('once'): g.append('once')
                if ch.get('when') or ch.get('show'): g.append('cond')
                t = ch['text'] if isinstance(ch['text'], str) else ch['text'][0]['text']
                print(f"{cid}.{nid} CHOICE '{t[:40]}' {r} sets={sorted(sets(ch.get('effects')))} {'+'.join(g) or 'UNGUARDED'}")

"""Merge the romance Act 1 data drafts into the live dialogue.json, three-way.

base  = dialogue.json the drafts were built from (romance branch, e1ff637)
draft = docs/romance/data/<who>.json
live  = godot/data/content/dialogue.json

Per node: new or draft-only change -> draft; live-only change -> live; both
changed -> must be listed in MANUAL with a resolution. Entry lists the same.
Run from the worktree root: python romance_merge.py sella maeca keegan rav
"""
import json, os, subprocess, sys

BASE = 'e1ff6374a2d6c396c38ed150c858cf64a4be1a7e'
LIVE = os.path.join('godot', 'data', 'content', 'dialogue.json')


def J(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def load_base():
    out = subprocess.run(['git', 'show', f'{BASE}:godot/data/content/dialogue.json'], capture_output=True)
    return json.loads(out.stdout.decode('utf-8'))


def merge(who, base_all, live_all, manual):
    d = json.load(open(os.path.join('docs', 'romance', 'data', who + '.json'), encoding='utf-8'))
    draft = d.get(who, d)
    base, live = base_all[who], live_all[who]
    out = {}
    for k in list(live.keys()) + [k for k in draft if k not in live]:
        if k == 'nodes':
            continue
        b, dr, l = base.get(k), draft.get(k), live.get(k)
        if J(b) == J(dr):
            out[k] = l
        elif J(b) == J(l):
            out[k] = dr
        elif J(dr) == J(l):
            out[k] = l
        else:
            key = f'{who}.{k}'
            assert key in manual, f'conflict at {key}'
            out[k] = manual[key](b, dr, l)
    nodes = {}
    order = list(live['nodes'].keys()) + [n for n in draft['nodes'] if n not in live['nodes']]
    for n in order:
        b, dr, l = base['nodes'].get(n), draft['nodes'].get(n), live['nodes'].get(n)
        if dr is None and b is not None:
            # the draft dropped a node the base had: keep live's (drafts keep every node)
            nodes[n] = l
            continue
        if J(b) == J(dr):
            v = l
        elif J(b) == J(l):
            v = dr
        elif J(dr) == J(l):
            v = l
        else:
            key = f'{who}.nodes.{n}'
            assert key in manual, f'conflict at {key}'
            v = manual[key](b, dr, l)
        if v is not None:
            nodes[n] = v
    # keep key order: npc, entry, ..., nodes last as live has it
    res = {}
    for k in live.keys():
        res[k] = nodes if k == 'nodes' else out.get(k)
    for k in out:
        if k not in res:
            res[k] = out[k]
    return res


def maeca_entry(b, dr, l):
    """Both changed maeca's entry list. Live's order and live's edits win
    (the implementation's fixes); a base entry the draft edited and live did
    not takes the draft's edit; entries new in the draft are inserted after
    the entry that precedes them in the draft."""
    bj = [J(e) for e in b]

    def nth(lst, node, k):
        same = [x for x in lst if x.get('node') == node]
        return same[k] if k < len(same) else None

    res = []
    for e in l:
        if J(e) in bj:
            # unchanged in live: did the draft edit the same entry (same node, same occurrence)?
            i = bj.index(J(e))
            k = [x.get('node') for x in b[:i]].count(e.get('node'))
            cand = nth(dr, e.get('node'), k)
            res.append(cand if cand is not None else e)
        else:
            res.append(e)
    for k, e in enumerate(dr):
        if J(e) in bj or any(J(e) == J(x) for x in res):
            continue
        if any(x.get('node') == e.get('node') and J(x) == J(e) for x in res):
            continue
        if e.get('node') in [x.get('node') for x in b]:
            continue  # an edited base entry, handled above
        prev = dr[k - 1].get('node') if k > 0 else None
        at = max([j for j, x in enumerate(res) if x.get('node') == prev], default=-1)
        res.insert(at + 1, e)
    return res


MANUAL = {
    'maeca.entry': maeca_entry,
}

if __name__ == '__main__':
    who_list = sys.argv[1:]
    base_all = load_base()
    live_all = json.load(open(LIVE, encoding='utf-8'))
    for who in who_list:
        live_all[who] = merge(who, base_all, live_all, MANUAL)
        print('merged', who, len(live_all[who]['nodes']), 'nodes')
    with open(LIVE, 'w', encoding='utf-8', newline='\r\n') as h:
        h.write(json.dumps(live_all, indent=1, ensure_ascii=False) + '\n')

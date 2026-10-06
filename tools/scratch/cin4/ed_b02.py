import json
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7a4c20bcfd7ccfd3'
p = W + r'\tools\cinematics\boards.py'
t = open(p, encoding='utf-8').read()
a = '            api["30:3"]["inputs"]["seed"] = spec.get("seed", 1000) + i'
b = '            api["30:3"]["inputs"]["seed"] = entry.get("seed", spec.get("seed", 1000) + i)'
if a in t:
    t = t.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='\n').write(t)


def setspec(cid, changes):
    p = W + rf'\docs\cinematics\shoot\boards\{cid}.json'
    f = json.load(open(p, encoding='utf-8'))
    for sid, ch in changes.items():
        e = f['shots'][sid]
        if not isinstance(e, dict):
            e = f['shots'][sid] = {"prompt": e}
        e.update(ch)
    # One line per shot, as the files are laid out.
    lines = ['{', f'  "seed": {f["seed"]},', '  "people": {']
    ppl = list(f['people'].items())
    for k, (n, d) in enumerate(ppl):
        lines.append(f'    {json.dumps(n)}: {json.dumps(d, ensure_ascii=False)}' + (',' if k < len(ppl) - 1 else ''))
    lines += ['  },', '  "shots": {']
    sh = list(f['shots'].items())
    for k, (n, e) in enumerate(sh):
        lines.append(f'    {json.dumps(n)}: {json.dumps(e, ensure_ascii=False)}' + (',' if k < len(sh) - 1 else ''))
    lines += ['  }', '}', '']
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))


if __name__ == '__main__':
    setspec('c02', {
        '7': {"denoise": 0.72, "prompt": "two-shot at a misty river ford at night showing their huge difference in size: {warden}, a giant three times her height, bending far down from above over {her}, who stands only as tall as his hip, seen from behind her as she looks up at him; he holds his square cage-lamp with its cold pale blue flame down toward her face; a square stone pillar with a cold blue flame in an iron cup at frame left"},
        '8': {"denoise": 0.6, "prompt": "extreme close-up of a young woman's face, eyes, nose and lips, one side of her face lit cold pale blue by a lamp just out of frame, a tiny blue point of light reflected in each eye, wet dark red hair at the edges; her lips parted and no breath showing at all"},
        '11': {"seed": 1311},
        '3': {"denoise": 0.66, "prompt": "insert, low angle: one huge ancient armoured gauntlet, black with river slime and hung with weed, standing straight up out of dark water, its fist closed round the bail of a square cage-lamp of clean new black forged iron that hangs from it, a small cold pale blue flame inside; pines and a square stone pillar behind in the dark"},
    })
    print('ok')

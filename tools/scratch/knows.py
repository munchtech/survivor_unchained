"""Knowledge learned and knowledge asked about, across content and code."""
import json, re, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/godot/'
learned, asked = set(), set()
def walk(e):
    if isinstance(e, dict):
        for k, v in e.items():
            if k == 'learn':
                if isinstance(v, str): learned.add(v)
                elif isinstance(v, list): learned.update(v)
            if k in ('knows', 'notKnows') and isinstance(v, str): asked.add(v)
            walk(v)
    elif isinstance(e, list):
        for x in e: walk(x)
for f in glob.glob(G + 'data/content/*.json'):
    walk(json.load(open(f, encoding='utf-8')))
for path in glob.glob(G + 'logic/**/*.cs', recursive=True) + glob.glob(G + 'src/**/*.cs', recursive=True):
    t = open(path, encoding='utf-8').read()
    for m in re.finditer(r'"learn"\s*:\s*(\[[^\]]*\]|"[\w.]+")', t):
        learned.update(re.findall(r'"([\w.]+)"', m.group(1)))
    asked.update(re.findall(r'"knows"\s*:\s*"([\w.]+)"', t))
    asked.update(re.findall(r'\bKnows\("([\w.]+)"\)', t))
    asked.update(re.findall(r'Knows\s*=\s*"([\w.]+)"', t))
    asked.update(re.findall(r'Knowledge\.Contains\("([\w.]+)"\)', t))
    learned.update(re.findall(r'Knowledge\.Add\("([\w.]+)"\)', t))
# Backgrounds teach some at the start.
arch = json.load(open(G + 'data/content/archetypes.json', encoding='utf-8'))
def bgwalk(e):
    if isinstance(e, dict):
        for k, v in e.items():
            if k == 'knowledge' and isinstance(v, list): learned.update(v)
            bgwalk(v)
    elif isinstance(e, list):
        for x in e: bgwalk(x)
bgwalk(arch)
print('ASKED, NEVER LEARNED:', sorted(asked - learned))
print('LEARNED, NEVER ASKED:', sorted(learned - asked))

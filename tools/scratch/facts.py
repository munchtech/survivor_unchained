"""Facts written and read across the content JSON and the logic's C#, the
way StoryLint reads them: which are written and never read?"""
import json, re, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
G = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/godot/'
files = ["dialogue.json", "quests.json", "rules.json", "concerns.json", "folk.json", "shops.json", "npcs.json", "archetypes.json"]
read, written = set(), set()
CK = {"when", "show", "if"}
def walk(e, cond):
    if isinstance(e, dict):
        for k, v in e.items():
            asc = cond or (k in CK and isinstance(v, dict) and 'text' not in v)
            if asc:
                if k == 'fact' and isinstance(v, str): read.add(v)
            else:
                if k in ('set', 'add') and isinstance(v, dict): written.update(v.keys())
            walk(v, asc)
    elif isinstance(e, list):
        for x in e: walk(x, cond)
    elif isinstance(e, str):
        for m in re.finditer(r'\{fact:([\w.]+)\}', e): read.add(m.group(1))
for f in files:
    walk(json.load(open(G + 'data/content/' + f, encoding='utf-8')), False)
Body = r'((?:[^{}]|\{\{[^{}]*\}\})*)'
for path in glob.glob(G + 'logic/**/*.cs', recursive=True) + glob.glob(G + 'src/**/*.cs', recursive=True):
    t = open(path, encoding='utf-8').read()
    for m in re.finditer(r'"(?:set|add)"\s*:\s*\{' + Body + r'\}', t):
        for k in re.findall(r'"([\w.]+)"\s*:', m.group(1)): written.add(k)
    written.update(re.findall(r'Facts\["([\w.]+)"\]\s*=', t))
    written.update(re.findall(r'\bf\["([\w.]+)"\]\s*=', t))
    written.update(re.findall(r'TurnHostile\("([\w.]+)"', t))
    rel = os.path.relpath(path, G).replace('\\', '/')
    read.update(re.findall(r'"fact"\s*:\s*"([\w.]+)"', t))
    read.update(re.findall(r'\b(?:F|Fact|Num|Is|S|f)\((?:c,\s*|w,\s*)?"([\w.]+)"', t))
    read.update(re.findall(r'FactKey\s*=\s*"([\w.]+)"', t))
    read.update(re.findall(r'Facts\.TryGetValue\("([\w.]+)"', t))
never = sorted(written - read)
print(len(written), 'written', len(read), 'read')
print('WRITTEN, NEVER READ:')
for k in never: print('  ', k)

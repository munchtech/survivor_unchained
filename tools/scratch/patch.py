p='check_story.py'
s=open(p,encoding='utf8').read()
s=s.replace(r'''    for k in re.findall(r'\b(?:F|Fact)\("([\w.]+)"\)', t): r("fact", k, f)''',
r'''    for k in re.findall(r'\b(?:F|Fact|Num)\((?:c, *)?"([\w.]+)"\)', t): r("fact", k, f)
    for k in re.findall(r'\bf\["([\w.]+)"\]\s*=', t): w("fact", k, f)
    for k in re.findall(r'TurnHostile\("([\w.]+)"', t): w("fact", k, f)
    for m in re.finditer(r'"(?:set|add)"\s*:\s*\{\s*"([\w.]+)"\s*:\s*\{\{', t): w("fact", m.group(1), f)''')
s=s.replace('''            if k in ("when", "show", "if") and isinstance(v, dict): walk_cond(v, f); continue''',
'''            if k in ("when", "show", "if") and isinstance(v, dict) and "text" not in v: walk_cond(v, f); continue''')
s=s.replace('''    for k in re.findall(r'\b(?:HasItem|Has)\("(\w+)"\)', t): r("item", k, f)''',
'''    for k in (re.findall(r'\b(?:HasItem|h\.Has)\("(\w+)"\)', t) if "/Zones/" in f or "Objectives" in f else []): r("item", k, f)''')
s=s.replace('''            (r if "status" not in body and f == "dialogue.json" and False else w)("entry", f"{qid.group(1)}/{ent.group(1)}", f)''',
'''            w("entry", f"{qid.group(1)}/{ent.group(1)}", f)
    for m in re.finditer(r'"entry"\s*:\s*"\{\{\(\w+ \? "(\w+)" : "(\w+)"\)\}\}"', t):
        w("entry", f"beasts/{m.group(1)}", f); w("entry", f"beasts/{m.group(2)}", f)''')
open(p,'w',encoding='utf8').write(s)

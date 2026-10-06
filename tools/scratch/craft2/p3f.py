"""The story lead's phase 3 words (d132033f), verbatim, into our crafters; slurry renames."""
import json, os, re, subprocess
from js import load, save, DIR
from ed import sub, ROOT

WT = os.path.dirname(ROOT)
theirs = json.loads(subprocess.run(["git", "show", "d132033f:godot/data/content/crafting.json"], cwd=WT, capture_output=True, text=True, encoding="utf-8").stdout)
tv, ts = theirs["crafters"]["vonnra"], theirs["crafters"]["snib"]

p = os.path.join(DIR, "crafting.json")
s = open(p, encoding="utf-8").read()
d = json.loads(s)


def block(name):
    """The crafter's block as text (two-space indented key to its closing brace)."""
    start = s.index(f'  "{name}": {{')
    depth, i = 0, s.index("{", start)
    while True:
        c = s[i]
        if c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return start, i + 1
        i += 1


def j(v):
    return json.dumps(v, ensure_ascii=False)


def lines_text(lines):
    return ",\n".join(f'    {j(k)}: {j(v)}' for k, v in lines.items())


vl = dict(tv["lines"])
v_easier = vl.pop("terms.accused")[0]
vonnra = f'''  "vonnra": {{
   "name": "Vonnra",
   "place": {j(tv["place"][0].upper() + tv["place"][1:])},
   "verbs": ["bind"],
   "when": {j(tv["when"])},
   "closedLine": {j(tv["closedLine"])},
   "respectPerCraft": 1,
   "respectFromCraft": 10,
   "lines": {{
{lines_text(vl)}
   }},
   "easier": [
    {{ "when": {{ "fact": "vonnra.accused", "eq": true }}, "gold": -10, "needs": "after you have accused her", "line": {j(v_easier)} }}
   ]
  }}'''
sl = dict(ts["lines"])
snib = f'''  "snib": {{
   "name": "Snib",
   "place": {j(ts["place"][0].upper() + ts["place"][1:])},
   "verbs": ["steep", "buy"],
   "when": {j(ts["when"])},
   "closedLine": {j(ts["closedLine"])},
   "respectPerCraft": 0,
   "respectFromCraft": 0,
   "easier": [],
   "lines": {{
{lines_text(sl)}
   }}
  }}'''
for name, text in (("vonnra", vonnra), ("snib", snib)):
    a, b = block(name)
    s = s[:a] + text + s[b:]
# Outcome "slurry" is "affix" in the words; the affixes' new names.
s = s.replace('"odds": { "up": 25, "slurry": 25, "nothing": 30, "down": 20 }', '"odds": { "up": 25, "affix": 25, "nothing": 30, "down": 20 }')
s = s.replace('"affixes": ["seeping", "of_the_sump", "green_veined"]', '"affixes": ["fevered", "of_the_sump", "pipe_lads"]')
# The sale follows the crafter's own condition (the story lead's): met, and the pump not stopped.
s = re.sub(r'  "sold": \{.*?\},\n  "odds"', '  "sold": ' + j(ts["when"]) + ',\n  "odds"', s, flags=re.S)
json.loads(s)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("crafting.json")

items = load("items")
items["items"]["slurry_jar"]["lore"] = sl["jar"][0]
save("items", items)

g = load("dialogue")
for c in g["vonnra"]["nodes"]["hub"]["choices"]:
    if c.get("action") == "craft": c["text"] = "Can you move what's in one thing into another?"
# Snib's jars open his bench: the jar and the steeping, side by side.
for c in g["snib"]["nodes"]["hub"]["choices"]:
    if c.get("action") == "slurry": c["action"] = "craft"
save("dialogue", g)

sub('logic/Rpg/Items.cs', [
('new() { Id = "seeping", Name = "Seeping", Prefix = true,', 'new() { Id = "fevered", Name = "Fevered", Prefix = true,'),
('new() { Id = "green_veined", Name = "Green-Veined", Prefix = true,', 'new() { Id = "pipe_lads", Name = "Pipe-Lad\'s", Prefix = true,'),
])
sub('logic/Rpg/Crafting.cs', [
('public Dictionary<string, int> Odds = new() { ["up"] = 25, ["slurry"] = 25, ["nothing"] = 30, ["down"] = 20 };',
 'public Dictionary<string, int> Odds = new() { ["up"] = 25, ["affix"] = 25, ["nothing"] = 30, ["down"] = 20 };'),
('if (pick is "up" or "down" && plain.Count == 0) pick = pick == "up" ? "slurry" : "nothing";',
 'if (pick is "up" or "down" && plain.Count == 0) pick = pick == "up" ? "affix" : "nothing";'),
('            case "slurry":\r\n            {\r\n                var pool = s.Affixes', '            case "affix":\r\n            {\r\n                var pool = s.Affixes'),
('if (a?.Kindled != null) { q.Blocked = Line(crafter, "bind.coal") ?? "That one is caged. It will not come out."; return q; }',
 'if (a?.Kindled != null) { q.Blocked = Line(crafter, "bind.caged") ?? "That one is caged. It will not come out."; return q; }'),
('    /// <summary>What a gamble came to, once done ("up", "slurry", "nothing", "down").</summary>',
 '    /// <summary>What a gamble came to, once done ("up", "affix", "nothing", "down").</summary>'),
])

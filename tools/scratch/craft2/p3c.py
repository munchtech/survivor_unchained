"""Phase 3's data: Vonnra's table, Snib's jars. Lines marked draft until the story lead's come."""
import json, os
from js import load, save, DIR
from ed import sub

PUMP = {"any": [{"not": {"fact": "dig.pump", "exists": True}}, {"fact": "dig.pump", "eq": "running"}]}

# crafting.json is hand-laid (one-line rules): edit it as text.
p = os.path.join(DIR, "crafting.json")
s = open(p, encoding="utf-8").read()
rules = ''' "_bind": "Vonnra's binding (design 7.3): a shard and 40 gold a grade bound; the piece that takes it spends 5-7 heat; the donor is unmade.",
 "bind": { "shardsPerGrade": 1, "goldPerGrade": 40, "heat": [5, 7], "crafter": "vonnra" },
 "_slurry": "Snib's jars (design 9), while the pump runs: 30 gold, three a day. Steeping, by weight: a grade past the cap, a slurry affix past the seams, only the veins, a grade lost. It sets the piece.",
 "slurry": {
  "jar": "slurry_jar", "crafter": "snib", "mark": "slurried", "gold": 30, "perDay": 3,
  "sold": { "all": [{ "met": "snib" }, { "any": [{ "not": { "fact": "dig.pump", "exists": true } }, { "fact": "dig.pump", "eq": "running" }] }] },
  "odds": { "up": 25, "slurry": 25, "nothing": 30, "down": 20 },
  "affixes": ["seeping", "of_the_sump", "green_veined"]
 },
'''
anchor = ' "_crafters":'
assert anchor in s and '"bind":' not in s
s = s.replace(anchor, rules + anchor, 1)
crafters = '''  "vonnra": {
   "name": "Vonnra",
   "place": "The Toll-House Table",
   "verbs": ["bind"],
   "when": { "met": "vonnra" },
   "respectPerCraft": 1,
   "respectFromCraft": 10,
   "_draft": "Lines below are the crafting lead's drafts until the story lead's come (no {name}: her name-takes are spliced).",
   "lines": {
    "greet": ["Sit. Put it on the cloth. Not that one. That one.", "The lamp is lit. What would you have kept?"],
    "bind": ["It has let go. It is yours now.", "Done. The other is ash. That is the price."],
    "first.bind.before": ["(She holds the lesser piece over the lamp and waits. Not long. Something in it lets go, and she closes her hand on it.)"],
    "first.bind": ["What leaves can be kept. It only needs somewhere to go."],
    "bind.coal": ["That one is caged. It will not come out for me."],
    "history.bind": ["Bound at the toll-house table by {who}, day {day}"]
   },
   "easier": [
    { "when": { "fact": "vonnra.accused", "eq": true }, "gold": -10, "needs": "after you have accused her", "line": "She charges you a tenth less. She does not say why." }
   ]
  },
  "snib": {
   "name": "Snib",
   "place": "The Dig",
   "verbs": ["steep"],
   "when": { "met": "snib" },
   "respectPerCraft": 0,
   "respectFromCraft": 0,
   "easier": [],
   "_draft": "Lines below are the crafting lead's drafts until the story lead's come.",
   "lines": {
    "jar.sale": ["Thirty. Snib does not haggle. Snib haggles. Thirty."],
    "jar.none": ["No more today. Pump needs its sleep. Pump does not sleep."],
    "steep.up": ["The veins take, and the iron drinks."],
    "steep.slurry": ["Something green settles in it and stays."],
    "steep.nothing": ["Green-black veins, and nothing else."],
    "steep.down": ["It hisses. Something in it gives."],
    "history.steep": ["Steeped in the Dig's slurry, day {day}"]
   }
  },
  "wenna": {'''
assert '  "wenna": {' in s
s = s.replace('  "wenna": {', crafters, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
json.loads(s)
print("crafting.json")

d = load("items")
d["items"]["slurry_jar"] = {
    "id": "slurry_jar", "name": "Slurry Jar", "plural": "slurry jars", "kind": "material", "rarity": 2, "icon": "slurry_jar", "value": 30, "stack": 10,
    "description": "Steep a piece in it, from the pack: a grade past what the forge can do, or something green and strong with a price, or only the veins, or a grade lost. It sets the piece for good.",
    "lore": "It's the GOOD stuff. Mostly. Snib would not drink it.",
}
save("items", d)

g = load("dialogue")
v = g["vonnra"]["nodes"]["hub"]["choices"]
if not any(c.get("action") == "craft" for c in v):
    i = next(k for k, c in enumerate(v) if c.get("text") == "What do you sell?")
    v.insert(i, {"text": "Can you move a power from one thing to another?", "action": "craft"})
sn = g["snib"]["nodes"]
for node in ("hub", "first"):
    ch = sn[node]["choices"]
    if not any(c.get("action") == "slurry" for c in ch):
        i = next(k for k, c in enumerate(ch) if c.get("text") in ("Leave.",))
        ch.insert(i, {"text": "Sell me a jar of that.", "show": PUMP, "action": "slurry"})
save("dialogue", g)

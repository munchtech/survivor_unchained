"""The town talks about your nights: append "said" lines (npcs.json) and the daily rule (rules.json)."""
import json
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a035208561a66c171\godot\data\content"

def load(f): return json.loads(open(f"{WT}\\{f}.json", "rb").read().decode("utf-8"))
def save(f, d): open(f"{WT}\\{f}.json", "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))

TONIGHT = {"fact": "arena.last.ago", "eq": 0}                       # back in from it, the same night
MORNING = {"fact": "arena.last.ago", "eq": 1}                       # the day after
FRESH = {"any": [TONIGHT, {"all": [MORNING, {"not": {"time": "night"}}]}]}
def f(k, **c): return {"fact": f"arena.last.{k}", **c}
def all_(*c): return {"all": list(c)}
def people(p): return f("people", eq=p)
FELL, WON, STORY, TABLE = f("fell", eq=True), f("won", eq=True), f("story", eq=True), f("story", eq=False)

lines = {
    "holloway": [
        dict(text="One in. Count's right, for once.", night=True, when=TONIGHT),
        dict(text="Heard you put down what rules out there. Proof it can be done.", night=False, when=all_(MORNING, WON)),
        dict(text="Seven nights out, seven back. I've taken you out of the missing column.", night=False, once=True,
             when=all_(MORNING, {"fact": "arena.nights", "gte": 7})),
    ],
    "rook": [
        dict(text="Lamp burned all night for you, pet. A night's ember. It's on your slate.", night=True, when=all_(TONIGHT, f("past", gte=5))),
        dict(text="Face like a wet week. Eat first. It'll still be there after.", night=False, when=all_(MORNING, STORY, f("won", eq=False))),
        dict(text="Sit down before you fall down. Again.", night=False, when=all_(MORNING, FELL)),
    ],
    "chid": [
        dict(text="Oh, you're cold! Colder than usual, I mean. Come and sit by the flame.", night=True, once=True, when=all_(TONIGHT, FELL)),
        dict(text="Back again! You always are. Sit, sit; the flame likes company.", night=True, when=all_(TONIGHT, FELL, {"fact": "arena.fell", "gte": 2})),
        dict(text="Out ever so long! The whole dark was up, like moths round a candle.", night=True, once=True, when=all_(TONIGHT, f("past", gte=15))),
    ],
    "maeca": [
        dict(text="Heard you out by the Hollow last night. From the Blind. How many?", night=False,
             when=all_(MORNING, people("pack"), {"not": {"fact": "beasts.outcome", "exists": True}})),
        dict(text="Mine don't run at fire. Whatever came at you last night wasn't mine.", night=False,
             when=all_(MORNING, people("pack"), {"any": [{"fact": "beasts.outcome", "eq": "cured"}, {"fact": "beasts.outcome", "eq": "allied"}]})),
        dict(text="There's no Pack left. I counted the pelts. So what were you killing?", night=False,
             when=all_(MORNING, people("pack"), {"fact": "beasts.outcome", "eq": "slaughtered"})),
    ],
    "rav": [
        dict(text="Red on your sleeve, pal, and it's not yours. Don't tell me whose.", night=False,
             when=all_(MORNING, people("kerchiefs"), {"not": {"fact": "redcowl", "eq": "dead"}})),
        dict(text="Red on your sleeve again. There's not enough Kerchiefs left to bleed like that.", night=False,
             when=all_(MORNING, people("kerchiefs"), {"fact": "redcowl", "eq": "dead"})),
        dict(text="Back on your feet. Doctor's orders: drink, then fall over somewhere soft.", night=True, when=all_(TONIGHT, FELL)),
    ],
    "brannoc": [
        dict(text="Hill went gold last night. Open lamps. Not mine.", night=False, when=all_(MORNING, people("lamplings"))),
    ],
    "tam": [
        dict(text="The hill lit up last night and Pa said marsh-lights and it was you.", night=False, once=True, when=MORNING),
        dict(text="Pa says I'm not to watch the hill at night. I watch it.", night=False, when=MORNING),
    ],
    "wenna": [
        dict(text="Hot stone on you, child. Last I smelled that was the fever year.", night=False, once=True,
             when=all_(MORNING, {"fact": "arena.nights", "gte": 2})),
    ],
    "sella": [
        dict(text="Tell me about last night, love. I pay better than the Wayfinder.", once=True, when=FRESH),
        dict(text="Back, and all your bits still on. Pity to waste them on sleep.", night=True, when=all_(TONIGHT, f("fell", eq=False))),
    ],
    "keegan": [
        dict(text="The risen, last night. I have made a note. A perfectly ordinary note.", night=False,
             when=all_(MORNING, people("dead"))),
        dict(text="Down last night, they say, and up by breakfast. You are, if I may, robust.", night=False, once=True, when=all_(MORNING, FELL)),
    ],
    "pell": [
        dict(text="Roughly how much ember did you burn last night? I'm keeping a column.", night=False, once=True,
             when=all_(MORNING, {"fact": "arena.nights", "gte": 2})),
    ],
    "vonnra": [
        dict(text="A light went out on the hill tonight. Not for long.", night=True, once=True, when=all_(TONIGHT, FELL)),
    ],
}
outsiders = {
    "wayfinder": [
        dict(text="Your longest yet. That's going in the margin. Somebody will want to read it.", once=True, when=all_(FRESH, f("longest", eq=True))),
        dict(text="Longer again. You're making my margins untidy.", when=all_(FRESH, f("longest", eq=True), {"fact": "arena.nights", "gte": 3})),
        dict(text="You stayed on past it. The ones who do, I usually end up drawing.", when=all_(FRESH, WON, f("past", gte=10))),
        dict(text="You went down in there and came out anyway. I've a column for that.", when=all_(FRESH, FELL, TABLE)),
    ],
}

n = load("npcs")
def add(person, new):
    said = person.setdefault("said", [])
    have = {s["text"] for s in said}
    for l in new:
        if l["text"] in have: continue
        said.append({k: v for k, v in (("text", l["text"]), ("night", l.get("night")), ("once", l.get("once")), ("when", l["when"])) if v is not None})
for k, v in lines.items(): add(n["npcs"][k], v)
for k, v in outsiders.items(): add(n["outsiders"][k], v)
save("npcs", n)

r = load("rules")
if not any(x["id"] == "arena.ago" for x in r["rules"]):
    # Each dawn the last night is a day further off (0: the night itself; 1: the day after).
    r["rules"].append({"id": "arena.ago", "when": {"fact": "arena.last.ago", "exists": True}, "effect": {"add": {"arena.last.ago": 1}}})
save("rules", r)
print("ok", sum(len(v) for v in lines.values()) + sum(len(v) for v in outsiders.values()))

"""Builds godot/data/content/lamps_v2.json: the Lamps board v2 (docs/design/LAMPS_V2_RULES.md, the contract).

Reads lamps.json (v1, from lamps_build.py) and board_v2.json (the frozen layout), keeps the v1 lamps' words and
effects, and writes the 286 new lamps' names, lines and effects from the tables below. Deterministic: run it, commit both.

Most lines are rendered from their effects (render()), so a number can't drift from its tooltip. The few written by
hand (Hand lamps, blue lamps) are checked: every number in the args must appear in the line or the price.

Every new lamp carries "draft": true: its name and line wait for the story writer. Smalls and attributes are unnamed,
as in v1.

Run: python tools/classes/lamps_v2.py
"""
import collections
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.normpath(os.path.join(HERE, "..", "..", "godot", "data", "content"))
V1 = os.path.join(CONTENT, "lamps.json")
BOARD = os.path.join(CONTENT, "board_v2.json")
HANDS = os.path.join(CONTENT, "hands.json")
SKILLS = os.path.join(CONTENT, "skills.json")
OUT = os.path.join(CONTENT, "lamps_v2.json")

# v1's effect helpers (M, A, R, F, FM ...): lamps_build.py's own, exec'd up to its layout section (the rest builds v1).
_src = open(os.path.join(HERE, "lamps_build.py"), encoding="utf-8").read()
_ns = {"__file__": os.path.join(HERE, "lamps_build.py")}
exec(_src[:_src.index("# ----------------------------------------------------------------- layout --")], _ns)  # its own OUT stays in _ns
M, A, R, F, FM = _ns["M"], _ns["A"], _ns["R"], _ns["F"], _ns["FM"]

# ------------------------------------------------------------ the contract --

MECHS = {"heavy": {"every"}, "stone": set(), "bleed": {"share"}, "bind": {"seconds"}, "ground": set(), "mark": {"seconds"},
         "opening": {"seconds"}, "far": {"range", "chance"}, "hand": {"share"}}
TRIGGERS = {"block": set(), "dash": set(), "heavy": set(), "champion_kill": set(), "hurt": {"share"}, "low": set(), "flare": set(),
            "crowd": {"count", "radius"}, "still": {"seconds"}, "kills": {"count"}, "status_kill": {"status"}}
SMALL_RULES = {"tags.more": {"more", "when", "vs"}, "tags.area": {"inc"}, "tags.sooner": {"sooner"}, "tags.duration": {"inc"},
               "tags.projectiles": {"add"}, "tags.status": {"status", "chance"}, "tags.kill_mend": {"share"}}
WHENS = {"Moving", "Still", "LowHealth", "FullHealth", "InBurning", "AfterDash", "Healthy"}
STATUSES = {"burn", "bleed", "chill", "frozen", "poison", "shock", "mark", "sear", "stun", "fear", "charm", "bound"}
BLUES = {"shambles.blue": "blue.butchers_block", "night_road.blue": "blue.tethered_stars", "firebreak.blue": "blue.kindled_frost",
         "duelists_road.blue": "blue.bell_and_blade", "vigil.blue": "blue.vigil", "poachers.blue": "blue.poachers_mercy",
         "ford.unhoused": "blue.unhoused", "path.steel.blue": "blue.iron_pilgrim", "path.host.blue": "blue.pack_remembers",
         "path.storm.blue": "blue.lightning_rod", "path.grave.blue": "blue.mourners_debt", "path.weave.blue": "blue.unspun",
         "path.pyre.blue": "blue.pyre_walker", "path.rime.blue": "blue.drowned_lung", "path.wild.blue": "blue.feral",
         "path.hunt.blue": "blue.long_watch", "path.dawn.blue": "blue.unsetting_sun"}
# The road whose mech each crossing side brings (groups[].callings order). The Vigil and Poacher's Crossing sit exactly
# between two roads of each calling (board_v2 distances tie), so these two are chosen by theme: marks and stones keep the
# Vigil; bleeding and the far shot are poaching.
CROSS_ROADS = {"shambles": ("sunderer", "butcher"), "night_road": ("chainbound", "moonweaver"), "firebreak": ("kindler", "verge_hunter"),
               "duelists_road": ("roadknife", "bulwark"), "vigil": ("moonweaver", "bulwark"), "poachers": ("butcher", "verge_hunter")}
ROAD_MECH = {"sunderer": "heavy", "bulwark": "stone", "butcher": "bleed", "chainbound": "bind", "kindler": "ground",
             "moonweaver": "mark", "roadknife": "opening", "verge_hunter": "far"}
FIRST_ROAD = {"warden": ("sunderer", "bulwark"), "reaver": ("butcher", "chainbound"), "arcanist": ("kindler", "moonweaver"),
              "stalker": ("roadknife", "verge_hunter")}
# Tags each road's own kit already carries (its skills' tags and its mechanic's): its rites go elsewhere.
ROAD_TAGS = {"sunderer": "melee,steel,physical,area,heavy,holy,nova,spell", "bulwark": "melee,steel,physical,area,holy,nova,shield,aura",
             "butcher": "melee,steel,physical,area,orbit,thrown", "chainbound": "melee,physical,area,hook,storm",
             "kindler": "fire,frost,explosion,projectile,spell,zone", "moonweaver": "arcane,projectile,spell",
             "roadknife": "melee,steel,physical,thrown,projectile,twin", "verge_hunter": "projectile,ranged,physical,trap"}

# ------------------------------------------------------------------ words --

NOUN = {"spell": "spells", "projectile": "projectiles", "summon": "summons", "aura": "auras"}
ADJ = {"dot": "rot", "heal": "healing"}
VS = {"bleed": "bleeding", "burn": "burning", "chill": "chilled", "frozen": "frozen", "poison": "poisoned", "shock": "shocked",
      "mark": "marked", "sear": "seared", "stun": "stunned", "fear": "frightened", "bound": "Bound"}
WHEN = {"Moving": "while you move", "Still": "standing still", "LowHealth": "below 35% of health", "FullHealth": "at full health",
        "Healthy": "above 80% of health", "InBurning": "standing in burning ground", "AfterDash": "for 1.5 s after a dash"}
STATUS_VERB = {"bleed": "make what they strike bleed", "burn": "set what they strike burning", "chill": "chill what they strike",
               "frozen": "freeze what they strike", "poison": "poison what they strike", "shock": "shock what they strike",
               "mark": "mark what they strike", "sear": "sear what they strike", "stun": "stun what they strike",
               "fear": "frighten what they strike", "bound": "bind what they strike"}
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 10: "ten", 12: "twelve", 20: "twenty"}


def num(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s


def pct(v):
    return num(v * 100) + "%"


def subject(tags):
    adjs = [ADJ.get(t, t) for t in tags if t not in NOUN]
    nouns = [NOUN[t] for t in tags if t in NOUN]
    if not nouns: return " and ".join(adjs) + " skills"
    if not adjs: return " and ".join(nouns)
    return " and ".join(adjs) + " skills and " + " and ".join(nouns)


def cap(s):
    return s[0].upper() + s[1:]


def chance(c):
    k = 1 / c
    if abs(k - round(k)) < 0.01 and round(k) in WORDS: return f"one time in {WORDS[round(k)]}"
    return f"{pct(c)} of the time"


def predicate(e):
    """What a tags.* effect does, with its subject left off ("strike bleeding things 10% harder")."""
    r, a = e["rule"], e.get("args", {})
    if r == "tags.more":
        vs = f" {VS[a['vs']]} things" if "vs" in a else ""
        return f"strike{vs} {pct(a['more'])} harder"
    if r == "tags.area": return f"reach {pct(a['inc'])} wider"
    if r == "tags.sooner": return f"come {pct(a['sooner'])} sooner"
    if r == "tags.duration": return f"last {pct(a['inc'])} longer"
    if r == "tags.projectiles": return f"loose {a['add']} more projectile" + ("s" if a["add"] > 1 else "")
    if r == "tags.status": return f"{STATUS_VERB[a['status']]} {chance(a['chance'])}"
    raise KeyError(r)


def clause(e, first=True):
    a = e.get("args", {})
    s = subject(e["tags"])
    if e["rule"] == "tags.kill_mend":
        return f"kills by {s} mend {pct(a['share'])} of health" if first else f"their kills mend {pct(a['share'])} of health"
    w = WHEN[a["when"]] + ", " if "when" in a else ""
    if first: return f"{w}{s} {predicate(e)}"
    return f"{w}they {predicate(e)}" if w else f"they {predicate(e)}"


def render(effects):
    """One line from a small's or notable's tags.* effects (and an attribute, or a v1 rule written by hand)."""
    if effects[0]["do"] == "attr":
        return f"+{effects[0]['value']} {cap(effects[0]['attr'])}."
    c1 = clause(effects[0])
    if len(effects) == 1: return cap(c1) + "."
    e2 = effects[1]
    c2 = clause(e2, first=e2["tags"] != effects[0]["tags"])
    if "when" in e2.get("args", {}) and e2["tags"] == effects[0]["tags"]:
        c2 = f"{WHEN[e2['args']['when']]} they {predicate(e2)}"
    return cap(c1) + ", and " + c2 + "."


def rite_line(e):
    a, mech = e.get("args", {}), e["args"]["mech"]
    s = "your " + subject(e["tags"])
    if mech == "heavy": return cap(f"every {a['every']}th firing of {s} is a heavy blow: it stuns, throws back and staggers.")
    if mech == "stone": return cap(f"{s} lay a stone when they strike a champion, once a firing.")
    if mech == "bleed": return cap(f"what {s} strike bleeds {pct(a['share'])} of the hit over 3 s.")
    if mech == "bind": return cap(f"the first thing {s} strike each firing is Bound {num(a['seconds'])} s (a champion {num(a['seconds'] / 2)} s).")
    if mech == "ground":
        t = e["tags"][0]
        school = {"fire": "burning", "frost": "frozen", "arcane": "arcane"}.get(t, "burning")
        return cap(f"kills by {s} leave {school} ground, as an arcanist's spell does.")
    if mech == "mark": return cap(f"what {s} strike is Marked for {num(a['seconds'])} s.")
    if mech == "opening": return f"For {num(a['seconds'])} s after a dash, {s} strike true."
    if mech == "far": return cap(f"{s} strike true {chance(a['chance'])} from beyond {num(a['range'])} m.")
    if mech == "hand":
        return cap(f"{s} take your Hand: a warden's heavy blow, a reaver's {pct(a['share'])} bleed, an arcanist's ground, a stalker's Opening.")
    raise KeyError(mech)


def link_line(e):
    a = e["args"]
    t = a["trigger"]
    when = {"block": "When you block", "dash": "When you dash", "heavy": "When a heavy blow lands",
            "champion_kill": "When a champion dies", "low": "When you fall below half health", "flare": "When you press a Flare",
            "hurt": f"When one blow takes {pct(a.get('share', 0))} of your health or more",
            "crowd": f"When {a.get('count')} or more things are within {num(a.get('radius', 0))} m",
            "still": f"After {num(a.get('seconds', 0))} s standing still",
            "kills": f"On every {a.get('count')}th kill",
            "status_kill": f"When a {VS.get(a.get('status'), '')} thing dies"}[t]
    return f"{when}, the skill you pick fires once, free (at most every {num(a['wait'])} s)."


# ---------------------------------------------------------------- effects --

def TM(tags, more, when=None, vs=None):
    a = {"more": more}
    if when: a["when"] = when
    if vs: a["vs"] = vs
    return R("tags.more", tags=tags, **a)


def TA(tags, inc): return R("tags.area", tags=tags, inc=inc)
def TS(tags, sooner): return R("tags.sooner", tags=tags, sooner=sooner)
def TD(tags, inc): return R("tags.duration", tags=tags, inc=inc)
def TP(tags, add): return R("tags.projectiles", tags=tags, add=add)
def TK(tags, share): return R("tags.kill_mend", tags=tags, share=share)


def TST(tags, status, chance_):
    # The contract puts the status in args (R's own `status` keyword is v1's top-level skill.status field).
    e = R("tags.status", tags=tags, chance=chance_)
    e["args"] = {"status": status, "chance": chance_}
    return e


RITE_ARGS = {"heavy": {"every": 6}, "stone": {}, "bleed": {"share": 0.3}, "bind": {"seconds": 1}, "ground": {}, "mark": {"seconds": 4},
             "opening": {"seconds": 2}, "far": {"range": 8, "chance": 0.25}, "hand": {"share": 0.3}}


def RITE(tag, mech):
    return R("rite", tags=tag, mech=mech, **RITE_ARGS[mech])


def LINK(trigger, wait, tags, **a):
    status = a.pop("status", None)  # into args, as the contract says (R's own `status` is v1's top-level field)
    e = R("link", tags=tags, trigger=trigger, wait=wait, **a)
    if status: e["args"]["status"] = status
    return e


def HAND(**deltas): return R("hand", **deltas)


# ------------------------------------------------------------------ the 286 --
# Each table: lamp id -> (name, effects) for rendered lines, or (name, effects, text[, price]) for lines written by hand.

HEARTHS = {
    "warden.hearth.p1": ("", [TM("melee,thrown", 0.08, vs="stun")]),
    "warden.hearth.p2": ("", [TM("holy", 0.1, when="Still")]),
    "reaver.hearth.p1": ("", [TM("melee,area", 0.08, vs="bleed")]),
    "reaver.hearth.p2": ("", [TM("area", 0.1, when="LowHealth")]),
    "arcanist.hearth.p1": ("", [TM("spell", 0.08, when="InBurning")]),
    "arcanist.hearth.p2": ("", [TM("fire,frost", 0.08, vs="mark")]),
    "stalker.hearth.p1": ("", [TM("projectile", 0.1, when="AfterDash")]),
    "stalker.hearth.p2": ("", [TM("melee,steel", 0.1, when="AfterDash")]),
}

# The Hand ladders (hand1 to hand4, each a step on hands.json). Totals at hand4, against the Hand alone:
#   warden: heavy every 6th -> 4th (+50%), throw 1.5 -> 2, boss stagger 0.1 -> 0.15, heavy blows on champions lay stones;
#   reaver: Frenzy's top 6.4% -> 10% attack speed (+56%), the low-health swell 15% -> 20% from 60%, held 5 s;
#   arcanist: ground 2.5 s, 1.1 m, burns 40%: about +73% ground, and 16 grounds at once, marks pass 8 m;
#   stalker: the window 2 -> 3 s (+50%), pierce 1 -> 2 (the one count doubled), true blows on champions refund 25% of a dash.
HANDS_LADDER = {
    "warden.hand1": ("Heavy Habit", [HAND(every=-1)], "Your Hand's heavy blow comes every 5th firing, not every 6th."),
    "warden.hand2": ("Throw Them Back", [HAND(knockback=0.5, stagger=0.05)],
                     "Heavy blows throw things 2 times as far, not 1.5, and fill a boss's stagger bar by 0.15, not 0.1."),
    "warden.hand3": ("Every Fourth", [HAND(every=-1)], "Your Hand's heavy blow comes every 4th firing, not every 5th."),
    "warden.hand4": ("Stone in the Blow", [R("hand.warden.heavy_stone")], "A heavy blow on a champion lays a stone, once a firing."),
    "reaver.hand1": ("Quicker Blood", [HAND(per=0.002)], "Each stack of Frenzy gives 1% attack speed, not 0.8%."),
    "reaver.hand2": ("Bleed for It", [HAND(below=0.1, area=0.05)], "Your area skills swell below 60% of health, not 50%, and by 20%, not 15%."),
    "reaver.hand3": ("Deeper Frenzy", [HAND(cap=2)], "Frenzy stacks to 10, not 8."),
    "reaver.hand4": ("Long Fury", [HAND(fade=2)], "Frenzy holds 5 s after your last hit, not 3 s."),
    "arcanist.hand1": ("Slow Embers", [HAND(seconds=0.5)], "Your Hand's ground lasts 2.5 s, not 2 s."),
    "arcanist.hand2": ("More Hearths", [HAND(cap=4, reach=2)], "Up to 16 of your Hand's grounds lie at once, not 12, and marks pass 8 m, not 6 m."),
    "arcanist.hand3": ("Wider Ash", [HAND(radius=0.5)], "Your Hand's ground spreads 1.5 m round, not 1 m."),
    "arcanist.hand4": ("Hotter Ground", [HAND(burn=0.05)], "Your Hand's fire ground burns at 40% of the spell's blow a second, not 35%."),
    "stalker.hand1": ("Long Breath", [HAND(seconds=0.5)], "Your Hand's window after a dash lasts 2.5 s, not 2 s."),
    "stalker.hand2": ("Clean Through", [HAND(pierce=1)], "In the window, projectiles pierce 2 more things, not 1."),
    "stalker.hand3": ("Longer Breath", [HAND(seconds=0.5)], "Your Hand's window after a dash lasts 3 s, not 2.5 s."),
    "stalker.hand4": ("Second Wind", [R("hand.stalker.second_wind", share=0.25)], "A true blow on a champion in the window gives back 25% of a dash, once a dash."),
}

# Each road: s8, s9 (smalls on its mechanic), n6, four rites (its mech on four tags it doesn't carry), two links.
ROADS = {
    "sunderer": {
        "s8": ("", [TM("melee,holy", 0.1, when="Still")]),
        "s9": ("", [TST("melee,steel", "stun", 0.05)]),
        "n6": ("Earthshaker", [TA("melee,nova", 0.15), TM("melee,nova", 0.15, vs="stun")]),
        "rites": [("projectile", "Weighted Shot"), ("summon", "Iron in the Host"), ("storm", "Thunderclap"), ("beam", "Hammer of Light")],
        "link1": ("Aftershock", LINK("heavy", 6, "nova,area")),
        "link2": ("Felled Oak", LINK("champion_kill", 4, "melee,area")),
    },
    "bulwark": {
        "s8": ("", [TK("holy,nova", 0.002)]),
        "s9": ("", [TM("holy,aura", 0.1, when="Healthy")]),
        "n6": ("The Wall Teaches", [TA("aura,zone", 0.15), TM("aura,zone", 0.15, when="Still")]),
        "rites": [("spell", "Spellstone"), ("projectile", "Sling Stones"), ("summon", "The Host Builds"), ("zone", "Ground Held")],
        "link1": ("Answering Blow", LINK("block", 8, "holy,nova")),
        "link2": ("Bruised Oath", LINK("hurt", 6, "holy,aura", share=0.1)),
    },
    "butcher": {
        "s8": ("", [TST("melee,steel", "bleed", 0.1)]),
        "s9": ("", [TM("orbit,melee", 0.1, when="Moving")]),
        "n6": ("Bloodletter", [TST("melee,area", "bleed", 0.2), TK("melee,area", 0.003)]),
        "rites": [("projectile", "Barbed Shot"), ("shadow", "Black Blood"), ("summon", "Blooded Hounds"), ("chain", "Red Lightning")],
        "link1": ("Last Drop", LINK("status_kill", 6, "melee,area", status="bleed")),
        "link2": ("Cornered Beast", LINK("low", 4, "melee,steel")),
    },
    "chainbound": {
        "s8": ("", [TS("storm,chain", 0.08)]),
        "s9": ("", [TST("melee,area", "bound", 0.05)]),
        "n6": ("Dragnet", [TA("area,nova", 0.15), TM("area,nova", 0.15, vs="bound")]),
        "rites": [("projectile", "Hooked Shot"), ("beam", "Tether Light"), ("summon", "Leashed Host"), ("orbit", "Tether-Wheel")],
        "link1": ("Tight Knot", LINK("crowd", 10, "area,nova", count=6, radius=4)),
        "link2": ("Snapped Chain", LINK("status_kill", 6, "storm,chain", status="bound")),
    },
    "kindler": {
        "s8": ("", [TA("fire,explosion", 0.08)]),
        "s9": ("", [TK("fire,frost", 0.002)]),
        "n6": ("Thaw and Kindle", [TM("frost", 0.2, vs="burn"), TM("fire", 0.2, vs="chill")]),
        "rites": [("melee", "Ember Edge"), ("thrown", "Hot Coals"), ("summon", "Funeral Host"), ("holy", "Altar Fire")],
        "link1": ("Kindling", LINK("status_kill", 6, "fire,explosion", status="burn")),
        "link2": ("Hemmed In", LINK("crowd", 10, "frost,nova", count=8, radius=5)),
    },
    "moonweaver": {
        "s8": ("", [TM("spell,projectile", 0.08, when="Moving")]),
        "s9": ("", [TST("projectile,orbit", "mark", 0.1)]),
        "n6": ("Moonlit Hunt", [TM("spell,projectile", 0.18, vs="mark"), TK("spell,projectile", 0.003)]),
        "rites": [("melee", "Moonlit Steel"), ("thrown", "Moon-Thrown"), ("storm", "Moonstorm"), ("nature", "Moon on the Leaves")],
        "link1": ("Moon Tolls", LINK("status_kill", 6, "arcane,projectile", status="mark")),
        "link2": ("Count the Dead", LINK("kills", 6, "spell,projectile", count=15)),
    },
    "roadknife": {
        "s8": ("", [TST("steel,thrown", "poison", 0.1)]),
        "s9": ("", [TM("thrown,projectile", 0.1, when="Moving")]),
        "n6": ("Knife Dance", [TM("melee,thrown", 0.2, when="AfterDash"), TS("melee,thrown", 0.1)]),
        "rites": [("spell", "Quick Words"), ("shadow", "From the Dark"), ("storm", "Lightning Step"), ("orbit", "Wheel and Slip")],
        "link1": ("Parting Gift", LINK("dash", 6, "steel,thrown")),
        "link2": ("Last Breath", LINK("status_kill", 6, "melee,physical", status="poison")),
    },
    "verge_hunter": {
        "s8": ("", [TM("projectile,ranged", 0.1, when="Still")]),
        "s9": ("", [TM("projectile,ranged", 0.1, when="Healthy")]),
        "n6": ("Hide and Loose", [TM("projectile,ranged", 0.2, when="FullHealth"), TK("projectile,ranged", 0.003)]),
        "rites": [("spell", "Far Spell"), ("beam", "Long Beam"), ("chain", "Far Fork"), ("bounce", "Skip Shot")],
        "link1": ("Drawn Breath", LINK("still", 8, "projectile,ranged", seconds=1)),
        "link2": ("Too Close", LINK("crowd", 10, "projectile,thrown", count=3, radius=3)),
    },
}

BRIDGES = {  # rite1: the calling's first road's mech, rite2 the second's
    "warden": [("shadow", "Black Hammer"), ("thrown", "Thrown Stones")],
    "reaver": [("nature", "Bramble Cuts"), ("shadow", "Shadow Fetter")],
    "arcanist": [("arcane", "Moonfield"), ("frost", "Frostbrand")],
    "stalker": [("nova", "Burst Out"), ("thrown", "Long Throw")],
}

BLUE = {  # id -> (name, effects, text, price)
    "shambles.blue": ("Butcher's Block", [R("blue.butchers_block", share=1.0, health=0.2)],
                      "Heavy blows on bleeding things burst the bleed: all of its damage at once.", "20% less maximum health."),
    "night_road.blue": ("Tethered Stars", [R("blue.tethered_stars", count=2, seconds=2, slower=0.2)],
                        "Bound things count as Marked, and a Bound thing that dies binds the 2 nearest for 2 s.", "Spells come 20% slower."),
    "firebreak.blue": ("Kindled Frost", [R("blue.kindled_frost", softer=0.25)],
                       "Fire striking a chilled thing freezes it first, so Fire on Ice shatters it.", "Your frost skills strike 25% softer."),
    "duelists_road.blue": ("Bell and Blade", [R("blue.bell_and_blade", shorter=0.3)],
                           "A perfect dash counts as a block, and a block as a perfect dash.", "Both windows are 30% shorter."),
    "vigil.blue": ("Vigil Fire", [R("blue.vigil", stones=3, more=0.3)],
                   "While you hold 3 stones or more, spells strike 30% harder.", "The wall never answers: no rebuke."),
    "poachers.blue": ("Poacher's Mercy", [R("blue.poachers_mercy", mul=2, charges=1)],
                      "A blow that strikes true on a bleeding thing doubles its bleed.", "1 dash charge fewer."),
    "ford.unhoused": ("Unhoused", [R("blue.unhoused")],
                      "Lamps on other callings' roads open with no depth: their gates are ignored.", "Your Hand is gone."),
    "path.steel.blue": ("Iron Pilgrim", [R("blue.iron_pilgrim", phase=5)],
                        "Thrown skills return through you and strike again.", "You can't carry projectile spells."),
    "path.host.blue": ("The Pack Remembers", [R("blue.pack_remembers", per=0.02, cap=0.4, charges=1)],
                       "Summons stay the night and grow 2% with every kill, to 40%.", "1 dash charge fewer."),
    "path.storm.blue": ("Lightning Rod", [R("blue.lightning_rod", more=0.4, missiles=0.25)],
                        "Storm and chain skills strike the nearest champion first, and 40% harder.", "Missiles strike you 25% harder."),
    "path.grave.blue": ("Mourner's Debt", [R("blue.mourners_debt", share=0.01)],
                        "Kills by shadow skills mend 1% of health.", "Nothing else mends you."),
    "path.weave.blue": ("Unspun", [R("blue.unspun", sooner=0.3, cost=0.01)],
                        "Arcane skills come 30% sooner.", "Each arcane firing costs 1% of health."),
    "path.pyre.blue": ("Pyre-Walker", [R("blue.pyre_walker", more=0.25, burns=0.5)],
                       "Burning ground never harms you, and standing in it you strike 25% harder.", "Your burns last half as long."),
    "path.rime.blue": ("Drowned Lung", [R("blue.drowned_lung", faster=0.5)],
                       "Frost skills freeze in half the time.", "You can't be mended while you stand still."),
    "path.wild.blue": ("Feral", [R("blue.feral", more=0.4)],
                       "While you move, nature skills strike 40% harder.", "You can't block or strike true."),
    "path.hunt.blue": ("Long Watch", [R("blue.long_watch", far=10, near=4, more=0.35, less=0.35)],
                       "Blows from beyond 10 m strike 35% harder.", "Blows within 4 m strike 35% softer."),
    "path.dawn.blue": ("Unsetting Sun", [R("blue.unsetting_sun", mend=0.003, slower=0.2)],
                       "Holy skills sear what they strike, and a seared thing that dies mends 0.3% of health.",
                       "By night, holy skills come 20% slower."),
}

CROSSINGS = {  # rite1: side A's road's mech, rite2 side B's (CROSS_ROADS)
    "shambles": {"rite1": ("explosion", "Blasting Weight"), "rite2": ("nova", "Red Ring"),
                 "link": ("Blood Answers", LINK("hurt", 6, "melee,steel", share=0.08))},
    "night_road": {"rite1": ("arcane", "Star Chain"), "rite2": ("steel", "Moon on the Blade"),
                   "link": ("Dead Current", LINK("status_kill", 6, "storm,arcane", status="shock"))},
    "firebreak": {"rite1": ("physical", "Smoldering Shafts"), "rite2": ("frost", "Cold Distance"),
                  "link": ("Thaw Strike", LINK("status_kill", 6, "fire,projectile", status="frozen"))},
    "duelists_road": {"rite1": ("holy", "Bright Opening"), "rite2": ("steel", "Steel Mortar"),
                      "link": ("Return Fire", LINK("block", 8, "projectile,thrown"))},
    "vigil": {"rite1": ("holy", "Marked by Morning"), "rite2": ("arcane", "Moonstone"),
              "link": ("Keeping Vigil", LINK("still", 8, "spell,holy", seconds=2)),
              "a1": ("", [A("wits")]), "a2": ("", [A("resolve")]),
              "s1": ("", [TM("spell,holy", 0.08, when="Still")]),
              "s2": ("", [TM("holy,arcane", 0.1, vs="mark")]),
              "n1": ("Lamplit Watch", [TA("zone,aura", 0.15), TD("zone,aura", 0.25)]),
              "n2": ("Stones and Stars", [R("stones.barrier", at=3, more=0.2), TM("spell", 0.15, when="Still")],
                     "With 3 stones or more your barrier is 20% stronger, and standing still, spells strike 15% harder.")},
    "poachers": {"rite1": ("thrown", "Gutting Knives"), "rite2": ("nature", "Far Thorns"),
                 "link": ("Trophy", LINK("champion_kill", 4, "projectile,steel")),
                 "a1": ("", [A("might")]), "a2": ("", [A("finesse")]),
                 "s1": ("", [TM("projectile,thrown", 0.08, vs="bleed")]),
                 "s2": ("", [TST("projectile,thrown", "bleed", 0.1)]),
                 "n1": ("Skinning Knife", [TM("steel,thrown", 0.2, vs="bleed"), TK("steel,thrown", 0.003)]),
                 "n2": ("Snare and Gut", [TM("projectile,ranged", 0.2, vs="bound"), TST("projectile,ranged", "bleed", 0.1667)])},
}

FORD = {
    "ford.hub": ("", [TS("melee,spell", 0.06)]),
    "ford.s1": ("", [TK("area,nova", 0.002)]),
    "ford.s2": ("", [TM("melee,spell", 0.08, when="Healthy")]),
    "ford.n1": ("Wanderer's Hands", [TM("melee,projectile", 0.15, when="Moving"), TS("melee,projectile", 0.1)]),
    "ford.n2": ("Any Road Home", [TA("spell,area", 0.15), TK("spell,area", 0.003)]),
}


def oldroad(tags, smalls, notables, rites, link):
    """smalls: six effects; notables: four (name, [one or two effects]); rites: two (tag, name); link: (name, LINK)."""
    return {"tags": tags, "smalls": smalls, "notables": notables, "rites": rites, "link": link}


OLD = {
    "steel": oldroad("steel,physical",
        [TM("steel,physical", 0.1, vs="bleed"), TS("steel,physical", 0.06), TK("steel,physical", 0.002),
         TST("steel,physical", "bleed", 0.1), TM("steel,physical", 0.1, when="Moving"), TA("steel,melee", 0.08)],
        [("Opened to the Bone", [TST("steel,physical", "bleed", 0.2), TM("steel,physical", 0.15, vs="bleed")]),
         ("Iron Rhythm", [TS("steel,physical", 0.12), TM("steel,physical", 0.12, when="Moving")]),
         ("Edge Kept", [TA("steel,orbit", 0.15), TD("steel,orbit", 0.2)]),
         ("Blood for Blood", [TM("steel,physical", 0.2, when="LowHealth"), TK("steel,physical", 0.004)])],
        [("steel", "Old Iron"), ("physical", "Bare Hands")], ("Pain's Edge", LINK("hurt", 6, "steel,physical", share=0.1))),
    "host": oldroad("summon,aura",
        [TM("summon,aura", 0.1, when="Still"), TD("summon,aura", 0.12), TA("summon,aura", 0.08),
         TM("summon,aura", 0.1, when="Healthy"), TS("summon,aura", 0.06), TK("summon,aura", 0.002)],
        [("Old Comrades", [TD("summon,aura", 0.25), TM("summon,aura", 0.15, when="Still")]),
         ("Under the Banner", [TA("summon,aura", 0.2), TS("summon,aura", 0.1)]),
         ("Hounds of the Host", [TST("summon,aura", "fear", 0.1), TM("summon,aura", 0.15, vs="fear")]),
         ("Muster", [TM("summon,aura", 0.2, when="LowHealth"), TK("summon,aura", 0.003)])],
        [("summon", "The Host's Oath"), ("aura", "Old Banner")], ("Rally", LINK("low", 4, "summon,aura"))),
    "storm": oldroad("storm,chain",
        [TM("storm,chain", 0.1, vs="shock"), TST("storm,chain", "shock", 0.1), TA("storm,chain", 0.08),
         TS("storm,chain", 0.06), TM("storm,chain", 0.1, when="Moving"), TM("storm,chain", 0.1, vs="bound")],
        [("Gathering Charge", [TST("storm,chain", "shock", 0.15), TM("storm,chain", 0.2, vs="shock")]),
         ("Forked Sky", [TA("storm,chain", 0.15), TD("storm,chain", 0.2)]),
         ("Thunder Underfoot", [TS("storm,chain", 0.12), TM("storm,chain", 0.15, when="Still")]),
         ("Lightning Eats", [TM("storm,chain", 0.2, when="Healthy"), TK("storm,chain", 0.003)])],
        [("storm", "Sky's Hand"), ("chain", "Forked Hand")], ("Grounded", LINK("status_kill", 6, "storm,chain", status="shock"))),
    "grave": oldroad("shadow,dot",
        [TM("shadow,dot", 0.1, vs="poison"), TD("shadow,dot", 0.12), TA("shadow,dot", 0.08),
         TST("shadow,dot", "fear", 0.05), TM("shadow,dot", 0.1, when="LowHealth"), TS("shadow,dot", 0.06)],
        [("Long Rot", [TD("shadow,dot", 0.25), TM("shadow,dot", 0.15, vs="poison")]),
         ("Dread", [TST("shadow,dot", "fear", 0.125), TM("shadow,dot", 0.15, vs="fear")]),
         ("Grave Hunger", [TM("shadow,dot", 0.25, when="LowHealth"), TA("shadow,dot", 0.12)]),
         ("Barrow Wind", [TS("shadow,dot", 0.12), TM("shadow,dot", 0.15, when="Still")])],
        [("shadow", "Grave's Hand"), ("dot", "Slow Hand")], ("Gravedigger", LINK("kills", 6, "shadow,dot", count=15))),
    "weave": oldroad("arcane,orbit",
        [TM("arcane,orbit", 0.1, vs="mark"), TS("arcane,orbit", 0.06), TA("arcane,orbit", 0.08),
         TM("arcane,orbit", 0.1, when="Moving"), TD("arcane,orbit", 0.12), TST("arcane,orbit", "mark", 0.1)],
        [("Spun Tight", [TS("arcane,orbit", 0.12), TM("arcane,orbit", 0.12, when="Still")]),
         ("Silver Thread", [TST("arcane,orbit", "mark", 0.2), TM("arcane,orbit", 0.15, vs="mark")]),
         ("Wide Orbit", [TA("arcane,orbit", 0.2), TD("arcane,orbit", 0.2)]),
         ("Moon's Due", [TM("arcane,orbit", 0.2, when="Healthy"), TK("arcane,orbit", 0.003)])],
        [("arcane", "Woven Hand"), ("orbit", "Circling Hand")], ("Spindle", LINK("still", 8, "arcane,orbit", seconds=1.5))),
    "pyre": oldroad("fire,explosion",
        [TM("fire,explosion", 0.1, vs="burn"), TA("fire,explosion", 0.08), TM("fire,explosion", 0.1, when="InBurning"),
         TST("fire,explosion", "burn", 0.1), TS("fire,explosion", 0.06), TK("fire,explosion", 0.002)],
        [("Stoke", [TST("fire,explosion", "burn", 0.2), TM("fire,explosion", 0.15, vs="burn")]),
         ("Blast Radius", [TA("fire,explosion", 0.2), TS("fire,explosion", 0.1)]),
         ("Firewalker", [TM("fire,explosion", 0.25, when="InBurning"), TD("fire,explosion", 0.2)]),
         ("Ash Harvest", [TM("fire,explosion", 0.15, vs="chill"), TK("fire,explosion", 0.004)])],
        [("fire", "Pyre's Hand"), ("explosion", "Blasting Hand")], ("Pyre Spark", LINK("status_kill", 6, "fire,explosion", status="burn"))),
    "rime": oldroad("frost,zone",
        [TM("frost,zone", 0.1, vs="chill"), TD("frost,zone", 0.12), TA("frost,zone", 0.08),
         TST("frost,zone", "chill", 0.1), TM("frost,zone", 0.1, when="Still"), TM("frost,zone", 0.1, vs="frozen")],
        [("Hard Frost", [TST("frost,zone", "frozen", 0.05), TM("frost,zone", 0.15, vs="frozen")]),
         ("Long Winter", [TD("frost,zone", 0.25), TA("frost,zone", 0.15)]),
         ("Black Ice", [TM("frost,zone", 0.2, vs="chill"), TS("frost,zone", 0.1)]),
         ("Snow-Blind", [TM("frost,zone", 0.2, when="Healthy"), TK("frost,zone", 0.003)])],
        [("frost", "Cold Hand"), ("zone", "Held Ground")], ("Shatter Call", LINK("status_kill", 6, "frost,zone", status="frozen"))),
    "wild": oldroad("nature,heal",
        [TM("nature,heal", 0.1, when="Moving"), TD("nature,heal", 0.12), TA("nature,heal", 0.08),
         TST("nature,heal", "poison", 0.1), TS("nature,heal", 0.06), TK("nature,heal", 0.002)],
        [("Thorn and Root", [TST("nature,heal", "bound", 0.1), TM("nature,heal", 0.15, vs="bound")]),
         ("Run With Them", [TM("nature,heal", 0.2, when="Moving"), TS("nature,heal", 0.1)]),
         ("Green Blood", [TD("nature,heal", 0.2), TK("nature,heal", 0.004)]),
         ("Bramble", [TA("nature,heal", 0.2), TM("nature,heal", 0.15, vs="poison")])],
        [("nature", "Green Hand"), ("heal", "Mending Hand")], ("Hare's Leap", LINK("dash", 6, "nature,heal"))),
    "hunt": oldroad("projectile,ranged",
        [TM("projectile,ranged", 0.1, vs="bound"), TS("projectile,ranged", 0.06), TM("projectile,ranged", 0.1, when="FullHealth"),
         TST("projectile,ranged", "bleed", 0.1), TM("projectile,ranged", 0.08, when="Moving"), TK("projectile,ranged", 0.002)],
        [("Deep Draw", [TM("projectile,ranged", 0.2, when="Still"), TS("projectile,ranged", 0.1)]),
         ("Broadheads", [TST("projectile,ranged", "bleed", 0.1667), TM("projectile,ranged", 0.15, vs="bleed")]),
         ("Pinned", [TST("projectile,ranged", "bound", 0.05), TM("projectile,ranged", 0.2, vs="bound")]),
         ("Spare Quiver", [TP("projectile,ranged", 1)])],
        [("projectile", "Fletcher's Hand"), ("ranged", "Long Hand")], ("Big Game", LINK("champion_kill", 4, "projectile,ranged"))),
    "dawn": oldroad("holy,beam",
        [TM("holy,beam", 0.1, vs="sear"), TST("holy,beam", "sear", 0.1), TA("holy,beam", 0.08),
         TS("holy,beam", 0.06), TM("holy,beam", 0.1, when="Healthy"), TK("holy,beam", 0.002)],
        [("First Light", [TST("holy,beam", "sear", 0.2), TM("holy,beam", 0.15, vs="sear")]),
         ("Noonday", [TA("holy,beam", 0.2), TD("holy,beam", 0.2)]),
         ("Morning Prayer", [TM("holy,beam", 0.2, when="Still"), TS("holy,beam", 0.1)]),
         ("Light Mends", [TM("holy,beam", 0.15, when="FullHealth"), TK("holy,beam", 0.004)])],
        [("holy", "Morning Hand"), ("beam", "Lamp Hand")], ("Sunrise", LINK("flare", 4, "holy,beam"))),
}


# ---------------------------------------------------------------- assemble --

def content():
    """id -> {name, effects, text[, price]} for the 286."""
    out = {}

    def put(lid, name, effects, text=None, price=None):
        assert lid not in out, lid
        out[lid] = {"name": name, "effects": effects, "text": text or render(effects)}
        if price: out[lid]["price"] = price

    def rite(lid, tag, mech, name):
        e = RITE(tag, mech)
        put(lid, name, [e], rite_line(e))

    def link(lid, name, e):
        put(lid, name, [e], link_line(e))

    for lid, (nm, effs) in HEARTHS.items(): put(lid, nm, effs)
    for lid, (nm, effs, text) in HANDS_LADDER.items(): put(lid, nm, effs, text)
    for rid, r in ROADS.items():
        for k in ("s8", "s9", "n6"): put(f"{rid}.{k}", r[k][0], r[k][1])
        for i, (tag, nm) in enumerate(r["rites"], 1): rite(f"{rid}.rite{i}", tag, ROAD_MECH[rid], nm)
        for k in ("link1", "link2"): link(f"{rid}.{k}", *r[k])
    for calling, two in BRIDGES.items():
        for i, (tag, nm) in enumerate(two, 1): rite(f"{calling}.bridge.rite{i}", tag, ROAD_MECH[FIRST_ROAD[calling][i - 1]], nm)
    for cid, c in CROSSINGS.items():
        for i in (1, 2): rite(f"{cid}.rite{i}", c[f"rite{i}"][0], ROAD_MECH[CROSS_ROADS[cid][i - 1]], c[f"rite{i}"][1])
        link(f"{cid}.link", *c["link"])
        for k in ("a1", "a2", "s1", "s2", "n1", "n2"):
            if k in c: put(f"{cid}.{k}", *c[k])
    for lid, v in FORD.items(): put(lid, *v)
    for path, p in OLD.items():
        g = f"path.{path}"
        for i, e in enumerate(p["smalls"], 1): put(f"{g}.s{i}", "", [e])
        for i, (nm, effs) in enumerate(p["notables"], 1): put(f"{g}.n{i}", nm, effs)
        for i, (tag, nm) in enumerate(p["rites"], 1): rite(f"{g}.rite{i}", tag, "hand", nm)
        link(f"{g}.link", *p["link"])
    for lid, (nm, effs, text, price) in BLUE.items(): put(lid, nm, effs, text, price)
    return out


# ------------------------------------------------------------------ checks --

def numbers_in(text):
    return {float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)}


def check_numbers(lid, eff, text, hand_base=None):
    """Every number in a hand-written line's args must be in its line (or price): as itself, a percent, a word, or
    for a Hand lamp the new total."""
    nums = numbers_in(text)
    low = text.lower()
    for k, v in eff.get("args", {}).items():
        if not isinstance(v, (int, float)) or isinstance(v, bool): continue
        cands = {abs(v), round(abs(v) * 100, 6)}
        if hand_base is not None: cands |= {round(hand_base[k], 6), round(hand_base[k] * 100, 6)}
        ok = bool(cands & {round(n, 6) for n in nums})
        ok = ok or (v == 2 and "double" in low) or (v == 0.5 and "half" in low) or (v == 1.0 and "all" in low)
        assert ok, f"{lid}: arg {k}={v} isn't in its line: {text}"


def check_effect(lid, kind, e, hands, skill_tags):
    if e["do"] != "rule": return
    r, a, tags = e["rule"], e.get("args", {}), e.get("tags", [])
    if r == "rite":
        assert kind == "rite", lid
        assert a["mech"] in MECHS and set(a) - {"mech"} <= MECHS[a["mech"]], (lid, a)
        assert len(tags) == 1 and tags[0] in skill_tags, (lid, tags)
    elif r == "link":
        assert kind == "link", lid
        assert a["trigger"] in TRIGGERS and set(a) - {"trigger", "wait"} == TRIGGERS[a["trigger"]], (lid, a)
        assert 4 <= a["wait"] <= 12 and tags and all(t in skill_tags for t in tags), (lid, a, tags)
        if a["trigger"] == "status_kill": assert a["status"] in STATUSES, lid
    elif r == "hand":
        calling = lid.split(".")[0]
        assert kind == "hand" and set(a) <= set(hands[calling]), (lid, a)
    elif r.startswith("hand."):
        assert kind == "hand" and r.split(".")[1] == lid.split(".")[0], lid
    elif r in SMALL_RULES:
        assert set(a) <= SMALL_RULES[r] and tags and all(t in skill_tags for t in tags), (lid, r, a, tags)
        if "when" in a: assert a["when"] in WHENS, lid
        if "vs" in a: assert a["vs"] in STATUSES, lid
        if r == "tags.status": assert a["status"] in STATUSES and 0 < a["chance"] < 1, lid
    elif r.startswith("blue."):
        assert BLUES.get(lid) == r, (lid, r)
    else:
        assert e.get("phase", 1) > 1 or r in V1_RULES, f"{lid}: rule {r} is neither the contract's nor v1's"


def main():
    global V1_RULES
    v1 = json.load(open(V1, encoding="utf-8"))
    board = json.load(open(BOARD, encoding="utf-8"))
    hands = json.load(open(HANDS, encoding="utf-8"))
    skill_tags = {t for s in json.load(open(SKILLS, encoding="utf-8"))["skills"] for t in s["tags"]}
    V1_RULES = {e["rule"] for l in v1["lamps"] for e in l["effects"] if e["do"] == "rule"}
    old = {l["id"]: l for l in v1["lamps"]}
    new = content()

    lamps = []
    for b in board["lamps"]:
        lid = b["id"]
        L = {"id": lid}
        if b["v1"]:
            o = old[lid]
            L["name"] = o.get("name", "")
        else:
            c = new.pop(lid)
            L["name"], L["draft"] = c["name"], True
        L.update({"kind": b["kind"], "region": b["region"], "group": b["group"], "road": b["group"]})
        if b.get("calling"): L["calling"] = b["calling"]
        L.update({"x": b["x"], "y": b["y"], "at": b["at"], "gate": b["gate"]})
        if b["v1"]:
            for k in ("text", "feeds", "early"):
                if o.get(k): L[k] = o[k]
            L["effects"] = o["effects"]
        else:
            L["text"] = c["text"]
            if "price" in c: L["price"] = c["price"]
            L["effects"] = c["effects"]
        lamps.append(L)
    assert not new, f"content for ids not on the board: {sorted(new)}"

    # ---- the asserts
    assert len(lamps) == 574, len(lamps)
    fresh = [l for l in lamps if l.get("draft")]
    assert len(fresh) == 286, len(fresh)
    hand_sum = collections.defaultdict(dict)
    hand_rules = collections.Counter()
    for l in fresh:
        lid, kind, effs = l["id"], l["kind"], l["effects"]
        assert l["text"] and effs and l["draft"] is True, lid
        assert len(effs) <= 2 or kind == "blue", lid
        for e in effs: check_effect(lid, kind, e, hands, skill_tags)
        if kind == "small":
            (e,) = effs
            assert e["do"] == "attr" or len(e.get("tags", [])) >= 2 or {"when", "vs"} & set(e.get("args", {})), f"{lid}: a bare small"
        if kind == "attribute": assert effs[0]["do"] == "attr", lid
        if kind == "blue":
            assert l.get("price") and effs[0]["rule"] == BLUES[lid], lid
            check_numbers(lid, effs[0], l["text"] + " " + l["price"])
        if kind == "rite": assert effs[0]["rule"] == "rite", lid
        if kind == "link": assert effs[0]["rule"] == "link", lid
        if kind == "hand":
            calling = lid.split(".")[0]
            e = effs[0]
            if e["rule"] == "hand":
                tot = hand_sum[calling]
                for k, d in e["args"].items(): tot[k] = round(tot.get(k, hands[calling][k]) + d, 6)
                check_numbers(lid, e, l["text"], hand_base=tot)
            else:
                hand_rules[calling] += 1
                check_numbers(lid, e, l["text"])
    assert all(n <= 1 for n in hand_rules.values()), hand_rules
    assert sum(1 for l in fresh if l["kind"] == "hand") == 16
    # rites: never on their own road's tags
    for l in fresh:
        if l["kind"] == "rite" and l["region"] == "road":
            assert l["effects"][0]["tags"][0] not in ROAD_TAGS[l["group"]].split(","), l["id"]
    # the blues all present
    assert {l["id"] for l in fresh if l["kind"] == "blue"} == set(BLUES)
    # American spelling, one line, no doubled spaces
    for l in fresh:
        t = l["text"] + l.get("price", "")
        for brit in ("colour", "armour", "metre", "grey", "favour", "honour", "smoulder", "towards"):
            assert brit not in t.lower(), (l["id"], brit)
        assert "  " not in t and t.endswith("."), l["id"]

    data = {"version": 2, "story": v1["story"], "roads": v1["roads"], "flares": v1["flares"], "groups": board["groups"], "lamps": lamps}
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    def phase(l): return max([e.get("phase", 1) for e in l["effects"]] or [1])
    print(f"{len(lamps)} lamps ({len(fresh)} new) -> {OUT}")
    by = collections.Counter((l["region"], l["kind"]) for l in fresh)
    for region in ("hearth", "road", "bridge", "crossing", "ford", "oldroad"):
        print(f"  {region:9s}", ", ".join(f"{k} {n}" for (r, k), n in sorted(by.items()) if r == region))
    print("  by kind:", dict(sorted(collections.Counter(l["kind"] for l in fresh).items())))
    print("  by phase:", dict(sorted(collections.Counter(phase(l) for l in fresh).items())))


V1_RULES = set()

if __name__ == "__main__":
    main()

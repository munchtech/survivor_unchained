"""Stage 6: what the text promises, the world keeps (audit item 8)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *
from sub import sub

# ------------------------------------------------------------------ code --
from sub import ROOT
if "wolf.blood" not in open(ROOT + "logic/World/Standing.cs", encoding="utf8").read():
  sub("logic/World/Standing.cs", '''    /// <summary>At their own den the Pack holds off for someone who knows how to come to it.</summary>
    public static bool HollowCalm(Ctx c) => WolvesFriendly(c) || (!F(c, "hollow.hostile").Truthy &&
        Rules.Test(new Cond { Any = [new() { Knows = "beastlore" }, new() { Knows = "hint.greymuzzle" }, new() { HasTag = "wolf_fang" }] }, c));''',
    '''    /// <summary>At their own den the Pack holds off for someone who knows how to come to it,
    /// as Maeca tells it: no wolf blood on you since you last slept, and none of
    /// their skins on your back. Their kin worn into the Hollow undoes any peace
    /// short of running with them.</summary>
    public static bool HollowCalm(Ctx c)
    {
        if (F(c, "hollow.hostile").Truthy) return false;
        if (Rules.Test(new Cond { HasTag = "wolf_pelts" }, c) && !F(c, "pack.allied").Truthy) return false;
        return WolvesFriendly(c) || (!F(c, "wolf.blood").Truthy &&
            Rules.Test(new Cond { Any = [new() { Knows = "beastlore" }, new() { Knows = "hint.greymuzzle" }, new() { HasTag = "wolf_fang" }] }, c));
    }''')

VG = "logic/Play/Zones/Verge.cs"
if "wolf.blood" not in open(ROOT + VG, encoding="utf8").read():
  sub(VG, '''            f["verge.wolf_kills"] = Num("verge.wolf_kills") + 1;''',
      '''            f["verge.wolf_kills"] = Num("verge.wolf_kills") + 1;
              // Blood on you until you next sleep (rules.json washes it off at dawn): the Hollow can smell it.
              f["wolf.blood"] = Num("wolf.blood") + 1;
              // You knelt to Greymuzzle and promised him; the Pack keeps count.
              if (F("promise.pack").Truthy && !F("promise.broken").Truthy)
                  G.Apply($$"""[{ "set": { "promise.broken": true } }, {{Hist("broke_promise", "promised Greymuzzle a cure, and killed his wolves", ["beasts", "wolves", "betrayal"], 2, null, """{ "maeca": { "trust": -30, "affection": -20 } }""")}}]""");''')
  sub(VG, '''            if (HollowCalm()) G.Say("The wolves watch you come. None of them move to stop you.", null, 4);
              else G.Say("Low growling from every side of the Hollow.", null, 3);''',
      '''            if (HollowCalm()) G.Say("The wolves watch you come. None of them move to stop you.", null, 4);
              else if (Test("""{ "hasTag": "wolf_pelts" }""") && !F("pack.allied").Truthy) G.Say("They smell the cloak before they see you. Every wolf in the Hollow is on its feet.", null, 4);
              else if (F("wolf.blood").Truthy && Knows("hint.greymuzzle")) G.Say("They smell the blood on you before they see you. Maeca said none since you last slept.", null, 5);
              else G.Say("Low growling from every side of the Hollow.", null, 3);''')

print("code ok")

# ----------------------------------------------------------------- rules --
R = load("rules.json")
R["rules"].append({"id": "wolf.blood.washes", "when": fact("wolf.blood", gt=0), "effect": setd({"wolf.blood": 0})})
save("rules.json", R)

# -------------------------------------------------------------- dialogue --
D = load("dialogue.json")
g = D["greymuzzle"]["nodes"]
promise = next(c for c in g["show"]["choices"] if "I will stop whatever" in c["text"])
promise["effects"].append(setd({"promise.pack": True}))
g["again"]["text"] = V(
    (eq("promise.broken", True), "Greymuzzle comes out of the rocks, looks at you for a long moment, and lies down with his back to you. Behind him, the others do the same."),
    (all_(eq("promise.pack", True), eq("beasts.outcome", "ignored")), "Greymuzzle doesn't come out. Two of the wolves you saw lying in the dirt are not there any more. The others watch you the way they watch weather."),
    (eq("beasts.outcome", "cured"), "Greymuzzle is on his feet. So are the others. He looks at you, and then away, which from a wolf is as good as thanks."),
    "Greymuzzle watches you from the rocks. He does not get up.")
# Maeca hears.
mc = D["maeca"]
mc["nodes"]["cb_broke_promise"] = node(
    "You knelt to him. You held out your hand and he let you in. Then you killed his. ...I've nothing to say to you that I'd want to have said.",
    [ch("...", end=True)], effects=[setflag("maeca", "cb:broke_promise")])
mc["entry"].insert(len(mc["entry"]) - 1, {"when": all_(met("maeca"), hist("broke_promise"), noflag("maeca", "cb:broke_promise")), "node": "cb_broke_promise"})

# Snib's bribe is a deed someone will hear of.
s = D["snib"]["nodes"]["bribe"]
forty = next(c for c in s["choices"] if c["text"] == "Forty gold.")
forty["effects"].append(history("bribed_snib", "paid the Dig's foreman to break his own pump", ["beasts", "corrupt"], 1,
                                reactions={"wenna": {"respect": 5}, "pell": {"respect": 10}}, witnesses=["snib"]))
# Pell, who hears everything that is paid for, says so.
p = D["pell"]
p["nodes"]["cb_bribed_snib"] = node("I hear the Dig's pump broke. Pumps do. And I hear a very small foreman is forty gold richer. You might have come to me; I'd have done it for thirty-five, and kept it quieter.",
                                    effects=[setflag("pell", "cb:bribed_snib")], next="hub")
p["entry"].insert(len(p["entry"]) - 1, {"when": all_(met("pell"), hist("bribed_snib"), noflag("pell", "cb:bribed_snib")), "node": "cb_bribed_snib"})

# The fortune knows a broken promise too.
fb = D["vonnra"]["nodes"]["f_beasts"]["text"]
fb.insert(0, {"when": all_(eq("promise.broken", True), not_(eq("beasts.outcome", "slaughtered"))),
              "text": "I see an old wolf who let you into his house, and you, coming back to it with his children's blood on your hands. Whatever else you did about the wolves, he will remember that first. So will I."})
save("dialogue.json", D)
print("promises ok")

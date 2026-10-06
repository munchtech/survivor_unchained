"""The story lead's notes for Vonnra and Harlan (a035208561a66c171, 4 October): wants, hides and
notes only; the three changed lines' directions; Harlan's preview text."""
import glob
import json
import re
from collections import OrderedDict

FILES = sorted(glob.glob("tools/vo/direction/*.json"))


def patch(lid, upd=None, fn=None):
    hits = [p for p in FILES if re.search(r'^ "' + re.escape(lid) + r'": ', open(p, encoding="utf-8").read(), re.M)]
    if not hits:  # no direction yet: a new entry in additions.json
        p = "tools/vo/direction/additions.json"
        t = open(p, encoding="utf-8").read().rstrip()
        t = t[:-1].rstrip() + ",\n " + json.dumps(lid) + ": {}\n}\n"
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        hits = [p]
    hit = hits[-1]
    t = open(hit, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', t, re.M)
    d = json.loads(m.group(1))
    d.update(upd or {})
    if fn:
        fn(d)
    line = m.group(0)
    t = t.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(t)
    open(hit, "w", encoding="utf-8", newline="\n").write(t)


def add_note(extra):
    return lambda d: d.update(note=(d.get("note", "") + " " + extra).strip())


OWN = ("The warmth of ownership, not tenderness: level and exact, as if she has always had the name. That is what frightens.")

# --- Vonnra
for lid in ("dlg.cin_drowned_fire.call.0", "say.bc92c07d79db"):
    patch(lid, fn=add_note("The kindness is in 'Come up'. 'No charge, this once.' is level and a little dry, a favour entered "
                           "in a ledger, and the fortune says it the same way so the ear can match them."))
patch("dlg.vonnra.first.0", {"hides": "that she called this traveller up the road last night"})
patch("dlg.vonnra.first.1", fn=lambda d: d.update(
    wants="to take your measure before anyone else does",
    hides="how much this matters: she drowned twenty-six to get you",
    note=(d.get("note", "") + " 'Sooner than I had thought' is literal; she expected to drown more.").strip()))
patch("dlg.vonnra.first.2", {"wants": "your toll, and your face remembered", "hides": "that she has been waiting for you"})
patch("dlg.vonnra.hub.2", {"emo": "calm, measured", "vol": "quiet"})
patch("bark.vonnra.night.3", {"emo": "still", "intent": "she counts the lights", "pace": "slow", "vol": "quiet",
                              "note": "Still, quietly. 'Somebody should.' is civic duty. She is counting her own work (the lights "
                                      "that go out are her ledger's lines), but nothing of that plays."})
patch("dlg.vonnra.vault.0", fn=add_note("'without charging' is exact. Everything else she gives free she prices first and then "
                                        "waives ('That would be five gold. This once, no charge.'), so it stays owed. This one "
                                        "she never prices."))
_f0 = {}


def grab(d):
    _f0.update(d)


patch("dlg.vonnra.fortune.0", fn=grab)
patch("dlg.vonnra.fortune.2", fn=lambda d: d.update(emo=_f0["emo"], vol="quiet", note=_f0.get("note", ""),
                                                    pace=_f0.get("pace", d.get("pace"))))
patch("dlg.vonnra.f_self.0", {"wants": "to learn whether you know what you are", "hides": "that she is the 'what'"})
patch("dlg.vonnra.f_self.3", {"wants": "you to believe the lamps chose you",
                              "hides": "that she lit them, and they have lit for twenty-six before you"})
patch("dlg.vonnra.risen.0", {"hides": "that she holds the note"})
patch("dlg.vonnra.jessop.0", {"wants": "the subject closed",
                              "hides": "that she sent Jessop down, not south: through the sealed door. The narrator's page-turn "
                                       "is the tell; she plays none"})
for lid in ("dlg.vonnra.f_ember.5", "dlg.vonnra.f_ember.6"):
    patch(lid, {"wants": "to see whether you will be the one who stops them",
                "hides": "she let the caravan be taken so these crates would never reach the Dig", "vol": "quiet"})


def own(d):
    n = d.get("note", "")
    n = re.sub(r"the only warmth anywhere in her part, and it should frighten\.?", OWN, n)
    if OWN not in n:
        n = (n + " The name: " + OWN).strip()
    d["note"] = n


for lid in ("dlg.vonnra.f_accuse.0", "dlg.vonnra.f_door.0", "dlg.vonnra.hub.0"):
    patch(lid, fn=own)

# --- Harlan
patch("dlg.harlan.hub.1", {"emo": "numb grief", "vol": "quiet", "pace": "slow",
                           "note": "'I heard. I heard.' 'They were fed' is Holloway's comfort, and it isn't one. The cold, "
                                   "plainly. The brick is where he breaks. Then hollow kindness."})
patch("dlg.harlan.notwolves.0", {"hides": "who would want those crates stopped"},
      add_note("'Who—' is him starting to guess, and not daring to."))
patch("dlg.harlan.pell.0", {"hides": "Pell keeps the books for the Dig trade, and could hang him with them. The fury is on "
                                     "top; the fear is under it, unplayed"})
for lid in ("dlg.harlan.be.0", "dlg.harlan.g.0", "dlg.harlan.be_dig.0"):
    patch(lid, {"hides": "the buyer is the Dig, and he has known for two years"})
patch("dlg.harlan.ledger_early.0", fn=add_note("'If I knew, I'd do something I'd hang for.' plain, a man stating a fact about "
                                               "himself."))
patch("dlg.harlan.crates.0", {"wants": "the crates delivered, because the Dig has paid", "hides": "that he means to send them on"})
patch("dlg.harlan.t_harlan.0", {"hides": "his sister died in the fever year, of the ember sickness, and he sells the stuff "
                                         "anyway; he has never let himself see it, so never play the irony"})

P = "tools/vo/cast.json"
c = json.load(open(P, encoding="utf-8"), object_pairs_hook=OrderedDict)
v = c["voices"]["vonnra"]
v["wants"] = ("the chain held and the valley alive, and for that, one Unchained who will walk down a stair; every line "
              "measures the survivor for it")
v["hides"] = ("she lit the ford lamps; she drowned twenty-six to get one; she called this one up the road; her sight is bought "
              "(Rook, Sella, Pell). Her 'No charge' and 'This once' are debts entered, not gifts: she prices a thing, then "
              "waives it, so it stays owed")
h = c["voices"]["harlan"]
h["wants"] = "Jory home, and the Company alive"
h["hides"] = ("the Company has sold the Dig its blasting ember for two years, through Pell's books and the Kerchiefs' road; he "
              "put Jory on the road with six crates he knew were bound for the hole. His grief is real and so is his guilt, and "
              "every 'Jory' carries both. His sister died in the fever year, of the ember sickness, and he sells the stuff "
              "anyway; he has never let himself see that, so never play the irony")
assert "lamp oil" in h["ref_text"], h["ref_text"]
h["ref_text"] = h["ref_text"].replace("lamp oil", "salt, iron and Morrow cloth")
open(P, "w", encoding="utf-8", newline="\n").write(json.dumps(c, indent=1, ensure_ascii=False) + "\n")
print("ok")

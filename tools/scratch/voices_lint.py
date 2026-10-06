"""VOICES.md's mechanical rules over the spoken data: retired words, Vonnra's
contractions, bark length. Prints offenders."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content"
d = json.load(open(ROOT + r"\dialogue.json", encoding="utf-8"))
npcs = json.load(open(ROOT + r"\npcs.json", encoding="utf-8"))
folk = json.load(open(ROOT + r"\folk.json", encoding="utf-8"))

RETIRED = [r"\bmostly\b", r"\bHm\.", r"I will not forget", r"nobody listens"]
CONTR = re.compile(r"\b\w+'(s|t|re|ve|ll|d|m)\b", re.I)


def spoken(text):
    """Strip narrator parentheticals."""
    return re.sub(r"\([^)]*\)", "", text)


lines = []
for cid, c in d.items():
    for nid, n in c["nodes"].items():
        sp = n.get("speaker") or c.get("npc") or cid
        t = n.get("text")
        for i, v in enumerate(t if isinstance(t, list) else [{"text": t or ""}]):
            lines.append((f"dlg.{cid}.{nid}.{i}", sp, v["text"]))
for k, n in npcs["npcs"].items():
    for key in ("barks", "nightBarks"):
        for i, b in enumerate(n.get(key) or []):
            lines.append((f"bark.{k}.{key}.{i}", k, b))
    for i, s in enumerate(n.get("said") or []):
        lines.append((f"bark.{k}.said.{i}", k, s["text"]))
for i, l in enumerate(folk["lines"]):
    lines.append((f"folk.{i}", "folk", l["text"]))

for lid, sp, text in lines:
    for r in RETIRED:
        if re.search(r, text):
            print("RETIRED", lid, sp, "|", text[:200])
    if sp == "vonnra" or lid.startswith("dlg.vonnra."):
        if lid.startswith("dlg.vonnra.") and (sp in (None, "vonnra") or True):
            s = spoken(text)
            # Vonnra's own words only: skip narrator nodes
            if sp == "narrator":
                continue
            for m in CONTR.finditer(s):
                w = m.group(0)
                if w.lower().endswith("'s") and not w.lower() in ("it's", "that's", "there's", "here's", "what's", "who's", "he's", "she's", "let's"):
                    continue  # possessive
                print("VONNRA-CONTRACTION", lid, "|", w, "|", s[:160])
for lid, sp, text in lines:
    if lid.startswith("bark.") and ".said." in lid and len(text.replace("...", "").split()) > 12:
        print("LONG-SAID", lid, text)

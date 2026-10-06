"""The voice director's first reads for the story lead: Chid at Nell's grave,
Maeca's walk and dark, the Wayfinder's opener. Edits dialogue.json in place,
keeping its own format (indent 1, CRLF, trailing newline)."""
import json, sys

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc"
P = ROOT + r"\godot\data\content\dialogue.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))


def variants(conv, node):
    t = d[conv]["nodes"][node]["text"]
    return t if isinstance(t, list) else None


def swap(conv, node, old, new, idx=None):
    n = d[conv]["nodes"][node]
    t = n["text"]
    if isinstance(t, list):
        hits = [i for i, v in enumerate(t) if old in v["text"] and (idx is None or i == idx)]
        assert len(hits) == 1, (conv, node, old, hits)
        t[hits[0]]["text"] = t[hits[0]]["text"].replace(old, new)
    else:
        assert old in t, (conv, node, old)
        n["text"] = t.replace(old, new)


# Maeca names them as a people from her first line (VOICES: "the Pack" or "them").
swap("maeca", "first", "The wolves aren't the problem.", "The Pack aren't the problem.")

# Quoted words go to their speaker: a bare "she says" goes, so the subtitle and
# the voice match. The walk no longer says "Eating": the cured first night's
# laugh at the hides ("They're eating.") is where that lands.
swap("maeca", "blind_walk", "\"Him,\" she says. \"And the bitch with the white foot. Eating.\"",
     "\"Him. And the bitch with the white foot.\"")
swap("maeca", "blind", "\"They're eating,\" she says, and pulls you down onto the hides.",
     "\"They're eating.\" She pulls you down onto the hides.")

# Night three: she is counting your heart between the sentences (she says so at
# dawn, blind3_morning: "I counted between."). The pause is shown, not named.
swap("maeca", "blind_dark",
     "She lifts her head. \"They don't do that,\" she says. \"Not for me. Not for anyone.\" She lies back down. \"You walk quiet. You came into my Hollow and knelt to him and he let you. You never talk about before.\" A pause. \"What were you?\"",
     "She lifts her head. \"They don't do that. Not for me. Not for anyone.\" She lies back down, her ear where it was. \"You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk about before.\" Against your chest you feel her lips move, without a sound. \"What were you?\"")
swap("maeca", "blind_dark",
     "listening the way she listens to the Hollow. \"You walk quiet,\" she says. \"You never talk about before.\" A pause. \"What were you?\"",
     "listening the way she listens to the Hollow. \"You walk quiet. You never talk about before.\" Against your chest you feel her lips move, without a sound. \"What were you?\"")

# The Wayfinder's opener was a line any game could use. Hers is about who comes
# back: her trade (the margin), her buyer (the notes) and, unsaid, the survivor.
swap("wayfinder", "first",
     "You've the look of someone who walks toward trouble on purpose. Good.",
     "You've the look of someone who comes back. Good. The other sort only ever buy the one map.")

# Chid after the burial: never on its morning before it, and never telling a
# survivor who stood at the graveside what they saw.
chid = d["chid"]
for e in chid["entry"]:
    if e.get("node") == "cb_nell":
        e["when"]["all"].append({"any": [
            {"not": {"fact": "nell.burying", "eq": True}},
            {"zone": {"id": "waystation", "key": "burial", "eq": True}},
        ]})
        break
else:
    sys.exit("cb_nell entry not found")
n = chid["nodes"]["cb_nell"]
old = n["text"]
assert isinstance(old, str) and old.startswith("We buried Nell"), old
tail = old[old.index("(He is quiet"):]
n["text"] = [
    {"when": {"zone": {"id": "waystation", "key": "burial", "eq": True}},
     "text": "I sang it flat. I always have. There's always somebody who has the tune. " + tail},
    {"text": old},
]

out = json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
open(P, "wb").write(out.encode("utf-8"))
print("ok")

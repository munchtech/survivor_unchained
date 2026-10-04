"""Every line the game can say aloud, read out of the content and the code.

Builds tools/vo/manifest.json: one entry per line, with who says it, what is
said (split where the narrator speaks inside someone's line), the text's hash
(so a line rewritten by the writer is known to need a new take), the
direction for the actor, and where the line stands in production. Run it
whenever the writing changes; it keeps what it knew (directions, takes,
status) and marks a line `stale` when its text has moved under a take.

    python tools/vo/lines.py            # rebuild the manifest
    python tools/vo/lines.py --report   # counts by voice and status

Line ids:
  dlg.<npc>.<node>.<variant>   a line of a conversation (dialogue.json)
  ply.<npc>.<node>.<choice>    the survivor's reply (choices; voiced later)
  bark.<npc>.<day|night>.<i>   said to the air in town (npcs.json)
  bark.<npc>.said.<i>          the same, only while the world is a certain way (npcs.json "said")
  guard.<i>                    a gate guard (npcs.json)
  folk.<i>                     a passer-by (folk.json)
  say.<hash>                   the narrator, or a voice, from the zone code
  cbark.<hash>                 a named voice in a fight (the zone code)

The game finds a line's take by id, or, for lines written in code, by the
hash of the text it is about to show; either way it plays a take only if the
take was made from exactly that text.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter, OrderedDict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONTENT = os.path.join(ROOT, "godot", "data", "content")
LOGIC = os.path.join(ROOT, "godot", "logic")
HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "manifest.json")
DIRECTION = os.path.join(HERE, "direction")


def text_hash(s: str) -> str:
    """The first 12 hex digits of the SHA-1 of the text as the game holds it
    (the same function is VoiceOver.Hash in the game)."""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


# Who owns a conversation's voice (the npc id is the voice id unless said here).
NPC_VOICE = {"survivor": "lampling", "wayfinder": "ysolde", "board": None, "greymuzzle": "narrator"}
# Named speakers of the zone code's lines and barks.
SPEAKER_VOICE = {"The Ford-Warden": "warden", "Grimtunnel": "grimtunnel", "Snib": "snib",
                 "The dead Watchman": "watchman", "The bones": "bones", "Jory Coyle": "jory",
                 "A Kerchief woman": "kerchief_woman", "The Barrow Lord": "barrow_lord"}
# A conversation node's own speaker (the cinematics name theirs).
NODE_VOICE = {"ford_warden": "warden", "barrow_lord": "barrow_lord", "kerchief_woman": "kerchief_woman", "guard": "guard"}


def name_elided(s: str) -> tuple[str, bool]:
    """A line with the survivor's name in it, said without the name (the
    subtitle still shows it). False when the name cannot be lifted out cleanly."""
    if "{name}" not in s:
        return s, True
    t = s
    t = re.sub(r",\s*\{name\}\s*([.,:;!?])", r"\1", t)       # "Late, {name}." -> "Late."
    t = re.sub(r"^\{name\}[.:,]\s*", "", t)                  # "{name}. Your chapter..." -> "Your chapter..."
    t = re.sub(r"([.!?]\s+)\{name\}[.:,]\s*", r"\1", t)      # "... Go home, {name}." handled above; mid-line vocative
    t = re.sub(r"\b([Aa]nd) \{name\}:\s*", r"\1 ", t)                # "And {name}: run." -> "And run."
    if "{name}" in t:
        return s, False
    # A sentence may now start in lower case.
    t = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
    return t, True


def segments(text: str, voice: str, owner: str | None = None) -> list[dict]:
    """Split a line into who says what (docs/VOICES.md):

    - in a person's line, a capitalised (parenthesis.) is the narrator's, and a
      lower-case (parenthesis) is how the person says it: no one reads it
      aloud; it becomes an acted tag in their take (`acted`);
    - in narration inside a person's conversation (`owner`), a "quote" is
      that person speaking; the narrator reads the rest.
    """
    out: list[dict] = []

    def add(v: str, said: str, acted: str):
        said, acted = said.strip(), acted.strip()
        if not said:
            if acted and out and out[-1]["voice"] == v:  # a direction after the words
                out[-1]["acted"] = (out[-1].get("acted", out[-1]["text"]) + " " + acted).strip()
            return
        if out and out[-1]["voice"] == v:
            prev = out[-1]
            prev["acted"] = f"{prev.get('acted', prev['text'])} {acted}"
            prev["text"] = f"{prev['text']} {said}"
        else:
            out.append({"voice": v, "text": said, "acted": acted})

    if voice != "narrator":
        pos, pending = 0, ""
        for m in re.finditer(r"\(([^)]*)\)", text):
            inner = m.group(1).strip()
            before = text[pos:m.start()]
            if inner[:1].islower():
                # How it is said: kept in the acted text, out of the words.
                pending += before + f" [{inner}] "
                if before.strip():
                    add(voice, before, pending)
                    pending = ""
            else:
                add(voice, before, pending + before)
                pending = ""
                if inner:
                    add("narrator", inner, inner)
            pos = m.end()
        add(voice, text[pos:], pending + text[pos:])
    else:
        merged = re.sub(r"\(([^)]*)\)", r"\1", text)
        if owner and owner != "narrator":
            pos = 0
            for m in re.finditer('"([^"]+)"|“([^”]+)”', merged):
                add("narrator", merged[pos:m.start()], merged[pos:m.start()])
                q = (m.group(1) or m.group(2)).strip()
                add(owner, q, q)
                pos = m.end()
            add("narrator", merged[pos:], merged[pos:])
        else:
            add("narrator", merged, merged)
    for s in out:
        s["text"] = re.sub(r"\s+", " ", s["text"]).strip()
        s["acted"] = re.sub(r"\s+", " ", s.get("acted", "")).strip()
        if s["acted"] == s["text"]:
            s.pop("acted")
    return out


def cast_voices() -> set:
    return set(json.load(open(os.path.join(HERE, "cast.json"), encoding="utf-8"))["voices"])


def variants(t):
    if isinstance(t, str):
        return [{"text": t}]
    return [v if isinstance(v, dict) else {"text": v} for v in t]


def from_dialogue(lines: list):
    d = json.load(open(os.path.join(CONTENT, "dialogue.json"), encoding="utf-8"))
    for npc, convo in d.items():
        owner = NPC_VOICE.get(npc, npc)
        for nid, node in convo["nodes"].items():
            speaker = node.get("speaker")
            voice = NODE_VOICE.get(speaker, speaker) if speaker and speaker != "player" else owner
            for i, v in enumerate(variants(node["text"])):
                raw = v["text"]
                line = {"id": f"dlg.{npc}.{nid}.{i}", "kind": "dialogue", "voice": voice, "text": raw,
                        "where": f"dialogue.json {npc}/{nid}#{i}"}
                if npc == "board" or v.get("add"):
                    line["skip"] = "a notice, read not heard"
                elif raw.lstrip().startswith("[explicit scene"):
                    line["skip"] = "the owner's writer's slot"
                elif voice is None:
                    line["skip"] = "no voice"
                lines.append(line)
            for ci, c in enumerate(node.get("choices") or []):
                for vi, v in enumerate(variants(c["text"])):
                    lines.append({"id": f"ply.{npc}.{nid}.{ci}" + (f".{vi}" if vi else ""), "kind": "choice", "voice": "survivor",
                                  "text": v["text"], "where": f"dialogue.json {npc}/{nid} choice {ci}",
                                  "skip": "the survivor's replies are voiced in a later pass"})


def from_npcs(lines: list):
    d = json.load(open(os.path.join(CONTENT, "npcs.json"), encoding="utf-8"))
    for group in ("npcs", "outsiders"):
        for npc, n in d[group].items():
            voice = NPC_VOICE.get(npc, npc)
            for key, tag in (("barks", "day"), ("nightBarks", "night")):
                for i, b in enumerate(n.get(key) or []):
                    lines.append({"id": f"bark.{npc}.{tag}.{i}", "kind": "bark", "voice": voice, "text": b,
                                  "where": f"npcs.json {npc}.{key}[{i}]"})
            # Said only while the world is a certain way (what the survivor settled).
            for i, s in enumerate(n.get("said") or []):
                lines.append({"id": f"bark.{npc}.said.{i}", "kind": "bark", "voice": voice, "text": s["text"],
                              "where": f"npcs.json {npc}.said[{i}]"})
    for i, g in enumerate(d.get("guards") or []):
        lines.append({"id": f"guard.{i}", "kind": "bark", "voice": "guard", "text": g["line"], "where": f"npcs.json guards[{i}]"})


def from_folk(lines: list):
    d = json.load(open(os.path.join(CONTENT, "folk.json"), encoding="utf-8"))
    for i, l in enumerate(d["lines"]):
        lines.append({"id": f"folk.{i}", "kind": "folk", "voice": "folk", "text": l["text"], "where": f"folk.json lines[{i}]"})


_STR = r'"(?:[^"\\]|\\.)*"'


def _unescape(lit: str) -> str:
    return json.loads(lit)


def _args(src: str, start: int) -> tuple[list[str], int]:
    """The top-level arguments of a call whose '(' is at src[start]."""
    depth, i, cur, args = 0, start, [], []
    while i < len(src):
        ch = src[i]
        if ch == '"':
            m = re.compile(_STR).match(src, i)
            if m:
                cur.append(m.group(0)); i = m.end(); continue
        if ch in "([{":
            depth += 1
            if depth == 1 and ch == "(":
                i += 1; continue
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                args.append("".join(cur).strip()); return args, i
        elif ch == "," and depth == 1:
            args.append("".join(cur).strip()); cur = []; i += 1; continue
        cur.append(ch); i += 1
    return args, i


def from_code(lines: list):
    """The narrator's and the named voices' lines written in the zone code."""
    seen = set()
    for dirpath, _, files in os.walk(LOGIC):
        for f in files:
            if not f.endswith(".cs"):
                continue
            path = os.path.join(dirpath, f)
            src = open(path, encoding="utf-8").read()
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            # Arrays of lines said by index (Verge's CageLines).
            arrays = {}
            for m in re.finditer(r"static readonly string\[\] (\w+)\s*=\s*\[(.*?)\];", src, re.S):
                arrays[m.group(1)] = [_unescape(s) for s in re.findall(_STR, m.group(2))]
            for m in re.finditer(r"\bG\.Say\(", src):
                args, _ = _args(src, m.end() - 1)
                if not args:
                    continue
                texts = [_unescape(s) for s in re.findall(_STR, args[0])]
                for name, arr in arrays.items():
                    if name in args[0]:
                        texts += arr
                who = _unescape(args[1]) if len(args) > 1 and re.fullmatch(_STR, args[1]) else None
                for t in texts:
                    if t in seen or "{" in t and "$" in args[0]:
                        continue
                    seen.add(t)
                    lines.append({"id": f"say.{text_hash(t)}", "kind": "say", "voice": SPEAKER_VOICE.get(who or "", "narrator"), "text": t,
                                  "who": who, "where": rel})
            for m in re.finditer(r"new Ev\.Bark\s*\{([^}]*)\}", src):
                body = m.group(1)
                sp = re.search(r"Speaker\s*=\s*(" + _STR + ")", body)
                tm = re.search(r"Text\s*=\s*(.*?)(?:,\s*Speaker|$)", body, re.S)
                texts = [_unescape(s) for s in re.findall(_STR, tm.group(1))] if tm else []
                speaker = _unescape(sp.group(1)) if sp else None
                for t in texts:
                    if t in seen:
                        continue
                    seen.add(t)
                    line = {"id": f"cbark.{text_hash(t)}", "kind": "combat", "voice": SPEAKER_VOICE.get(speaker or "", None),
                            "text": t, "who": speaker, "where": rel}
                    if speaker is None:
                        line["skip"] = "a fight's caption, not a voice"
                    lines.append(line)
            # A boss's own barks (IBossArena.Bark(x, z, text, speaker)): shouted like any named bark.
            for m in re.finditer(r"\b\w+\.Bark\(", src):
                args, _ = _args(src, m.end() - 1)
                if not args or len(args) < 4 or not re.fullmatch(_STR, args[3].strip()):
                    continue
                speaker = _unescape(args[3].strip())
                for t in (_unescape(s) for s in re.findall(_STR, args[2])):
                    if t in seen:
                        continue
                    seen.add(t)
                    line = {"id": f"cbark.{text_hash(t)}", "kind": "combat", "voice": SPEAKER_VOICE.get(speaker),
                            "text": t, "who": speaker, "where": rel}
                    if line["voice"] is None:
                        line["skip"] = f"no voice cast for {speaker}"
                    lines.append(line)


def build() -> list[dict]:
    lines: list[dict] = []
    from_dialogue(lines)
    from_npcs(lines)
    from_folk(lines)
    from_code(lines)
    for l in lines:
        l["hash"] = text_hash(l["text"])
        if l.get("skip"):
            continue
        said, ok = name_elided(l["text"])
        if not ok:
            l["skip"] = "the survivor's name is part of the sentence"
            continue
        if said != l["text"]:
            l["name_elided"] = True
        if "{" in said:
            l["skip"] = "a number from the world"
            continue
        owner = None
        if l["id"].startswith("dlg.") and l["voice"] == "narrator":
            npc = l["id"].split(".")[1]
            owner = NPC_VOICE.get(npc, npc)
            owner = owner if owner in cast_voices() else None
        l["segments"] = segments(said, l["voice"], owner)
        if not l["segments"]:
            l["skip"] = "nothing to say"
    return lines


def load_directions() -> dict:
    """tools/vo/direction/*.json: per line id, how it is to be said, and any
    segment voices set by hand (a quote in a narrator line given to its speaker)."""
    out = {}
    if os.path.isdir(DIRECTION):
        for f in sorted(os.listdir(DIRECTION)):
            if f.endswith(".json"):
                out.update(json.load(open(os.path.join(DIRECTION, f), encoding="utf-8")))
    return out


def cast() -> dict:
    return json.load(open(os.path.join(HERE, "cast.json"), encoding="utf-8"))["voices"]


def expand(lines: list[dict], directions: dict) -> list[dict]:
    """A line several people say (a passer-by's, a guard's) becomes one line
    per voice, `<id>.<f|m>`: the game picks the take that fits who is speaking."""
    voices = cast()
    out = []
    for l in lines:
        d = directions.get(l["id"]) or {}
        if "voices" not in d or l.get("skip"):
            out.append(l)
            continue
        for v in d["voices"]:
            sex = voices[v]["sex"]
            c = json.loads(json.dumps(l))
            c["id"] = f"{l['id']}.{sex}"
            c["voice"] = v
            c["sex"] = sex
            if "segments" in c:
                c["segments"] = [dict(s, voice=v) for s in c["segments"]]
            directions.setdefault(c["id"], {k: x for k, x in d.items() if k != "voices"})
            out.append(c)
    return out


def merge(lines: list[dict]) -> list[dict]:
    old = {}
    if os.path.exists(MANIFEST):
        old = {l["id"]: l for l in json.load(open(MANIFEST, encoding="utf-8"))["lines"]}
    directions = load_directions()
    lines = expand(lines, directions)
    out = []
    for l in lines:
        prev = old.get(l["id"], {})
        d = directions.get(l["id"])
        if d:
            l["direction"] = {k: v for k, v in d.items() if k not in ("segments", "voice", "skip")}
            if "voice" in d:
                l["voice"] = d["voice"]
                if "segments" in l:
                    l["segments"] = [dict(s, voice=d["voice"]) if s["voice"] != "narrator" else s for s in l["segments"]]
            if "say" in d:
                # Said otherwise than written (a quotation read out, initials spelt).
                l["segments"] = [{"voice": l["voice"], "text": d["say"]}]
            if "segments" in d:
                l["segments"] = d["segments"]
            if "skip" in d:
                l["skip"] = d["skip"]
                l.pop("segments", None)
        take = prev.get("take")
        if take:
            l["take"] = take
            l["status"] = prev.get("status", "done") if take.get("hash") == l["hash"] else "stale"
        elif prev.get("status") == "failed" and prev.get("hash") == l["hash"]:
            # No clean take yet: stays failed (with why) until someone retries it.
            l["status"] = "failed"
            l["failed"] = prev.get("failed")
        else:
            l["status"] = "skip" if l.get("skip") else "todo"
        if l.get("skip"):
            l["status"] = "skip"
        out.append(l)
    return out


def save(lines: list[dict]):
    doc = OrderedDict(about="Every line the game can say aloud; built by tools/vo/lines.py, takes by tools/vo/produce.py.",
                      lines=lines)
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")


def report(lines):
    by = Counter()
    for l in lines:
        by[(l.get("voice") or "-", l["status"])] += 1
    voices = sorted({v for v, _ in by})
    for v in voices:
        row = {s: n for (vv, s), n in by.items() if vv == v}
        print(f"{v:12s}", row)
    print(Counter(l["status"] for l in lines))



# The cinematics in story order (docs/cinematics/cNN_<name>.md).
CINEMATICS = sorted((f[:-3] for f in os.listdir(os.path.join(ROOT, "docs", "cinematics")) if re.match(r"c\d\d_.*\.md$", f)),
                    key=lambda n: n) if os.path.isdir(os.path.join(ROOT, "docs", "cinematics")) else []
CIN_ORDER = {n[4:]: i for i, n in enumerate(sorted(CINEMATICS))}
NPC_ORDER = ["rook", "chid", "brannoc", "holloway", "wenna", "tam", "maeca", "harlan", "jory", "sella", "pell", "rav",
             "vonnra", "keegan", "wayfinder", "survivor", "greymuzzle", "redcowl"]


def impact(l: dict) -> tuple:
    """Most heard and earliest first: the opening cinematic, the prologue,
    the other cinematics in story order, the rest of the scenes,
    conversations in the order the town is met, then barks and passers-by."""
    i = l["id"]
    if i.startswith("dlg.cin_"):
        name = i.split(".")[1][4:]
        n = CIN_ORDER.get(name, 99)
        return (0 if n == 0 else 2, n, 0)
    if i.startswith("say.") and "Prologue" in l.get("where", ""):
        return (1, 0, 0)
    if i.startswith("say."):
        return (3, 0, 0)
    if i.startswith("dlg."):
        npc = i.split(".")[1]
        return (4, NPC_ORDER.index(npc) if npc in NPC_ORDER else len(NPC_ORDER), 0)
    if i.startswith(("bark.", "guard.")):
        return (5, 0, 0)
    if i.startswith("cbark."):
        return (6, 0, 0)
    return (7, 0, 0)

if __name__ == "__main__":
    lines = merge(build())
    save(lines)
    if "--report" in sys.argv:
        report(lines)
    else:
        print(f"{len(lines)} lines, {sum(1 for l in lines if l['status'] != 'skip')} to voice -> {os.path.relpath(MANIFEST, ROOT)}")

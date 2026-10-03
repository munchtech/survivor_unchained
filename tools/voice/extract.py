#!/usr/bin/env python3
"""Every spoken line in the game, as a recording script.

    python3 tools/voice/extract.py            (writes the manifest, the scripts and CASTING.md)
    python3 tools/voice/extract.py --check    (says what changed; writes nothing)

Reads the content (dialogue.json, npcs.json, folk.json, quests.json) and the
zone scripts' spoken lines (G.Say and named barks in logic/Play/Zones, and the
chapter's page in logic/World/Chapter.cs), and writes:

  godot/data/voice/lines.json      the manifest: one entry per take
  docs/voice/script/<voice>.md     the recording script, one per voice
  docs/voice/CASTING.md            the casting sheet (from tools/voice/voices.json)

Nothing in the content is changed. A line's ID comes from where it lives (the
conversation, the node, the variant's place; the bark's place in its list), so
it survives a rewrite of its words; its hash comes from the words, so a
rewrite marks its audio stale. Hand-written direction lives in
tools/voice/directions.json, keyed by line ID (or by conversation.node for
every variant of a node), and is kept with the hash of the words it was written
for, so direction written for old words is reported.

Standard library only.
"""
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GODOT = os.path.join(ROOT, "godot")
CONTENT = os.path.join(GODOT, "data", "content")
MANIFEST = os.path.join(GODOT, "data", "voice", "lines.json")
SCRIPTS = os.path.join(ROOT, "docs", "voice", "script")
CASTING = os.path.join(ROOT, "docs", "voice", "CASTING.md")
HERE = os.path.dirname(os.path.abspath(__file__))

ZONE_FILES = [("prologue", "logic/Play/Zones/Prologue.cs"), ("waystation", "logic/Play/Zones/Waystation.cs"),
              ("verge", "logic/Play/Zones/Verge.cs"), ("arena", "logic/Play/Zones/ArenaRun.cs")]
CHAPTER_FILE = "logic/World/Chapter.cs"

# Names the zone scripts give speakers, to the voice that says them.
SPEAKER_NAMES = {
    None: "narrator", "The Ford-Warden": "ford_warden", "Grimtunnel": "grimtunnel", "Snib": "snib",
    "The dead Watchman": "dead_watchman", "The bones": "bones",
}
# Conversation speakers whose voice has another name.
SPEAKER_VOICE = {"survivor": "lampling", "board": "narrator", "greymuzzle": "narrator", "player": "player"}


def text_hash(s):
    """The first twelve hex digits of the SHA-1 of the words as written (UTF-8),
    tokens and all: VoiceLines.Hash in godot/logic/World/VoiceLines.cs."""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]


def load(name):
    with open(os.path.join(CONTENT, name), encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)


def load_here(name, default):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)


# ----------------------------------------------------------- conditions --

def cond_words(c):
    """A condition (logic/World/Logic.cs Cond) in plain words."""
    if c is None:
        return ""
    if not isinstance(c, dict):
        return json.dumps(c)
    def cmp(c):
        bits = []
        if "exists" in c:
            bits.append("is set" if c["exists"] else "is not set")
        if "eq" in c:
            bits.append(f"= {json.dumps(c['eq'])}")
        if "ne" in c:
            bits.append(f"≠ {json.dumps(c['ne'])}")
        for k, sym in (("gte", "≥"), ("lte", "≤"), ("gt", ">"), ("lt", "<")):
            if k in c:
                bits.append(f"{sym} {c[k]}")
        return " ".join(bits) if bits else "is true"
    if "all" in c:
        return " and ".join(f"({cond_words(x)})" if ("any" in x) else cond_words(x) for x in c["all"])
    if "any" in c:
        return " or ".join(cond_words(x) for x in c["any"])
    if "not" in c:
        return f"not [{cond_words(c['not'])}]"
    if "fact" in c:
        return f"fact {c['fact']} {cmp(c)}"
    for k, say in (("knows", "survivor knows {}"), ("notKnows", "survivor does not know {}"), ("bg", "background is {}"),
                   ("archetype", "calling is {}"), ("hasItem", "carries {}"), ("hasTag", "carries something tagged {}"),
                   ("trait", "has the trait {}"), ("met", "has met {}"), ("history", "has done {}"),
                   ("sex", "the survivor is taken for {}")):
        if k in c:
            return say.format(c[k])
    if "rel" in c:
        r = c["rel"]
        return f"{r.get('npc')}'s {r.get('axis', 'trust')} {cmp(r)}".lower()
    if "npcFlag" in c:
        r = c["npcFlag"]
        return f"{r.get('npc')} flag {r.get('key')} {cmp(r)}"
    if "npcKnows" in c:
        r = c["npcKnows"]
        return f"{r.get('npc')} has heard of {r.get('event')}"
    if "faction" in c:
        r = c["faction"]
        return f"standing with {r.get('id')} {cmp(r)}"
    if "quest" in c:
        r = c["quest"]
        bits = [f"quest {r.get('id')}"]
        if "status" in r:
            bits.append(f"is {r['status']}")
        if "entry" in r:
            bits.append(f"has entry {r['entry']}")
        return " ".join(bits)
    for k in ("day", "level", "gold", "kills"):
        if k in c:
            return f"{k} {cmp(c[k])}"
    if "time" in c:
        t = c["time"]
        return "time is " + (" or ".join(t) if isinstance(t, list) else str(t))
    if "zone" in c:
        r = c["zone"]
        return f"zone {r.get('id')} {r.get('key')} {cmp(r)}"
    return json.dumps(c)


def sex_of(c):
    """'female' or 'male' if the condition turns on who the survivor is taken for."""
    if not isinstance(c, dict):
        return None
    if "sex" in c:
        return c["sex"]
    for k in ("all",):
        for x in c.get(k, []):
            s = sex_of(x)
            if s:
                return s
    if "not" in c:
        s = sex_of(c["not"])
        if s:
            return "male" if s == "female" else "female"
    return None


# ------------------------------------------------------- voiceable form --

TOKEN = re.compile(r"\{(name|day|gold|fact:[\w.]+)\}")
PLACEHOLDER = re.compile(r"\[explicit scene:[^\]]*\]")
PAREN = re.compile(r"\s*\(([^()]*)\)")
# How people address the survivor as a man or a woman: a line that does so
# with no variant for the other wants one.
GENDERED = re.compile(r"(^|,\s*|\.\s+)(lad|lass|laddie|lassie|sir|madam|ma'am|my lady|my lord|missus|mister)(?=[.!?,;:—])", re.I)


def voiceable(text, narrator, sexed=False):
    """The words as they can be said aloud, the stage directions taken out of
    them, and what was flagged on the way. Tokens the game fills in ({name})
    cannot be recorded, so they are dropped with the punctuation that hangs
    on them; the subtitle still shows them."""
    flags, stage = [], []
    say = text
    if PLACEHOLDER.search(say):
        flags.append("placeholder")
        say = PLACEHOLDER.sub("", say)
    if not narrator:
        # Every aside in brackets in a spoken line is the narrator's (what the
        # speaker does), so it leaves the take; where it fell mid-line it
        # leaves a pause behind it.
        def strip(m):
            stage.append(m.group(1).strip())
            return " ... "
        say = PAREN.sub(strip, say)
        if stage:
            flags.append("stage-direction")
    tokens = TOKEN.findall(say)
    if tokens:
        flags += sorted({"token:" + t for t in tokens})
        s = say
        s = re.sub(r"^\{name\}\.\s*", "", s)
        s = re.sub(r"^\{name\},\s*", "", s)
        s = re.sub(r",\s*\{name\}(?=[.!?,:;])", "", s)
        s = re.sub(r"\s+\{name\}:\s*", ": ", s)
        s = re.sub(r"\bAs \{name\}\b", "As you are", s)
        s = TOKEN.sub("", s)
        say = s
    say = re.sub(r"\s*(\.\.\.\s*){2,}", " ... ", say)
    say = re.sub(r"([.!?,;:—])\s*\.\.\.\s*\.\.\.", r"\1 ...", say)
    say = re.sub(r"(?<=[.!?])\s*\.\.\.\s*(?=\.\.\.)", " ", say)
    say = re.sub(r"\s{2,}", " ", say).strip()
    say = re.sub(r"^(\.\.\.\s*)+(?=\.\.\.)", "", say)
    say = re.sub(r"^\.\.\.\s*", "", say) if stage or tokens else say
    say = re.sub(r"\s*\.\.\.$", "", say) if stage and text.rstrip().endswith(")") else say
    say = re.sub(r"\s+([,!?;:]|\.(?!\.))", r"\1", say)
    if say and say[0].islower():
        say = say[0].upper() + say[1:]
    if not narrator and not sexed and GENDERED.search(PAREN.sub("", text)):
        flags.append("gendered-address")
    return say, stage, flags


# ------------------------------------------------------------ direction --

def auto_direction(voice, text, say, stage, kind, node_id=None, cast=None):
    """A first direction from the words themselves, the voice's resting
    manner and where the line sits; tools/voice/directions.json overrides it."""
    v = (cast or {}).get(voice, {})
    emotion = v.get("rest", "even")
    intensity = 2
    pace = v.get("pace", "measured")
    notes = []
    caps = re.findall(r"\b[A-Z]{3,}\b", say)
    if caps and not say.isupper():
        notes.append("lean on " + ", ".join(dict.fromkeys(caps).keys()) + " (written in capitals)")
        intensity += 1
    if say.isupper() and len(say) > 6:
        notes.append("shouted or proclaimed")
        intensity = 4
    if "!" in say:
        intensity += 1
    if say.endswith(("...", "—", "-")):
        notes.append("trails off or is cut off at the end")
    if "..." in say[:-3] or "—" in say[:-1]:
        notes.append("breaks mid-line where the dash or dots are")
    if say.rstrip().endswith("?"):
        notes.append("a real question: lift at the end")
    if stage:
        notes.append("stage directions in the text: " + " / ".join(stage))
    nid = node_id or ""
    wants = None
    if nid in ("first",) or nid.startswith("first"):
        wants = "to size up a stranger"
    elif nid.startswith("cb_"):
        wants = "to say what they have heard about what you did"
    elif nid in ("wanted",):
        wants = "to get you out, or in irons"; emotion = "cold"; intensity += 1
    elif nid in ("back", "again", "hub", "greet", "return"):
        wants = "to pick up where you left off"
    elif nid.startswith(("bye", "leave", "farewell")):
        wants = "to close the conversation"
    if kind in ("bark", "folk"):
        notes.append("said to the air in passing, not to anyone: short, off-mic, no performance")
        intensity = min(intensity, 3)
    if kind == "notice":
        notes.append("read off the notice board: the narrator's flat reading voice, capitals as a sign-writer's emphasis")
    if kind == "chapter":
        notes.append("the chapter's last page, read back: warm, settled, a little slower than in play")
    return OrderedDict([("emotion", emotion), ("intensity", max(1, min(5, intensity))), ("pace", pace),
                        ("wants", wants or v.get("wants", "")), ("notes", "; ".join(notes)), ("source", "auto")])


# ------------------------------------------------------------ the lines --

class Lines:
    def __init__(self, cast):
        self.lines = []
        self.ids = set()
        self.cast = cast

    def add(self, **kw):
        line = OrderedDict()
        for k in ("id", "speaker", "voice", "kind", "text", "say", "hash", "file", "takes", "flags", "skip", "optional",
                  "context", "direction"):
            if k in kw and kw[k] not in (None, [], ""):
                line[k] = kw[k]
        if line["id"] in self.ids:
            raise SystemExit(f"two lines share the ID {line['id']}")
        self.ids.add(line["id"])
        self.lines.append(line)
        return line


def make(lines, lid, speaker, voice, kind, text, context, narrator=False, node_id=None, optional=False):
    say, stage, flags = voiceable(text, narrator or voice == "narrator", bool(context.get("survivor")))
    d = auto_direction(voice, text, say, stage, kind, node_id, lines.cast)
    skip = None
    if "placeholder" in flags and not re.sub(r"[\W_]+", "", say):
        skip = "a slot for the owner's writer, not recorded"
    return lines.add(id=lid, speaker=speaker, voice=voice, kind=kind, text=text, say=say if say != text else None,
                     hash=text_hash(text), file=f"res://audio/vo/{voice}/{lid}.ogg", flags=flags, skip=skip,
                     optional=optional or None, context=context, direction=d)


def short(s, n=170):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def first_text(t):
    if isinstance(t, str):
        return t
    if isinstance(t, list) and t:
        return t[0].get("text", "") if isinstance(t[0], dict) else str(t[0])
    return ""


def dialogue(lines, persons):
    d = load("dialogue.json")
    for cid, convo in d.items():
        npc = convo.get("npc", cid)
        nodes = convo.get("nodes", {})
        incoming = defaultdict(list)
        for nid, n in nodes.items():
            for c in n.get("choices") or []:
                if c.get("goto"):
                    incoming[c["goto"]].append((nid, first_text(c.get("text")), c))
            if n.get("next"):
                incoming[n["next"]].append((nid, None, None))
        entries = defaultdict(list)
        for e in convo.get("entry", []):
            entries[e["node"]].append(cond_words(e.get("when")) or "always (the fallback)")
        for nid, n in nodes.items():
            sp = n.get("speaker") or npc
            voice = SPEAKER_VOICE.get(sp, sp)
            if voice == "player":
                continue
            t = n.get("text")
            variants = [OrderedDict([("text", t)])] if isinstance(t, str) else list(t or [])
            to = "the survivor" if voice != "narrator" else "the player (narration)"
            ctx = OrderedDict()
            ctx["conversation"] = f"{cid} ({persons.get(npc, npc)})"
            ctx["node"] = nid
            ctx["to"] = to
            if nid in entries:
                ctx["opens"] = entries[nid]
            before = []
            for src, choice, c in incoming.get(nid, []):
                prev = nodes.get(src, {})
                item = OrderedDict([("node", src), ("said", short(first_text(prev.get("text")), 200))])
                if choice is not None:
                    item["chose"] = short(choice, 140)
                    if c and (c.get("when") or c.get("show")):
                        item["choice_when"] = cond_words(c.get("when") or c.get("show"))
                before.append(item)
            if before:
                ctx["before"] = before
            after = [short(first_text(c.get("text")), 90) for c in (n.get("choices") or [])]
            if after:
                ctx["answers"] = after
            elif n.get("next"):
                ctx["continues_to"] = n["next"]
            add_mode = any(isinstance(v, dict) and v.get("add") for v in variants)
            sexes = [sex_of(v.get("when")) if isinstance(v, dict) else None for v in variants]
            many = len(variants) > 1
            for i, v in enumerate(variants, 1):
                text = v.get("text", "") if isinstance(v, dict) else str(v)
                lid = f"{cid}.{nid}" + (f".{i}" if many else "")
                vctx = OrderedDict(ctx)
                if many:
                    w = v.get("when") if isinstance(v, dict) else None
                    vctx["variant"] = f"{i} of {len(variants)}" + (" (all that hold are read in turn)" if add_mode else " (the first whose condition holds)")
                    vctx["when"] = cond_words(w) if w else ("always" if add_mode else "otherwise (the fallback)")
                    s = sexes[i - 1]
                    if not s and not w and any(sexes):
                        # The fallback of a node split by sex is the other sex's take.
                        s = "male" if "female" in sexes else "female"
                    if s:
                        vctx["survivor"] = s
                kind = "notice" if cid == "board" else "dialogue"
                make(lines, lid, sp, voice, kind, text, vctx, narrator=voice == "narrator", node_id=nid)


def barks(lines, persons):
    n = load("npcs.json")
    for group in ("npcs", "outsiders"):
        for nid, p in n.get(group, {}).items():
            for key, label in (("barks", "day"), ("nightBarks", "night")):
                for i, t in enumerate(p.get(key) or [], 1):
                    ctx = OrderedDict([("where", f"over {p.get('name', nid)}'s head as you pass, {'after dark' if label == 'night' else 'by day' if p.get('nightBarks') else 'day or night'}"),
                                       ("to", "nobody in particular")])
                    make(lines, f"bark.{nid}.{i}" if label == "day" else f"bark.{nid}.night.{i}", nid, nid, "bark", t, ctx)
    for i, g in enumerate(n.get("guards", []), 1):
        ctx = OrderedDict([("where", "a watchman on the Waystation's gate, as you pass"), ("to", "the survivor, or the road")])
        for sx, voice in (("m", "watchman"), ("f", "watchwoman")):
            make(lines, f"bark.guard.{i}.{sx}", f"guard{i - 1}", voice, "bark", g["line"], ctx)


# A passing line only one sex could say ("my husband") gets only that take;
# a walker of the other sex says it silently.
ONLY_WOMAN = re.compile(r"\b(my husband|my man|was a girl|as a girl|my first husband)\b", re.I)
ONLY_MAN = re.compile(r"\b(my wife|my missus|was a boy|as a boy)\b", re.I)


def sexes_for(text):
    if ONLY_WOMAN.search(text):
        return (("f", "townswoman"),)
    if ONLY_MAN.search(text):
        return (("m", "townsman"),)
    return (("m", "townsman"), ("f", "townswoman"))


def folk(lines):
    f = load("folk.json")
    for i, l in enumerate(f.get("lines", []), 1):
        when = []
        if "night" in l:
            when.append("after dark" if l["night"] else "by day")
        if l.get("when"):
            when.append(cond_words(l["when"]))
        if l.get("died"):
            when.append("after the survivor has died and come back")
        ctx = OrderedDict([("where", "a passer-by in the Waystation, as you walk past"), ("to", "the survivor, or nobody")])
        if when:
            ctx["when"] = "; ".join(when)
        if l.get("child"):
            ctx["who"] = "a child at play"
            make(lines, f"folk.{i}", "folk", "child", "folk", l["text"], ctx)
        elif l.get("watch"):
            ctx["who"] = "a watchman or watchwoman on the rounds"
            for sx, voice in (("m", "watchman"), ("f", "watchwoman")):
                make(lines, f"folk.{i}.{sx}", "folk", voice, "folk", l["text"], ctx)
        else:
            takes = sexes_for(l["text"])
            ctx["who"] = "a townsman or townswoman (the walker's sex decides the take)" if len(takes) == 2 else \
                f"a {takes[0][1]} only (the words say so); the other sex's walkers say it unvoiced"
            for sx, voice in takes:
                make(lines, f"folk.{i}.{sx}", "folk", voice, "folk", l["text"], ctx)


# ---------------------------------------------------- C# string scanning --

ESC = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\", '"': '"', "'": "'", "a": "\a", "b": "\b", "f": "\f", "v": "\v"}


def read_literal(src, i):
    """A C# string literal starting at src[i]: (value, end, interpolated, holes)."""
    interp = False
    verbatim = False
    j = i
    while src[j] in "$@":
        if src[j] == "$":
            interp = True
        else:
            verbatim = True
        j += 1
    if src.startswith('"""', j):
        k = src.index('"""', j + 3)
        return src[j + 3:k].strip("\n"), k + 3, interp, False
    assert src[j] == '"', src[i:i + 20]
    j += 1
    out, holes = [], False
    while True:
        ch = src[j]
        if verbatim and ch == '"':
            if src[j + 1] == '"':
                out.append('"'); j += 2; continue
            return "".join(out), j + 1, interp, holes
        if not verbatim and ch == "\\":
            nx = src[j + 1]
            if nx == "u":
                out.append(chr(int(src[j + 2:j + 6], 16))); j += 6; continue
            if nx == "x":
                m = re.match(r"[0-9a-fA-F]{1,4}", src[j + 2:])
                out.append(chr(int(m.group(0), 16))); j += 2 + len(m.group(0)); continue
            out.append(ESC.get(nx, nx)); j += 2; continue
        if ch == '"':
            return "".join(out), j + 1, interp, holes
        if interp and ch == "{":
            if src[j + 1] == "{":
                out.append("{"); j += 2; continue
            depth, k = 1, j + 1
            while depth:
                if src[k] == "{":
                    depth += 1
                elif src[k] == "}":
                    depth -= 1
                elif src[k] == '"':
                    _, k, _, _ = read_literal(src, k); continue
                k += 1
            out.append(src[j:k]); holes = True; j = k; continue
        if interp and ch == "}" and src[j + 1] == "}":
            out.append("}"); j += 2; continue
        out.append(ch); j += 1


def balanced(src, i):
    """From an opening bracket at src[i], the index just past its partner."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = [pairs[src[i]]]
    j = i + 1
    while stack:
        ch = src[j]
        if ch in "$@\"" and (ch == '"' or src[j + 1] in '"$@'):
            _, j, _, _ = read_literal(src, j); continue
        if ch == "'":
            j = src.index("'", j + 2 if src[j + 1] == "\\" else j + 1) + 1; continue
        if ch == "/" and src[j + 1] == "/":
            j = src.index("\n", j); continue
        if ch in pairs:
            stack.append(pairs[ch])
        elif ch == stack[-1]:
            stack.pop()
        j += 1
    return j


def split_args(s):
    out, depth, cur, j = [], 0, [], 0
    while j < len(s):
        ch = s[j]
        if ch in "$@\"" and (ch == '"' or (j + 1 < len(s) and s[j + 1] in '"$@')):
            _, k, _, _ = read_literal(s, j); cur.append(s[j:k]); j = k; continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append("".join(cur)); cur = []; j += 1; continue
        cur.append(ch); j += 1
    out.append("".join(cur))
    return [a.strip() for a in out]


def literals(expr):
    """Every string literal in an expression (a ternary gives two), in order."""
    out, j = [], 0
    while j < len(expr):
        ch = expr[j]
        if ch == '"' or (ch in "$@" and re.match(r'[$@]+"', expr[j:])):
            v, k, interp, holes = read_literal(expr, j)
            out.append((v, holes)); j = k; continue
        j += 1
    return out


def line_of(src, i):
    return src.count("\n", 0, i) + 1


def nearest(src, i, pattern, back=1600):
    m = None
    for m in re.finditer(pattern, src[max(0, i - back):i]):
        pass
    return m.group(1) if m else None


def zone_context(src, i, rel):
    ctx = OrderedDict([("where", f"{rel}:{line_of(src, i)}")])
    thing = nearest(src, i, r'Name = "([^"]+)"', 900)
    verb = nearest(src, i, r'Verb = "([^"]+)"', 900)
    if thing and verb:
        ctx["trigger"] = f"the survivor chooses \"{verb}\" at {thing}"
    lstart = src.rfind("\n", 0, i) + 1
    lead = src[lstart:i].strip()
    m = re.search(r"(if|else if)\s*\((.*)\)\s*$", lead)
    if m:
        ctx["when"] = "code: " + short(m.group(2), 160)
    elif lead.startswith("else"):
        ctx["when"] = "code: otherwise (the else of the line above)"
    after = re.search(r"G\.After\(([\d.]+)", lead)
    if after:
        ctx["timing"] = f"{after.group(1)} s after the line before"
    return ctx


def zones(lines):
    for zone, rel in ZONE_FILES:
        path = os.path.join(GODOT, rel)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        n = 0
        arrays = {}
        for m in re.finditer(r"static readonly string\[\] (\w+) =\s*\[", src):
            body = src[m.end() - 1:balanced(src, m.end() - 1)]
            arrays[m.group(1)] = [v for v, _ in literals(body)]
        for m in re.finditer(r"\bG\.Say\(", src):
            n += 1
            end = balanced(src, m.end() - 1)
            args = split_args(src[m.end():end - 1])
            who = literals(args[1])[0][0] if len(args) > 1 and literals(args[1]) else None
            voice = SPEAKER_NAMES.get(who, re.sub(r"\W+", "_", (who or "").lower()).strip("_"))
            ctx = zone_context(src, m.start(), "godot/" + rel)
            ctx["to"] = "the player (a caption under the picture)" if voice == "narrator" else "the survivor"
            arr = re.match(r"(\w+)\[", args[0])
            if arr and arr.group(1) in arrays:
                for k, v in enumerate(arrays[arr.group(1)], 1):
                    c = OrderedDict(ctx); c["variant"] = f"{arr.group(1)}[{k - 1}]"
                    make(lines, f"{zone}.{arr.group(1).lower()}.{k}", who or "narrator", voice, "zone", v, c, narrator=voice == "narrator")
                continue
            lits = literals(args[0])
            for k, (v, holes) in enumerate(lits, 1):
                c = OrderedDict(ctx)
                if len(lits) > 1:
                    c["variant"] = f"{k} of {len(lits)} (picked by the code at the call)"
                line = make(lines, f"{zone}.say.{n}" + (f".{k}" if len(lits) > 1 else ""), who or "narrator", voice, "zone", v, c,
                            narrator=voice == "narrator")
                if holes:
                    line.setdefault("flags", []).append("interpolated")
        b = 0
        for m in re.finditer(r"new Ev\.Bark\s*\{", src):
            end = balanced(src, m.end() - 1)
            body = src[m.end():end - 1]
            sp = re.search(r'Speaker\s*=\s*"([^"]+)"', body)
            if not sp:
                continue  # a callout over the fight ("Executed"), not a voice
            b += 1
            tm = re.search(r"Text\s*=\s*", body)
            rest = body[tm.end():]
            lits = literals(split_args(rest)[0])
            ctx = zone_context(src, m.start(), "godot/" + rel)
            ctx["to"] = "the survivor, over the fight"
            voice = SPEAKER_NAMES.get(sp.group(1), re.sub(r"\W+", "_", sp.group(1).lower()).strip("_"))
            for k, (v, holes) in enumerate(lits, 1):
                make(lines, f"{zone}.bark.{b}" + (f".{k}" if len(lits) > 1 else ""), sp.group(1), voice, "bark", v, ctx)
        sc = re.search(r"StallCalls = new\(\)\s*\{", src)
        if sc:
            body = src[sc.end() - 1:balanced(src, sc.end() - 1)]
            calls = [(km.group(1), body[km.end() - 1:balanced(body, km.end() - 1)]) for km in re.finditer(r'\["(\w+)"\]\s*=\s*\[', body)]
            fallback = re.search(r'\["Come and look!"\]', src)
            if fallback:
                calls.append(("any", '"Come and look!"'))
            for kind, arr in calls:
                for k, (v, _) in enumerate(literals(arr), 1):
                    ctx = OrderedDict([("where", f"a stall-keeper calling their wares ({kind}) in the Waystation square, by day"),
                                       ("to", "anyone passing"), ("who", "the keeper's sex decides the take")])
                    for sx, voice in sexes_for(v):
                        make(lines, f"bark.stall.{kind}.{k}.{sx}", "stall-keeper", voice, "bark", v, ctx)


def chapter(lines):
    """The chapter's last page, which nobody reads aloud yet: here so it can be."""
    path = os.path.join(GODOT, CHAPTER_FILE)
    if not os.path.exists(path):
        return
    src = open(path, encoding="utf-8").read()
    n = 0
    seen = set()
    for m in re.finditer(r'(outcome = |beats\.Add\(|return )(?=\$?")', src):
        v, _, _, holes = read_literal(src, m.end())
        if v in seen or len(v.split()) < 3:
            continue
        seen.add(v)
        n += 1
        ctx = OrderedDict([("where", f"godot/{CHAPTER_FILE}:{line_of(src, m.start())}"), ("to", "the player, on the chapter's last page")])
        line = make(lines, f"chapter.{n}", "narrator", "narrator", "chapter", v.replace("{ch.Name}", "{name}").replace('{Out("with_kerchiefs")}', "").strip(),
                    ctx, narrator=True, optional=True)
        if holes and "{ch.Name}" not in v and "Out(" not in v:
            line.setdefault("flags", []).append("interpolated")
    q = load("quests.json")
    for qid in ("beasts", "caravan"):
        for key, v in (q.get(qid, {}).get("outcomes") or {}).items():
            if not v:
                continue
            ctx = OrderedDict([("where", f"quests.json {qid}.outcomes.{key}, on the chapter's last page"), ("to", "the player")])
            make(lines, f"chapter.{qid}.{key}", "narrator", "narrator", "chapter", v, ctx, narrator=True, optional=True)


# ---------------------------------------------------------- directions --

def apply_directions(lines, directions):
    """Hand direction over the automatic one; report direction written for other words."""
    stale = []
    by_id = {l["id"]: l for l in lines}
    used = set()
    for l in lines:
        node_key = ".".join(l["id"].split(".")[:2]) if l["kind"] in ("dialogue", "notice") else None
        # The two takes of a passer-by's line share one direction.
        take_key = re.sub(r"\.[mf]$", "", l["id"]) if l["id"].endswith((".m", ".f")) else None
        for key in (node_key, take_key, l["id"]):
            d = directions.get(key) if key else None
            if not d:
                continue
            used.add(key)
            if d.get("hash") and key in (l["id"], take_key) and d["hash"] != l["hash"]:
                stale.append(l["id"])
            dd = l["direction"]
            for k in ("emotion", "intensity", "pace", "wants", "notes"):
                if d.get(k) not in (None, ""):
                    dd[k] = d[k]
            dd["source"] = "hand"
            if d.get("say") and key in (l["id"], take_key):
                l["say"] = d["say"]
    unknown = [k for k in directions if k not in used and k not in by_id and not k.startswith("_")]
    return stale, unknown


# ------------------------------------------------------------- writing --

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def md_escape(s):
    return s.replace("|", "\\|")


def lexicon_for(text, lexicon):
    hits = []
    for word, how in lexicon.items():
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            hits.append((word, how))
    return hits


def write_scripts(lines, cast, lexicon):
    os.makedirs(SCRIPTS, exist_ok=True)
    for old in os.listdir(SCRIPTS):
        if old.endswith(".md"):
            os.remove(os.path.join(SCRIPTS, old))
    by_voice = defaultdict(list)
    for l in lines:
        by_voice[l["voice"]].append(l)
    for voice, ls in sorted(by_voice.items()):
        c = cast.get(voice, {})
        out = [f"# {c.get('name', voice)}: recording script", ""]
        out.append(f"Voice `{voice}`. Generated by `tools/voice/extract.py` from the game's content: do not edit by hand "
                   "(direction goes in `tools/voice/directions.json`; casting in `tools/voice/voices.json`, rendered to `docs/voice/CASTING.md`).")
        out.append("")
        if c:
            out.append(f"**Who:** {c.get('who', '')}")
            out.append("")
            out.append(f"**Resting manner:** {c.get('rest', '')}; pace {c.get('pace', '')}. {c.get('habits', '')}")
            out.append("")
        recorded = [l for l in ls if not l.get("skip")]
        out.append(f"{len(recorded)} takes" + (f" ({sum(1 for l in recorded if l.get('optional'))} optional)" if any(l.get("optional") for l in recorded) else "") +
                   (f"; {len(ls) - len(recorded)} lines not recorded (writer's slots)" if len(ls) > len(recorded) else "") + ".")
        out.append("")
        words = " ".join(l.get("say") or l["text"] for l in ls)
        hits = lexicon_for(words, lexicon)
        if hits:
            out.append("## Pronunciation")
            out.append("")
            for w, how in hits:
                out.append(f"- **{w}**: {how}")
            out.append("")
        group = None
        for l in ls:
            g = l["context"].get("conversation") or {"bark": "Barks", "folk": "Passing lines", "zone": "In the world", "notice": "Notices",
                                                    "chapter": "The chapter's last page"}.get(l["kind"], l["kind"])
            if l["kind"] in ("zone",):
                g = "In the world: " + l["context"]["where"].split(":")[0].split("/")[-1].replace(".cs", "")
            if g != group:
                group = g
                out.append(f"## {g}")
                out.append("")
            out.append(f"### `{l['id']}`" + (" (optional)" if l.get("optional") else "") + (" (not recorded)" if l.get("skip") else ""))
            out.append("")
            say = l.get("say") or l["text"]
            out.append("> " + say.replace("\n", "\n> "))
            out.append("")
            if l.get("say"):
                out.append(f"*As written:* {l['text']}")
                out.append("")
            ctx = l["context"]
            bits = []
            if "node" in ctx:
                bits.append(f"node `{ctx['node']}`, to {ctx['to']}")
            elif "to" in ctx:
                bits.append(f"to {ctx['to']}")
            for k in ("where", "who", "trigger", "timing"):
                if k in ctx:
                    bits.append(f"{k}: {ctx[k]}")
            if bits:
                out.append("- " + "; ".join(bits))
            if "opens" in ctx:
                out.append("- Opens the conversation when: " + " | ".join(ctx["opens"]))
            if "variant" in ctx:
                out.append(f"- Variant {ctx['variant']}; when: {ctx.get('when', '')}" + (f"; **survivor: {ctx['survivor']}**" if ctx.get("survivor") else ""))
            elif "when" in ctx:
                out.append(f"- When: {ctx['when']}")
            for b in ctx.get("before", [])[:4]:
                if "chose" in b:
                    out.append(f"- After `{b['node']}` (\"{b['said']}\"), the survivor chose: \"{b['chose']}\"" + (f" (offered when {b['choice_when']})" if b.get("choice_when") else ""))
                else:
                    out.append(f"- Follows `{b['node']}`: \"{b['said']}\"")
            if len(ctx.get("before", [])) > 4:
                out.append(f"- …and {len(ctx['before']) - 4} more ways in")
            if ctx.get("answers"):
                out.append("- The survivor can answer: " + " / ".join(f"\"{a}\"" for a in ctx["answers"]))
            d = l["direction"]
            out.append(f"- **Direction** ({d['source']}): {d['emotion']}, intensity {d['intensity']}/5, {d['pace']}." +
                       (f" Wants {(d['wants'][0].lower() + d['wants'][1:]).rstrip('.')}." if d.get("wants") else "") +
                       (f" {d['notes'][0].upper() + d['notes'][1:].rstrip('.')}." if d.get("notes") else ""))
            if l.get("flags"):
                out.append("- Flags: " + ", ".join(f"`{f}`" for f in l["flags"]))
            out.append("")
        with open(os.path.join(SCRIPTS, f"{voice}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(out).rstrip() + "\n")


def write_casting(cast, counts, lexicon):
    out = ["# Casting", "",
           "Every voice in the game, for the local TTS and for anyone casting real actors. Rendered from "
           "`tools/voice/voices.json` by `tools/voice/extract.py`: edit that file, not this one. How each person "
           "talks on the page is `docs/VOICES.md`; who they really are is `docs/STORY_BIBLE.md` §5.", "",
           "The **voice design** paragraph of each is written for a model that builds a voice from a description "
           "(Qwen3-TTS VoiceDesign): one paragraph, physical and concrete, no names. Generate several candidates "
           "from it, audition them on the **audition lines**, and keep the winner as the reference clip "
           "(`tools/voice/refs/<voice>.wav`) so every later take is cloned from the same voice. Audition lines come "
           "from the script where it shows the range; a few are written for the audition alone and are not in the game.", "",
           "| Voice | Who | Takes | Shares with |", "|---|---|---|---|"]
    for k, c in cast.items():
        if k.startswith("_"):
            continue
        out.append(f"| `{k}` | {c.get('name', k)} | {counts.get(k, 0)} | {c.get('share', '') or '-'} |")
    out.append("")
    for k, c in cast.items():
        if k.startswith("_"):
            continue
        out.append(f"## {c.get('name', k)} (`{k}`)")
        out.append("")
        out.append(c.get("who", ""))
        out.append("")
        for label, key in (("Apparent age", "age"), ("Origin and accent", "accent"), ("Timbre", "timbre"), ("Pace", "pace"),
                           ("Range", "range"), ("Verbal habits", "habits"), ("At rest", "rest"), ("Never", "never")):
            if c.get(key):
                out.append(f"- **{label}:** {c[key]}")
        if c.get("share"):
            out.append(f"- **Can share a voice with:** {c['share']}")
        out.append("")
        if c.get("design"):
            out.append("**Voice design:**")
            out.append("")
            out.append("> " + c["design"])
            out.append("")
        if c.get("auditions"):
            out.append("**Audition lines:**")
            out.append("")
            for a in c["auditions"]:
                out.append(f"1. {a}")
            out.append("")
    if lexicon:
        out.append("## Pronunciation")
        out.append("")
        out.append("For every voice. Respell in the text sent to the TTS only if a take gets one wrong (`say` in "
                   "`tools/voice/directions.json`); the subtitle keeps the spelling.")
        out.append("")
        for w, how in lexicon.items():
            out.append(f"- **{w}**: {how}")
        out.append("")
    with open(CASTING, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out).rstrip() + "\n")


def main():
    check = "--check" in sys.argv
    voices = load_here("voices.json", OrderedDict())
    lexicon = voices.pop("_lexicon", OrderedDict())
    directions = load_here("directions.json", OrderedDict())
    n = load("npcs.json")
    persons = {k: v.get("name", k) for g in ("npcs", "outsiders", "speakers") for k, v in (n.get(g) or {}).items() if isinstance(v, dict)}
    lines = Lines(voices)
    dialogue(lines, persons)
    barks(lines, persons)
    folk(lines)
    zones(lines)
    chapter(lines)
    stale_dirs, unknown_dirs = apply_directions(lines.lines, directions)
    manifest = OrderedDict([("generated_by", "tools/voice/extract.py"),
                            ("about", "Every spoken line: its ID, who says it, the words, the hash of the words, where its take goes, and how to say it. "
                                      "Regenerate with python3 tools/voice/extract.py; voice with tools/voice/tts_batch.py."),
                            ("lines", lines.lines)])
    old = None
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            old = {l["id"]: l for l in json.load(f).get("lines", [])}
    new = {l["id"]: l for l in lines.lines}
    if old is not None:
        added = [i for i in new if i not in old]
        gone = [i for i in old if i not in new]
        changed = [i for i in new if i in old and old[i]["hash"] != new[i]["hash"]]
        print(f"{len(new)} lines: {len(added)} new, {len(changed)} with changed words, {len(gone)} gone since the last manifest")
        for label, ids in (("new", added), ("changed", changed), ("gone", gone)):
            for i in ids[:12]:
                print(f"  {label}: {i}")
            if len(ids) > 12:
                print(f"  ...and {len(ids) - 12} more {label}")
    else:
        print(f"{len(new)} lines")
    for i in stale_dirs:
        print(f"  direction written for other words: {i}")
    for k in unknown_dirs:
        print(f"  direction for a line that is not there: {k}")
    if check:
        return
    write_json(MANIFEST, manifest)
    counts = defaultdict(int)
    for l in lines.lines:
        if not l.get("skip"):
            counts[l["voice"]] += 1
    write_scripts(lines.lines, voices, lexicon)
    if voices:
        write_casting(OrderedDict(voices), counts, lexicon)
    missing = sorted({l["voice"] for l in lines.lines} - set(voices))
    if missing:
        print("voices with no casting in tools/voice/voices.json: " + ", ".join(missing))


if __name__ == "__main__":
    main()

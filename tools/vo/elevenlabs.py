"""ElevenLabs recording packets: one per character, for the owner to record
by hand in ElevenLabs, a character at a time (the owner's route for the
final voices; placeholders stand in meanwhile, tools/vo/placeholders.py).

Each packet (docs/voice/elevenlabs/<voice>.md) has the person and how they
sound, a casting brief for ElevenLabs Voice Design, the model and settings,
and every line they speak in recording order: the direction (what they want,
what they hide, the beats), the text to paste with ElevenLabs audio tags, the
words the subtitle shows (what the importer checks), and the exact file name
to save the take as. tools/vo/import_takes.py brings the takes into the game.

    python tools/vo/elevenlabs.py                 # every packet, and the README's table
    python tools/vo/elevenlabs.py rook narrator   # these
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lines as lines_mod  # noqa: E402
from analyse import lexicon  # noqa: E402
from common import ROOT, cast  # noqa: E402

OUT = os.path.join(ROOT, "docs", "voice", "elevenlabs")
VOICES_MD = os.path.join(ROOT, "docs", "VOICES.md")
# Where each part's sheet starts in docs/VOICES.md.
SHEET = {"narrator": "The narrator.", "rook": "Mother Rook", "holloway": "Captain Holloway", "maeca": "Maeca Barefoot",
         "wenna": "Old Wenna", "tam": "Tam", "brannoc": "Brannoc", "harlan": "Harlan Coyle", "pell": "Pell Varrow",
         "rav": "Rav Cutwell", "chid": "Chid", "vonnra": "Vonnra Ash-of-Morrow", "keegan": "Dame Keegan Orme", "sella": "Sella",
         "redcowl": "Redcowl", "snib": "Snib", "grimtunnel": "Grimtunnel", "warden": "The Ford-Warden.",
         "barrow_lord": "The Barrow Lord", "guard": "The Waystation's watchmen.", "guard_f": "The Waystation's watchmen.",
         "kerchief_woman": "The Kerchiefs.", "lampling": "The babbling lampling.", "jory": "Jory Coyle.",
         "ysolde": "Ysolde Marrow", "watchman": "Nell, Wat, Corran."}
# Held for the story lead's review (a7622ae77d19e31dc): whole parts, and kinds of line.
HOLD_VOICES: dict = {}
# Lines waiting on the story lead or the owner: (id prefix, why).
HOLD_LINES = (("dlg.keegan.vonnra.", "the story lead's confirmation of Keegan's kenning"),)
TAG = {"beat": "…", "breath": "[inhales]", "laugh": "[laughs]", "laughs": "[laughs]", "chuckle": "[chuckles]",
       "sigh": "[sighs]", "sighs": "[sighs]", "sniff": "[sniffs]", "gasp": "[gasps]", "silence": "[long pause]", "name": "",
       "whisper": "[whispers]"}
VOL_TAG = {"hushed": "whispers", "quiet": "quietly", "raised": "loudly", "shout": "shouting"}
REGION = {"Yorkshire": "Yorkshire", "Lancashire": "Lancashire", "Welsh": "Welsh", "Somerset": "Somerset, West Country",
          "Cornish": "Cornish", "Bristol": "Bristol", "London": "London", "Glasgow": "Glaswegian", "Irish": "Irish",
          "Scots": "Scottish", "Edinburgh": "Edinburgh Scottish", "northern": "northern English", "West Country": "West Country",
          "RP": "Received Pronunciation", "empire": "old-fashioned upper-class English"}


def sheet(voice: str) -> str:
    name = SHEET.get(voice)
    if not name:
        return ""
    text = open(VOICES_MD, encoding="utf-8").read()
    i = text.find(f"**{name}")
    if i < 0:
        return ""
    j = text.find("\n\n", i)
    return re.sub(r"\s*\n\s*", " ", text[i: j if j > 0 else None]).strip()


def held(line: dict, voice: str) -> str | None:
    if "iron_marker" in line["id"] and ".verse" in line["id"]:
        return "the owner's choice of how the hymn is sung (README)"
    if voice in HOLD_VOICES:
        return HOLD_VOICES[voice]
    for prefix, why in HOLD_LINES:
        if line["id"].startswith(prefix):
            return why
    return None


def say(text: str) -> str:
    """Names respelt the way they are said (the same respellings the
    placeholders use)."""
    lex = lexicon().get("say", {})
    for k in sorted(lex, key=len, reverse=True):
        text = re.sub(rf"(?<![\w']){re.escape(k)}(?![\w'])", lex[k], text)
    return text


def words(t: str) -> list[str]:
    return re.findall(r"[a-z']+", re.sub(r"\[[^\]]*\]", " ", t.lower()))


ACTED = {"a sniff": "sniffs", "a laugh": "laughs", "a sigh": "sighs", "a gasp": "gasps"}


def acted_tag(m) -> str:
    inner = m.group(1).strip()
    inner = ACTED.get(inner, inner)
    return "[" + re.sub(r"^sung\b", "singing", inner) + "]"


def paste(seg_text: str, d: dict, narrator_aside: bool, plain: bool = False, acted: str | None = None) -> str:
    """What to paste into ElevenLabs: a direction tag, then the words with
    the writer's beats as audio tags where a beats part says exactly them."""
    text = re.sub(r"\[([^\]]+)\]", acted_tag, acted) if acted else seg_text
    if not narrator_aside:
        for part in (d.get("beats") or "").split("|"):
            if words(part) and words(part) == words(seg_text):
                text = re.sub(r"\[([a-z]+)[^\]]*\]", lambda m: TAG.get(m.group(1), ""), part)
                break
    text = re.sub(r"\s+", " ", text).replace(" …", "…").strip()
    text = re.sub(r"[.,;:]…", "…", text)
    text = re.sub(r"…[,;:]", "…", text)
    how = [] if narrator_aside or plain else [re.split(r";", d.get("emo", ""))[0].strip()]
    vol = "quiet" if narrator_aside else d.get("vol", "level")
    if plain and vol == "hushed" and not d.get("whisper"):
        vol = "quiet"  # the narrator whispers only where his direction says so
    if VOL_TAG.get(vol):
        how.append(VOL_TAG[vol])
    tag = ", ".join(h for h in how if h)
    return (f"[{tag}] " if tag else "") + say(text)


def brief(voice: str, v: dict) -> str:
    sex = "Female" if v.get("sex") == "f" else "Male"
    age = v.get("age") or 0
    ages = f"{age // 10 * 10}s" if age >= 20 else (f"a child of about {age}" if age else "ageless, not human")
    region = next((r for k, r in REGION.items() if k.lower() in v.get("accent", "").lower()), "British")
    persona = v.get("maya", "").split(". ")[0].split(", ")[-1] if v.get("maya") else v["name"]
    accent = (f"Crisp {region}." if "Pronunciation" in region or "upper-class" in region
              else f"Thick {region} accent." if region != "British" else "")
    return (f"Native English (British, {region}). {sex}, {ages}. Studio quality. "
            f"Persona: {persona}. {v['design']} {accent} No reverb or effects.").replace("  ", " ")


def entries(man: list[dict], voice: str) -> list[dict]:
    """Every part this voice speaks, in recording order: scenes in the order
    the player meets them, each line's parts together."""
    out = []
    for n, l in sorted(enumerate(man), key=lambda il: (lines_mod.impact(il[1]), il[0])):
        if l["status"] == "skip":
            continue
        for k, s in enumerate(l["segments"]):
            if s["voice"] == voice:
                out.append({"line": l, "part": k, "seg": s})
    return out


def scene(l: dict) -> str:
    i, where = l["id"], l.get("where", "")
    if i.startswith("say."):
        return "Scenes: " + re.sub(r"(?<=[a-z])(?=[A-Z])", " ", os.path.splitext(os.path.basename(where))[0])
    if i.startswith("dlg.cin_"):
        return "Cinematic: " + i.split(".")[1][4:].replace("_", " ")
    if i.startswith("dlg."):
        npc = i.split(".")[1]
        return "Conversations: " + {"survivor": "the survivor", "wayfinder": "the Wayfinder", "greymuzzle": "Greymuzzle"}.get(npc, npc.capitalize())
    if i.startswith(("bark.", "guard.")):
        return "Said in passing"
    if i.startswith("cbark."):
        return "In a fight"
    return "Passers-by"


def file_name(line: dict, part: int) -> str:
    return f"{line['id']}.wav" if len(line["segments"]) == 1 else f"{line['id']}.p{part}.wav"


def packet(voice: str, man: list[dict]) -> tuple[str, dict]:
    v = cast()[voice]
    es, first = [], {}
    for e in entries(man, voice):
        key = e["seg"].get("acted", e["seg"]["text"])
        if key in first:
            first[key]["also"].append(file_name(e["line"], e["part"]))
            continue
        e["also"] = []
        first[key] = e
        es.append(e)
    chars = sum(len(e["seg"]["text"]) for e in es)
    holds = [e for e in es if held(e["line"], voice)]
    spoken = " ".join(e["seg"]["text"] for e in es)
    lex = {k: x for k, x in lexicon().get("say", {}).items() if k != x and re.search(rf"(?<![\w']){re.escape(k)}(?![\w'])", spoken)}
    w = [f"# {v['name']}: ElevenLabs packet", "",
         f"Voice id in the game: `{voice}`. {len(es)} takes to record ({chars:,} characters; about {chars * 3:,} credits at three "
         f"tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.", ""]
    if holds:
        w += [f"**Hold {len(holds)} of these** (marked HOLD below, with why); the rest can be recorded now.", ""]
    w += ["## Who they are", "", sheet(voice) or v["design"], ""]
    if v.get("wants") or v.get("hides"):
        w += [f"*Wants:* {v.get('wants', '')}. *Hides:* {v.get('hides', '')}.", ""]
    w += [
          "## Casting the voice", "",
          "In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below "
          "as the text; generate, listen to the three, and regenerate until one is this person. Save it as "
          f"`SU {v['name']}`. Never describe a voice as sounding like a real person.", "",
          "```", brief(voice, v), "```", "",
          "Preview text:", "", "```", say(v.get("ref_text", "")), "```", "",
          f"In the Voice Library instead: search for *{v.get('accent', '')}*, *{'female' if v.get('sex') == 'f' else 'male'}*, "
          f"*{(v.get('age') or 0) // 10 * 10 or 'ageless'}*, and listen for this: {v['design'].split('. ')[0]}. Use only voices "
          "whose library licence allows commercial use.", "",
          "## Settings", "",
          "- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.",
          f"- Stability: **{55 if voice == 'narrator' else 45}** (lower is more expressive and less steady; raise it if the "
          "voice drifts from line to line). Similarity: **75**.",
          "- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text "
          "are free within two hours.",
          "- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take "
          "into one folder under the exact name given, e.g. `~/Downloads/su_vo/" + file_name(es[0]["line"], es[0]["part"]) + "`."
          if es else "", "",
          "Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or "
          f"wrong):", "", "```", f"python tools/vo/import_takes.py ~/Downloads/su_vo --voice {voice}", "```", ""]
    if lex:
        w += ["## Saying the names", "", "The text to paste already respells these; keep the respelling: " +
              ", ".join(f"{k} as *{x}*" for k, x in sorted(lex.items())) + ".", ""]
    if voice == "narrator":
        w += ["## How he reads", "", "The narrator never shows a feeling: plain, the same pace throughout, and the facts do "
              "the work (the story lead's rule). The notes say what each line is doing; play none of it. His tags say only "
              "how loud.", ""]
    w += ["## The lines", "",
          "Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: "
          "they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.", ""]
    section = None
    for n, e in enumerate(es, 1):
        l, k, s = e["line"], e["part"], e["seg"]
        sec = scene(l)
        if sec != section:
            section = sec
            w += [f"## {sec}", ""]
        d = l.get("direction") or {}
        aside = s["voice"] == "narrator" and l["voice"] != "narrator"
        hold = held(l, voice)
        w.append(f"### {n}. `{file_name(l, k)}`" + (f"  HOLD: {hold}" if hold else ""))
        w.append("")
        if e["also"]:
            w.append(f"*The same words are also* {', '.join(f'`{x}`' for x in e['also'])}*: record once; the importer copies the take.*")
        ctx = f"{l.get('where', '')}"
        if len(l["segments"]) > 1:
            ctx += f"; part {k + 1} of {len(l['segments'])}: " + " / ".join(
                ("**" if i == k else "") + f"{x['voice']}: {x['text'][:90]}{'…' if len(x['text']) > 90 else ''}" + ("**" if i == k else "")
                for i, x in enumerate(l["segments"]))
        w.append(f"*Where:* {ctx}")
        if aside:
            w.append("*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.")
        else:
            bits = [d.get("emo", "")] + [f"{label}: {d[x]}" for x, label in (("intent", "doing"), ("pace", "pace"), ("vol", "volume"))
                                         if d.get(x)]
            if any(bits):
                w.append(f"*Played:* {'; '.join(b for b in bits if b)}.")
            for key, label in (("wants", "Wants"), ("hides", "Hides"), ("note", "Note")):
                if d.get(key):
                    w.append(f"*{label}:* {d[key]}")
        w += ["", "```", paste(s["text"], d, aside, plain=voice == "narrator", acted=s.get("acted")), "```", f"Subtitle: {s['text']}", ""]
    return "\n".join(w) + "\n", {"voice": voice, "name": v["name"], "takes": len(es), "chars": chars, "held": len(holds)}


def main(argv):
    man = lines_mod.merge(lines_mod.build())
    voices = [x for x in cast() if not argv or x in argv]
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for voice in voices:
        text, info = packet(voice, man)
        if not info["takes"]:
            continue
        with open(os.path.join(OUT, f"{voice}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        rows.append(info)
        print(f"{voice:16s} {info['takes']:4d} takes {info['chars']:7,d} chars {info['held']:3d} held")
    if not argv:
        table = "\n".join(f"| [{r['name']}]({r['voice']}.md) | {r['takes']} | {r['chars']:,} | {r['held'] or ''} |" for r in
                          sorted(rows, key=lambda r: -r["chars"]))
        readme = os.path.join(OUT, "README.md")
        old = open(readme, encoding="utf-8").read() if os.path.exists(readme) else ""
        block = "<!-- PACKETS -->\n| Character | Takes | Characters | Held |\n|---|---|---|---|\n" + table + "\n<!-- /PACKETS -->"
        new = re.sub(r"<!-- PACKETS -->.*?<!-- /PACKETS -->", lambda _: block, old, flags=re.S) if "<!-- PACKETS -->" in old else old
        open(readme, "w", encoding="utf-8", newline="\n").write(new)


if __name__ == "__main__":
    main(sys.argv[1:])

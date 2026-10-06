"""elevenlabs.py, round two of the story lead's review: acted tags, one take per distinct text, the narrator whispers
only where marked, character wants and hides, the holds lifted; and the importer copies a take to its duplicates."""
p = "tools/vo/elevenlabs.py"
t = open(p, encoding="utf-8").read()


def rep(old, new, count=1):
    global t
    assert old in t, old[:80]
    t = t.replace(old, new, count)


rep('''HOLD_VOICES = {"chid": "the story editor's review of section 17", "maeca": "the story editor's review of section 17",
               "ysolde": "the story editor's review of section 17"}
HOLD_LINES = (("bark.", ".said."), ("cbark.", "grimtunnel"), ("cbark.", "barrow_lord"))''',
'''HOLD_VOICES: dict = {}
# Lines waiting on the story lead or the owner: (id prefix, why).
HOLD_LINES = (("dlg.keegan.vonnra.", "the story lead's confirmation of Keegan's kenning"),)''')
rep('''    if voice in HOLD_VOICES:
        return HOLD_VOICES[voice]
    for a, b in HOLD_LINES:
        if line["id"].startswith(a) and (b in line["id"] or any(s["voice"] == b for s in line["segments"])):
            return "the story editor's review of section 17"
    return None''',
'''    if voice in HOLD_VOICES:
        return HOLD_VOICES[voice]
    for prefix, why in HOLD_LINES:
        if line["id"].startswith(prefix):
            return why
    return None''')
# Acted directions as ElevenLabs tags.
rep('''def paste(seg_text: str, d: dict, narrator_aside: bool, plain: bool = False) -> str:''',
'''ACTED = {"a sniff": "sniffs", "a laugh": "laughs", "a sigh": "sighs", "a gasp": "gasps"}


def acted_tag(m) -> str:
    inner = m.group(1).strip()
    inner = ACTED.get(inner, inner)
    return "[" + re.sub(r"^sung\\b", "singing", inner) + "]"


def paste(seg_text: str, d: dict, narrator_aside: bool, plain: bool = False, acted: str | None = None) -> str:''')
rep('''    text = seg_text
    if not narrator_aside:''', '''    text = re.sub(r"\\[([^\\]]+)\\]", acted_tag, acted) if acted else seg_text
    if not narrator_aside:''')
rep('''    vol = "quiet" if narrator_aside else d.get("vol", "level")''',
'''    vol = "quiet" if narrator_aside else d.get("vol", "level")
    if plain and vol == "hushed" and not d.get("whisper"):
        vol = "quiet"  # the narrator whispers only where his direction says so''')
rep('''paste(s["text"], d, aside, plain=voice == "narrator")''', '''paste(s["text"], d, aside, plain=voice == "narrator", acted=s.get("acted"))''')
# One take per distinct text.
rep('''    es = entries(man, voice)
    chars = sum(len(e["seg"]["text"]) for e in es)''',
'''    es, first = [], {}
    for e in entries(man, voice):
        key = e["seg"].get("acted", e["seg"]["text"])
        if key in first:
            first[key]["also"].append(file_name(e["line"], e["part"]))
            continue
        e["also"] = []
        first[key] = e
        es.append(e)
    chars = sum(len(e["seg"]["text"]) for e in es)''')
rep('''        w.append(f"### {n}. `{file_name(l, k)}`" + ("  HOLD" if hold else ""))
        w.append("")''',
'''        w.append(f"### {n}. `{file_name(l, k)}`" + (f"  HOLD: {hold}" if hold else ""))
        w.append("")
        if e["also"]:
            w.append(f"*The same words are also* {', '.join(f'`{x}`' for x in e['also'])}*: record once; the importer copies the take.*")''')
rep('''    w += ["## Who they are", "", sheet(voice) or v["design"], "",''',
'''    w += ["## Who they are", "", sheet(voice) or v["design"], ""]
    if v.get("wants") or v.get("hides"):
        w += [f"*Wants:* {v.get('wants', '')}. *Hides:* {v.get('hides', '')}.", ""]
    w += [''')
rep('''        why = sorted({held(e['line'], voice) for e in holds})
        w += [f"**Hold {len(holds)} of these** (marked HOLD below) until {', '.join(why)} is back; the rest can be recorded now.", ""]''',
'''        w += [f"**Hold {len(holds)} of these** (marked HOLD below, with why); the rest can be recorded now.", ""]''')
open(p, "w", encoding="utf-8", newline="\n").write(t)

p = "tools/vo/import_takes.py"
t = open(p, encoding="utf-8").read()
rep('''    for m, faults, said in wrong:''', '''    # One take serves every part with the same words in the same voice (the packets list them once).
    same: dict = {}
    for l in man:
        for i, s in enumerate(l.get("segments") or []):
            same.setdefault((s["voice"], s.get("acted", s["text"])), []).append((l["id"], i, len(l["segments"])))
    for m in list(kept):
        seg = by_id[m["line"]]["segments"][m["part"]]
        src = final_path(m["line"], m["part"], len(by_id[m["line"]]["segments"]))
        for lid, i, n in same.get((seg["voice"], seg.get("acted", seg["text"])), []):
            dst = final_path(lid, i, n)
            if (lid, i) != (m["line"], m["part"]) and not os.path.exists(dst):
                shutil.copyfile(src, dst)
                kept.append({**m, "line": lid, "part": i, "copy": True})
    for m, faults, said in wrong:''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("ok")

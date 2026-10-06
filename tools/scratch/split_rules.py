p = "tools/vo/lines.py"
t = open(p, encoding="utf-8").read()
s = t.index("def segments(text: str, voice: str) -> list[dict]:")
e = t.index("def variants(t):")
new = r'''def segments(text: str, voice: str, owner: str | None = None) -> list[dict]:
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


'''
t = t[:s] + new + t[e:]
old = '''        l["segments"] = segments(said, l["voice"])'''
new2 = '''        owner = None
        if l["id"].startswith("dlg.") and l["voice"] == "narrator":
            npc = l["id"].split(".")[1]
            owner = NPC_VOICE.get(npc, npc)
            owner = owner if owner in cast_voices() else None
        l["segments"] = segments(said, l["voice"], owner)'''
assert old in t
t = t.replace(old, new2)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("ok")

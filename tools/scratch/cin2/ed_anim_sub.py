import os
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\tools\cinematics\animatic.py"
s = open(p, encoding="utf-8").read()

old = '''def line_seconds(line_id):
    vo, raw, _ = find_line(line_id)
    if raw == "":
        return 0.0
    t = take_of(vo, raw)
    if t:
        return t.get("read") or t["sec"]
    return reading(raw)'''
new = '''def subtitle(raw):
    """The words as the subtitle shows them (CineLines.Subtitle): a lower-case
    (parenthesis) is how the line is said and is dropped; a capitalised one,
    such as a translation, stays. A direction saying it is sung sets italics."""
    sung = False

    def cut(m):
        nonlocal sung
        if not m.group(1).lstrip()[:1].islower():
            return m.group(0)
        if "sung" in m.group(0).lower():
            sung = True
        return " "
    shown = re.sub(r"\\s*\\(\\s*([^()\\s][^()]*)\\)\\s*", cut, raw)
    shown = re.sub(r"[ \\t]{2,}", " ", shown).strip()
    shown = shown.replace(" ,", ",").replace(" ?", "?").replace(" !", "!")
    return shown, sung


def line_seconds(line_id):
    vo, raw, _ = find_line(line_id)
    if raw == "":
        return 0.0
    t = take_of(vo, raw)
    if t:
        return t.get("read") or t["sec"]
    return reading(subtitle(raw)[0])'''
assert old in s, "line_seconds"
s = s.replace(old, new)

old = '''                take = take_of(vo, raw)
                secs = (take["sec"] if take else reading(raw)) + c.get("linger", 0.7)'''
new = '''                take = take_of(vo, raw)
                shown, sung = subtitle(raw)
                secs = (take["sec"] if take else reading(shown)) + c.get("linger", 0.7)'''
assert old in s, "secs"
s = s.replace(old, new)
old = '''                subs.append((t, t + secs, raw, name))'''
new = '''                subs.append((t, t + secs, shown, name, sung))'''
assert old in s, "append"
s = s.replace(old, new)
old = '''        for a, b, raw, name in subs:
            if a <= t < b:
                k = min(1.0, (b - t) / 0.25)
                f = F_ITAL if name is None else F_WORDS'''
new = '''        for a, b, raw, name, sung in subs:
            if a <= t < b:
                k = min(1.0, (b - t) / 0.25)
                f = F_ITAL if name is None or sung else F_WORDS'''
assert old in s, "draw"
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")

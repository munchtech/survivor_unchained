"""Docs follow the second reading: the laugh's direction first, the chart's margins said plainly.
Replaces across line breaks (the docs wrap), keeping each file's line endings."""
import re, sys
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a54dc034ed29f2e02"
def fix(rel, pairs):
    p = W + "\\" + rel
    raw = open(p, "rb").read().decode("utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    t = raw.replace("\r\n", "\n")
    for old, new in pairs:
        # match the old text whatever its wrapping
        rx = re.compile(r"\s+".join(re.escape(w) for w in old.split()))
        if not rx.search(t): sys.exit(f"{rel}: not found: {old[:50]}")
        t = rx.sub(lambda m: new if "\n" not in m.group(0) else new.replace(" ", "\n  ", 0), t)
    open(p, "wb").write(t.replace("\n", nl).encode("utf-8"))
    print("fixed", rel)

laugh = [("Ha! (a laugh, and it costs him) ...You", "(a laugh, and it costs him) Ha! ...You")]
fix(r"docs\cinematics\c11_raid_on_the_roost.md", laugh)
fix(r"docs\WRITING_PASS.md", laugh + [("It is the Wayfinder's, and the margins are full.)", "It is in the Wayfinder's hand, and its margins are written full.)")])
fix(r"docs\STORY_BIBLE.md", [("\"It is the Wayfinder's, and the margins are full.\"", "\"It is in the Wayfinder's hand, and its margins are written full.\"")])

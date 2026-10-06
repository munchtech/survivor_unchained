"""Mood concepts for the page's ground and framing (not finals): one queued graph, then free."""
import json
import os
import sys
import urllib.request

WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d"
sys.path.insert(0, os.path.join(WT, "tools", "uiforge"))
os.chdir(os.path.join(WT, "tools", "uiforge"))
import krea  # noqa: E402

BASE = ("A full-screen character sheet page of a dark fantasy action role-playing game interface, seen straight on, "
        "the whole screen, crisp and highly detailed, AAA game UI concept art, no readable text: ")
JOBS = [
    ("vellum", BASE + "the page is black-dyed vellum like a medieval book of hours, its blocks of content ruled with fine "
               "gold ink lines and tiny gold corner ornaments, bound across the top and the foot by bands of black oxblood "
               "leather with gilt tooling and a slim forged iron rail, a framed portrait of a hooded warrior at the left, "
               "four tall iron-framed cards with round bronze medallions in the middle, columns of small figures at the "
               "right, warm lamplight pooled on the page, deep shadow at its edges", 2101),
    ("iron", BASE + "a page of dark hammered blackened iron plates with riveted strap borders and gold wire inlay, "
             "ember light glowing low along the foot, a framed portrait of a hooded warrior at the left, four tall "
             "iron-framed cards with round bronze medallions in the middle, columns of small figures at the right, "
             "violet-black iron, warm gold accents", 2102),
    ("world", BASE + "the game world behind the page softly out of focus and darkened to deep blue-violet night, the "
              "page's columns frameless, each column topped by a slim gilt rule with a small square gold coin at its "
              "middle, a header band of black leather with gold tooling, a framed portrait of a hooded warrior at the "
              "left, four tall iron-framed cards with round bronze medallions in the middle, warm candle glow", 2103),
]

made = krea.t2i_many([(n, p, s) for n, p, s in JOBS], size=(1344, 768), tag="page_concepts", n=2)
for k, v in made.items():
    print(k, v)
req = urllib.request.Request("http://127.0.0.1:8188/free", data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
                             headers={"Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=30)
print("freed")

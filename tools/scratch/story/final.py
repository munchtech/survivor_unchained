import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *
from sub import sub

D = load("dialogue.json")
for m in D["holloway"]["marker"]:
    if m["when"] == {"hasItem": "greymuzzle_fang"}:
        # A fang he will no longer pay for is not news for him.
        m["when"] = all_(item("greymuzzle_fang"), not_(eq("bounty.stopped", True)))
save("dialogue.json", D)
sub("../README.md", """  notice board changes as the world does, and each morning's report says
  who heard what about you overnight.""", """  notice board changes as the world does, and each morning's report says
  who heard what about you overnight. People quote your deeds back to you,
  size up your calling, notice when you have become dangerous, and keep
  the promises the text makes (Maeca's rule at the Hollow, a promise to
  Greymuzzle); one of them, Maeca, can be more than a friend. Intimate
  scenes cut away unless the settings ask for them in full.""")
print("ok")

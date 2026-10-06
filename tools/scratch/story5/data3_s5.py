"""Second reading: the direction before Redcowl's laugh, and the chart's margins said plainly."""
import sys
sys.path.insert(0, r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\story5")
from jsonio_s5 import load, save

d = load("dialogue.json")
n = 0
for v in d["cin_raid_on_the_roost"]["nodes"]["spared"]["text"]:
    old = "Ha! (a laugh, and it costs him) ..."
    assert v["text"].startswith(old), v["text"]
    v["text"] = "(a laugh, and it costs him) Ha! ..." + v["text"][len(old):]
    n += 1
for v in d["vonnra"]["nodes"]["f_chart"]["text"]:
    old = "It is the Wayfinder's, and the margins are full.)"
    assert old in v["text"]
    v["text"] = v["text"].replace(old, "It is in the Wayfinder's hand, and its margins are written full.)")
    n += 1
save("dialogue.json", d)
print("changed", n)

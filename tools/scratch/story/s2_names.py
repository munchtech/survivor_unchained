"""Stage 2: names with the wit in what people say, not in the names (audit item 14)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *
from sub import sub

N = load("npcs.json")
N["npcs"]["vonnra"]["name"] = "Vonnra Ash-of-Morrow"
N["npcs"]["rav"]["name"] = "Rav Cutwell"
N["npcs"]["keegan"]["name"] = "Dame Keegan Orme"
N["npcs"]["keegan"]["title"] = "Of the Argent Vigil (probationary)"
save("npcs.json", N)

D = load("dialogue.json")
rav = D["rav"]["nodes"]["first"]["text"][0]
rav["text"] = "Well, well. Somebody who knows how to wear a kerchief without looking like a parrot. Sit. I'm Rav Cutwell. Doctor Cutwell, if you are bleeding. Doctor McBreathless, if you are the Watch."
fd = D["vonnra"]["nodes"]["f_door"]["effects"][1]["history"]
fd["text"] = "had your fortune read by Vonnra Ash-of-Morrow"
k = D["keegan"]["nodes"]
k["first"]["text"] = "Halt! None pass north. Dame Keegan Orme, of the Argent Vigil. Probationary. It is a real title."
for n in k.values():
    for c in n.get("choices", []):
        if c["text"] == "Why \"Professor\"?":
            c["text"] = "The children call you \"Professor\"."
k["prof"]["text"] = "I taught rhetoric at Saint Wend's before I took the oath, and somebody's mother found out. Now I am Professor to everyone under four feet. Rhetoric is very useful for telling people no."
save("dialogue.json", D)

# The design notes name them too.
B = "../docs/BETA_DESIGN.md"
sub(B, "| **Vonnra Hydrocheck** |", "| **Vonnra Ash-of-Morrow** |")
sub(B, "| **Dr. Rav McBreathless** |", "| **Rav Cutwell** (\"Doctor McBreathless\" to the Watch) |")
sub(B, "| **Professor Keegan** |", "| **Dame Keegan Orme** |")
print("stage 2 ok")

from lib_s7 import *
d = load("dialogue.json")
replace_text(d["holloway"]["nodes"]["cb_nemesis_slain"], "I've known men who wouldn't go back for their own boots.",
             "Most leave a thing where it beat them. I've a few things there myself.")
replace_text(d["scene_gate_dawn"]["nodes"]["gate"], "a bottle by his boot", "a bottle by his hand")
save("dialogue.json", d)
print("ok")

from lib_s7 import *
r = load("rules.json")
R = r["rules"]
home = next(x for x in R if x["id"] == "jory.home")
R.remove(home)
home["report"] = ("When the teamsters came up the Old Road, thin as rakes and walking, Holloway was on the gate, and the whole "
                  "square heard him: \"Three in! Count's— hell, I don't know what the count is!\" Harlan ran the length of the "
                  "street in his apron.")
R.insert(next(i for i, x in enumerate(R) if x["id"] == "jory.nights"), home)
save("rules.json", r)
print("ok")

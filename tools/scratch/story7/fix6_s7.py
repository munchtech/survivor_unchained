"""The knocking from day 3 on every road (the scene is the ground turning over), so the
confession lands in the middle of Act 1, before the fortune, without waiting for the Dig."""
from lib_s7 import *
r = load("rules.json")
k = next(x for x in r["rules"] if x["id"] == "holloway.knocking")
k["when"] = all_({"day": {"gte": 3}}, fact("prologue.done", True), nott(fact("scene.dusk", exists=True)))
save("rules.json", r)
print("ok")

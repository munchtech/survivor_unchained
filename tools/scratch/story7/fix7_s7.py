from lib_s7 import *
r = load("rules.json")
k = next(x for x in r["rules"] if x["id"] == "holloway.knocking")
k["when"]["all"].append(nott(fact("holloway.confessed", True)))
save("rules.json", r)
print("ok")

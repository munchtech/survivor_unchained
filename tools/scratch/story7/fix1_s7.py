from lib_s7 import *
r = load("rules.json")
for x in r["rules"]:
    if x["id"] == "holloway.count":
        x["when"]["all"].insert(1, fact("holloway.waited", True))
save("rules.json", r)
print("ok")

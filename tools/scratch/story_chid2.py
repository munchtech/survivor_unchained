import json
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content\dialogue.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))
# Keegan's supper has "Sit. Not there; that stone... Here." Chid's grief must not
# borrow her gesture: his is the want under the care. He needs the company.
old = "...Sit down a minute. Not there. There."
new = "...Sit down a minute. Not on the step. Here. By me."
n = 0
for v in d["chid"]["nodes"]["cb_nell"]["text"]:
    assert v["text"].endswith(old), v["text"]
    v["text"] = v["text"][: -len(old)] + new
    n += 1
assert n == 2
open(P, "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))
print("ok")

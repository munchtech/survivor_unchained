"""JSON data files, edited and written back in the repo's own layout (one-space indent).
load(name) -> data; save(name, data); roundtrip() checks the layout is reproduced."""
import json, os
DIR = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7debf1459f14dfe7\godot\data\content"


def path(name):
    return os.path.join(DIR, name + ".json")


def load(name):
    return json.load(open(path(name), encoding="utf-8"))


def dumps(d):
    return json.dumps(d, indent=1, ensure_ascii=False) + "\n"


def save(name, d):
    open(path(name), "w", encoding="utf-8", newline="\n").write(dumps(d))
    print("saved", name)


def roundtrip():
    for n in ["items", "crafting", "dialogue", "npcs", "shops", "quests"]:
        s = open(path(n), encoding="utf-8").read()
        print(n, dumps(json.loads(s)) == s)


if __name__ == "__main__":
    roundtrip()

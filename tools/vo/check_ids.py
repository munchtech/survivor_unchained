"""Which lines the game can say aloud have a take that will play.

Lists every id the game can produce (dlg., bark., folk., guard., say.,
cbark., name. ...), and for each says whether a recording plays: the id is
in godot/data/vo/index.json, the file is under godot/art/vo/, and the
index's hash is the hash of the text now in the game (a take made from other
words stays silent). Run it before and after a change to the writing:

    python tools/vo/check_ids.py --save before.json
    python tools/vo/check_ids.py --compare before.json

--compare fails (exit 1) unless every take that played before still plays,
under whatever id the line has now, with the very same audio bytes.
"""
import hashlib
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as L  # noqa: E402

VO = os.path.join(L.ROOT, "godot", "art", "vo")
INDEX = os.path.join(L.ROOT, "godot", "data", "vo", "index.json")


def state():
    built = L.expand(L.build(), L.load_directions())
    index = json.load(open(INDEX, encoding="utf-8"))["lines"]
    ids = {}
    for l in built:
        ids[l["id"]] = l
    voiced = {}
    for i, l in ids.items():
        t = index.get(i)
        if not t:
            continue
        path = os.path.join(VO, *t["file"].split("/"))
        if os.path.exists(path) and t.get("hash") == l["hash"]:
            voiced[i] = hashlib.sha256(open(path, "rb").read()).hexdigest()
    orphans = [i for i in index if i not in ids]
    return ids, voiced, orphans


def main(argv):
    ids, voiced, orphans = state()
    kinds = Counter(i.split(".")[0] for i in ids)
    pk = Counter(i.split(".")[0] for i in voiced)
    print(f"ids the game can produce: {len(ids)}  with audio that plays: {len(voiced)}")
    for k in sorted(kinds):
        print(f"  {k:6} {kinds[k]:5} ids  {pk.get(k, 0):3} voiced")
    print(f"say.+cbark. ids: {kinds['say'] + kinds['cbark']}  voiced: {pk.get('say', 0) + pk.get('cbark', 0)}")
    print(f"index entries no line produces (silent): {len(orphans)} {orphans}")
    for a in argv:
        if a.startswith("--save"):
            path = argv[argv.index(a) + 1]
            json.dump(voiced, open(path, "w"), indent=1)
        if a.startswith("--compare"):
            before = json.load(open(argv[argv.index(a) + 1]))
            lost = Counter(before.values()) - Counter(voiced.values())
            gained = Counter(voiced.values()) - Counter(before.values())
            print(f"before: {len(before)} voiced, after: {len(voiced)} voiced; audio lost {sum(lost.values())}, new {sum(gained.values())}")
            return 1 if lost or gained or len(before) != len(voiced) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

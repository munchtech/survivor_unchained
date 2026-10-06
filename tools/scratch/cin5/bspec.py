"""Rewrite a board spec (docs/cinematics/shoot/boards/<id>.json) one shot per line.
python bspec.py CID CHANGES.py   (CHANGES.py defines SHOTS = {id: {...}} and optionally PEOPLE = {name: text})"""
import importlib.util
import json
import sys

W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aece7b87e89b13f19"


def setspec(cid, shots, people=None):
    p = W + rf"\docs\cinematics\shoot\boards\{cid}.json"
    f = json.load(open(p, encoding="utf-8"))
    for n, d in (people or {}).items():
        f["people"][n] = d
    for sid, ch in shots.items():
        e = f["shots"].get(sid)
        if not isinstance(e, dict):
            e = f["shots"][sid] = {"prompt": e} if e else {}
        e.update(ch)
    lines = ["{", f'  "seed": {f["seed"]},', '  "people": {']
    ppl = list(f["people"].items())
    for k, (n, d) in enumerate(ppl):
        lines.append(f"    {json.dumps(n)}: {json.dumps(d, ensure_ascii=False)}" + ("," if k < len(ppl) - 1 else ""))
    lines += ["  },", '  "shots": {']
    sh = list(f["shots"].items())
    for k, (n, e) in enumerate(sh):
        lines.append(f"    {json.dumps(n)}: {json.dumps(e, ensure_ascii=False)}" + ("," if k < len(sh) - 1 else ""))
    lines += ["  }", "}", ""]
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines))


if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("c", sys.argv[2])
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    setspec(sys.argv[1], getattr(m, "SHOTS", {}), getattr(m, "PEOPLE", None))
    print("ok")

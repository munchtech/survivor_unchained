"""The house layout for a cinematic timeline (godot/data/cinematics/*.json):
readable by a writer, one cue to a line, so a retime is a one-line diff.

    python tools/cinematics/timeline_fmt.py FILE...   # rewrite in place
"""
import json
import sys


def one(o):
    return json.dumps(o, ensure_ascii=False, separators=(", ", ": "))


def fmt(d):
    out = ["{"]
    keys = list(d.keys())
    for i, k in enumerate(keys):
        v = d[k]
        comma = "," if i < len(keys) - 1 else ""
        if k in ("marks", "cast") and isinstance(v, dict):
            out.append(f'  "{k}": {{')
            items = list(v.items())
            for j, (mk, mv) in enumerate(items):
                out.append(f'    {json.dumps(mk)}: {one(mv)}' + ("," if j < len(items) - 1 else ""))
            out.append("  }" + comma)
        elif k == "shots":
            out.append('  "shots": [')
            for j, s in enumerate(v):
                out.append("    {")
                sk = [x for x in s.keys() if x != "cues"]
                lines = [f'      {json.dumps(x)}: {one(s[x])}' for x in sk]
                cues = s.get("cues", [])
                if cues:
                    lines.append('      "cues": [\n' + ",\n".join(f"        {one(c)}" for c in cues) + "\n      ]")
                else:
                    lines.append('      "cues": []')
                out.append(",\n".join(lines))
                out.append("    }" + ("," if j < len(v) - 1 else ""))
            out.append("  ]" + comma)
        else:
            out.append(f"  {json.dumps(k)}: {one(v)}{comma}")
    out.append("}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    for p in sys.argv[1:]:
        d = json.load(open(p, encoding="utf-8"))
        open(p, "w", encoding="utf-8").write(fmt(d))
        print("formatted", p)

#!/usr/bin/env python3
"""Texture import groups: tools/godot/tex_groups.json is the source, `apply` writes it into the
.import files, `check` verifies (exit 1 on drift), `list` reports. Generators call
group_params(res_rel_path) to get a group's params instead of hard-coding their own.

    python tools/godot/tex_groups.py list
    python tools/godot/tex_groups.py apply [--group NAME]
    python tools/godot/tex_groups.py check
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GODOT = os.path.abspath(os.path.join(HERE, "..", "..", "godot"))
TABLE = os.path.join(HERE, "tex_groups.json")
IMPORTERS = ("texture", "2d_array_texture")
SKIP_DIRS = {".godot", ".shots", ".git"}


def _rx(glob):
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i): out += "(?:.*/)?"; i += 3
        elif glob.startswith("**", i): out += ".*"; i += 2
        elif glob[i] == "*": out += "[^/]*"; i += 1
        elif glob[i] == "?": out += "[^/]"; i += 1
        else: out += re.escape(glob[i]); i += 1
    return re.compile("^" + out + "$", re.I)


def load():
    t = json.load(open(TABLE, encoding="utf-8"))
    never = [_rx(g) for n in t["never"] for g in n["globs"]]
    groups = []
    for g in t["groups"]:
        groups.append(dict(g, _in=[_rx(x) for x in g["globs"]], _ex=[_rx(x) for x in g.get("exclude", [])]))
    return never, groups


def find_group(rel, never=None, groups=None):
    if never is None: never, groups = load()
    if any(r.match(rel) for r in never): return None
    for g in groups:
        if any(r.match(rel) for r in g["_in"]) and not any(r.match(rel) for r in g["_ex"]):
            return g
    return None


def val(v):
    return "true" if v is True else "false" if v is False else str(v)


def wanted(g, rel, importer):
    p = dict(g["params"])
    low = os.path.basename(rel).lower()
    if importer == "texture" and any(m in low for m in g.get("normal_match", [])):
        p.update(g.get("normal_params", {}))
    return p


def group_params(rel, importer="texture"):
    """For generators: {key: 'value'} for the group covering res-relative path `rel` (under godot/), or {}."""
    g = find_group(rel.replace("\\", "/"))
    return {k: val(v) for k, v in wanted(g, rel, importer).items()} if g else {}


def read_import(path):
    raw = open(path, "rb").read().decode("utf-8")
    m = re.search(r'^importer="([^"]*)"', raw, re.M)
    return raw, (m.group(1) if m else None)


def merge(raw, want):
    """Return raw with `want` set inside [params]; everything else byte-identical."""
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    try: s = lines.index("[params]")
    except ValueError: return raw
    e = next((i for i in range(s + 1, len(lines)) if lines[i].startswith("[")), len(lines))
    seen = set()
    for i in range(s + 1, e):
        k = lines[i].split("=", 1)[0]
        if k in want and "=" in lines[i]:
            lines[i] = f"{k}={val(want[k])}"; seen.add(k)
    last = e
    while last > s + 1 and lines[last - 1] == "": last -= 1
    for k in want:
        if k not in seen:
            lines.insert(last, f"{k}={val(want[k])}"); last += 1
    return nl.join(lines)


def scan():
    never, groups = load()
    for root, dirs, files in os.walk(GODOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not os.path.islink(os.path.join(root, d))]
        for f in files:
            if not f.endswith(".import"): continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p[:-7], GODOT).replace("\\", "/")
            g = find_group(rel, never, groups)
            if not g: continue
            raw, imp = read_import(p)
            if imp not in IMPORTERS: continue
            yield g, rel, p, raw, imp


def pixels(path):
    try:
        from PIL import Image
        with Image.open(path) as im: return im.size[0] * im.size[1]
    except Exception:
        return 0


def cmd_list(a):
    stats = {}
    for g, rel, p, raw, imp in scan():
        s = stats.setdefault(g["name"], [0, 0, 0, 0])
        s[0] += 1
        if merge(raw, wanted(g, rel, imp)) == raw: s[1] += 1
        else: s[2] += 1
        s[3] += pixels(p[:-7])
    for g in load()[1]:
        n, ok, ch, px = stats.get(g["name"], [0, 0, 0, 0])
        print(f"{g['name']:12} files {n:4}  match {ok:4}  would change {ch:4}  source {px/1e6:8.1f} MP  ({g['why'][:60]})")


def cmd_apply(a):
    c = {}
    for g, rel, p, raw, imp in scan():
        if a.group and g["name"] != a.group: continue
        new = merge(raw, wanted(g, rel, imp))
        s = c.setdefault(g["name"], [0, 0]); s[0] += 1
        if new != raw:
            open(p, "wb").write(new.encode("utf-8")); s[1] += 1
    for k, (n, ch) in c.items(): print(f"{k}: {n} files, {ch} changed")


def cmd_check(a):
    bad = [rel for g, rel, p, raw, imp in scan() if merge(raw, wanted(g, rel, imp)) != raw]
    for b in bad: print("DRIFT", b)
    print(f"{len(bad)} file(s) differ from their group")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list"); sp.add_parser("check")
    sp.add_parser("apply").add_argument("--group")
    a = ap.parse_args()
    sys.exit({"list": cmd_list, "apply": cmd_apply, "check": cmd_check}[a.cmd](a) or 0)

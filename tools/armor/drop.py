"""Game side of "export from Marionette, drop in the game" (docs/armor/PIECE_SCHEMA.md, docs/handoff/armor.md item 9).

  python tools/armor/drop.py <id> [--from DIR] [--item "Name"] [--no-build] [--replace]

Copies <from>/<id>/piece.json and any .glb beside it to godot/art/armor/src/<id>/, validates it against the schema
page (refusing with a reason; a refusal copies nothing), runs tools/armor/build.py <id> (unless --no-build) and prints
the index row written. --item adds a matching item to godot/data/content/items.json.
"""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ART = os.path.join(ROOT, "godot", "art")
SRC = os.path.join(ART, "armor", "src")
LIB = os.path.join(ART, "armor", "lib")
DEFAULT_FROM = "C:/Users/munch/Desktop/Marionette/generated/to_game/armor"
INDEXES = [os.path.join(ART, "people", "armor_index.json"), os.path.join(ART, "armor", "armor_index.json")]
NEW_INDEX = INDEXES[1]
ITEMS = os.path.join(ROOT, "godot", "data", "content", "items.json")
SLOTS = ["top", "bottom", "legwear", "gloves", "skirt", "belt", "collar", "bracers", "greaves", "boots", "pauldrons", "cloak", "head"]
# Wear.cs Group(): the item slot (ItemKind in items.json) whose group holds a visual slot
KIND_OF = {"head": "head", "pauldrons": "shoulders", "top": "body", "collar": "body", "bracers": "bracers", "gloves": "hands",
           "belt": "belt", "skirt": "belt", "bottom": "legs", "legwear": "legs", "greaves": "legs", "boots": "feet", "cloak": "cloak"}
ICON_OF = {"body": "armor_heavy", "head": "helm", "cloak": "cloak"}  # the rest: armor_light


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def index_ids(path):
    return {r["id"] for r in load(path)} if os.path.exists(path) else set()


def has_name(names, n):
    """A pair stem (no side) means both _l and _r; with a side, that one only."""
    return n in names or (f"{n}_l" in names and f"{n}_r" in names)


def validate(pid, d, folder, replace):
    errs = []
    if not re.fullmatch(r"[a-z0-9_]+", pid):
        errs.append(f"id '{pid}' is not [a-z0-9_]+")
    if d.get("id") != pid:
        errs.append(f"piece.json id is '{d.get('id')}', not '{pid}'")
    for p in INDEXES:
        if pid in index_ids(p) and not (replace and p == NEW_INDEX):
            errs.append(f"id '{pid}' is already in {os.path.relpath(p, ROOT)}" + (" (use --replace)" if p == NEW_INDEX else " (a calling's piece: never replaced)"))
    if os.path.isdir(os.path.join(SRC, pid)) and not replace:
        errs.append(f"godot/art/armor/src/{pid} already exists (use --replace)")
    slot = d.get("slot")
    if slot == "ink":
        errs.append("slot 'ink' is a calling's skin, never a piece slot")
    elif slot not in SLOTS:
        errs.append(f"slot '{slot}' is not one of {', '.join(SLOTS)}")
    for c in d.get("covers", []):
        if c not in SLOTS:
            errs.append(f"covers '{c}' is not a visual slot")
    if not d.get("name"):
        errs.append("name is missing")
    if d.get("tier") not in (1, 2, 3):
        errs.append(f"tier {d.get('tier')} is not 1, 2 or 3")
    if d.get("material") not in load(os.path.join(ART, "people", "outfit_materials.json")):
        errs.append(f"material '{d.get('material')}' is not in outfit_materials.json")
    if d.get("tint") is not None and not re.fullmatch(r"#?[0-9a-fA-F]{6}", str(d["tint"])):
        errs.append(f"tint '{d['tint']}' is not an sRGB hex or null")
    base = d.get("base")
    if base:
        if not os.path.isfile(os.path.join(SRC, base, "piece.json")):
            errs.append(f"base '{base}' is not a piece in godot/art/armor/src/")
    elif not d.get("style"):
        errs.append("no base and no style: nothing defines the shell")
    # sockets and rims: the base's built file, else its own
    sk = None
    for owner in ([base] if base else []) + [pid]:
        p = os.path.join(ART, "armor", f"{owner}.sockets.json")
        if os.path.isfile(p):
            sk = load(p)
            sk_owner = owner
            break
    adorn = d.get("adorn", [])
    if sk is None and any(a.get("socket") or a.get("rim") for a in adorn):
        print(f"note: no built {base or pid}.sockets.json yet; sockets and rims are checked at build", file=sys.stderr)
    libids = load(os.path.join(LIB, "lib.json"))
    for n, a in enumerate(adorn):
        k = a.get("kind")
        tag = f"adorn[{n}] ({k})"
        if k not in ("row", "mesh", "trim", "paint"):
            errs.append(f"{tag}: unknown kind")
            continue
        if sk is not None:
            for field, table in (("socket", "sockets"), ("rim", "rims")):
                if a.get(field) and not has_name(sk.get(table, {}), a[field]):
                    errs.append(f"{tag}: {field} '{a[field]}' is not in {sk_owner}.sockets.json (has: {', '.join(sorted(sk.get(table, {})))})")
        if k in ("row", "mesh"):
            m = a.get("mesh")
            stem = m[:-4] if isinstance(m, str) and m.endswith(".glb") else m
            if not m:
                errs.append(f"{tag}: no mesh")
            elif not (os.path.isfile(os.path.join(folder, stem + ".glb")) or stem in libids):
                errs.append(f"{tag}: mesh '{m}' is neither beside piece.json nor in armor/lib/lib.json")
        if k == "paint" and not str(a.get("pattern", "")).startswith("etch_"):
            errs.append(f"{tag}: pattern must be etch_<name>")
    return errs


def add_item(d, name):
    pid, kind = d["id"], KIND_OF[d["slot"]]
    with open(ITEMS, "rb") as f:
        raw = f.read().decode("utf-8")
    items = json.loads(raw)["items"]
    if any(i.get("wear") and pid in i["wear"] for i in items.values()):
        print(f"item: a piece already wears '{pid}'; no item added")
        return
    iid = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    if iid in items:
        sys.exit(f"refused: item id '{iid}' already exists in items.json")
    tier = d.get("tier", 1)
    item = {"id": iid, "name": name, "kind": kind, "rarity": tier, "icon": ICON_OF.get(kind, "armor_light"), "value": 40 * tier,
            "description": f"{d['name']}: a {d.get('tier_name', 'forged')} {d['slot']} piece, worn over her own.", "wear": [pid]}
    text = json.dumps({iid: item}, indent=1, ensure_ascii=False)[2:-2]  # drop the outer braces
    text = "\r\n".join(" " + ln for ln in text.split("\n"))
    m = re.search(r"\r?\n \},\r?\n \"raritynames\"", raw)
    if not m:
        sys.exit("refused: could not find the end of the items table in items.json")
    # the table's last entry closes with "  }" just before m.start(); add a comma, then the new entry
    new = raw[:m.start()] + ",\r\n" + text + raw[m.start():]
    json.loads(new)
    with open(ITEMS, "wb") as f:
        f.write(new.encode("utf-8"))
    print(f"item: added '{iid}' ({kind}, wear [{pid}]) to items.json")


def main(argv):
    if not argv or argv[0].startswith("--"):
        sys.exit(__doc__)
    pid = argv[0]
    def opt(k, dflt=None):
        return argv[argv.index(k) + 1] if k in argv else dflt
    frm = os.path.join(opt("--from", DEFAULT_FROM), pid)
    pj = os.path.join(frm, "piece.json")
    if not os.path.isfile(pj):
        sys.exit(f"refused: {pj} not found")
    d = load(pj)
    errs = validate(pid, d, frm, "--replace" in argv)
    if errs:
        print(f"refused '{pid}':")
        for e in errs:
            print("  - " + e)
        sys.exit(1)
    dest = os.path.join(SRC, pid)
    os.makedirs(dest, exist_ok=True)
    for fn in os.listdir(frm):
        if fn == "piece.json" or fn.lower().endswith(".glb"):
            shutil.copy2(os.path.join(frm, fn), os.path.join(dest, fn))
    print(f"validated and copied to {os.path.relpath(dest, ROOT)}")
    if opt("--item"):
        add_item(d, opt("--item"))
    if "--no-build" not in argv:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "armor", "build.py"), pid], cwd=ROOT)
        if r.returncode:
            sys.exit(f"build.py failed ({r.returncode})")
        row = next((r_ for r_ in load(NEW_INDEX) if r_["id"] == pid), None)
        print("index row:", json.dumps(row, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])

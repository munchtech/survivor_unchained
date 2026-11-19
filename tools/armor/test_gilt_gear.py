"""The Hollow's Gilt (demo drops, 17 Nov): every wear id a gilt item lists must be a row in B's built gear index, and a plain
(default, no --only) build of B must produce them, so a rebuild of B's gear index cannot drop the kit."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gear_fit as gf  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
B_DIR = REPO / "godot" / "art" / "people" / "body_p1"


def gilt_wear_ids():
    items = json.load(open(REPO / "godot" / "data" / "content" / "items.json", encoding="utf-8"))
    items = items if isinstance(items, list) else items.get("items", items)
    items = list(items.values()) if isinstance(items, dict) else items
    ids = {w for i in items if str(i.get("id", "")).startswith("gilt_") for w in i.get("wear", [])}
    assert ids, "no gilt item lists a wear id"
    return ids


def test_committed_gear_index_has_every_gilt_wear_id():
    idx = json.load(open(REPO / "godot" / "art" / "gear" / "out" / "body_p1" / "gear_index.json", encoding="utf-8"))
    have = {r["id"] for r in idx["rows"]}
    assert not gilt_wear_ids() - have, sorted(gilt_wear_ids() - have)


def test_a_default_build_of_B_makes_every_gilt_row(tmp_path):
    """The default build (only=None) takes B's native rows (godot/art/armor/body_p1/armor_index.json, stamped to B's
    glb) whole: the kit rows are in it without any --only, and none is skipped for a stale body stamp."""
    said = []
    bodies = gf.load_bodies(str(B_DIR))
    got = gf.native_rows(bodies, str(tmp_path), None, say=said.append)
    missing = gilt_wear_ids() - set(got)
    assert not missing, (sorted(missing), said)

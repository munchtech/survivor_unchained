"""build.json body-keyed values (kit_build.by_body, armor-D 17 Nov): body A reads what it read before; a named body
reads its own values, in lists and nested objects too."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_build as kb  # noqa: E402


CFG = {"clear": 0.003, "plates": [
    {"name": "tasset", "tuck": 0.01},
    {"name": "hipf", "tuck": 0.01, "lames": [{"ride": {"thigh_hinge_l": 1.0}, "len": [0.065, 0.09]}],
     "by_body": {"p1": {"tuck": 0.025, "lames": [{"ride": {"hiptasset_hinge_l": 1.0}, "len": [0.19, 0.18]}],
                        "over": ["hip"]}}}]}


def test_body_a_reads_what_it_read_before():
    a = kb.by_body(CFG, "a")
    want = {k: v for k, v in CFG.items()}
    want["plates"] = [CFG["plates"][0], {k: v for k, v in CFG["plates"][1].items() if k != "by_body"}]
    assert a == want
    assert list(a["plates"][1]) == ["name", "tuck", "lames"]


def test_a_named_body_reads_its_own_values():
    b = kb.by_body(CFG, "p1")
    hipf = b["plates"][1]
    assert hipf["tuck"] == 0.025 and hipf["over"] == ["hip"]
    assert hipf["lames"] == [{"ride": {"hiptasset_hinge_l": 1.0}, "len": [0.19, 0.18]}]
    assert b["plates"][0] == CFG["plates"][0] and "by_body" not in hipf
    assert CFG["plates"][1]["tuck"] == 0.01  # (the source is not changed)


def test_shipped_recipes_keep_body_a():
    import json
    for pid in sorted(os.listdir(kb.SRC)):
        f = os.path.join(kb.SRC, pid, "build.json")
        if not os.path.exists(f):
            continue
        raw = json.load(open(f, encoding="utf-8"))
        if "by_body" not in json.dumps(raw):
            assert kb.by_body(raw, "a") == raw, pid

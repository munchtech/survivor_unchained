"""The manifest: every clip of hers the design asks for, what it answers in
the game, where it comes from, its licence and whether it is made.

    python tools/anim/manifest.py       (build.py runs it after packing)

Writes tools/anim/manifest.json. A clip is "made" when it is in the packed
library; otherwise the game plays the Universal Animation Library's clip
named under "fallback" (CC0), through HerPose as before.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "clips"

# name: (what the game asks for, fallback library clip, how it is made)
PLAN = {
    "idle_warden": ("idle, warden", "Idle_Loop", "100STYLE Heavyset_ID, arms keyed"),
    "idle_arcanist": ("idle, arcanist", "Idle_Loop", "100STYLE Strutting_ID, arms keyed"),
    "idle_reaver": ("idle, reaver", "Idle_Loop", "100STYLE Angry_ID, arms keyed"),
    "idle_stalker": ("idle, stalker", "Idle_Loop", "100STYLE Crouched_ID, arms keyed"),
    "idle_warden_break": ("idle break, warden", "-", "keyed"),
    "idle_arcanist_break": ("idle break, arcanist", "-", "keyed"),
    "idle_reaver_break": ("idle break, reaver", "-", "keyed"),
    "idle_stalker_break": ("idle break, stalker", "-", "keyed (100STYLE Followed for the glance)"),
    "catch_breath": ("standing after a hard run", "-", "keyed"),
    "run_warden": ("run, sword and buckler", "Jog_Fwd", "keyed by stride"),
    "run_reaver": ("run, axe", "Jog_Fwd", "keyed by stride"),
    "run_reaver_axes": ("run, two axes", "Jog_Fwd", "keyed by stride"),
    "run_arcanist": ("run, staff", "Jog_Fwd", "keyed by stride"),
    "run_arcanist_wand": ("run, wand", "Jog_Fwd", "keyed by stride"),
    "run_stalker": ("run, crossbow", "Jog_Fwd", "keyed by stride"),
    "run_stalker_daggers": ("run, daggers", "Jog_Fwd", "keyed by stride"),
    "sprint": ("sprint art, momentum", "Sprint", "keyed by stride"),
    "run_stop_l": ("stopping, left foot down", "-", "keyed"),
    "run_stop_r": ("stopping, right foot down", "-", "keyed"),
    "dash": ("the dash", "Roll", "keyed"),
    "sword_back": ("sword swing, first (left to right)", "Sword_Regular_A", "keyed"),
    "sword_fore": ("sword swing, second (right to left)", "Sword_Regular_B", "keyed"),
    "sword_heavy": ("sword, wide arc", "Sword_Attack", "keyed"),
    "axe_back": ("axe swing, first", "Sword_Attack", "keyed"),
    "axe_fore": ("axe swing, second", "Sword_Regular_B", "keyed"),
    "axe_heavy": ("axe, wide arc", "Sword_Heavy_Combo", "keyed"),
    "axes_left": ("two axes, left hand (left to right)", "Sword_Regular_A", "keyed"),
    "axes_right": ("two axes, right hand (right to left)", "Sword_Regular_C", "keyed"),
    "axes_heavy": ("two axes, wide arc", "Sword_Heavy_Combo", "keyed"),
    "daggers_back": ("daggers, first", "OverhandThrow", "keyed"),
    "daggers_fore": ("daggers, second", "OverhandThrow", "keyed"),
    "daggers_heavy": ("daggers, wide arc", "Sword_Regular_Combo", "keyed"),
    "throw": ("a knife or the disc thrown, the chain cast", "OverhandThrow", "keyed"),
    "cast_bolt": ("wand or staff loosing a spell", "Spell_Simple_Shoot", "keyed"),
    "cast_raise": ("the arcanist's heavy, creation", "Spell_Simple_Enter", "keyed"),
    "crossbow_shoot": ("a bolt loosed", "Pistol_Shoot", "keyed"),
    "warcry": ("warcry, sprint, cinder trail, wraith walk", "Punch_Cross", "keyed"),
    "hit": ("struck", "Hit_Chest", "keyed"),
    "death": ("falls", "Death01", "keyed"),
    "get_up": ("up again", "LayToIdle", "keyed"),
    "sit_log": ("the title: by the fire", "Sitting_Idle", "keyed"),
    "warden_show": ("creation flourish", "Sword_Block", "keyed"),
    "arcanist_show": ("creation flourish", "Spell_Simple_Enter", "keyed"),
    "reaver_show": ("creation flourish", "Sword_Regular_A", "keyed"),
    "stalker_show": ("creation flourish", "Pistol_Shoot", "keyed"),
}


def main():
    made = {}
    for f in sorted(OUT.glob("*.json")):
        d = json.loads(f.read_text())
        made[d["name"]] = d
    rows = []
    for name, (role, fallback, how) in PLAN.items():
        d = made.get(name)
        m = d["meta"] if d else {}
        rows.append({
            "clip": name, "plays_for": role, "status": "made" if d else "fallback",
            "fallback": fallback, "made_by": how,
            "source": m.get("source", ""), "licence": m.get("licence", ""), "changes": m.get("changes", ""),
            "length": round(d["length"], 3) if d else None, "layer": m.get("layer", ""),
        })
    for name, d in made.items():
        if name not in PLAN:
            m = d["meta"]
            rows.append({"clip": name, "plays_for": "(not in the plan)", "status": "made", "fallback": "-",
                         "made_by": "", "source": m.get("source", ""), "licence": m.get("licence", ""),
                         "changes": m.get("changes", ""), "length": round(d["length"], 3), "layer": m.get("layer", "")})
    out = {
        "library": "godot/art/anim/heroine.res",
        "sources": {
            "keyed": "Keyed in code in tools/anim (gait.py, keyed.py, clips/*.py): the project's own work.",
            "100STYLE": "Ian Mason et al., 100STYLE (2022), https://zenodo.org/record/8127870, CC BY 4.0: "
                        "retargeted to her skeleton, feet locked, looped, arms re-keyed.",
            "UAL": "Quaternius, Universal Animation Library 1 and 2, CC0: the fallback for clips not yet made.",
        },
        "made": sum(1 for r in rows if r["status"] == "made"),
        "planned": len(PLAN),
        "clips": rows,
    }
    (HERE / "manifest.json").write_text(json.dumps(out, indent=1))
    print(f"manifest: {out['made']} made of {len(PLAN)} planned")


if __name__ == "__main__":
    main()

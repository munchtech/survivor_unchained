"""Give every weapon-holding clip its meta "weapon" (the grip it sits in)."""
from pathlib import Path

A = Path(r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa15f092820132274\tools\anim\clips")
EDITS = {
    "soul.py": [
        ('build("warden_show", rig, keys, base=base, meta={"layer": "full"})', 'build("warden_show", rig, keys, base=base, meta={"layer": "full", "weapon": "sword+shield"})'),
        ('build("arcanist_show", rig, keys, base=base, meta={"layer": "full"})', 'build("arcanist_show", rig, keys, base=base, meta={"layer": "full", "weapon": "staff"})'),
        ('build("reaver_show", rig, keys, base=base, meta={"layer": "full"})', 'build("reaver_show", rig, keys, base=base, meta={"layer": "full", "weapon": "axe"})'),
        ('build("stalker_show", rig, keys, base=base, meta={"layer": "full"})', 'build("stalker_show", rig, keys, base=base, meta={"layer": "full", "weapon": "crossbow"})'),
        ('build("idle_warden_break", rig, keys, base=base, meta={"layer": "full"})', 'build("idle_warden_break", rig, keys, base=base, meta={"layer": "full", "weapon": "sword+shield"})'),
        ('build("idle_arcanist_break", rig, keys, base=base, meta={"layer": "full"})', 'build("idle_arcanist_break", rig, keys, base=base, meta={"layer": "full", "weapon": "staff"})'),
        ('build("idle_reaver_break", rig, keys, base=base, meta={"layer": "full"})', 'build("idle_reaver_break", rig, keys, base=base, meta={"layer": "full", "weapon": "axe"})'),
        ('build("idle_stalker_break", rig, keys, base=base, meta={"layer": "full"})', 'build("idle_stalker_break", rig, keys, base=base, meta={"layer": "full", "weapon": "crossbow"})'),
    ],
    "arts.py": [
        ('meta={"layer": "full", "note": "keyed: 0.4 s shield charge, then the plant and shove"}', 'meta={"layer": "full", "weapon": "sword+shield", "note": "keyed: 0.4 s shield charge, then the plant and shove"}'),
        ('meta={"layer": "full", "note": "keyed: yanked off her feet and flown in on the chain, held"}', 'meta={"layer": "full", "weapon": "axe", "note": "keyed: yanked off her feet and flown in on the chain, held"}'),
        ('meta={"layer": "full", "contact": 2 / 30,\n', 'meta={"layer": "full", "contact": 2 / 30, "weapon": "axe",\n'),
    ],
    "actions.py": [
        ('build("cast_bolt", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0})', 'build("cast_bolt", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0, "weapon": "staff"})'),
        ('build("cast_raise", rig, keys, meta={"layer": "upper", "contact": 10 / 30})', 'build("cast_raise", rig, keys, meta={"layer": "upper", "contact": 10 / 30, "weapon": "staff"})'),
        ('build("cast_flick", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0})', 'build("cast_flick", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 0.0, "weapon": "wand"})'),
        ('build("crossbow_shoot", rig, keys, meta={"layer": "upper", "contact": 0.0})', 'build("crossbow_shoot", rig, keys, meta={"layer": "upper", "contact": 0.0, "weapon": "crossbow"})'),
        ('build("throw", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 2.5 / 30})', 'build("throw", rig, keys, lead=STRIKE, meta={"layer": "upper", "contact": 2.5 / 30, "weapon": "daggers"})'),
    ],
    "sprint_stop.py": [
        ('build(f"stop_{calling}_{side}", rig, keys, meta={"layer": "full"})', 'build(f"stop_{calling}_{side}", rig, keys, meta={"layer": "full", "weapon": idle.IDLES[f"idle_{calling}"][2]})'),
    ],
}
for f, eds in EDITS.items():
    p = A / f
    t = p.read_text(encoding="utf-8")
    for a, b in eds:
        assert t.count(a) == 1, (f, a)
        t = t.replace(a, b)
    p.write_text(t, encoding="utf-8")
    print(f, len(eds))

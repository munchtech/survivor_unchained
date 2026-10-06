import os

p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'README.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert a in s, a[:80]
    s = s.replace(a, b)


rep("""  tells her she lit the lamps (C09), and it is the first time she has looked at
  the survivor's face at all. Three in Act 1; do not add a fourth.""",
    """  tells her she lit the lamps (C09), and it is the first time she has looked at
  the survivor's face at all. Three in Act 1; do not add a fourth. What a keeper
  looks for, holding a lamp to a face at night, is breath. In the lamp's light,
  the survivor's does not show (C02 shot 8; C09 shot 14a, beside Vonnra's, which
  does). Nobody ever says so: it is the reason for the gesture, and the player
  who notices has the whole motif.""")
rep("""A variant whose text is empty is no line:
nothing plays and no subtitle shows (`cin_heart_goes_down.answer#1`, for
everyone who is not devout).""",
    """A variant whose text is empty is no line:
nothing plays and no subtitle shows. (Use one where a beat is spoken for some
survivors and silent for the rest; none of the Act 1 scripts needs one now.)""")
rep("""8. **Breath-smoke** on people in the cold at night, absent on the survivor
   while the ember burns (C01, C04, and every night after).""",
    """8. **Breath-smoke** on people in the cold at night, absent on the survivor
   while the ember burns (C01, C04, and every night after); a breath that a
   lamp's flame leans from (C09).""")
rep("""10. **Sets**: a roof on the toll tower to stand on (C09); Brannoc's anvil and
    the rack with two lamp-irons by the smithy (C07, and all of Act 1); the
    Roost's people (women, the old, children, cooking fires) and an old red
    standard with Ashford's arms (C06); Nell's iron marker by Ashe's grave in
    the Quiet Garden (C08).""",
    """10. **Sets**: a roof on the toll tower to stand on (C09), with a backdrop of
    the valley whose lights follow the world's facts; Brannoc's anvil and the
    rack with two lamp-irons by the smithy (C07, and all of Act 1); the Roost's
    people (women, the old, children, cooking fires) and an old red standard
    with Ashford's arms (C06); Nell's iron marker by Ashe's grave in the Quiet
    Garden, and the empty hook over the Last Lamp's door (C08); a den's mouth at
    the edge of the Pack's arena (C10). Props with writing: the ledger page,
    twenty-seven lines in a small violet hand, twenty-six ruled through (C09);
    the marker's plate, NELL punched with a nail (C08).""")
rep("""    composed motifs named in the scripts (the Warden's song, the lamp motif,
    Chid's hymn).""",
    """    composed motifs named in the scripts (the Warden's song, which is the
    Order's evening call; the lamp motif; the burial hymn "Lie Down", sung by
    Chid and a crowd, C08).""")

# index lengths
rep("| C04 | First Light | The north bank; the Waystation | The ember goes out; chapter one opens | 1 | 40 s + 25 s |",
    "| C04 | First Light | The north bank; the Waystation | The ember goes out; chapter one opens | 1 | 40 s + 26 s |")
rep("| C08 | The Iron Marker | The Waystation, the Quiet Garden | Conditional payoff (Nell's burial) | 2 | 68 s |",
    "| C08 | The Iron Marker | The Waystation, the Quiet Garden | Conditional payoff (Nell's burial) | 2 | 72 s |")
rep("| C09 | The Fortune | The toll tower's roof | Act 1 closes; choice | 1 | about 2 min |",
    "| C09 | The Fortune | The toll tower's roof | Act 1 closes; choice | 1 | 1 min 55 s to 2 min 10 s |")
rep("| 3 | 9 s + 14 s | `c10_hollow_by_night.md` |", "| 3 | 9 s + 16 s | `c10_hollow_by_night.md` |")
rep("| 3 | 10 s + 16 s | `c11_raid_on_the_roost.md` |", "| 3 | 10 s + 17 s | `c11_raid_on_the_roost.md` |")
rep("| 3 | 12 s + 8 s + 16 s | `c13_behind_the_door.md` |", "| 3 | 12.5 s + 8 s + 16 s | `c13_behind_the_door.md` |")

s = s.rstrip('\n') + """

## 8. Storyboard frames

Six frames in `boards/`, made on this machine with the local Krea 2 model, at
2.39:1. They are references for mood, light and framing only. The survivor in
them is a stand-in: in the game she is the player's face, hair and calling, so
build to the script, not to her. Nor are their costumes, props or architecture
canon (the script and the zone are).

| Frame | Script, shot | What it is for |
|---|---|---|
| `c01_s08_no_breath.jpg` | C01, shot 8 | The waking close-up: frost, wet hair, night, and no breath in the cold. |
| `c02_s07_lamp_to_face.jpg` | C02, shot 7 | The Warden bending to lift the lamp to her face; the drowned standing in the pool; the blue posts. |
| `c03_s08_heart.jpg` | C03, shot 8 | The heart's cold light reaching toward her hand over the water. |
| `c04_a5_first_breath.jpg` | C04, shot A5 | Dawn through the trees, and her first breath smoking. |
| `c07_s04_hammer_raised.jpg` | C07, shot 4 | Brannoc at the anvil, the two lamp-irons by the door, the lane in daylight. |
| `c09_s01_tower_roof.jpg` | C09, shot 1 | The roof, the lamp on the table, the town below and the dark valley. (Made before C09 was restaged: in the script Vonnra sits with her back to the town, facing the Verge.) |
"""
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')

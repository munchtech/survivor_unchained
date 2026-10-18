# Grip standard

**Why:** new weapons should not need new animation. Her fist is fitted once per weapon TYPE (keyed.py WRAP and GRIP lean, the WeaponSockets pocket). Each new piece's grip is brought to its type's grip, so that type's fist holds it unchanged. New animation work is needed only for a new type.

## The spec: `tools/anim/data/grip_spec.json`

| Type | Section (mm, in life) | Grip length | Grip point below guard | Fitted on |
|---|---|---|---|---|
| Staff | round, r 13.65 | 382 | - (anchor) | mage_staff's grip_wrap |
| Blade1H | round, r 13.70 | 131 | 84.0 | chevalier_sword (thinned) |
| Dagger | flat hexagon, 29.2 across x 15.2 toward the palm | 128 | 71.1 | daggers (Cube_004) |
| Axe | flat, 32 x 27.3 (PROVISIONAL) | - | - | none yet: no fist is fitted on an axe |

- **Section:** the grip's half-extents about its centre line, in its own principal frame. Width is across the flats' long way; depth is toward the palm. A round section has width equal to depth.
- **Grip point and axis (the anchor_grip rule, handoff/animation.md):** the origin is on the shaft where the fist grips. -Y runs down toward the tip, and +Z lands on the piece's +Z.
- **Glove:** the radial offset a thicker glove adds around the fist. It is 0 for every type for now; fistfit is where it would apply.

## The import step: `tools/assets/grip_conform.py`

1. `measure`: lays each Arms.Spec row as Arms.Make does, finds the grip (rings out from the grip point until a guard or pommel rises), and prints its section against its type's.
2. `conform <piece> --out <scratch>`: scales only the grip's vertices about the grip's centre line, width and depth separately, so the widest section matches the spec. The swell and the flats are kept. With `--round`, a round type's grip outline is drawn to the circle, which makes a flat hilt round. Normals and tangents are carried through the same map. The guard, pommel, blade, UVs, indices and every other byte stay as they were. It then writes an `anchor_grip` that reproduces the old mount exactly. With `--seat`, the grip point moves to the type's distance below the guard.
3. `check`: re-measures the output. It passes when the section is within 0.3 mm of the spec (half-extents; for a round type, no corner past the circle), no vertex outside the grip has changed, the UVs and all other accessors are byte-identical, and the mount is unchanged.
4. Copy the file into `public/assets/weapons`, re-dump arms_local (ArmsDump), then run `fistfit.py <piece>` as the numeric pass or fail. No judge is needed. Then set the Arms.Spec row's `Seated: true`.

A piece the automatic band misreads (a wire-wrapped grip, a strap beside a bead strand) gets its own `t`, `parts` or `centre` entry under the spec's `pieces`. `grip_thin.py` still works for the chevalier sword's history. grip_conform supersedes it.

# Grip standard: the grip frame every weapon lands on

**Why (the owner, 18 October: "we want to be able to build and just drag over armor and weapons without having to rebuild hopefully anything animation wise or character wise"):** her fist is fitted ONCE per weapon KIND: a grip pose (keyed.py WRAP), a lean (keyed.py GRIP) and a pocket (WeaponSockets). A new piece of a known kind only has to bring its grip to its kind's frame below, and every clip of that kind holds it unchanged: no clip, rig or body work. New animation work is needed only for a new KIND.

## 1. The hand socket (where a held piece hangs)
- The piece hangs from a `BoneAttachment3D` on `hand_r` (or `hand_l`); a shield on `lowerarm_*` (Arms.Hold, Arms.MountTransform).
- **hand_r's space:** +Y along the fingers (wrist to knuckles), +Z toward the thumb's side, the palm toward -X. Millimetres below are in this space, on her rest skeleton (`tools/anim/data/heroine_skeleton.json`; the hero shares the clips and the seats).
- **The plain mount** (a kind with no fitted fist): origin (-25, 75, 0) mm, the piece's +X on hand +Y, its +Y (the shaft) on hand +Z, turned `Spec.Lean` degrees about hand +X toward the fingers.
- **The pocket** (a fitted kind): a point and a direction in hand_r's space, the centre line of the hollow her fist closes round. `Arms.Seat` lays the piece's grip point ON the point and its shaft ALONG the direction (`WeaponSockets.FistSeat`; the crossbow `PistolSeat`). For a seated piece the plain mount, Lean and Spec.Grip no longer matter.
- **The left hand** is the right one mirrored through her body (`WeaponSockets.MirrorRL`, `ToLeft`; not a plain X flip). Only the Dagger has a fitted left fist (DaggerLeftAt, WRAP["daggers_l"]); every other kind in the left hand keeps the plain mount.

## 2. The piece's grip frame (what a weapon file carries)
- **`anchor_grip`** node (any depth; in a multi-piece file, under the piece's own node): **origin = the grip point**, on the shaft's centre line where her fist grips; **-Y down the shaft toward the tip** (blade, staff head, the crossbow's bow); **+Z the edge or face direction** (a blade's edge, an axe's bit, a shield's face, the crossbow stock's top).
- **`anchor_sheath`** node, same axes: the point the piece hangs from when sheathed (docs/handoff/animation.md section 0b; the socket per kind is `WeaponSockets.SocketOf`).
- **The kind tag:** a glTF node extra `"kind": "<kind>"`, or a node named `kind_<kind>`; it beats the Spec row's Kind. Values (`WeaponSockets.Parse`, any case): `blade1h blade2h blunt axe axe2h dagger wand staff shield crossbow`.
- **Scale:** `Arms.Make` scales the piece so its long extent is `Spec.Length` metres. Model at life size and give the true length.
- **The grip's section** must match its kind's (`tools/anim/data/grip_spec.json` "types", within 0.3 mm), or her fingers go into it or float off it. `tools/assets/grip_conform.py conform` brings a bought or generated grip to it (section 5).
- Without anchors the game falls back to the bounds' long axis, `Spec.Grip` (0 butt, 1 tip), `Flip` and `Roll`: legacy only. **Every new piece carries anchor_grip.**

## 3. Per kind (the data and where it lives)
| Kind | Pocket, hand_r mm (WeaponSockets) | Shaft direction | Grip pose (WRAP) / lean (GRIP) | Grip section (grip_spec.json) | Fitted on | Status |
|---|---|---|---|---|---|---|
| Blade1H | BladeAtR (-43.1, 88.8, -13.1) | BladeDirR: hand +Z turned 35 deg toward the fingers | sword / 35 | round r 13.70; 131 long; grip point 84.0 below the guard | chevalier_sword; viking_sword conformed | live (fistfit 13/13) |
| Dagger | DaggerAtR (-32.4, 72.0, -13.9); left: DaggerLeftAt, mirrored | DaggerDirR: 30 deg | daggers, daggers_l / 30 | flat hexagon 29.2 across x 15.2 toward the palm; 128; 71.1 below the guard | daggers, dagger_b | live (right 8/8, left 7/8) |
| Staff | FistAtR (-32.6, 84.1, -10.4) | FistDirR: a diagonal, 27.7 deg off hand +Z | staff / 18 | round r 13.65; 382 | mage_staff's grip wrap | live (10/10) |
| Crossbow | CrossbowAtR (-41.0, 95.1, -9.2) | CrossbowDirR: the pistol grip's line, hand +Z turned PistolRake 22.5 deg; the stock along hand +Y | crossbow / pistol | round r 13.7; 84; rake 22.5 deg | crossbow (grip: tools/assets/crossbow_grip.py) | live (8/8) |
| Axe | AxeAtR (fitted, NOT live: not in PocketR) | AxeDirR | none / 30 | flat 32 x 27.3, PROVISIONAL | none (viking_axe's haft is too thick) | plain mount |
| Blade2H, Blunt, Axe2H, Wand | none | plain mount + Lean | none / wand 30 | none | none | plain mount |
| Shield | the forearm (MountTransform: ShieldOff, ShieldAlong) | - | - | - | shield_round | forearm mount |

In the anchor's terms: the grip point goes to the pocket point and the anchor's -Y to the pocket direction. **The crossbow differs:** its anchor's -Y is the STOCK (toward the bow), +Z the stock's top, the origin on the pistol grip's line ANCHOR mm below the stock; the grip's own line in the piece is (0, sin 22.5, cos 22.5), and PistolSeat lays that line on CrossbowDirR with the stock forward.

**Where each part lives:** pockets and seats in `godot/logic/Play/WeaponSockets.cs` (PocketR, PocketL, FistSeat, PistolSeat; tests in `godot/tests/WeaponSocketsTests.cs`); reading the anchors, the seat and the mount in `godot/src/Actors/Arms.cs` (Make, Seat, MountTransform; the `All` table of Spec rows); grip poses in `tools/anim/keyed.py` (WRAP, WRAP_LEFT, wrap_of; GRIP, grip_of: a clip's meta "weapon" picks them, so every clip of a kind closes the same fist); grip sections in `tools/anim/data/grip_spec.json`; the numeric check in `tools/anim/fistfit.py` (its PIECES table names each checked piece and the clip frames it is measured on).

## 4. A new weapon of a known kind (no animation)
1. Model it at life size with the kind's grip section, or run `python tools/assets/grip_conform.py conform <piece> --out <dir>` (`--seat` moves the grip point to the kind's distance below the guard; `--round` or `--cylinder` for round kinds) and `check` it.
2. Give it `anchor_grip` (and `anchor_sheath`) and the kind tag (section 2). Marionette's export writes them (Marionette/HANDOFF.md, Marionette commit 9757a13).
3. Put the .glb in `public/assets/weapons/` and add its row to `Arms.All`: `new("<file>", <length m>, <grip 0-1, fallback only>, Kind: WeaponKind.<Kind>)`, plus `Pistol: true` for a crossbow and `Node:` when the file holds several pieces. An anchored piece is seated on its kind's pocket automatically (`Seated: true` is only for an UNanchored piece whose Spec.Grip was measured on the fist). Today the row is one line of C#; a data file is the pipeline's to add.
4. Re-dump the arms (`tools_scenes/arms_dump.gd`, headless; `tools/scratch/anim38/dump.sh`), add a fistfit PIECES row copied from its kind's, and run `python tools/anim/fistfit.py <piece>`: the numeric pass (every finger's pads on it, nothing into it). Then `python tools/anim/armscheck.py --sockets` for its sheathed socket. A piece whose grip passes needs no animation judge.

A grip that can't take its kind's section (a haft too thick, a wire wrap the band misreads) gets a `pieces` entry in grip_spec.json, or becomes a new kind: that one IS animation work (a WRAP fit, a pocket, the kind's clips).

## 5. The import step in detail: `tools/assets/grip_conform.py`
1. `measure`: lays each Arms.Spec row as Arms.Make does, finds the grip (rings out from the grip point until a guard or pommel rises), and prints its section against its type's.
2. `conform <piece> --out <scratch>`: scales only the grip's vertices about the grip's centre line, width and depth separately, so the widest section matches the spec. The swell and the flats are kept. With `--round`, a round type's grip outline is drawn to the circle, which makes a flat hilt round; `--cylinder` draws each ring to the circle (tapers, beads). Normals and tangents are carried through the same map. The guard, pommel, blade, UVs, indices and every other byte stay as they were. It then writes an `anchor_grip` that reproduces the old mount exactly. With `--seat`, the grip point moves to the type's distance below the guard.
3. `check`: re-measures the output. It passes when the section is within 0.3 mm of the spec (half-extents; for a round type, no corner past the circle), no vertex outside the grip has changed, the UVs and all other accessors are byte-identical, and the mount is unchanged.
4. Copy the file into `public/assets/weapons`, re-dump arms_local (ArmsDump), then run `fistfit.py <piece>` as the numeric pass or fail.

- **Section:** the grip's half-extents about its centre line, in its own principal frame. Width is across the flats' long way; depth is toward the palm. A round section has width equal to depth.
- **Glove:** the radial offset a thicker glove adds round the fist; 0 for every kind (the fists are fitted on her skin and the ranger's glove).
- A piece the automatic band misreads (a wire-wrapped grip, a strap beside a bead strand) gets its own `t`, `parts` or `centre` entry under the spec's `pieces`. `grip_thin.py` is the chevalier sword's history; grip_conform supersedes it.

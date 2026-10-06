# Cinematics: status

Agent a7a4c20bcfd7ccfd3 (succeeded a79b6d8c81e14dc63 on 5 October), branch `worktree-agent-a7a4c20bcfd7ccfd3`. The brief: shooting scripts, boards and animatics for C01 to C14, and the in-engine cinematic player. Pipeline and timeline format: `docs/cinematics/shoot/README.md`. Predecessor's handoff: `docs/handoff/cinematics.md`.

## State (5 October)

- **Hand-over into play (the owner's rule, `docs/cinematics/README.md` 5a).** Play now takes her exactly where a cinematic leaves her, facing as she faces:
  - her own body plays each last shot from its cut (`play`); a walk still going at the end carries on and eases to a stop;
  - the last shot blends into the game's camera, turning its view rather than sliding a far point, and the camera's snap no longer drops 0.8 m; the HUD fades in with the bars;
  - arrivals in any zone face their way (the figure stood facing south until it moved: that was C01's snap);
  - `CinemaTests` holds every timeline that ends in play to it. C01 to C04 B all comply.
- **Lowford's camp is made for its close-ups** (`src/World/Camp.cs`, `Campfire.cs`; seen in the title, creation and C01): sawn pine logs (Poly Haven's Pine Bark) with weathered, checked end grain; a ring of eleven made stones, sooted inside; a bed of coals and burnt sticks that glows from within and under-lights a hand held over it; no tripod or pot. The coals are kept out of their own fire's light. Nothing grows in a fire pit.
- **C01** burns down to coals (no flames; the light sinks to just over them). Shot 5 is from the west, through the coals' light (no leg or stone across her); 6 holds her face and hands; 6a's hand is under-lit over the coals; 10 holds focus as she rises. The new staging is rendered (`st1`); its board prompts are rewritten for the camp.
- **The Prologue (C01 to C04)** is otherwise as handed over: surveyed, wired, playing, on the Warden's judged clips.

## Next, in order

1. Stage animation's new C01 and C04 clips (handoff Next 1), film C04 A's hand-over again, then render the staging for C02, C03 and C04 B (the heart's ring halo in C03); draw the boards (C02's s3, s5, s7, s8, s11; then C01, C03, C04 A and C04 B), each at full size.
2. Recut the Prologue animatic (`animatics/prologue.txt`; C01's shot 4 is now 6a).
3. The male hero through the Prologue (`prev.py --male`).
4. C02's and C03's line choices, then C07 and C09.
5. C10 to C13 once combat's successor lands the marks and `c10_spared` (their handoff §4.3, item one); the Dig (C12) now exists in code.

## Key decisions

- **Her own body ends every cinematic that ends in play,** swapped in on a cut: the walk play continues is the walk the shot showed, same gait and stride, with no pose seen to change.
- **The engine's frame is the staging truth; boards are drawn over it** (God of War's previs-first). Cameras aim at bones (Baldur's Gate 3), so a shot follows the body it is given.
- **One traveller's fire:** no tripod or pot at the camp. A bed of coals carries C01 better than flames, and nothing stands across the low cameras round her.
- **Looks are head turns;** the cinematic owns a boss's body while it plays.

## Blockers and notes for others

- **UI design / experience:** the title and creation now show the made camp (no tripod or pot); the HUD fades in after a cinematic rather than appearing at once.
- **Performance:** each ring fire has one more small light (the coals' glow: no shadows, 1.1 m) and about 6k more triangles (stones and coals).
- **Provenance:** `art/world/stone_fire_pit.glb` is no longer drawn (the ring is made); Pine Bark is credited.
- **Animation:** still to come: the Warden's `lie_arm_up` and `wade_drag`; Grimtunnel's burst, sniff and dive; C04's `wade_out`, `flask_drink`, `walk_uphill`, `unfold_arms`; C01's `letter` and `kneel_to_stand_snap`.
- **Face:** `mouth_open` above 0.15 shows the teeth as a grin in C01's close-ups. Her hand reads smooth at C01's insert distance (no visible pores).
- **Voice:** none needed; no new placeholders.

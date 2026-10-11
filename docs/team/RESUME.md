# Where we are: read this after README.md, before your handoff

The one page of what's current. Every lead starts from the latest `claude/vigilant-galileo-l6jqyx`. Merge it first and keep your own workflow; this page says what has changed around you. Updated by the main session, 5 October 2026.

## How the team runs now (README has the detail)

- **Tokens and quality, always (the owner, 7 October):** the cheapest route that ends at the same quality, as standing permission. Long-running leads are `su-lead-high`; max effort goes to short-lived `su-lead-max` judges and solvers (story writer and editor stay `su-lead-max` leads). Pass `effort` on every spawn. README "Working lean".

- 3 to 5 leads at once. The rest are paused with their handoffs and resumed in turn.
- Heavy work takes turns (`tools/turn.py`): `gpu` (ComfyUI, TRELLIS, MoGe, one at a time), `blender` (two), `godot` (three). A fair queue: ask again within 90 s to keep your place.
- Batch shots and look once. Hand off at about 300k tokens of context. Lean handoffs. See README "Working lean".
- Before you show the main session anything, run a strict self-critique at 1:1 and send the findings with it.

## The owner's standing decisions (newest first)

- **UI:**
  - Panels over the live world, not full pages ("we like to see our beautiful game").
  - No fades: panels end cleanly, on a ground ever so slightly translucent (about 0.9).
  - No "AI boxes": data is type on the page; stats are a ledger line.
  - Minimal dead space, strict symmetry and grid.
  - Soul through world objects that mean something: the chain (Survivor *Unchained*), coals, the watch-lamp, painted pieces, used sparingly.
  - Toasts, tips and ground labels are stylised type on the world, with no plates.
- **Sound:** CC0 is acceptable (logged in ASSET_PROVENANCE). Our own is best. The owner may send real recordings to `incoming/`.
- **Coverage:** pixel-perfect. Cover exactly what must be covered (the areola, a 2.4 cm midline strip), show everything else, and never a hole or see-through. Her skin under garments is tucked in the shader, not cut. There were never genital issues. Fit means tighter, not bigger.
- **Loot:** fewer, better drops; legendaries (some early) and sets; item level by zone; a filter; slotless stores (pouch, satchel, key ring, belt, purse).
- **Story fights:** small, specialised arenas with ARPG bosses and no endless phase. A loss wakes her at Chid's a day on. Redcowl can be spared or killed. One rise in Act 1; later only via the rise skill.
- **Models:** everything ours over time. The boar is ours (creatures lead). The heroine's and hero's bodies stay. Never Hunyuan3D, free web tools, or real people or others' art. Krea 2 is allowed (US$1M cap).
- **Cinematics:** a cinematic ending in play hands over her exact pose and facing, mid-stride, with the camera easing into play.
- **Animation:** natural, correct motion; be sceptical; sign off per clip.
- **The bar:** "we are striving for perfection". Improved isn't enough.

## 10 October 2026, early morning: wound down by the owner after a usage stop. Restart here

The four wave-1 successors ran about three hours, then the weekly limit stopped them; the owner switched to usage credit, then asked for a wind-down. **Nothing is merged into integration: no area has passed its judge.** Each lead stopped cleanly with a "Paused here; next:" block at the top of its handoff **on its own branch** (the integration copy of the handoff is older). Restart each as a fresh successor (`su-lead-high`, max judges in the foreground): merge its branch first, read the block, pick up.
- **Scratch:** the leads' scratch is in this coordinator's session scratchpad (`C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\`, about 11 GB, mostly outfit renders). Verdicts, crops and every script and text file are backed up to `C:\Users\munch\Desktop\survivorsunchained_inputs\scratch_181eef02\` (same layout). Judge verdicts: `judge_ey2`, `judge_br2`, `judge_hr2` (face), `judge_helpers` (animation), `judge_c10` to `judge_c13b` (rendering).
- **Disk:** C: is 95% full (50 GB free). Keep renders lean.
- **Process (new):** background runners' and judges' reports reach the coordinator, not the lead; leads run them in the foreground when the next step depends on them (coordinator.md, Procedures).

1. **Face** (`worktree-agent-a2d632df7c7f21ec0` @ adf52ba6, built art committed, unjudged; GPU): round-2 fix pass applied (eyes, swatches, lashes lit, brows, hair). **The owner's neck note is found and fixed** (the face lay painted the portraits' shadowed necks onto hers; `under_jaw` cut and `heroine_jaw_cut.py` on all ten heads); residuals: a faint seam step, a stepped edge under the ear (own, Highborn), a crease under the chin (Moonlit, Saffron), Sunborn's neck redder. Next: measure f4, one fresh judge (neck at 1:1 on the checklist), iterate, `dotnet test`, then the GPU re-lay of the ten paints. Open: a magenta cast on dark irises (root cause unknown); lashes unlit on the plain "hash" hair path (rendering's).
2. **Outfits** (`worktree-agent-a5ca10091b08dc429` @ 1420ac8b; built art uncommitted in the worktree): every rim bound but a 1 mm choker loop; g2 judged **FAIL** (keep gussets and bindings): skin through the ranger's pant leg and corset in chain_haul/chain_strike, a skin bump at the gusset-to-string junction (warden, reaver), cup and band slits from wip2's tucks, the warden pauldron corners knotting. Next: a max solver on tucked skin in motion (rule out a rig fold first), the binding sweep, tailoring. **The owner's taste answers (OWNER_NOTES, 10 October):** less nipple poke-through on the arcanist and ranger, equal both sides; improve the reaver's, ranger's and arcanist's boots. Also yours: the ranger's right knee piece (24 mm through at knee 90), and **a body-mesh defect** animation found: a doubled, reversed triangle at the left armpit (~0.156, 1.434, -0.022) and non-manifold fans under the left breast and at the pelvis back. A new worktree needs `dotnet build` in `godot/` after setup, or Godot renders blank.
3. **Animation** (`worktree-agent-af8dbda3195e438e4` @ eb8bba10; built art uncommitted): the helper bones failed narrowly twice (a big gain; defects: the knee crease tick, the arcanist sleeve/glove line, a round elbow end, the armpit speck, which is the mesh defect above). A crease-side pivot and crease cut is built, unjudged (the tick back to the old body's level). Next: elbow and knee sheets framed on the joint, a fresh judge; if it passes, helpers on by default, then tell the coordinator so outfits rebuilds. Head carry through one-shots committed, not seen in play.
4. **Rendering** (`worktree-agent-a4e0c353e61cca6dc`): @ 38cb3391, 775 green; judged in part): **FSR 2 native for play passed its judges at 1:1 (cycles 10-13)**: no TAA trail behind her, detail 9.6 to 11.7. Hair is drawn "two" by default (opaque core at cover 0.5 writing depth and motion, blended pass over, reactive eraser eased from 0.5); the Look always uses TAA + MSAA 4x and loses its depth of field (hair flicker 0.00%). **Merge it together with face's branch at the start of the next wave** (it changes hair defaults and the Look under face's baselines), then make FSR 2 native play's default. Next: checks against TAA in a 60 fps-capped fight and with wolves on screen; the Look's hair edge (targets in the handoff); ground and leaf fizz under FSR 2; see-through v2 (opaque, an irregular world-fixed edge, roofs lifted whole: today's best cuts a hard circle, the owner's "pedestrian"); face's items for rendering (strap cut at the right ear, neck shadow facets, card order). For face: the atlas darkens with coverage (dark card rims), wide transparent card ends, plank locks, a pale hairline band, lashes an even comb, eye highlights flicker under FSR 2. For combat/creatures: the risen horde moves in lockstep. For UI: the Blessing picker hides the world behind a black page.
Then UI design and UI art, as before.

## 7 October 2026, evening: stopped by the weekly limit (resets 10 October, 10pm Pacific). Restart here

Wave 1 (four `su-lead-max` leads) handed off cleanly; all merged, 775 green, pushed (4a76f9f7). Their successors (`su-lead-high`, max judges) were cut off mid-step by the limit. **Nothing of theirs is merged or verified.** Each one's work-in-progress is committed (code and docs only; built art left in its worktree) and pushed on its own branch. **Restart each from its handoff page (current in integration), then merge its WIP branch first and pick up where it says:**
1. **Face** (`worktree-agent-a6e8e6d0f539943bb`): eye shader and People.cs changes (lashes, resting lid, irises being shot). A max judge's verdict on rendering's c1 hair sheets went to rendering: blended hair is the direction; their side is side-hair mush (DOF, FSR depth), motion vectors and reactive mask, crown card order; ours is colour dilation (pale cheek ribbon, grey lash tips), hairline fine hairs, lock blocks, lashes. The brow pin A/B was shot and with a judge (verdict lost).
2. **Outfits** (`outfits-lead-wip3` @ d01007ab, in worktree agent-a4a8c84f9181d4acb): gussets as skin-tight pieces (2a8981f8): 0 bare at rest, margins 3.9–7.4 mm, unverified; the motion check was running. Rerun it via a runner and judge.
3. **Animation** (`worktree-agent-a8d33b2672b7be905`): the smooth-cut helper build was under way; rebuild and run the garment check (handoff step 1–2).
4. **Rendering** (`worktree-agent-a6a04e32348559b6c`): the reactive-mask eraser (`--hair-erase`, erase shaders, HairDraw, People.Hair, KitLook) is built but untested; the c2 batch ran (its numbers are in the runner's output, tools/scratch/perf8/ if saved). Rerun c2 and judge.
Then UI design and UI art. **Measure** the high-effort leads' token use per judged piece against wave 1 (README "Working lean").

## 6 October 2026, night: wound down (usage low); every lead handed off. Restart here

All merged and pushed. **Every area restarts as a fresh successor from its handoff** (each lead passed about 500k). Brief them to read by section, not whole files (see memory, agent-token-handoffs).
1. **Face** (docs/handoff/face.md, su-lead-high): speckle on her breasts fixed; skin sharper (SSS 0.1). Next: brows re-laid (the code is ready, then a GPU turn), the eyes (a resting lid, irises, lashes), upper lips gathered into one refit, neck grain, then paints and sliders, then hair (blended cards, per rendering).
2. **Body and outfits** (docs/handoff/outfits.md, su-lead-high): the motion check works again, and the true baselines fail in motion on all four outfits. Fixes are written on `outfits-lead-wip` @ 77b9eacc (unbuilt; don't merge until built and checked). Pauldron_l's rim is unbound (the jagged line).
3. **Animation** (docs/handoff/animation.md, su-lead-high): elbows keep 59-70% of their volume (the helpers were folded out of her rig). Twist and helper bones are built but off (`--helpers`, HerJoints.cs); build them, see them at 1:1, then the outfits lead rebuilds and reruns the check. Then the full audit, arms through her body, follow-through, foot locking and a walk cycle in play.
4. **Rendering** (docs/handoff/performance.md, su-lead-high): the blur is Godot's TAA (a 50 px ghost). The leaning is FSR 2 native, sharpening off, no MSAA, but hashed hair crawls under it, so blended hair cards with a depth prepass come first, with the face lead. A pale wedge remains in the see-through behind the Waystation. Crops in docs/team/perf_sheets/.
5. **UI art** (docs/handoff/ui_art.md plus "For UI art" in docs/team/ui_design.md): paint the HUD instrument's real pieces. The coordinator's note: the skill slots still read as grey boxes, and the globes are glossy and generic. **UI design** (docs/handoff/ui_design.md): four fixes built but not shot; then its own Next.
6. **Writer** (paused by the owner; docs/team/story.md "paused here"): "three days", the ledger lie, the road, the two illustrated-cinematic shot scripts, the burial shot list. Then a **storybook (illustrated) cinematics lead** (new, su-lead-max), then a fresh editor for the next draft.
Then, as before: combat (the crowd push), the experience director, arena art, creatures (the boar; inputs in survivorsunchained_inputs/boar), cinematics (the burial), skills VFX, crafting, loot, the male hero.

## Current state by area: wound down 6 October 2026 (usage low); restart here

Integration is green (774 tests) and pushed. **A new coordinator reads docs/handoff/coordinator.md first** (its procedures, merge and context-check scripts in tools/scratch/coordinator/, and the old scratchpad scripts mirrored in tools/scratch/). Every lead below stopped at a clean point with a handoff; start each as a fresh successor from its handoff (the main session checks context on every report and hands off at 500k).

**Restart in this order** (3 to 5 at a time, see README):
1. **The face** (docs/handoff/face.md): v11 merged (b8ab21f9; no refit needed). Tones and irises meet the bar; her eyes and mouth read at play zoom. Short of the bar: grain at the finest scale (0.65, the AA's limit), her lips thinner and paler than her portrait's, the other faces' brows too light, skin a little smooth. Her head carried 8 degrees up in play needs animation's sign-off. Next: v12 to the bar, then face paints and sliders (freckles as a Look control; defaults hers 0.18, Hard-won 0.12, Wildling 0.1, Fey 0.06), then hair (many rounds; the hair "helmet" and pale temples are the hair pass's).
1b. **The heroine's body and outfits** (docs/handoff/outfits.md): until now the main session's own work; from now a lead of its own, spawned as `su-lead-high`, with every taste verdict (sex appeal, tailoring, pixel-perfect coverage) going to a short-lived `su-lead-max` judge. The coordinator still does the mechanical refit after face changes.
2. **Story** (docs/handoff/story.md): Act 1 rewritten in the data (e5d65111). Next: a fresh editor reads the Act 1 draft; the owner picks the love scenes (docs/story/LOVE_SCENES.md, A or B; the writer recommends the lovers' own lines); then Act 2, then Act 3. Voice: docs/voice/RERECORD.md lists Sella's and Rook's re-records; hold Holloway, Brannoc, Maeca, Vonnra, Harlan and the narrator.
3. **Rendering** (docs/handoff/performance.md): her motion judder found and fixed (positions drawn between ticks, bb86717b). Next: merge `perf-seethrough-wip` (the soft see-through, untested), run the A/B batch, choose the AA (expected: keep a temporal AA as the base for hair), exact motion data for her hair.
4. **The owner's HUD notes** (OWNER_NOTES: the HUD as the keystone, Journal and Map in the half panel, tips at full size): UI design and UI art, from their handoffs.
5. Then combat and animation (the crowd push), the experience director, arena art (the Vault's hall, the Roost), creatures (the boar), cinematics, skills VFX, crafting, loot, the male hero.

**Deferred by the owner:** the artists' kit (OWNER_NOTES); legal (paused until submission).

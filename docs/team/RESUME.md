# Where we are: read this after README.md, before your handoff

The one page of what's current. Every lead starts from the latest `claude/vigilant-galileo-l6jqyx`. Merge it first and keep your own workflow; this page says what has changed around you. Updated by the main session, 5 October 2026.

## 14 October, night: coordinator 1cc516bc (running; outfits, animation, face)
- The owner picked **B1 "with style"** (OWNER_NOTES). Styled G1/G2 being built; one judged sheet goes to the owner, on the new body.
- **The one body build** (outfits s25 from 9ed60792): hand pivots on both hands' own skin, back of hand, throat fill (face's judged fix), B1. **F1's builds had NO correctives** (stale game-skeleton dump: no panel_front, stale hand and forearm bones; integration's glb has elbow_point, F1's don't): the final build needs a fresh skeleton dump and gates on the correctives.
- **The Reaver thigh is NOT in the body build.** Knee drive can't hide it (animation 29), and a groin crease can't either: the true gap is 48-84 mm (outfits scratch 1cc516bc `outfits\hip
eed.py`). The fix is garment-side, Reaver only: the belt front and buckle ride up like panel_front, or the belt sits higher. It comes after the body build and the glove sheet. Knee drive stays.
- Animation 29 handed off @ c0e50030 (section 0a; idle_arcanist hip wrist 31-39 deg WIP, hand-on-thigh vs hand-on-hip for the judge). Successor 30 starts when the body build is final.

## 14 October, night: coordinator d7e64ca2 (outfits, animation, face only)
Scratch for every lead this session: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\d7e64ca2-6832-41bd-8851-2fc0175ecc1b\scratchpad\{outfits,anim,face}` (KEEP). Nothing merged yet this session except docs and tools (roster, lastmsg.py).
- **The next body build (outfits; ONE build, after the owner's glove pick):**
  - F1;
  - the hand at mcp 0.48 / p2 0.65: MCP 96.7-105.9 mm from the wrist (`anim\handpivots.json`, weighting in handpivots.md);
  - the thumb MCP 12.4 mm back (the "thumb" entry);
  - the back-of-hand drop moved to the new MCPs (an outfits solver);
  - the left hand's pivots by the same rule on its own skin (`handpivots_left.json`). No mirror re-projection, the coordinator's call: the body is 3.6 mm asymmetric by sculpt;
  - NOT the Reaver panel weights: panel3 found no weight or pivot change passes (`anim\panelweights.md`). Her thigh's top rises to belt height at knee drive, so the thigh shows through the panel and belt at the game camera (sprint f3, sit_log). Fix: (b) less knee drive in run, sprint and sit_log (animation measures it first), else (a) a hip-flexion corrective in this body build (outfits);
  - the Arcanist glove rebuild for the pick.
  Legal on whatever it re-tessellates.
- **Outfits** (s23 a58bbd501930f73d1, worktree agent-a5ca10091b08dc429):
  - The glove sheet: A / B1 white fingerless / B2 black / C bare. Judge gl1 NOT YET (jagged knuckle cut, B1 matte); both fixed, re-judging; then to the owner.
  - After it: the Arcanist chest fix, stockings.
  - The Ranger thigh line is the designed pant seam. The owner may dislike the pant reading as skin in warm light.
- **Animation** (lead 28 a48e0478734b53e88, worktree agent-af8dbda3195e438e4):
  - Relaxed idle hand PASS; re-judge after the build at +5 deg at the knuckles.
  - Reaver panel swing PASS, plus the fall lag (af30daf8).
  - Title seat PASS (f749ec7a; GameFront.Seat on 0.61 / down 0.18).
  - Flare FIX (the flare9 solver).
  - Sword: grip 13.7 mm (WE-01 logged). The tips still hang 2-5 mm on the modelled hand (short P3s; caps of 77 and 87 don't help). Candidates A `anim\grip\sword_fit.json` and B `anim\cap\cap77.json`, judged by eye on the real build.
  - Staff: on the new hand the pads sink 6-8 mm (Godot truth, grip_truth.gd). Refit after the build.
  - fistfit's thumb bug: the thumb sinks 3 mm into the forefinger. The fix is in `anim\thumb\tthumb.py`. Relaxed thumb_in goes to 18.
  - The merge request lands WITH F1 and the body build, repacked once.
- **Face** (s24 a76b8645c3a96d3d5, worktree agent-a2d632df7c7f21ec0):
  - The smile pass: interior judge rounds, cheek variants.
  - heroine.glb (m11) is shared with outfits' build: rebuild on integration, never pick a side.

### Restart order (only outfits, animation, face; classes and Flare VFX stay paused)
1. **Outfits:** a fresh successor 24 in worktree agent-a5ca10091b08dc429 @ 5f6fb567, from docs/handoff/outfits.md "Paused here".
   - Starts with the owner's glove pick (OWNER_NOTES 14 Oct night), then the one body build.
   - Panel3's weights are NOT coming: the Reaver thigh is a body or knee-drive fix. Ask animation's measure of the knee-drive cut first.
2. **Animation:** a fresh lead 29 in worktree agent-af8dbda3195e438e4 @ 5cee3e9a, section 0.
   - Before the body build: the Flare frame-offset check (a runner seeks the packed clip at frames 18-20), the f23-27 pelvis smoothing, and the Reaver knee-drive measurement.
   - After it: the refits and the judges.
3. **Face:** a fresh successor 25 in worktree agent-a2d632df7c7f21ec0 @ 67d38290, from its latest "Start here". The mouth interior is SHIP. The smile seam fix 083f41ab is unjudged and goes to a judge first. The heroine.glb m15 is uncommitted (unjudged art, also in `scratchpadace\seam\m15.glb`). Add the faint throat line in outfits' glove sheet (play row 1).

## 14 October, later: coordinator 34daaf5d (running lean to its 125% grace; the owner's choice)

### Merged
- Animation: the staff in her closed right fist (7e06d70b; re-shot on fresh imports, holds).
- Outfits: the Reaver loincloth (ea6a9417 via 4d552845; Reaver-only legal all 0).
- Team tools: `tools/freshness.py` gate in `turn.py take` (checks the caller's checkout or `--root`), `tools/half.py`; README rules: numeric-pass solvers on su-lead-high, half-size working pictures, scope checks to what changed. RESUME trimmed (old states in RESUME_ARCHIVE.md).

### Merged this session
Staff in fist (7e06d70b), Reaver loincloth (ea6a9417), lips at rest B3-15 on all ten faces (face-lips-rest 6743112e, judge r7 SHIP; 906 tests). Integration head pushed after 4ca5ca29.

### Restart order (the owner: ONLY outfits, animation, face until the beautification is done; classes and Flare VFX paused)
The PC restarted mid-session: every lead's uncommitted work was saved as a "WIP (coordinator, after the PC restart)" commit on its branch. Check it before use. Solvers that were running are gone; check their scratch folders (scratchpad 34daaf5d) and the branch log.
1. **Outfits** (worktree agent-a5ca10091b08dc429 @ 618b674d; docs/handoff/outfits.md latest "Paused here").
   - The body pass F1 (080103ba) is NOT merged yet: hand 11.3%, forearm +50 mm, head +7%, panel_front bone, and the Arcanist shoulder caps with elbow gloves. Hands judged better than shipped. Legal 0 on Warden, Ranger and Reaver; the Arcanist waits for the glove pick.
   - Then: the glove top edge at the elbow bend (a solver was on it; see 5ca11b9f), the glove options sheet (B1 white fingerless, B2 black, C bare) for the owner, the knuckles (MCP 59% of the hand vs about 53%: check against references, then fold into the next body build), the Arcanist chest fix, stockings.
   - Merge F1 together with animation's re-fits, since the clips depend on the rig.
2. **Animation** (agent-af8dbda3195e438e4 @ 40459bb4; handoff section 0). Every clip is rebuilt on the new rig; the tuck re-fit 6d909b35.
   - The sword grip is thinned to 15 mm (b72c551d, WIP, solver sword4).
   - The Flare re-fit on the new rig was running (flare_nr; its flare.py edits are in the WIP commit).
   - The Reaver panel needs a judge.
   - Then the relaxed idle hand, the sword wrist elbow-swivel, daggers, axe and crossbow.
3. **Face** (agent-a2d632df7c7f21ec0 @ 712b6937; successor 23 block).
   - The smile is NOT YET: interior WIP b64a8528 (the grey far-tooth column, too-pink tongue, per-row floors, tooth gaps), then the sculpt-border solver for the stitched upper-lip seam in the smile shapes.
   - Hardwon's 1-px pale tick at the 6x zoom (check at the Look's face zoom).
   - Then hair edges (speckle, the stray strand at +7%).
Stray untracked files in the main checkout: FlareFx.cs, FlareFx.Burns.cs at the root (likely the Flare lead's; left alone).

## 14 October, early: coordinator 1be2d2a9 wound down (three leads at 399k budgets, the owner's one-session trial). Restart here

Scratch to keep: the 1be2d2a9 scratchpad (anim, judge, flare) and 59a43b82's (outfits, cl11).

### Merged
- **Classes:** classes-11@bf5963c7 (1a6f7ae0), all five wave-6a Flares.
- **Outfits:** fin5 on the shipped face (db47b5a6; judge verdict_fin4 MERGE-READY; legal 0 on all four).
  - The owner's "legs stuck together" fix: `_as_skin` gave inner-thigh pieces the other leg's weights (0.91-1.00); AS_SKIN_SIDES.

### Restart order (each from its handoff; worktrees kept)
1. **Outfits:** worktree agent-a5ca10091b08dc429 @ db47b5a6, docs/handoff/outfits.md "Paused here". In order:
   - the glove skin through the Arcanist glove (animation judge j4: hide the hand skin under the glove, fix A);
   - the right glove brown vs the left purple;
   - the Reaver front fringe at sit_log;
   - polish.
   - Warden .bin is 51.9 MB (GitHub warns).
2. **Animation:** worktree agent-af8dbda3195e438e4 @ 21e9c31d, NOT merged. docs/handoff/animation.md section 0.
   - The staff is in her fist: 4eb83530 refit the pocket (FistAtR was 40-65 mm off), and j4 passes the hold. It waits on outfits' glove fix, then a re-judge, re-pack and merge request (74f53e84 pack stale).
   - **Lesson:** the coordinator merged it from an unjudged picture and the owner caught it. Judge "is it visibly inside her closed hand" first.
   - Flare r9 WIP 5bca5171.
   - bull_rush parked at 9b5486fc: it needs a new hand route.
   - Then the grip-fist system for the sword, daggers, axe and crossbow (same seat fault; the sword is the "mangled hilt").
3. **Flare VFX:** worktree agent-af0782e2e3f51bc1f, flare-1, NOT merged. @ b24624ca (tests 905), docs/handoff/flare.md "Paused here". Judge 4 NOT READY: BOOM FAIL (flat cream ball, then a black soot hole), shards FAIL, Return FAIL, ring and day WEAK, 2.5 swings/s at night FAIL; freeze, hold, frost, embers, sync good. First: the birth atlas to a fresh max solver via tools/fxsim/birth.py. Verdict: survivorsunchained_inputs/scratch_1be2d2a9/flare/f6/j4/verdict_j4.txt.
4. **Classes:** the owner's boss rules (OWNER_NOTES 13 Oct evening):
   - Flare boss share: AoE 10-15%, single-target 15-20%.
   - No hidden boss multipliers; retire bossMul, buff boss health instead.
   - A Flare stays the hardest hit.
   - Then phase 7.
5. **Face:** smile pass, then hair edges (docs/handoff/face.md).

## How the team runs now (README has the detail)

- **Tokens and quality, always (the owner, 7 October):** the cheapest route that ends at the same quality, as standing permission. Long-running leads are `su-lead-high`; max effort goes to short-lived `su-lead-max` judges and solvers (story writer and editor stay `su-lead-max` leads). Pass `effort` on every spawn. README "Working lean".

- 3 to 5 leads at once. The rest are paused with their handoffs and resumed in turn.
- Heavy work takes turns (`tools/turn.py`): `gpu` (ComfyUI, TRELLIS, MoGe, one at a time), `blender` (three), `godot` (four), with RAM and VRAM guards. A fair queue: ask again within 90 s to keep your place.
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


Older state (12-13 October and before): `docs/team/RESUME_ARCHIVE.md`. Read it only when a handoff points there.

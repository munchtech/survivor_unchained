# Where we are: read this after README.md, before your handoff

The one page of what's current. Every lead starts from the latest `claude/vigilant-galileo-l6jqyx`. Merge it first and keep your own workflow; this page says what has changed around you. Updated by the main session, 5 October 2026.

## 16 October: coordinator 007ccb1a, project finish line (face only)
- **One lead this stretch: face** (successor 27, in worktree agent-a2d632df7c7f21ec0), until the heroine's beautification is done. Outfits and animation stay paused at their handoffs, so the F1 merge stays HELD; face's merge-ready glb stays uncommitted until F1 lands.
- **The owner's project finish line:** judges at `effort: "xhigh"`; perfect = what the player sees, at 1:1 game-camera frames, never enlarged sheets (README "The finish line"). Face starts by re-checking its open list at 1:1 and closing what doesn't show.

## 14 October, night: coordinator 1847d1a6 wound down (outfits, animation, face only; restart here)
Scratch to KEEP: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1847d1a6-6513-4947-9408-126dd43ed5f8\scratchpad\{outfits,anim,face,judge_*}` (and 1cc516bc's).
- Nothing was merged this session except docs.
- New standing rules:
  - **The finish line** (README "Working lean"): judge critically at the game's own max zoom; marks beyond it are logged, not fixed; 2-3 rounds, then closed as known; a fixed list per area.
  - **Never kill processes by name** (README Safety).
- The owner picked the crossbow pistol grip (OWNER_NOTES).

### The owner's answers
- **ANSWERED: G3, with a louder top** (OWNER_NOTES 14 Oct night: one build with a deeper scallop and thicker cord at the top, judged at the game cameras; if it reads costume-y, G3 as is). Outfits' first job after the merge. Was: B1 (plain) vs G3 (plum-piped scalloped top and knuckle V, ivory satin).
  - Sheets: `outfits\s27\gl3_play_owner.jpg`, `gl3_detail_owner.jpg`. Judge PASS: `gl3_verdict.md`.
  - The coordinator's note: at play zoom G3's style is a quiet 1 px edge. A "louder G3" was offered: a deeper scallop and a thicker cord at the top, no lines on the hand.
  - G3 changes heroine.glb, colour only (the Arcanist tuck, 413 hand vertices). Face rebuilds once more, animation repacks on that commit, and Arcanist legal and the tests re-run.

### Restart order
1. **The F1 merge (coordinator, first).**
   - Outfits' `MERGE REQUEST worktree-agent-a5ca10091b08dc429@dfe686ed`: the final body B1j and the four outfits; legal 0 on all four; 917 tests.
   - It is HELD, to merge together with animation's repack, because integration's clips are built for the old rig.
   - Animation's merge gate: repack on dfe686ed's art, the hip-thumb fix (below), judges, MERGE REQUEST. Then tell face.
2. **Animation** (worktree agent-af8dbda3195e438e4 @ 0ed50202; handoff section 0, lead 33's). Lead 33 already copied dfe686ed's art in, repacked all 87 clips (motion no worse than F0; 930 tests); the hip-thumb gate is DONE (c8e73ef9: the 71 deg was an old clip; the break tuck and Flare reach fixed, need a look). Five sheets in `anim\l33` await ONE max judge (re-shoot the Arcanist rows on G3, add the game close-up and night). Then take outfits' G3 commit, repack once, MERGE REQUEST. Axe wrist cap CLOSED as known (round cap). The owner: chain_strike becomes two-handed (her left hand grips the chain; after the merge). The owner will check the axe swings in play.
   - **Done this session:**
     - the hip hand in the static clips;
     - the sword idle wrist, and the sword attacks off the ulnar limit (16-25 deg at contact);
     - the brim tuck pose and transitions;
     - stop_warden_l;
     - the cast_raise path;
     - the dagger fist (numeric PASS, seated in game) and the throw fist.
   - **Merge gate: in the hip clip, thumb_01_l turns 71 deg into the back of her hand.** That is outfits' "white flap" at the thumb hole, not the glove. Bring it to about 14 deg, with 0 points inside the hand by outfits' `outfits\s27\solve\pen.py`.
   - **Then:**
     - the cast_raise hand judge;
     - the wrist cap on the axe (2 rounds unconverged: park it, or one max solver), the chain, daggers and throw;
     - the viking sword and axe grips (round or thin the assets);
     - the crossbow pistol grip (the owner's pick).
3. **Face** (worktree agent-a2d632df7c7f21ec0 @ 5bdca23b; "Start here", successor 26).
   - **Merge path:** a merge-ready heroine.glb on B1j sits UNCOMMITTED in the worktree (md5 45fe3386; `face\b1j\j_noseal.glb`). After F1 merges: rebuild on merged, `R\cmp.py`, tests, MERGE REQUEST.
   - **Then:**
     - Own's chin dot at open 1.0;
     - the mouth seal's three failed items;
     - the teeth hue (the far lower row reads amber);
     - lip paint round 2 (Saffron's doubled line, the snarl's brown band, flecks);
     - Sunborn's doubled line (confirm whether it's still open);
     - the hair edges.
   - The laugh corner pocket is CLOSED as known.
4. **Outfits** (worktree agent-a5ca10091b08dc429 @ cbc57774; "Paused here", successor 27).
   - After the pick: commit the glove (or keep B1).
   - **Then:**
     - the right thumb, 2 mm off the staff;
     - the Reaver belt;
     - the Arcanist chest;
     - stockings in the glove's ivory and trim;
     - the groin fold;
     - the neck graft corner (Godot shots only);
     - the close-up skin detail. The coordinator's lean: a normal-map detail bake first, so the rig stays frozen; a denser mesh only if the judge says the bake can't read at the close-up.

## 14 October, late: coordinator 1cc516bc wound down (outfits, animation, face only; restart here)
Scratch to KEEP: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1cc516bc-727d-4e77-9f0e-4ed15fbf8ea6\scratchpad\{outfits,anim,face}` (and d7e64ca2's, 34daaf5d's). Nothing merged this session except docs. The owner picked **B1 "with style"** (OWNER_NOTES).

### Restart order (classes and Flare VFX stay paused)
1. **Outfits** (worktree agent-a5ca10091b08dc429 @ f618f3d5, coordinator WIP over handoff 2cb51946; "Paused here; next: (successor 25, 14 Oct, late)" plus the two solver reports below it).
   - **F0 is rig-final** (`outfits\prop\F0\art`; skeleton dump 810d51bf, correctives back: F1 had none). Pivots on both hands, throat fill PASS; back_of_hand OFF (judge FAIL: mesh too coarse; a post-F1 "close-up skin detail" item).
   - **Chest wedge** (geometry: sliver triangles bend the normals): CT2 misses p99 (20-21 vs 18) and adds 5 sharper edges; the coordinator's call: a max judge rules on those by eye. But CT2's GLB has 2 fewer vertices than F0: fix that first (the F0-identity promise to animation), then poke-through on all four, then the judge.
   - **Gloves:** G1 fixed by numbers; G2's laces and knot fixed, its V and bow unjudged. BLOCKER: the biceps pokes 1.3-1.7 mm (visible) through every glove at the elbow crook (brim) and the elbow-tip side (every bent-elbow clip). A tuck can't do it: a max solver on a glove-side fix (`outfits\gs2\m3.py` measures like Godot). Also cast_raise: the right glove drifts 5-8 mm off the forearm at 0.66 s. Small: a white corner under the thumb hole on the hip hand (animation's judge).
   - Then the final build (bones, weights, key deltas identical to F0), legal on all four, the ONE judged glove sheet (G1, G2 if clean, plain B1; its hand closes judge F0's hands too) to the owner, and the F1 MERGE REQUEST with animation's.
   - Then: the Reaver belt (garment-side: the belt front and buckle ride up like panel_front; true gap 48-84 mm, `outfits\hip\need.py`), the Arcanist chest, stockings (match the glove's trim), the groin fold crumple, the neck graft corner (confirm in game shots), close-up skin detail.
2. **Animation** (agent-af8dbda3195e438e4 @ e84896ba; section 0). **MERGE REQUEST e84896ba** waits for outfits' final body build (repack once). Clips rebuilt on F0; staff, sword A, relaxed hand, hand-on-hip (idle_arcanist) all PASS; 930 tests. Open: the first-frame hip-hand clips (break, stops, Flare end), the brim tuck FAIL (fingers rake her cheek), the sword wrist (32 deg sideways, needs 20 or less: the owner's "weird angle"), then daggers, axe, crossbow, viking sword, the other staff clips.
3. **Face** (agent-a2d632df7c7f21ec0 @ e1659c83; "Start here (14 Oct, successor 25 ...)"). Smile seam1, f1, g1 SHIP (unmerged). Open: the laugh corner pocket (3 faces), closed-smile bow dots (5 faces; changes rest, re-judge), own's inner lower lip, Sunborn's doubled line, the jaw-shadow band under the chin for the next judge. heroine.glb (g1 + tongue fix) uncommitted: rebuild on outfits' final body, then MERGE REQUEST.

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

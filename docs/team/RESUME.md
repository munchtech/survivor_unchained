# Where we are: read this after README.md, before your handoff

The one page of what's current. Every lead starts from the latest `claude/vigilant-galileo-l6jqyx`. Merge it first and keep your own workflow; this page says what has changed around you. Updated by the main session, 5 October 2026.

## 14 October, later: coordinator 34daaf5d (running lean to its 125% grace; the owner's choice)

### Merged
- Animation: the staff in her closed right fist (7e06d70b; re-shot on fresh imports, holds).
- Outfits: the Reaver loincloth (ea6a9417 via 4d552845; Reaver-only legal all 0).
- Team tools: `tools/freshness.py` gate in `turn.py take` (checks the caller's checkout or `--root`), `tools/half.py`; README rules: numeric-pass solvers on su-lead-high, half-size working pictures, scope checks to what changed. RESUME trimmed (old states in RESUME_ARCHIVE.md).

### Restart order for the next coordinator
1. **Animation** (successor started 14 Oct by 34daaf5d on the owner's one-time 385k coordinator budget; handed off @ ce9aedbc, worktree agent-af8dbda3195e438e4, docs/handoff/animation.md section 0). Sword grip fist NOT merge-ready: judge j1 failed it at the contact frames (scratchpad 34daaf5d sworderdict_j1.txt): fresh su-lead-high solver, measured AT the contact frames. Brim hand (idle_arcanist_break tuck) bc8a9bbe WIP, waits on outfits' glove choice. Flare r9 WIP; left fist off the shaft at f16-21 (a solver's report may be in the handoff). Reaver panel bone after.
2. **The owner, 14 Oct: the next session runs ONLY outfits, animation and face, "till there done with the beautification".** Outfits and face from their handoffs (filled in at wind-down). Classes and Flare VFX are paused at clean points; don't restart them until the owner says so.

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

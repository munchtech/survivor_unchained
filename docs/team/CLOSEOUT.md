# The closeout (3 November 2026): every area to a closed loop

**The owner, 3 Nov:** the demo reset closed the loops on the demo's path. Do the same for every area that still has loops, so that after the owner's demo run we move on to game development from a clean baseline.

**What "closed loop" means here.** Every open item in every handoff gets exactly one disposition, written down, so no list is left dangling:
- **FINISH-ONCE:** one lead, a fixed short list, round cap 1 (2 for a gate-class bug), one judge at most, merge, worktree removed. Only cheap, clearly-better items with no taste call for the owner.
- **CLOSED AS KNOWN:** the mark stays, with the reason (at the cap, invisible at 1:1, costs more than it reads). It reopens only on an owner note or inside a scheduled pass.
- **SCHEDULED PASS:** it belongs to a named pass in `DEMO_PLAN.md`'s after-the-demo order. The pass has a scope and an exit criterion; it is a project, not a list.
- **OWNER DECIDES:** one batched question with a recommendation and the default if there is no answer.
- **GAME DEV:** new content, not a loop (Act 2, loot, crafting, the bestiary). Starts after the demo is tagged.

**Merges hold until the owner has played demo-rc1** (the tag; the main checkout stays on it). Leads finish and push; the coordinator merges in one batch after the owner's notes, then tags `demo` and starts the Experience pass on the notes.

**Rules that carry over from the demo reset:** finish-once, no later lists; judge once on what varies; scrap what is far behind; every report says "the app can now X"; the cheapest route that ends at the same quality.

## Wave 1 (now, while the owner plays; code and numbers, no GPU, Godot shots only)

| Lead | Worktree | Fixed list | Judge | Est |
|---|---|---|---|---|
| **Classes 22** | classes-22 | (1) the moonweaver full board T3 1.37 / T4 1.45 over the x1.35 band: one medium solver, numbers only (Classes 21 est ~100k, 1-2 h CPU); (2) the Lamps §14 signatures (`LampBook.PathTo/LightPath/Sleeps/LinkPick/LinkChoices/SetLinkPick/Suggested`, `WickBook.Sum`) so `LampAsk.cs`'s stand-ins and the LampSleep/WickSumView records go; (3) acceptance table rerun; tests | none (numbers) | 0.3M |
| **UI 31** | ui-31 | text and data only, no look changes: the draft-card words ("Your road: Road of the ..." stutter, "at 24 Stones", "a boss's stagger fills", the "Walking The Weave" capital, the title gap) and `docs/SKILLS_DESIGN.md`'s old card words; damage numbers stacking "400!" over "40!"; the won result's "What you take out" emptying ~2 s later; the day loot-label flood and the tutorial popup at +1 s; the tracker's "!"; `dg_keeper_check.py` current; "THE MAP" hint showing despite `--no-banners`; the table's "Tonight's maps" by day and "a tome to write one time in 3" wording (with Experience's words) | one xhigh on the changed screens | 0.5M |
| **VFX 12** | vfx-12 | bugs and sync only: the arcanist staff light (`FindChild("arm:mage_staff")` never matches); Groundbreaker's numbers and flinch on the heave's landing, not the sim tick (~15 frames early); her auto-attack crescent over the Sunder line's base every 4th swing; Road's Toll and One Arrow barely show at the play camera (the owner's standing "every press visible": a visible-mark pass, not a redesign); the Flare's loot delay 4.2 s -> under 1 s (the owner, 29 Oct) | one high on a short clip | 0.4M |
| **Rendering 5** | render-5 | the r2 judge's crowd-under-lamp numbers, behind the existing switch, numbers only: lamp on crowd full within 2 m, half by 3.5 m, 10% at 6 m, 0 at 7 m, squared falloff; dead and flat bodies never under 0.6-0.8x their ground; skin >= 3x cloth under the lamp, hair not lifted, warm rim ~0.15 toward her; cool top fill -50%; crowd within 1.5 m ~25% under her. A runner measures the lit floors and perf (ABAB p99 within noise) | none; the owner sees it in play | 0.2M |

## Wave 2 (as wave 1 slots free; one judge each)

| Lead | Worktree | Fixed list | Judge | Est |
|---|---|---|---|---|
| **Animation 62** | anim-62 | (1) restage `idle_warden_town`'s hand-on-hip elbow per `body.md` Body 20's (A) spec (elbow 20-30 deg behind her side plane, flexion 85-100, wrist neutral): the cheap close of the arm item; (2) death and lunge fall directions, corpses sinking, frozen walkers (every night); (3) the Long Cut f0 entry pop (a 3-4 frame blend into the coil) | one xhigh, whole-frame gate | 0.5M |
| **Env 25** | env-25 | (1) the Deep Shaw grade crushing canopy shade to near-black (~20% of frame; the arena rule is at most a fifth flat black): a grade or fill fix, measured with `black.py`; (2) rooftops covering her at the town camera (`b_path_36`: an occlusion fade or a camera clamp); (3) road puddles reading as slabs at Verge day, one round only | one xhigh | 0.5M |
| **Cinematics 12** | cine-12 | (1) his lines labelled "THE FORD-WARDEN" before his s11 reveal (data: "A VOICE IN THE WATER"); (2) the s6 title card running into s8 (clear of her head); (3) C04 A0 (the lamp placed) and A8b (the letter's ink) one round each; (4) the drowned woman lifting a dead lamp at the ford, owed by Story 13, staged in Prologue.cs if it is one cue | one xhigh on the changed shots only | 0.4M |

## After the owner's demo notes

**SUPERSEDED (3 Nov, evening): the owner played demo-rc1 and it doesn't hook.** The passes 1-7 below do not start in this order; `DEMO_PLAN.md` "Phase 3 verdict" replaces them with the hook passes H1-H5 (combat teeth, one look, sound, seams, her arm route D). Experience 13's and Performance 4's items fold into H4; passes 1-5 fold into H2 under the look bible; 6-7 stay game dev. The dispositions above (finish-once, closed as known, owner decides) stand.

| Lead | Fixed list |
|---|---|
| **Experience 13** | the owner's Phase 3 notes (gate class) plus the open experience items: the "way out is open" banner leading its line and arrow by 1.6 s; what leaving takes at the ring; the Great Blessing shown over the entry black before she has seen the place; day 1's clock waiting on Rook; the tier-1 stakes call (the autopilot never fell under 93% life: the owner's feel decides); the first table night 30 min before its boss |
| **Performance 4** | after the owner is done playing (a measurement must not share the PC): a baseline of the demo loop at 1080p on demo-rc1 (title, town, Deep Shaw T1 night with the horde, C01-C04, SB00): p50/p99, worst hitches, VRAM; fix only what is over budget; the FSR 2 history reset on camera cuts. The old perf list (LOD blob, moonlight pass, fur r2, detail_blur, see-through v2, bush alpha steps, `--hair-draw`/`--coverage`) is CLOSED AS KNOWN unless the baseline names it |

Then `DEMO_PLAN.md`'s order, as passes with scope and an exit (one line each, the briefs come when they start):
1. **Her at the game cameras** (face, hair, skin, body, outfits, motion; Face 48-49's later lists, Body 18-22's, outfits' strap trims, cup colour, reaver cord kinks, crown and braid in lit close-ups, the skin defaults under cool keys, her own rim over the ring). Exit: one whole-frame max judge at the Look, the close-up and the play camera, bare and in each kit. The arm: see OWNER DECIDES.
2. **The HUD's soul** (the hand repaint, glass on the buff icons, the ward glyph, seat fills, glyph relief, the draft cards' look, the Lamps screen's beauty list incl. the first-open hitch and the Sunder/Oathblade shared glyph).
3. **The Ford-Warden at boss tier** (`warden_boss.md`'s ten, beard regenerated not patched; then the C02/C03 framing routes and the Warden placeholder's cinematic marks).
4. **The Warden's identity** (slab rock material, a dust wall that reads, Rebuke's flare and shimmer; auto-attacks "effortlessly badass": the sweep's weight, the Disc's speed) and then the other three callings.
5. **Painted-realism remakes** (art_style round 2's list: setts, iron, amber lantern, firs, camp floor; the Ford's far treeline and camp dressing; Barrow and Ruts to grade).
6. **SB00 p6** (the pan to the lake: a hard cut or a new plate, not a third patch) and the narrator's real takes (the owner's ElevenLabs route).
7. **The named NPC packages** (the other 11), then **Act 2** (the writer from `story.md` "Next for a writer"; `story/act2` is superseded by the WTF pass and the no-romance rule: start from the treatment, not that branch).

## Closed as known (recorded here; reopened only by an owner note or inside its pass)

- **Body/Armor:** the arm (bend, shoulder, armpit) after 4 rounds and ~3.3M: in-team rounds are over (Body 22). The r1-r3 posts and `shoulder_web_post.py` stay unregistered. Armor 18's R1/R2 clips and the owner-angle reshoot: superseded. The reaver tuck map (396/523 points off any new body) re-keys only if a new arm ships. The lower-belly "dirt" lines and the left-shoulder crease: pass 1.
- **Environment:** the canopy-fade later list (wipe band in metres, fade timings, day caps, stumps, the round-3 flake cause) and the single-tree old fade.
- **Rendering:** the night crowd starburst (switch on, net gain). The C02 blue grade flattening him and the SSS/bloom lines: pass 1 and pass 3.
- **Skills:** heave and aftershock clay blocks by day, barrier harmless, Sunder base thin at night, day dust under #8C7558, Sunder jets 1.34-1.41x: pass 4. Per-cast perf spikes: Performance 4's baseline.
- **Flare:** the judge 6/7 money-shot notes and the stand-ins for the seven other Flares: the next Flare build (game dev).
- **Animation:** the Long Cut hold's breath beat (0.5 px at the play camera); the reaver walk toes, the reaver run's jog, the warden walk's stiff arms: pass 1.
- **Cinematics:** camp pack, saddlebags and bedroll rumple at the play camera: pass 5. C02 s4 stays cut.
- **Storybook:** the eight marks closed at the cap (hood, halos, ladder reflection, jug, p3 grain, runes, doorway band, slab).
- **Classes:** Act 1's never-pressing cells (dig, hollow, roost, vault): pacing, the owner's feel in Phase 3.
- **Performance's old branch** (11 Oct, LOD art unjudged): retired; the baseline starts fresh.

## Owner decides (one answer each; the default runs if there is none)

1. **Her arm.** Routes: (A) restage the town idle so the bend is never seen side-on (Animation 62, in this wave); (C) an outside character artist on `docs/design/ARM_SCULPT_ARTIST_BRIEF.md` (work for hire; you said no once); (D) a new source arm through the Meshy-generator / Marionette-fixer route inside pass 1. **DECIDED by the owner, 3 Nov: A now (Animation 62), D in pass 1, no C.** (Body 22's outside-artist brief stays on disk, unused.)
2. **The Warden skill design pass** (slab rock, dust wall, Rebuke, auto-attack weight; VFX 11 left it as "the owner's call"). **Default: pass 4, after the HUD.**
3. **Stale branches, safe to delete** (all superseded by merged work): `classes-12`, `ui-11`, `anim-staff-pack-1`, `outfits-lead-wip`, `outfits-lead-wip2`, `claude/creatures-boar`, `story/act2`, and nine `worktree-agent-*`. **Default: left alone (they cost nothing); say "delete them" and they go.**
4. **Narrator takes and the SB00 bed:** yours (ElevenLabs, the hymn). No default.

## Game dev (after the tag; not loops)

Combat's not-started brief items (armour at depth, the Hollow's fourth beat, the Kerchiefs at tier 3, the Lamplings, the bestiary, the cinematics hooks), the toll's data presence (`TOLL_SPEC.md`), loot (`LOOT_DESIGN.md` then rules then content), crafting, the next Flare build, Act 2 and 3, the male hero (his model replaced first), the Wayfinder's atlas, legal's lawyer brief (the owner's track).

## Hygiene done this session

- `armor-7` merged (Body 21-22's handoff and unregistered scripts, 6 files) and its worktree removed; `docs/handoff/body.md` is current at Body 22 ("closed in-team; the route is the owner's").
- `tools/scratch/coordinator/wt_new.ps1`: a lead's worktree in one command (branch from integration, own assets junction, import cache seeded, cap checked). The app can now make a safe worktree without the junction DANGER.
- Scratch: `Temp\claude` at 6.1 GB; the handoff inventory this plan was built from is in `survivorsunchained_inputs\scratch_closeout\inventory.md`.

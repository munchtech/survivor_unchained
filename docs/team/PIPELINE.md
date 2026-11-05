# The pipeline plan (4 November 2026): planned, not soup

**The owner, 4 Nov:** "our goal of a pipeline is..not working. everything we try to add needs a TON of revision and work and I don't see much improvement ... plan a more conscious way of doing that with everything PLANNED instead of hacked together soup."

## Why revision explodes (the honest diagnosis)

1. **We patch downstream of bad sources.** Her body is a decimated sculpt with no edge loops; six post scripts (arm_contour, arm_sculpt, arm_carve, elbow_psd, arm_anatomy, shoulder_web) were stacked on it, none registered, and about 3.3M tokens later the arm still fails at 1:1. The armor's tuck maps are keyed to her vertex ids, so any change to her breaks every piece. A fix at the wrong stage is a fix forever.
2. **No stage has a contract.** Each asset goes source to game in one hand-built hop, and the only check is a judge looking at the end. So a judge's notes become the next lead's list, and the list never ends.
3. **Every asset is the first asset.** Nothing measures whether the second NPC, the second outfit, the second arena cost less than the first. They didn't, and nobody could see it.
4. **Fixes don't flow back.** A hand fix on an instance stays on the instance; the next instance has the same fault.

## The rule from now

**Every asset class has one source, one build command, one check command, and a game output. A revision is a change to the source or to a build step, followed by a rebuild. Nothing is hand-fixed on an output.** If a source cannot reach the bar through its build, the source is replaced (scrap-far-behind), never patched. Every lead's report names the pipeline it used and the cost of the asset through it, so the owner can see the second one get cheaper.

Each pipeline below has: source, stages, the check at each stage, the state today, and what to build. State is one of **BUILT** (source, build, check all exist and are used), **HALF** (exists, but hand steps or missing checks), **SOUP** (patches on outputs).

## The pipelines

| # | Pipeline | Source | Build (one command) | Check (one command, numbers) | State | To build |
|---|---|---|---|---|---|---|
| P1 | **Her** (body, face, rig) | her approved forms (the current sculpt, as a bake source only) + the shared quad base topology (the MakeHuman CC0 base Marionette uses) | wrap the base to her forms, bake normal and skin maps, rig on the base rig, weights and correctives (elbow, shoulder, knee), LODs, export one heroine.glb | joint-bend strips at 90 and 135 degrees measured against reference outlines; silhouette diff at the Look and close-up within 3 px; triangle budget per tier; the face unchanged at the Look | **SOUP** | **STARTED 4 Nov** (`docs/team/hook/P1_her_base.md`, worktree body-p1): our own slider base (the CC0 quad topology, one rig with correctives, our blend-target catalogue, build + check commands) and her as its first body; the owner's bare-shape gate before anything downstream. The owner: "if we need to build our own makehuman type bodies with sliders we should right?" Yes. **4 Nov evening, the owner: "if AAA build their own, shouldn't we?" Yes: P1 builds OUR OWN base topology as a build step from a loop-plan spec (density per camera tier, UVs by paintable region matching L1's texture authoring, placed for the ~125-joint skeleton); MakeHuman is only the CC0 shape and proportion reference it retopologizes over; her 114 face keys wrapped once onto the new face loops; +0.3-0.5M inside P1; the A|B gate unchanged. Remake over patch everywhere (the owner: "if they need to be redone so be it").**  **P1 ledger (4 Nov night, via 5b4265e7):** our topology from `tools/body/loopplan.json` (generated once on a reference body, then a fixed vertex order for every slider body and NPC, which P2's fit needs); hands and feet from templates converted to our own source files in v1; her approved head topology KEPT for the gate (a face retopo is its own ~0.3M item only if L1's Stage C cel judge breaks the terminator across the face loops); the neck ring designed into the loop plan to match the head one-to-one. Derivation audit: three inherited things undone (A's +7% Head bone scale baked into the rest shape; head weights re-derived by our rule; weights, sliders and landmarks re-keyed off MakeHuman vertex ids onto our topology). Cost estimate ~2.0-2.3M total (own topology ~0.6-0.9M). Bends on hm08: elbow 90 passing, elbow 135 open, knee/hip/shoulder next. |
| P2 | **Gear** (smart slot parts) | a piece modeled on the base topology's slot shell | auto-fit to her (and any NPC on the base), tuck and tier data, dye, export | fit at play and close-up (no clipping across the animation set, automated), every slot shows, cost per piece | HALF (fits her current vertex ids) | rebuild the fit on the base topology after P1, so one fit serves her and every NPC |
| P3 | **NPCs and creatures** | Meshy generation from a judged concept | Marionette fixer: clean, painterly repaint, wrap to the base, rig on the base rig, export | the same bend strips as P1; judged once at the dialogue camera (NPCs) or the play camera (creatures); cost per NPC | HALF (each NPC hand-finished) | the fixer as app tools on the base (Marionette's current pass); the Ford-Warden remake runs through it as the proof |
| P4 | **Animation** | clips on the base rig | retarget, foot lock, pack | contact and foot-lock numbers; the motion judge on the whole-frame question | BUILT, fragile (every rig change breaks it) | after P1 the rig is shared and stops moving |
| P5 | **World and arenas** | the kit, presets (atmospheres, grade), `boards.json`, `zone_resets.json` | zone build, paint_tex presets at one brush scale, lamps and pools | `frames.py` + `palette.py` against the look bible's numbers; the board's lanes and chokepoints measured | HALF | the arena floor (R2b) through paint_tex as a preset, never a hand paint |
| P6 | **Combat content** | `teeth.json`, `telegraphs.json`, `boards.json`, `Enemies.cs`, the director | data | the harness bots (standing, idler, kiter, human, careless, deft) and `danger.py` | BUILT (H1, H6) | H6 adds the idler gate; every new foe or tier is data plus a harness run |
| P7 | **Skills and Flares** | `Palette.Of(school)`, the telegraph kit, the Flare family (H7) | data | the marked-vs-hit test, frame time, the clip judge | HALF (H7 building the family) | after H7 a new Flare is data on the family |
| P8 | **Sound** | `sounds.json` + the gen tool (ElevenLabs) | generate, mix to -20 LUFS | LUFS numbers, the listening sheet | BUILT (H3) | music as its own pass on the same bank |
| P9 | **Cinematics** | cue data per film, the cut rule (`GameSeam.cs`) | play | `cut_check.py` on every hand-back | BUILT (H4) | nothing; new films are data |
| P10 | **Storybook** | plates (Krea or ChatGPT) + `ink_recarve.py` | compose | bible swatches | BUILT | nothing |
| P11 | **UI** | `Style.cs` + bible rule 8 (one screen language) | screens | a judge on the screens; no numbers yet | SOUP (every screen its own look: "vibe coded") | R9: one language as data in Style.cs, screens built from it, after the style answer |
| P12 | **The look** (gate for all) | `LOOK_BIBLE.md` | `frames.py shoot` | `palette.py` + one judge on "the same game?" | BUILT (H2) | the cel test if the owner asks for it |

## How a lead works from now

1. Name the pipeline before touching anything. If the asset's pipeline is SOUP, the first task is the pipeline, not the asset.
2. Change the source or the build step; rebuild; run the check; then one judge on what the check can't measure. A judge's note goes back to the source or the build, never to a patch on the output.
3. The report says: "P<n>: the app can now X; this asset cost Y; the next of its kind costs about Z."
4. **Derivation (the owner, 4 Nov evening: "was the skeleton built around hacked together mesh and vice versa back and forth? that is a concern you know? for a lot of our stuff. we have a direction and stuff but we got there haphazardly."):** each part of a pipeline states what it was derived FROM, one of (a) the game's need, (b) a reference (named), or (c) inherited (named: the file, the lead, the date). Anything found to be designed around an old hack is undone and reported, never kept. Every brief carries this rule. For L1 especially: the cel shading model, the material library and the lighting rigs are built from the references and the game's cameras, never fitted to today's maps or scenes; the frames get rebuilt to the blocks, not the blocks bent to the frames. (P1's skeleton verified by 5b4265e7: a spec placed by landmarks; only the core bone names inherited.)
5. This page is the ledger. The coordinator updates the state column and the last cost at every merge, so the owner can see which pipelines got cheaper and which did not.

## The order

1. **P1, her rig-first rebuild** (3-5M, GPU turns, the 23 Oct bare-shape gate at the owner's angle). It replaces H5 (the arm) and runs before R10 (her painted surfaces), so the paint pass runs once on the new mesh. It is independent of H6, H7 and H8.
2. **P2 on the base** right after P1, then **P3** with the Ford-Warden remake as its proof.
3. P11 and P5's floor after the owner's style answer; P6-P10 as they are.

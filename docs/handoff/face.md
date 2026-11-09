# Handoff: the heroine's face, hair and creation's Look

Read `docs/team/README.md` ("Working lean", "Safety"), `RESUME.md`, `OWNER_NOTES.md` (the face's order and bar; "Neck length"), this page, then `docs/team/face.md`. Read by section (grep, then line ranges). Hand off at about 300k.

## Face 49 (1 Nov): COOL-LIGHT SKIN, MR READY (face-49); C02 s8 and C03 s8 SHIP (max), C02 s4 stays cut
**The bug:** under a cool key (moon, the Warden's blue-white lantern, the heart) her skin read bronze/beige and pasted in. Cause, measured: the zone's grade re-saturates weakly coloured pixels, so cool-lit skin went back to its warm hue (`--grade-off`: lit C 2.5 h44; graded C 4.9 h47). Not her rig, not the skin guard.
**What the game can now do:**
- **Cool hold in her skin material** (`heroine_skin.gdshader` `cine_cool` block, set by `People.HerCineCool` from `GameCinemaHer.HerCoolShare`: the cool share of light at her eyes, by night and close): each lamp's light on her keeps 0.3 of its colour (hue and lightness kept, never lavender), the sky light leans to the shade colour, easing to 0.9 on richer paint (lips 2.0x, ear 2.2x her face's chroma; window 1.45-2.0) and the terminator's warm edge; face roughness -0.1 under a cool key. Hair, eyes, gear untouched. The richness value rides in `mouth_f`'s whole part (the shader is at Godot's 32-varying limit). Switches: A = `--cine-her-off cool`; knobs `--cine-her-cool-lit/-amb/-shade-w/-rough/-keep/-win`, `--cine-her-cool-dbg T`. Round 1's screen-space stage (`Atmosphere.SetViewSkinCool`) is off by default: `--cine-her-on gradecool`.
- Shot cues: `skin` cue `rim` (her rig rim x K for the shot); `lamp` cue `light` (share of the orb's glow reaching things as light, `OrbView.LightShare`). Diagnostics: `--cine-rig-mute NAME,..`, `--cine-grade-cue off`, `--cine-dof-q/-shape/-amount`.
**Shot edits (light/grade cleared by main; C03 s8 pose+camera cleared after the owner's 1 Nov neck note):**
- C02 s8: the shot's warm grade cue (shade #3a3226, moonDrop 0.35) replaced by lowford's own night grade (deleting it let s5's grade carry over); the held lantern panes x3.75 (energy 8, halo 0.6, glass 3); `lampkey` shadow size 0.01 -> 0.08 (the "under-eye blot" was her head's own aliased shadow), spec 0.8, from lens [-0.95,-0.8,-1.3] -> [-0.59,-0.8,-0.96] (25 deg toward the lens: took the blue-grey temple patch away).
- C03 s8: camera 3/4 front ~40 deg on the heart's side (pos off [1.38,1.5,-1.8], at [0.19,1.48,0.01], 50 mm, focus her eyes f/8); `head` amount 1.0 -> 0.5 (head stacked over the collarbone: the owner's "neck looks wild" fixed); `skin` cue `sky 0.3, ear 1.0, off key,cool,cap`; heart rigs: spill 7 -> 3 (cone 20), chin 0.6, heartnear #5fa0ff 0.8 no shadow, a warm-neutral `warm` rig #ffe6c7 0.9 to 3.25 s; heart `lamp light 0.15` (back to 1 at 3.25 s). Her close key is placed 2.6 m out at 30 deg up near where she faces, so with her face down it lit her crown: that's why heart-lit shots went black.
- C02 s4: stays CUT (max r2: far; needs a new moon-behind lighting setup, not a restage).
**Tests 1337/0/10 after merging integration e7dcaa03a (C02 s8 frame identical after the merge; C03 s8 differs only off her).** **Judges (max):** r1 all NO medium (grade route dulled hair/trim/lips); r2 all NO (s8 close: temple patch; s4 far; C03 s8 medium: ash); restage judge: C02 s8 SHIP (gate YES), C03 s8 SHIP (3 stills YES; still 3 close: the heart dims to dark glass; optional: a vein emission floor ~60% through s8).
**Later / routed:** Rendering: brick-red SSS line on shoulder tops/clavicles under the straps (C02 s8); inner ear grey-blue in C03 s8; faint bloom halo on forehead/nose edge against dark (C03 s8). Outfits: the frame-right strap's gold trim wavy at its top edge (C02 s8); pauldron plate edges as pale outlines (C03 s8); heart and bra cup the same blue. Hair: crown glossy shell, hard dark hairline strand ends (C03 s8); braid reads tan rope / lilac-grey (C03), a faceted tube (s4). Cinematics: the s6 title card runs into s8 (clear of her head). Skin default's own later list (judge r2): the sky light on her shade side isn't held (a hard hue edge where the key's shadow falls), a lit-chroma floor ~2.5 under saturated cool keys, blush on the same hold as base skin.
**Spend:** solvers 160k, 200k, 133k; judges (max) 135k, 140k, 121k; runner 26k; lead ~200k. About 1.1M; API $0. Scratch backed up to `survivorsunchained_inputs\scratch_face49\` (briefs, shoot.py, measure.py, verdict notes); owner sheet `survivorsunchained_inputs\face49_owner\`.

## Face 48 (29 Oct): HER IN CINEMATIC LIGHT, MR READY (face-48); round cap used, final judge FAIL close (staging), rig KEPT
**What the game can now do (`godot/src/Game/GameCinemaHer.cs`, cinematics only):** when a shot frames her face close (eyes in frame, face >= 90 px per 10 cm or lens within 3 m), the close-up camera's own rig runs on her from the cinematic camera. That means a key from the strongest light at her head (its colour limited on her skin, true on hair and gear), a side light for a second source, a cool fill, a rim plus a hair rim, hair and gear twins at the close view's sheen, a body key, a catchlight light aimed by gaze, a painted catchlight floor of 0.45, eyes-night and the skin guard. Her face light is held to a band, exposure-matched. Shot rigs keep 0.2 on her (catchlights whole). **Face-scale cap:** the lens widens so her face is at most 300 px per 10 cm, and the change is logged. Switches: `--cine-her off` (before), `--cine-her-off <parts>`, `--cine-her-on spec2,kick,shadehue` (built in r4, judged WORSE, off by default), `--cine-her-lights` / `--camlog` logs.
- **Diagnosis:** the shots lit her weakly (35-84% of the close key), cool and frontal, with the moon and ambient at exposure 1.3-1.5 carrying her face flat. That is light, not her asset.
- Before -> r3:
  - C03 s3b: neck vs face hue gap +46 -> +1, lid hue 247 -> 42.
  - C02 s4: cheek hue 15 -> 48, lids 287 -> 51.
- **Judges (max, 3 rounds):**
  - r2: FAIL medium. Keep the rig.
  - r3: FAIL close. C02 s4 and s8 gate YES.
  - r4: FAIL close. The r4 sheen twins, kicker and grade hue lift were WORSE (white cut-out lines, a sallow shade, ginger hair), so they are off by default. aim, catchfloor, front and cap2 were KEPT.
  - Shipped = r3 plus the KEEP parts (r5 frames: C02 lit 72-73, about 3 L under r3, toward the judge's cap of 75; not re-judged).
- **Also in this MR:**
  - **Braid net fixed (0a6cf61c0):** draw order. The plaits are now drawn solid with depth first (`heroine_hair_rope_core.gdshader`); `--rope-core off` restores the old order.
  - **FolkLight off bosses and cinematic cast (b0340c1cc):** a new `PlayerView.CastLayer` (bit 14). The Warden's warm wash at C02 s12 is gone (R-B +6.8 -> -17), and her night play is unchanged.
- **Shared files touched:**
  - GameCloseUp.cs: the CastLayer on its lights, and the grade and skin guard skipped while a cinematic runs.
  - heroine_skin.gdshader and heroine_eye.gdshader: the `cine_spec_split` tag (0 outside cinematics) and the cornea-only eye light.
  - heroine_hair.gdshaderinc: a 4-line block used only by the rope core.
  - Also People.cs, PersonView.cs, PlayerView.cs, GameCinema.cs, GameFront.cs, WorldScene.cs, Atmosphere.cs, ZoneView.cs and HairDraw.cs.
  - Tests 1308/0/10.
- **For Cinematics (re-shoot):**
  - Stage her close like C02 s4 and s8: a 3/4 turn, head and shoulders, the key 50-75 deg off the lens on her near side, a dark textured background, the face no more than about 550 px tall.
  - C01 s3: fill the black foreground void and ease the 90-degree roll.
  - C01 s8: turn her 3/4 to the fire with the glow in frame, or backlight her.
  - C03 s3b: bring the heart into frame or let it rake her from the side, 3/4.
  - C02 s4: dim the white plank top-left by at least 1.5 stops.
- **Later list:**
  - LIGHT:
    - A soft cool diffuse rim on her true silhouette.
    - A sheen cap that scales the sheen rather than clamping it, so it keeps the source's colour.
    - A real 2-4 px cornea catchlight (none measured yet).
    - Shade hue set in the skin material, never in the grade.
    - The cap applied to world light (C03 s3b lit 79).
    - The scene's own colour reaching her as fill.
  - ASSET:
    - A white hair fleck above the far ear (C02 s4/s8, shows at 1:1).
    - The braid tie reads as a striped white-blue band.
    - Strap trims are wavy and doubled (C01 s8, C02 s8): outfits.
    - A cup notch at C01 s3: outfits.
- Scratch backed up to `survivorsunchained_inputs\scratch_61174ebb\face48\` (briefs, shoot.py, measure.py and measure4.py, testcopies, r3 and r5 after frames, the owner sheet sources). The pad `face48\` (1.8 GB of runs) is left for the sweep: Recycle Bin failed non-interactively. Owner sheet (judge-passed r3 frames): `survivorsunchained_inputs\face48_owner\cine_her_AB_half.jpg`.
- **Spend:**
  - Solvers: 185k, 200k, 198k, 198k (light) and 101k (braid).
  - Workers: 61k and 47k.
  - Judges: 128k, 135k and 113k.
  - About 1.37M in all; API $0.


Older blocks: history/face.md (grep by keyword, never read whole).

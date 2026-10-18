# Heroine face, hair and creation's Look: status

Work branch `worktree-agent-a2d632df7c7f21ec0` (face 30: hair round merged 18 October at 49534777; the cinematic skin fixes and the neck MERGE REQUESTED). The face rebuild merged earlier (40e08eb9, integration 6bbf9425). Handoff: `docs/handoff/face.md` ("Start here (face 30)").

## Current state (18 October, face 30: hair round, MERGE REQUESTED)
- **Hair (braid default, ponytail, pixie):** max judge j3 at 1:1 (Look by night and day, town close-up, spins 90 and 360): braid SHIP, ponytail SHIP, pixie CLOSE (the nape edge, closed as known at the round cap).
  - H1, the pale patch behind the ears: the "ear" region in both the scalp tint mask (heroine_features.py) and the hair cap's `_flap` (heroine_hair.py) took in 1 cm of scalp. Both now count only vertices the ear keys move by at least 1/4 of their max (b2918c19, c7b4a84d).
  - Clipping into her back: HairSway stepped before her skeleton modifiers (HerCarriage's lift), so the chain hung 3-9 cm off the hair. It now steps on `SkeletonUpdated` (7d3e4b91). The back's collision is widened toward the shoulder blades and the arm balls padded for fast spins (20a0e2f2; `NOBACKWIDE=1` compares).
  - Ponytail round, not a ribbon (cards face round the bundle, `merge_cards`, `cards(u_by_width)`). The braid tie wraps the braid. The side locks on braid and ponytail were removed (they read as scars). The pixie crown is filled.
  - Closed as known: the pixie's nape is a slightly ragged edge at Look turns 135-180 (noticeable, not obvious). The fix needs a per-style scalp tint, because extending the shared tint below the nape would darken the braid's and ponytail's bare neck. The pixie has strands within 1.7-2.7 mm of her nape crease in bind pose, none over 3 mm. Ponytail spin 360: 0.08-0.42% of strands > 3 mm in, run to run.
- **F1, the mouth at open 0.25 (c04a A5):** CLOSED AS KNOWN, keeping round 3 (21268a1e: an ivory teeth band while barely parted, a shell filling the gaps, the lower lip's lift muted to her lip colour). Judge: clearly better than before, nothing a player would call broken; the teeth read as a plain band, and a grey slab steps against it on her left. The dark molars at 0.6 are unreachable (the game stops at 0.25).
- **H10, F2, F3 (the cinematic close-ups), 18 Oct, xhigh judge SHIP:** two skin fixes. The mouth corners' darkening now applies only as a smile folds them, through a `fold` uniform (the black smudge at c02 s8). A per-lamp sheen cap `spec_cap` 0.2 stops the cheeks clipping white at c02 s8 (afed0723, d648c80b, 5ff65c2b). The Look and the town close-up are unchanged. The rest is lighting, sent to main for the cinematics lead: dead eyes (no light into the sockets: an eye light of about 0.3 on the people layer), c02 s8's blue held lamp (the braid goes beige, the skin greys), c01 s8's blue patch under the eye, c01 s7's unlit back of the head, and c02 s8's mist wisp. Shot-only switches: env CINEDBG, env HAIRSET.
- **The grey neck and jaw shade (OWNER_NOTES "neck discolouration"), 18 Oct, max judge SHIP:** a dark grey-violet blob was painted into the own and Highborn head paints, on the side of the neck under the jaw. It is healed from the paint around it, keeping the grain (6cef3861, tools/scratch/face30/neck/nk_heal.py; also applied to the git-ignored raws in tools/comfy/out/heroes). Logged: own's under-jaw reads neutral-cool against her face tint, because her neck takes the body's tone. The judge advised against warming it.
- **The hair-fit re-check on the new body build (c31c1760), 18 Oct: PASS, no new judge.** Posed, strands > 3 mm into her: braid 0.02-0.03%, ponytail 0.01% at idle, 0.10% at spin 180 and 0.60% at spin 360, pixie 0.10%. Chains clear (ponytail +7.3 mm at 360). Bind pose, the head skin: braid 13 strands > 3 mm (worst 5.7 mm), ponytail 0, pixie 0 (worst 1.7 mm). The "into body" lines of 8-15 mm are measured against the body's neck tube, which is hidden inside the head mesh (a measuring artefact, per the body lead). Its max nape judge r2 PASSED all three styles on this art with frames truly from behind. Raw output: S30\fit\. Note: the Look's `--turn` adds to the Hair section's own turn (CreateLook.SectionTurn: braid -1.75, ponytail -1.4, pixie -0.95 rad), so our "t180" hair frames were near profile.
- **Face 30's list is DONE.** Open for a later list: the pixie nape (needs a per-style scalp tint), own's cool under-jaw (her neck takes the body tone), the cinematic lighting items (with the cinematics lead).

## Earlier state (13 October)
- **Face ship:** every part passed its judges (s1, rj1-rj7). Last item, the turned jaw's orange-brown wedge at the Look, was the skin shader's warm shade tint on her jaw's underside (not the ear map, not the paint); fixed by `shade_thin` 0.75 (rj7 PASS). Residual, not blocking: moonlit and fey's under-jaw a touch deep at 2x (lightness, a later fill pass).
- **Next (owner said yes):** the smile pass (upper teeth, mouth interior, open-smile corner wedges, the at-rest lip fix for five faces carried into the smile shapes; the soft version ships unless the new one clearly wins). Then hair: hard pale scalp edge at the hairline, pale scalp slivers above the ear, strands reading as cracks over the ear and scratches across the cheek, the review tool rendering her bald.

## Key decisions (why)
- Her chin is raised 12 degrees at the Look: the idle bowed her head, and from above her lower face read short.
- The warm shade tint stays (it keeps her shade from the night sky's blue) but thins where she faces down: a cap on its saturation took the fill's warmth from the front view too.
- Lip WIP (sculpt, recolour) stays off the ship: the owner turned down fuller lips; the smile pass revisits the five faces.

## Notes for other areas
- **Everyone (from face/ship):** her head and skin shader carry new uniforms (key/soft/edge/sky tone, shade tint and `shade_thin`, ear shade map, teeth `seep`); `body_lift` and her head's tones apply only under the Look's rig (`People.HerLookRig`), so play and cinematics keep integration's face tones. Picture switches: `--head-rig off`, `--ear-ao off`, `--skin-set PART:uniform=v`.
- **Animation:** the greatsword pommel at the close-up camera and the cinematic hand on the hilt are yours (coordinator). The review tool renders her bald on the face branch (face fixes it in the hair round).
- **Body/outfits:** the faceted chest in the cinematic close is yours.

## Big expressions (open 0.6+, laugh, snarl, pucker): fix when a scene first uses them
Closed as known (face 28, 17 October, the coordinator agreed). No screen or scene shows them yet. The Look has no expression preview, and HerFaceLife drives only blinks and lids. The cinematics' face cues go no higher than mouth_open 0.25, smile 0.15 and frown 0.2. Measured: at that range, on every face and at the jaw and mouth sliders' ends, no lower tooth or gum point comes within 1 mm of her chin skin. The lead of the first scene that opens her mouth wider (shouts, love scenes) picks these up, judged at that scene's camera at 1:1:
1. Own's chin dot at open 1.0: the lower gum's front 0.85 mm through her chin.
2. The back lower teeth read mustard or khaki (open 0.6, laugh).
3. A throat crescent under the chin as the jaw opens (worst on Saffron).
4. A chocolate band on the inner lower lip (Saffron and Sunborn; faint on fair skin) at snarl, laugh and open.
5. Hard-won's snarl teeth read as a grille in the night close-up.
6. Dirty corners at laugh 0.8.
7. Bright broken lower-teeth dashes at open 1.0.
8. A grey cheek streak from the corner at open 1.0 (own, Fey).
9. A chalky rim on own's upper lip at pucker.
- **Verdict and sheets** (1:1, 16 Oct): `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\007ccb1a-862a-405f-908e-2b7c3e433488\scratchpad\f27\j1\verdict.md`. The shoot script is `..\f27\tri.ps1`.
- **Item 1's start:** `gum_low()` in `tools/assets/heroine_mouth_inner.py`, kept but NOT hooked. It pushes the lower teeth and gum back in the teeth's mouth_open key, to keep 2 mm behind her chin. It also scales the mouth_height slider's teeth key by how far her skin follows the slider at each height. Run it alone with `gum_low_file(glb, out)` (about 90 s). The unjudged build is `..\f27\chin\g1.glb` (on the pre-G3 body), with its log in `dbg.txt`. Caution: its push reaches 7.6 mm at open 1.0, driven by the mouth_height Low slider (Sunborn, own). It applies to every face, so the front teeth may look sunk. Judge that before hooking it, or move the Low case into a corrective key.
- Also closed: hooking `heroine_mouth_seal.py`, since nothing it fixes shows at 1:1.

## Later: long and bob (deferred 18 Oct by the owner)

The owner, 18 Oct: "Yes: ship braid, ponytail and pixie, braid is her default, and long and bob leave the creation menu until they're rebuilt."

They come back with a rebuild or with Marionette's hair-card library. Their art and gltfs are kept on disk (and all of long's physics, HairSway's `Style == "long"` branch); they are only out of her `cuts` in `looks.json` and `People.HerHairs`. An old save or arg with "long" or "bob" lands on the braid (`Loadouts.HerHair`). The judge's items for them (verdict sections A and B):
- Long and bob read as a painted slab or helmet: one even copper, a lighter horizontal band across the back, a ragged crown, hard dark tips.
- Long moves as flat sheets (sprint frame, across #5), with a hard jagged top edge.
- Long is stiff with no trail while she runs (across #2); the spin frames match rest.
- Bob's front strands float off the head, and one hangs across the eye (spin #4), with a pale gap between front cards.
- Bob's forehead strand is a hook that reads as a drawn line (turns 0 and 45).
- Measured: the bob's main cards stand a median 15.6 mm off the face; the "glued" read is the fine layer at 1.6 mm (`tools/scratch/face29/facegap.py`).

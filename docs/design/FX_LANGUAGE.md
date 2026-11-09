# The FX language: how a skill is drawn in painted cel (L1 lead 6, 9 Nov)

For the skills lead (P7) and every later skill or Flare. The law is `LOOK_BIBLE.md` rule 13 (one family per school, hard graphic shapes in two or three stepped bands, a soft outer glow, painted sparks) and the owner's 8 Nov ask, "visually stunning cel shading painterly with vibrant colors": **a skill or a Flare is the most saturated thing in the frame, day and night.** Timing and layering come from `SKILL_VFX_STUDY.md` §2 (the owner's eleven references, measured); a Flare's own grammar stays in `FLARE_LOOK.md`. The data is `godot/data/look/fx_language.json`; the target is the G1 board MB5 (`survivorsunchained_inputs\look_l1\a2\r2\MB5_fire.png`: the stepped campfire, the fire bolt, the frost burst, the holy ring).

## 1. Two kinds of pixel: light and matter

- **Light** is the skill's own shape: bands, glow, sparks, glints, trails, afterimages. It is drawn after the grade (`FxAfter.Adopt(g)`), unshaded, from its school's bands (`FxCel.Apply(mat, school, after: true)` on a shader that includes `shaders/fx_cel.gdshaderinc` and calls `fx_cel(heat, along)`, `fx_sparks(...)`, `fx_out(...)`). Its hex is its displayed color on every rig, by day and by night. Its edge and mid bands sit at Oklab C 0.13-0.18. The world's surfaces are at 0.045-0.07 by day and 0.09-0.12 at night, so nothing else in the frame is this saturated. Fire's edge (0.177) is the ceiling.
- **Matter** is what the skill moves or leaves behind: dust, smoke, debris, chunks, slabs, scorch, a crack's broken rim, blood. It is drawn in the frame and lit by the rig, with the cel band and the world's colored shade, in the ground's own palette at the world's chroma. It is the dark bed under the light. Dust and smoke are flat puffs in two values (lit and shade) with hard edges and no ink. Chunks and slabs use the rock class from the material library, so they get the band and their class's ink.
- **Light on the world** is a real light: the pool on the ground and the bodies lit from below. It is an omni in the school's mid hue, wider than the shape, and it lasts 2-3 samples at a hit. By day the sun drowns the pool, so the shape has to carry the read on its own.

## 2. Colors by school (never a palette of a skill's own)

| School | Edge (outer, coolest heat) | Mid | Core (hottest) | State |
|---|---|---|---|---|
| **physical: the steel** | #c7701a amber | #f4b43a gold | #fbf1d8 white-gold | **authored 9 Nov** for the Warden: white edge, gold body, steel sparks #f6d389 (SKILL_VFX_STUDY §5; FLARE_LOOK §1.3 dawn-gold) |
| fire | #cb451e deep red | #fc8923 amber | #ffe496 white-gold | measured on MB5, charted |
| frost | #3373ba | #56a1e9 | #8dd3fc | measured on MB5, charted |
| holy | #916d4b | #c99555 | #fddd84 | measured on MB5, charted |
| storm, nature, arcane, shadow | from `Palette.Of` by the derive rules | | | derived, not yet checked: L1 calibrates a school before its first skill ships (ask via main) |

- **Two hues at most per skill:** its family plus white (the core), or plus one complementary glint. Never a rainbow.
- **The callings:** today every physical skill uses the Warden's steel. The Reaver's (blood-red ember), the Stalker's (steel and poison green) and the Arcanist's (ford-blue and ember) come later as `authored` entries in `fx_language.json`, written by L1 when their skills start. They are data only.
- **Shape tells siblings apart, not hue:** steel is crescents, streaks and glints with a white leading edge and a tight glow; holy is rings, shafts and stars with a yellow core; fire is tongues and teardrops with rising embers and a wide glow.

## 3. The ink and effects

- **Light carries no ink.** B5's ink pass is masked by the pre-transparent copy (`InkSnap`). The edge band, the darkest and most saturated band, is the spell's line, stepped hard (`fx_step`, antialiased over one pixel).
- **The world's ink stays under an effect.** Light composites over the inked frame, so a figure's line shows through the glow and the gaps, and only an opaque core band covers it.
- **Matter is inked by its class:** chunks and slabs yes, dust and smoke no.
- **Never** a black outline painted into an effect texture, never an edge made by a gaussian, and no rings, hoops or glyph circles as decoration (CLASSES §3.5's laws, FLARE_LOOK §1.3).

## 4. Cast, travel, hit

Times are in samples of 1/12 s (one sample is 83 ms, five frames at 60 fps).
- **Cast (the press, 0-0.25 s).** Every press shows on the first frame after it: a four-point star glint in the core color on the blade or the hand, for 2-3 frames. The build pulls light into the source: the core band grows while the glow shrinks and darkens for the 2 samples before the release, because the dip is what makes the hit land. Her pose carries the wind-up. Nothing circles her.
- **Travel.** One hard shape pointing along its motion. A crescent tapers to a hot leading edge: the core leads and the edge band trails to a point. A bolt is long and thin (MB5's body is 2.6:1, with a round head, flow-lane tongues, dark gaps and bites; `fx_cel_bolt`). A body moving (a dash or a leap) leaves a ribbon of the edge band that tapers to nothing in 2-3 samples, plus 2-3 flat afterimages in the mid band that step out. Sparks are painted tears along the flow (`fx_sparks`), never soft dots. The shape holds steady with no flicker, and it dies by stepping: holes open and the bands erode core, then mid, then edge. It never just fades its alpha.
- **Hit.** The peak lasts one sample at the contact: a hard star of 4-8 spikes in core, then mid. The struck figure's rim flashes for 2 frames in the mid band, sparks fly off the contact, the ground pool lights, and the first hit only gets 2-3 frames of hitstop. The decay takes 3-4 samples, with the bands stepping down. A scar (crack or scorch) is matter with a glowing heart that cools in steps (core, mid, edge, dark) over 1-4 s.
- **Budget at the hit:** mean luminance at most 1.5x the sample before, at most 3% of pixels above 0.9, at most 4 frames. Only a Flare's column breaks this, and it is the Flare's alone.
- **The vibrance check (a number before the judge):** `python tools/style/fx_measure.py shot <frame.png> X0,Y0,X1,Y1 --bg ...` reports the effect's saturated share (C 0.15 and up). MB5's bolt is 55%; a skill's body reads 40% or more at the play camera.

## 5. The three skills now (sketches; P7's judge rules)

- **Heroic Leap.**
  - The cast is a crouch, a dust kick (matter) and a glint on the blade.
  - In the air, her real shadow on the ground shrinks and then grows (top-down, the shadow is the only proof of height), and a short steel ribbon trails off the blade.
  - The target mark is light on the ground in the steel's mid band: a painted ring stroke with gaps that closes as she falls, at most half opacity, drawn under every danger mark.
  - The landing is a one-sample white-gold star flat on the ground. With it come the crack (matter, its heart cooling through the steel's bands over 1.5 s), a low dust ring rolling out in two values, chunks on gravity, and a gold pool light 1.5x the slam radius. The struck flash their rims and go down.
  - The camera gets 2-3 frames of hitstop and a short punch, never a long shake.
- **Cyclone / Bladestorm.**
  - Two or three steel crescents orbit her at knee height. Each has its core leading, a gold body, and an amber trail that tapers over 90-120 degrees of arc.
  - A low two-value dust swirl turns at her feet.
  - Each tick on a struck foe is a glint, tangential steel sparks and a 2-frame rim. Never a burst on every tick.
  - Her silhouette stays readable: the blades ring outside her body's screen area and cover at most 30% of her at any moment.
  - The two-slot Union is the same family: a bigger ring, more blades, and a gold pool light that moves with her.
- **The charge.** A dust kick at the start, a steel ribbon behind her, 2-3 afterimages in the mid band, and the impact drawn as a hit.

## 6. Known gaps (L1 fills them when P7 asks, via main)

- **After-grade light has no depth from skinned figures.** `FxAfter.Occlude` makes twins for static meshes only, so a blade passing behind her draws over her. The fix is a depth twin bound to her Skeleton3D and Skin.
- **Waiting on their skills:** the physical families for the other callings, and the calibration of storm, nature, arcane and shadow.
- **Day clips:** the bands keep their hex by day, but the pool fades. Each skill's judge sees a day clip as well as a night one.

**Who owns what:** L1 owns the families, the include, `FxAfter` and the calibration. P7 owns each skill's shapes, timing, layers, sound and numbers, and its judge. A skill's data never carries a hand-picked color: a new family or variant goes into `authored` in `fx_language.json` (built by `python tools/style/fx_measure.py build`), by L1.

# H2 step 2: the restyles, from the lock (art director, 3 Nov)

The bible: `docs/design/LOOK_BIBLE.md`. The frames as the owner played demo-rc1 (1c0f11064 + the tools): `survivorsunchained_inputs\look_h2\r0\` (`sheet.jpg`, `frames\`, `palette.jpg`, `palette.md`). Every restyle re-shoots with `python tools/style/frames.py shoot --out ...\look_h2\<round>` (about 12 minutes, one godot turn), measures with `tools/style/palette.py`, and is judged with `frames.py compare r0 <round>` on the question: is this the same game as the other twelve? Restyles, not remakes, except where said.

## The judgement, frame by frame (would it ship in AAA as it stands / is it the same game)
| Frame | Ship? | One game? | What is off the bible |
|---|---|---|---|
| 01 title | no | partly | the camp is flat and photographic; the title preset (`Atmospheres.Front`) has no paint grade at all (gray 41%); the logo and menu fit the HUD's gold |
| 02 SB00 p2 | yes | the key art | nothing: ember gold against indigo in three masses. The other twelve come to it, not it to them |
| 03 C01 s12 | nearly | yes, with 05-06 | the best 3D frame (key 3.2, indigo shade); her skin reads photographic beside what the world becomes |
| 04 Verge day | no | no | flat (key 1.39), olive-mud ground with gravel noise, no value masses, a naturalistic other game |
| 05 Low Ford night | no | partly | the palette is right (shade hue 249, gray 2%, cold 92%) but flat and murky (key 1.77, pool 0.27); noisy ground |
| 06 the Warden | no | partly | the river a glossy blue plane with sparkle; the boss a black blob (placeholder); telegraphs neon cyan vector outlines and labels |
| 07 Waystation day | no | partly | the violet shade is right; the square an empty flat field of setts (key 1.23), no sun-and-shade masses |
| 08 Lamps | no | no | a navy page of thin glowing nodes: a fourth screen language; she stands lit as a photograph |
| 09 Deep Shaw horde | no | no | the worst, and the core loop: brown-black murk (shade hue 66, gray 43%, cold 0%), noise ground, the pack pale gray smears, no pools |
| 10 Pack-Mother | no | no | as 09 (gray 62%); the boss doesn't read at all; a red herringbone telegraph like hazard tape |
| 11 result | no | partly | Style.cs's iron and gold, but floating on black; the night it sums up is gone |
| 12 HUD over play | no | no | the Drowned Girl's photographic bronze is the most realistic, brightest-detailed thing on screen, over a murky world |
| 13 her close-up | nearly, as a realistic game | no | a good warm day frame, but it is the realism the rest leaves; she follows the world's paint, not the reverse |

## The restyles (smallest change that reaches the bible; in the order to run them)
| # | Restyle | Carrier | Frames | Area | Rough cost |
|---|---|---|---|---|---|
| R1 | **The arena night**: its preset takes the play night's paint grade (moon indigo shade, `PaintShadowSkin`), a lower moon key that models the ground, and pools from real sources (the lamps to hold from H1's board, braziers); the crowd's `CrowdRim`/`CrowdFill` on | `logic/Maps/ArenaPlaces.cs` atmospheres, `Atmospheres.cs`, `--grade-try` | 09 10 12 | rendering + arena art (with H1's board) | 0.3M |
| R2 | **The ground, painted**: paint_tex `ground` preset (two or three value masses, gravel noise out) and `--texels-per-m` so one brush everywhere; the arena ground, the Verge and the Low Ford terrain, the title's camp; the grass cards pulled to the palette | `tools/assets/paint_tex.py`, `arena_ground.gdshader`, the terrain materials | 01 04 05 09 10 12 | environment + arena art | 0.6M |
| R3 | **The title**: `Atmospheres.Front` gets the play night's paint grade | one data line | 01 | rendering | 0.05M |
| R4 | **The foes at night**: the VAT crowd shaded as dark forms with a cold rim and her ember's warm side, not pale smears | `vat.gdshaderinc` crowd_fill/crowd_ember, `CrowdRim` | 05 09 10 12 | rendering | 0.3M |
| R5 | **The HUD in the light**: the Drowned Girl's bronze painted (broad bands, ember front, indigo rim, value under the play), the orb's glass `Style.Blood` | `hud_vessel.gdshader`, Dg* pieces, `Style.cs` | all play frames | UI art | 0.4M |
| R6 | **Marks as light**: telegraphs, rings and pins drawn as light on the ground in `Palette.Tele*`, no vector outlines, labels or stripes (H1 is building new telegraphs: one brief for both) | `src/Fx/Palette.cs`, the telegraph decals | 06 10 | VFX with H1 combat | 0.3M |
| R7 | **Painted water**: value bands of the sky, soft moon strokes, the sparkle tamed at the play camera | the water shader (`water_air`) | 06 (03 05) | environment | 0.3M |
| R8 | **The square**: setts with relief and joint dressing, sun-and-shade masses across it | paint_tex `stone`, the setts flags | 07 (13) | environment | 0.4M |
| R9 | **One screen language**: the Lamps page as bronze, parchment and ink (the board an inked map, the lamps lit nodes); the result over the dimmed arena, not black | `LampsScreen.cs`/`LampBoard.cs`, the result screen, `Style.cs` | 08 11 | UI design (+ Lamps) | 0.65M |
| R10 | **Her surfaces** (the owner's answer 2): her maps through paint_tex `skin`, `hair`, `cloth`, `leather`, `iron` at her texel density, the same two lights; forms untouched. After R2 and R8, so she matches the painted world. The owner sees A or B at the close-up first (23 Oct gate) | paint_tex presets, her shaders | 03 08 13 | face + body/outfits | 0.6M |
| R11 | **The Pack-Mother reads**: one silhouette and one color (H1's boss rule) with a rim | her material and scale, `Palette` | 10 | arena art with H1 | 0.2M |
| R12 | **The Ford-Warden: a REMAKE** (boss tier, decided 21 Oct): no restyle gets a black blob to the bar; placeholder until then | warden_boss | 06 | Warden boss | (its own pass) |

**Total before the Warden remake: about 4.1M**, inside DEMO_PLAN's 4-7M for H2 step 2 and H5. Run R1 and R3 first: cheap, and the arena is where the player spends the night. R2 and R4 next (most frames per change), then R5, R6 with H1, R7, R8, R9, and R10 last with the owner's gate. Each restyle passes when its frames pass the bible's numbers and a whole-frame judge says "same game" against r0 and the storybook frame 02.

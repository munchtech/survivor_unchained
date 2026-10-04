# Replacing what isn't ours: the plan

From the audit in `docs/legal/ASSET_PROVENANCE.md` (2026-10-04); the row ids (CR-02, UI-01...) are that file's. The owner's goal is to eventually remove anything not ours, and to sell on Steam with little or no issue.

This plan proposes; the owner decides. Nothing has been removed.

The order is by risk first (anything that can stop a sale or start a dispute), then by how much the player sees it.

Sizes: **S** is a day or less, **M** is days, **L** is a week or more of one lead's time.

Leads are named as in the roster in `docs/team/README.md`:

| Lead | Agent |
|---|---|
| Legal and Steam compliance | aa12c130ddf4b904c |
| Arena art | a52b851395b3ab3f4 |
| Animation | a435f4dd0ac80df75 |
| UI art | a1a394643aabfb169 |
| UI design | a69858664f1d3dd29 |
| Skills look and feel (VFX) | a63cd93fc73d5ed79 |
| Combat | a1d4562f44c7f6feb |
| Voice | a501b387a90d78b4e |
| Story | a73ca9d35d0c487a9 |
| Male hero | ab82cbe99e2937ddd |
| Heroine face | ade92e8285938438f |
| Performance | a7145e18b3eb78294 |

The main session owns heroine outfits and anything with no lead yet.

## Stage 0: answers and compliance (before any art; whatever else happens)

| # | What | Why | Owner | Size |
|---|---|---|---|---|
| 0.1 | The owner answers the seven provenance questions (`ASSET_PROVENANCE.md`, "Questions only the owner can answer"). Above all: what made `234.glb` and from what picture; where the reference sheet came from; what pictures the hero's and older woman's figures came from | Three UNKNOWN bodies and the cameos hang on these answers (PE-05, PE-06, PE-09, UI-05) | Owner, collected by the provenance auditor | S |
| 0.2 | Ship a `licenses/` folder with the build: Godot `LICENSE.txt` and `COPYRIGHT.txt`, .NET `THIRD-PARTY-NOTICES.TXT`, the three `OFL-*.txt`, `CREDITS.md`. Generate the in-game Credits from `CREDITS.md`, with licence links and the CC BY "changes" notes | Notices required by MIT, OFL and CC BY don't ship today (BU-01) | Legal specifies; main session builds it; UI design for the Credits screen | S |
| 0.3 | Exclude unused third-party and dev-only files from the export (list in BU-02), or switch to a resources-only export | Unused CC BY and UNKNOWN files ship today (BU-02) | Main session with the performance lead | S |
| 0.4 | Steam pre-generated AI disclosure: Krea 2 images, LTX effects and sounds, TRELLIS 2 sculpts, Kimodo motion, placeholder voices, and code and dialogue written with Claude | Steam's content survey; Krea §4.3; LTX Attachment A item 5 | Legal | S |
| 0.5 | Ask Krea (opensource@krea.ai) for enterprise terms, and record the answer | The US$1M revenue cap and 30-day termination (AI-01). This sets the deadline for stage 2 | Owner with legal | S |
| 0.6 | Rename Starfall, Moonfire and Fan of Knives. Review Consecration and Whirlwind beside them | The Ember Watch's own Warcraft guard lists them (DA-04) | Story lead with the combat lead | S |
| 0.7 | Keep the source clips and pictures of every AI asset (LTX clips, Krea raws) with their prompts and seeds | LTX §6: provenance must not be stripped from what we hold; the evidence also matters if a claim ever comes | Skills VFX and UI art leads | S |

## Stage 1: blockers (high risk, seen by every player)

| # | Replace | With (what we make, and how) | Owner | Size |
|---|---|---|---|---|
| 1.1 | **The boar** (CR-02): its page restricts commercial use despite the CC BY label | Our own boar, in this order: 1. modelled and sculpted in Blender from our own drawings; 2. retopologised and painted with CC0 materials; 3. rigged to one quadruped skeleton the wolf will share; 4. gait, charge and death keyed with `tools/anim`'s solver. Stop-gap if launch comes first: buy the Fab version and keep the receipt | Arena art (model), animation (rig, clips) | L |
| 1.2 | **The heroine's body** (PE-06), if 0.1 can't show a clean chain | Rebuild her on MakeHuman's CC0 body: `tools/assets/heroes.py` builds it, and `wrap_sculpt.py` shrink-wraps it onto a sculpt, here one we make ourselves to the brief, in Blender. Then refit the four outfits (`heroine_outfits.py`), the hair (`heroine_hair.py`) and the paint, and re-shoot the creation cameos (`creation_portraits.py`, UI-05) | Heroine face lead with the main session | L |
| 1.3 | **The male hero's body** (PE-09), if 0.1 can't show a clean chain | The same route: the MakeHuman man from `heroes.py`, sculpted to his brief. His head is already MakeHuman | Male hero lead | L |
| 1.4 | **Both heroes' Krea face paint and irises** (PE-08) | Skin painted by hand over the CC0 MakeHuman skin (Krita or Substance), or from our own photo shoot with a signed model release; irises drawn procedurally (the guide in `heroine_eyes.py` is already drawn) | Heroine face lead, male hero lead | M |

## Stage 2: Krea 2 everywhere else (high business risk; the interface is on screen all the time)

The deadline is set by 0.5, or by revenue nearing US$1M.

| # | Replace | With | Owner | Size |
|---|---|---|---|---|
| 2.1 | **Interface frames, plates, buttons, slots, cards, medallions, book, logo** (UI-01, 60 files) | Ship the forge and Blender renders without the Krea paint-over: their geometry and light are already ours (`tools/uiforge`, `paintover.py` is the only AI step). Where it needs a painter's hand, commission an illustrator to paint over our renders, with a written assignment of rights | UI art lead, with the UI design lead | M |
| 2.2 | **Colour icons** (UI-02, 117) | `emblems.py` already models each icon as shapes lit by our own matcaps; ship that render without the Krea pass, or commission an icon set | UI art lead | M |
| 2.3 | **Item icons** (UI-03, 48) | Re-photograph our own item models (after 3.1 and 4.1) in the studio light and grade them in code; no paint-over | UI art lead | S |
| 2.4 | **Ground marks** (FX-03, 7 marks) | Procedural decals in code: noise, SDF cracks and runes from the game's own glyph set | Skills VFX lead | S |

## Stage 3: medium risk

| # | Replace | With | Owner | Size |
|---|---|---|---|---|
| 3.1 | **Chevalier Sword and Medieval Shield** (WE-01, WE-10): built on other artists' concept art | Our own sword and shield designed for this world, modelled in Blender with the outfits' CC0 materials and regripped in `Arms.cs`. Alternatively, written permission from Guillem Daudén and Artyom Vlaskin | Main session (no weapons lead yet) | M |
| 3.2 | **LTX flipbooks** (FX-02, 14) | Fire, smoke, frost and bursts simulated in Blender (Mantaflow and particles), rendered on black and cut by the same `flipbook.py`; or fully procedural shaders | Skills VFX lead | L |
| 3.3 | **LTX combat tells** (AU-03, 5 takes) | Recorded (drum, horn, fuse hiss) or synthesised in the game's own synth | Combat lead | S |
| 3.4 | **Voice placeholders** (AU-04, 19 takes) | Per the owner, no placeholders: remove them from the build. Then record finals in ElevenLabs on a paid plan (keeping the plan, invoices and each voice's terms), or with actors under signed releases | Voice lead (paused by the owner) | M |
| 3.5 | **Anime body, refitted Quaternius hair, older woman body** (PE-03, PE-04, PE-05) | Nothing to make: they are dev-only paths. Drop them from the build (0.3), and later from the repo if the owner agrees | Main session | S |

## Stage 4: credited third-party work (low risk, but not ours, and seen)

| # | Replace | With | Owner | Size |
|---|---|---|---|---|
| 4.1 | **The other nine Sketchfab weapons** (WE-02 to WE-09, WE-11) | One coherent arsenal of our own designs (the world's smithing, as the UI's ironwork is), modelled in Blender. Then 2.3 again | Main session (assign a weapons owner) | L |
| 4.2 | **Wolf and lampling** (CR-01, CR-03) | Our own creatures, made as 1.1 (sharing the quadruped skeleton). The lampling deserves an original design | Arena art, animation | L |
| 4.3 | **100STYLE idles** (AN-02) | Keyed (`tools/anim`), or captured from the owner's own phone video through SAM 3D Body (check the SAM licence on outputs first) | Animation lead | M |
| 4.4 | **Mixamo clips** (AN-03: the leap and 10 folk clips) and **Kimodo clips** (AN-04: 10 folk clips) | Keyed, or our own capture as 4.3 | Animation lead | M |

## Stage 5: CC0 work (no legal risk; replace only for "all ours"), most visible first

| # | Replace | With | Owner | Size |
|---|---|---|---|---|
| 5.1 | **Townsfolk bodies and clothes** (PE-01, PE-02) | MakeHuman CC0 bodies in variety (`heroes.py` with folk presets), dressed by our own outfit pipeline | Male hero lead, main session (outfits) | L |
| 5.2 | **Town and nature kits** (EN-01 to EN-03) | Our own modular medieval kit and foliage in Blender (geometry nodes for trees and plants), textured with CC0 or our own scans | Arena art lead | L |
| 5.3 | **KayKit pieces in the zones' landmarks** (EN-04) | Already rebuilt in code (`World/Pieces.cs`): re-export the landmarks without them, then drop the KayKit files | Arena art lead | S |
| 5.4 | **Kenney sprites and sounds; OGA beds** (FX-01, AU-01, AU-02) | Sprites rendered from our Blender simulations (3.2); our own Foley and field recordings, or more of the game's own synthesis | Skills VFX, combat | M |
| 5.5 | **Poly Haven scans and textures; ambientCG** (EN-05, TX-01 to TX-05, TX-07) | Our own photogrammetry and photographed materials, or procedural materials (Material Maker, Blender) | Arena art lead; main session for the outfit fabrics | L |
| 5.6 | **The UAL fallback clips** (AN-01) | They fade out as clips are keyed. Keep the UAL skeleton itself as our rig standard (CC0; replacing it would mean retargeting everything for no legal gain) | Animation lead | — |

## Keeping, by design

These stay, credited:

- Godot and .NET (MIT);
- the three OFL typefaces;
- MakeHuman's CC0 head parts (optional to repaint).

## Never ship

- `tools/make3d` outputs (Hunyuan3D-2: not licensed in the EU, UK or South Korea; WL-04).
- The kmontesdev "fantasy" sounds, until their origin is shown (WL-02).
- Motion of identifiable Pexels performers (WL-03).
- Anything from the `MysticXXX_KREA2_v1` LoRA (AI-15).

New third-party assets go through `public/assets/CREDITS.md` and `ASSET_PROVENANCE.md`, with the source URL and licence, before they land.

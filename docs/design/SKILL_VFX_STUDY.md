# Skill VFX study: what the owner's 11 references teach, and what to build first

Purpose: learn why the owner's 11 skill-VFX videos read as AAA (inspiration only, never copied), hold our game against them, and rank the upgrades worth building. Sources: `survivorsunchained_inputs/vfx_refs/<id>/` (peaks and 1/12 s burst strips) and `survivorsunchained_inputs/vfx7/now/` (our captures). Study of 1 November 2026.

## 1. The references

The old numbers (CLASS_IDENTITY) had the right descriptions on the wrong video ids. Corrected here; the numbers below are used everywhere in this doc.

| # | Video id | What it is | The one thing to take |
|---|---|---|---|
| 1 | AoS3bivvFNQ | "Fighter": gold and white-violet punches, slam, dash, a ground crack | Impact without a screen flash; the gold crack line with dark chunks that dies from the near end out |
| 2 | HTPbHeqstT0 | RIOT character effects: mech beam, teal dome, spectral serpent | The 2-frame smear on a strike; the 1-frame release flash (a warning as much as a lesson) |
| 3 | I9-uYCadJ4g | Blood orb, whip, crystal spikes | One hue can carry a skill if the values run from black to hot; a scar that stands for seconds |
| 4 | NBA2L25WDcw | Lost Ark boss: sun in the sky, fire-lance rain, final beam | The column that leaves heaved slabs with glowing fissures, cooling over 3 s |
| 5 | RKtcNsFTPRg | Bird strike: a swarm, a vortex, a collapse and a burst | Seen from a camera like ours; VFX cast shadows; the scar cools white to gold to red to dark |
| 6 | dyYnofAdxQc | Unity portfolio: falling sword, lotus, tornado, glints | A small icon-clear silhouette top-down; a falling object stretched, then snapped to shape on landing |
| 7 | iXdos0VaPhU | Wave crash (cinematic) | Danger fill growing from its edges; struck bodies keep burning after the blow |
| 8 | vS1v4QjjcJk | 32 elemental fighting-game hits | Each element told by its debris (ink, petals, embers, shards), not by its color |
| 9 | yE5rjDocIAE | Constellation buff: star lines, sky galaxy, light column | Thin lines of light linking points; a column with a soft lit pool at its foot |
| 10 | 5ZQdZOK8hhg | UE5 + Houdini: lightning (strike, chain, bounce, crawl) | Light arrives before shape; a crack decal with height and a hot core; bounce arcs with tangent control |
| 11 | IPAfyFhDJcA | UE5 + Houdini: fire spell (circle, charge, fireball, explosion) | A projectile that lights the floor as it flies; pyro flipbooks split into emissive and non-emissive; a scorch that glows for 4 s |

## 2. What makes them read as AAA

Timings are from the burst strips, sampled at 1/12 s (one sample = 83 ms = 5 game frames at 60 fps). "1 sample" means the peak lasts at most 83 ms. Luminance is the mean of each sampled frame, 0 to 1.

**Shape language.**
- One silhouette per beat, readable in a quarter second: the crescent (1, 11), the line (1's crack, 10's bolt), the column (1, 4, 9), the star glint (1, 6), the falling blade (6).
- Shapes point. Crescents taper to a hot leading edge; bolts and lances are long and thin; burst spikes radiate from the contact point (1, 5, 8).
- Sharp shapes at the impact, soft at the decay: hard-edged spikes and glints for 1 to 2 samples, then billowing smoke and drifting motes (10, 11, 5).
- What fails our rules: 2's teal dome and 4's and 9's stacked glyph rings read as geometry and UI. That is our "no hoops" law, seen from outside.

**Timing.** Anticipation, then a peak of 1 sample, then a long decay.
- Normal hits: 2 to 3 samples of build (0.15 to 0.25 s), 1 sample of peak, 3 to 4 samples of decay (1's punch: peak at 1.20 s, gone by 1.53 s; 6's sword: 2 samples falling, 1 landing, 4+ of petals).
- Ultimates: a long build (5's vortex 12 samples, 1.0 s; 11's charge about 1.5 s), a 2-sample collapse, 1 sample of flash, 3 to 4 of burst, then 1 to 4 s of scar.
- 1's slam dips before it hits: the glow shrinks and darkens for 2 samples (3.03 to 3.12 s), then the column fires for 1 sample. The dip makes the hit.
- Peak to visible decay runs about 1 to 4 for hits and 1 to 12 or more for big spells. Scars last 2 to 4 s (1's crack about 2 s, 5's embers 2.3 s, 4's slabs 3.5 s, 11's scorch 3.9 s and still glowing).
- 10's strike: light first, shape second. The ground goes lavender for 1 sample before the bolt is drawn. Then the bolt holds 3 samples and frays into tendrils.

**Layering.** The full stack, seen whole in 10 and 11: hot core, glow, sparks, smoke (dark), debris chunks, ground decal, distortion, light on the ground. Every big event has at least five of these.
- Smoke is the dark bed under the light (10 at 19.27 s, 11 at 10.07 to 10.23 s). 11 bakes its pyro flipbooks as two maps, emissive and non-emissive, so smoke stays dark and lit by the scene while the fire glows. Burns Twice already works this way; keep it for every new sim.
- Debris sells weight: rock chunks thrown on arcs with gravity (1, 4, 10).

**Color and value.**
- Hot core near white, a saturated mid, dark smoke. Two hues at most: one main hue plus white, or one plus a complementary accent (10: violet bolt, orange fire; 1: gold with cool white-violet glints).
- 3 is one hue (blood red) with no white at all: 0% of pixels above 0.9 in every sample. It still reads, because its values run from black to bright red.
- Low saturation can still read if values are clear: 5 is cream and pale gold on blue-gray.

**Impact frames, measured.** Peak sample against the sample before it:

| Ref | Event | Mean luminance | Pixels above 0.9 | Inside our budget? (1.5x mean, 4 frames, 3%) |
|---|---|---|---|---|
| 1 | punch, slam | 1.2 to 1.25x | 1.4 to 1.6% | Yes |
| 5 | vortex collapse | 1.15x | 3.8% | Nearly |
| 6 | sword lands | 1.4x | 1.6% | Yes |
| 3 | spikes erupt | 1.0x | 0% | Yes |
| 4 | final beam lands | 2.2x | 2.6% | No |
| 11 | fireball hits | 3.3x | 11% | No |
| 2 | mech beam fires | 6x, 1 sample | 7% | No |
| 10 | lightning strike | 16x, 1 sample, then halves each sample | 5% (26% on the big strike) | No |
| 7 | wave whiteout | 2.3x, 4+ samples | 29% | No |

- So the hits that fit our budget sell the impact with a local burst, sparks and a ground light pool, not the whole frame. 1 is the model for her repeated attacks.
- The big spells (2, 10, 11) flash the whole frame. Our Flare may not. It must sell the BOOM by local light: the ground pool, bodies lit, shadows swinging, the drained world snapping back.
- Screen-space tricks at the impact: chromatic fringe for 1 to 2 samples (2, 5, 10, 11), radial blur on dashes and landings (1, 4). Use only behind the "Flashing" setting, never over 2 samples.
- Hitstop and camera: 1's dash zooms in with radial speed lines; 2's serpent holds a 2-sample smear. Camera shake is rare and short in all eleven.

**Screen space against world.** Almost everything is world-space and lit by, or lighting, the world. Screen-space is for 1 to 2 samples of seasoning only. Sky takeovers (4, 9) are cinematic, not gameplay.

**Ground marks.** 10 and 11 show their recipe: a decal texture with a height map (parallax occlusion), a normal map, and an emissive mask hot at the center. Char and broken rock read dark; the crack's heart glows and cools. 1 draws its crack as a line of gold sparkle on dark chunks. 4 heaves real slabs with lit gaps. 5's scar cools through red embers to a dark smudge. 3's blood pool stays.

**What sells scale.**
- Ground light pools wider than the effect (11's fireball lights most of the floor; 10's strike lights all of it for 1 sample).
- Debris on gravity arcs, dust rings rolling out low (1 at 2.95 s).
- Shadows of the effect on the ground (5's flock). Top-down, a shadow is the only proof of height.
- Tall shapes leaving the top of the frame (1's column, 4's beam).
- The world darkening around the event for 1 to 2 samples (1's orb at 6.58 s, a vignette that drains the scene).

## 3. Our game against that

**The captures did not show combat or a Flare.** All five runs (wd_day, wd_night, lc_day, lc_night, bt_day) play in the Waystation hub on Day 1, not in a fight. The Flare lamp reads "Q READY" in every frame of both Long Cut runs (5.9 to 9.8 s) and of the Burns Twice run (5.9 to 12.2 s), so no press registered. Roofs fill 30 to 50% of many frames, and twice a roof is caught mid-fade as a ghost (lc_day #2 and #22). What can be said:

- **Warden auto-attacks, day.** No attack is visible in 16 frames. She walks the square among townsfolk. Nothing to judge.
- **Warden auto-attacks, night.** Two frames (wd_night_15, lc_night_03) show the only skill-like thing in the set: a thin pale blue-white ribbon about 350 px long at 1080p, running from her outward and ending in a small gray puff. It is most likely the Judgement Disc's trail (not confirmed). Against the references it has no head (no silhouette), no hot core, no light on the ground, no hit burst, and a cold color off the dawn-gold palette. It reads as a contrail, not a holy disc. As a player at 1:1: would not ship.
- **The Long Cut, day and night.** Not pressed. By the code, a press today gives about 26 ember motes at her head in arcanist orange, one light, a camera jolt and a hitstop. Against the references that is an impact frame with nothing in it: no shape, no seam, no sweep, no column, no scar, no decay, the wrong hue. Would not ship. It is the tutorial's Flare.
- **Burns Twice.** Not pressed; nothing to compare. It remains the one Flare with a full layer stack (baked fire flipbook, meshes), and the bar the others must meet.
- **What does read.** The HUD Flare lamp's warm glow and the night's lamplight pools already show "light read as light", the language the skills must speak.

## 4. What our skills take, reference by reference

**The Warden (dawn-gold on steel).**
- Oathblade sweep: 1's gold crescents with cool white glints (two tones, gold body, white-hot edge); 11's tapered swipe texture; 2's 2-sample smear on the swing; 1's impact budget (1.2x mean, about 1.5% near-white).
- Judgement Disc: 6's small icon-clear silhouette and its stretch in flight; 11's light pool that moves on the floor under the projectile; 10's bounce arcs with tangent control if it ricochets; 6's and 1's 4-point star glint on the hit.
- Shield Bash: 1's slam (the 2-sample dip, then the burst, the dust ring rolling low); 8's material told by debris (steel sparks and stone chips, not a colored blob).
- The Long Cut: 1's crack line (gold sparkle in dark chunks, dying from her end outward); 10's and 11's crack decal (height, normal, hot emissive heart); 4's column and its slabs with lit fissures; 5's cooling ramp (white-gold, gold, red, dark) and VFX shadows; 11's split emissive and non-emissive dust, so the dust is lit by the seam rather than glowing.

**Other callings' Flares, briefly.**
- Burns Twice (Kindler, split cold against hot): 10 is that exact pairing (violet-white bolt, orange fire). Add 11's scorch decal with a glowing heart and 10's 1-sample light-before-shape.
- Butcher's Bill (dark, steady reds): 3 proves one red can carry it with no white and no flash; its spikes stand as the scar.
- One Arrow (almost no light): 6's stretched streak that snaps to shape on impact; 2's single-sample release, kept local.
- Drag Them Under: 2's ground vortex that rises; 7's struck bodies that keep burning after the blow.
- Branding: 9's thin lines of light linking the marked; 3's mark that lingers.

## 5. Sketches for the Warden's four queued skills

All four stay steel-gray and gold, small and below the knee, so they read under a Flare (the Flare owns the column and the big light).

- **Sunder** (220-degree cleave; every 4th swing a 7 m x 1.2 m split). The cleave is the Oathblade crescent widened: 4 samples, gold body, white edge, steel sparks on hits. The 4th swing is a short cousin of the seam: a crack decal revealed by a fuse in 0.15 s, 3 or 4 dust jets, 6 to 10 chunks, gold light only inside the crack, cooling in 1 s. No column, no shadow swing, no world drain, so it never steals the Long Cut's read. (1, 10, 11)
- **Groundbreaker** (a crack races to the densest pack within 10 m; the end heaves 2.5 m round). A running crack, 0.25 to 0.3 s, a faint gold under-light riding its tip. At the end: 5 to 8 slab meshes punch up with 1 sample of gold light under them, a dust ring rolls out low, chunks fly, then the slabs sink over 1.5 s while their gaps cool to red. The slabs cast real shadows. (4, 1)
- **Rebuke** (each block strikes the blocker and the 3 nearest). Thin dawn-gold threads (soft, gaussian, never a hard bolt) leap from her shield to each target, 0.05 s apart. Each lands as a 2-sample downward shaft with a white-gold star glint and a 2-frame rim on the target. Threads fade in 0.2 s. (9, 10's chain, 6, 1)
- **Watch Bell** (every 6 s, a toll 8 m round draws everything in for 2 s; barrier shimmer). No ring of any kind. The toll is told by sound, a bronze glint over her for 1 sample, a low dust wave rolling inward across 8 m, grass and cloth pushed toward her, and a 2-frame rim on the pulled. The barrier is a heat-shimmer refraction with no bright edge, fading out softly at its reach. It repeats every 6 s, so never a whole-frame swing. (1's dust ring run in reverse, 5's vortex at low strength; avoid 2's dome)

## 6. Ranked proposal

**1. Build The Long Cut for real (the seam of morning).** Today it has nothing of its own. It is her BOOM button, the tutorial teaches it, and every press should be the poster.
- *What the player sees:* she winds and holds (0.3 s, blade white-gold, lit from her hands). On the Spend a knee-height smear of light crosses 12 m, a short soft column flares at her for 2 to 4 frames, and the ground splits in a 24 m line. Its crack lights from below, front to tip, like a fuse in 0.4 s. Dust jets up in sequence, chunks fly, and every shadow swings away from the line. Then the seam cools gold, red, dark under a curtain of smoke for 2 s. The scar is gone by 6 s.
- *Layers and build:* the crack as a Blender-baked texture set (height, normal, emissive mask) on a ground strip with its own shader (fuse mask, cooling ramp), or 8 to 12 Godot decals lit in sequence if the strip fights the terrain; dust jets and the smoke curtain as one baked Blender smoke flipbook through tools/fxsim, split emissive and non-emissive; chunks as mesh GPU particles on gravity; the smear as a swipe mesh with a scrolling texture; the column as a soft camera-facing quad with a lit pool at its foot. Light: one shadowed omni riding the fuse front (that is what swings the shadows), two unshadowed omnis trailing it, the shadowed spend light at her for 0.4 to 0.6 s. Gold motes in the Warden's hue, not orange. Inside the luminance budget (1.5x mean, 3%), like refs 1 and 4, not 10 and 11.
- *Perf risk in a dense crowd:* medium. The moving shadowed omni and the smoke overdraw are the cost; the decal, chunks and smear are cheap. Measure at the night close-up with a packed horde; fall back to unshadowed lights and a shadowed spot above her.
- *Cost:* about 2 to 3M tokens (one new sim, one bake, one shader, the light rig, 3 judge rounds day and night, one perf run). Less than Burns Twice because its tools exist.

**2. Rebuild her two auto-attacks, the Oathblade sweep and the Judgement Disc, with a shared hit kit.** They fire every second all game long, so they are what the player sees most.
- *What the player sees:* the sweep is a gold crescent with a white-hot leading edge, 4 to 6 frames, a faint gold pool on the ground under it for 3 frames, steel sparks and a 2-frame rim on each enemy struck, a 2 to 3 frame hitstop on the first hit only. The disc is a small spinning white-gold disc with a dark steel rim (a head you can track), a short warm trail, a light pool moving with it on the ground, and a 4-point glint plus sparks and a dark chip puff on each hit.
- *Build:* swipe meshes and shaders, pooled GPU particles (one emitter, many emits, not a node per hit), at most 4 live unshadowed lights for discs. No sims.
- *Perf risk:* low to medium. It scales with attack speed and crowd size; cap by count, and hold to the white-flash cap.
- *Cost:* about 1 to 1.5M tokens for both, with 2 to 3 judge rounds each, day and night. First, a 0.1M recapture in a real fight to confirm the gap (section 3 could not).

**3. Give every plain Flare the shared breath, in its calling's hue.** Five Flares (The Long Cut, Butcher's Bill, One Arrow, Drag Them Under, Branding) today share an orange mote puff.
- *What the player sees:* on any press, the hairline ember web lights under the ground within the reach and threads stream up into her (Draw, 0.22 s); her weapon becomes the brightest thing on screen (Hold); and after the Spend the web glows once more and cools to dark (Return, 1.5 to 2.5 s). All in the calling's color.
- *Build:* one ground-web shader on a decal or ground strip, GPU motes and threads, one hue table per calling. The hue fix alone (Warden motes gold, not orange) is about 50k tokens and should land now.
- *Perf risk:* low.
- *Cost:* about 0.6 to 0.9M tokens. Each calling's own Spend still has to come later; this only stops every Flare from looking the same.

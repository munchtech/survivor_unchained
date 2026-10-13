# The Flare: how it looks, sounds and feels

Flare look director, 13 October 2026. Design only: nothing here is built. `CLASSES.md` §3 says what each Flare does and owns every number. This page owns how each Flare is staged. Where it changes a look number in §3.5 or §3.6, §1.9 lists the change.

> "I'm simply anxious to begin building super epic flare animations. like beyond anything we've done yet with effects and just awesomeness."
> "its supposed to be epic. an 'oh shit' button. a planned 'BOOM' button. a 'clear the whole room' button."
> "*most* are for arena mode type screen clears or saves etc - but some can be single target (or one or the other based on context). but pushing a flare should always do something visible."
> "take a look at sound research too. sounds that feel awesome, feel good. intangibles."

**In short**
- Every Flare breathes the same way, and the breath comes from the world. The valley's light is **drawn** up out of the ground into her, **held** while the world stops, **spent** in one BOOM, and it **returns** into the ground as the field cools.
- The press is answered on its first frame. Then the world waits at 8% while she winds up at full speed, and her key pose is the poster frame.
- The BOOM is a real light that swings every shadow on the field away from her. Its front travels, and the world's color comes back with it. The dead fall in a ripple, never in one frame, and nothing goes white.
- Sound and feel get their own section (§2): a confirm on the press, a riser made from the BOOM itself, a held-breath gap, a four-layer impact, and one frame on which sound, hitstop, shake, rumble and light all land.
- **The slice is Burns Twice** (§4). The frost glazes the whole field in a breath, then twelve embers fall out of the night and shatter it. It gives the most wow for the least, because its game logic is already staged.

---

## 0. The idea

**Every Flare's art is its own (the owner, 13 October: "flares should be unique. I really want these to be epic, not to mention our existing effects aren't perfect yet").** No Flare reuses a spell's flames, ice, sparks, textures or sounds. Shared engine tools (shaders' code, particle systems, the light rig) are fine; the art on them is made for the Flare, above the spells' bar.

A Flare is an Unchained burning, all at once, the ember she has gathered. Ember is the valley's light, leaking up through the ground. When it is burnt, it goes back down: "Nothing is ever let go: it goes round" (`STORY_BIBLE.md` §1). So every Flare is one breath:
- **Draw:** the light comes up out of the ground into her.
- **Hold:** it is held for a heartbeat.
- **Spend:** it is spent outward. This is the BOOM.
- **Return:** it sinks back into the earth.

The calling decides what the spending looks like. The breath never changes, so the player learns it once and feels it every time. The evening call says it already: "Lamps are lit. Stay where they reach." A Flare's light is its reach.

---

## 1. The shared grammar

### 1.1 What the best do (we take the principles, never the designs)

| Principle | Seen in | Here |
|---|---|---|
| The press stops the world and lights one figure. The stop is the declaration | Fighting-game super freeze; the Final Smash's darkened stage | The world drops to 8% and is drained of color, and she is lit (§1.2) |
| The ready state is worn on the body, where the eye already is | Smash's "standby": an aura and glowing eyes | Her weapon edge, hands and eyes glow, with a curl of wick-smoke |
| Player actions answer within a frame or two, so anticipation must cost no control | Game-animation practice (responsiveness over wind-up) | Frame 1 answers the press. The wind-up runs on her clock while the world waits |
| A super-skill must do what no other skill can | Path of Exile's Vaal skills: kept for "extreme effects that couldn't be seen in any other skill" | Each Flare has one image of its own (§3), never a bigger copy of a draft skill |
| An ultimate weaker than the everyday kit gets taken for its buffs | Diablo IV's ultimates, which players call the weakest skills | The Flare owns the frame (her other effects dim) and grows with the board |
| The activation itself is a blow | Devil May Cry 5's Sin Devil Trigger: untouchable, then an explosion | Every press is visible, even into empty ground (§1.7) |
| The struck shake more than the screen. The shake runs along the blow and decays, and the attacker keeps moving a little | Sakurai on hitstop | The struck shudder during hitstop, she runs at 10%, and the camera shakes once |
| The visual must end where the effect ends | Riot's VFX style guide (an ult that looked wider than it hit confused players) | Honest edges: where the light stops, the Flare stops |
| Tempo is a message: fast reads as aggressive | Diablo III's VFX (Julian Love, GDC 2013) | Each calling has its own Hold tempo (§1.2) |
| Light needs a dark bed. Additive light on light becomes "one large mass of white" | Diablo III's blend-add | Every light layer sits on smoke, soot, char, dust or steam |
| A screen clear in one frame is a white flash that needed a toggle | Vampire Survivors' pentagram flash and its Flashing VFX option | A front crosses the reach in 0.25 to 0.4 s, and the deaths ripple behind it |
| The world remembers | Vlambeer's "permanence" | Each Flare leaves scars that last 2 to 6 s |
| Never cut away | God of War (2018)'s single camera | The camera pushes, lifts and leads. It never cuts |
| Design for the camera you have | Lost Ark's awakenings, read from above | The ground carries the image, and the light's shadows tell what stands up (§1.3) |

### 1.2 The beats

Real time at 60 fps, for a Strike (Stands: §1.8).

| Beat | When | What the player sees |
|---|---|---|
| **Ready** | while full | The HUD's Flare lamp is lit and breathes. On her, the weapon edge, her hands and eyes glow in the calling's hue, breathing slowly (0.5 Hz). A thin curl of wick-smoke lifts off the edge, like a lamp just lit. At night her own light warms the ground at her feet a little. One sound plays: the catch (§2.3). When the ember answers (filled below a quarter), the weapon takes light in one rush: *now*. Banked Flame's second charge adds a second curl |
| **Press** | frames 0 to 1 | Answered on frame 1: the weapon flares, missiles within 6 m burst into ember puffs (the flare burns the air, seen), the confirm sounds and the pad ticks. The world's clock drops to 8% within 2 frames. **Hers doesn't** (her clock) |
| **Draw** | 0 to 0.22 s | A hairline web lights under the ground within the reach, faint ember-amber, like a banked fire under ash. Motes and three to six thin threads rise from it, and from any dead lying in it, and stream up into her weapon. The web fades softly at the reach's edge, so the reach is shown with no ring. The world drains (§1.5) and the camera pushes in (§1.4). She winds up at full speed. An updraft lifts her hair and cloth, and her chest and shoulders rise with the inhale. At night her one breath smokes |
| **Hold** | the key pose: stalker 0.15 s, reaver 0.2, warden and arcanist 0.3 | The poster frame. It is still but alive: hair, cloth and motes keep moving. Her weapon is the brightest thing on screen and lights her from her own hands: a rim along her body, her face lit from below. The enemies are near-still. Nothing shakes. The last 0.1 s is the gap (§2.2) |
| **Spend** | the release | Everything lands on one frame: the world's clock returns (over 0.08 s), the main blow and its hitstop, the sound's transient, the rumble's hit and the shake. The Flare's light peaks at its source for 2 to 4 frames and falls off over 0.4 s. It is a real light, so every body on the field throws its shadow away from it, and the night's shadows swing out from her. The front carries the effect across the reach in 0.25 to 0.4 s, color returns behind it, and the dead fall in a ripple |
| **Return** | 2 to 6 s after | The scar stays: seam, frost and char, furrows, planted arrows, scorch. The spent light sinks: the web glows once more under the scar and cools from hue to ember-amber, then dull red, then dark, over 1.5 to 2.5 s. The dead's light lifts off them like sparks off a banked fire. Dust, steam and smoke settle, and the sound tails into the place's room. The HUD comes back, and the camera eases back over 0.6 s. Scars are gone by 6 s |

### 1.3 Light

- **The Flare is the one bright light on the field for a heartbeat, then it is gone.** Light is shown by what it lights: the ground, the crowd's faces, the shadows. It is never a bright shape. §3.5's laws all stand: no hoops; light reads as light; a gaussian never makes an edge; light is held below the knee except a Flare's short column; danger marks draw over everything.
- **Shadows** prove a vertical light to a camera looking down. At the Spend, a shadowed light burns at the source for 0.4 to 0.6 s: an omni, or a wide spot 3 m above her if that is cheaper. Performance measures it in a packed horde.
- **Dark beds:** every light layer sits on smoke, soot, char, dust or steam.
- **Each calling has its own light (its value signature):**

| Calling | Spend light | Color |
|---|---|---|
| Warden | The brightest; the only calling with a column | Dawn-gold, white-gold core |
| Arcanist | Bright, split cold against hot | Kindler: ford-blue, then ember-amber. Moonweaver: silver, with violet |
| Reaver | Low and dark. Red and steady (Butcher); short cold flashes (Chainbound) | Blood-red ember; storm-blue |
| Stalker | Almost none: told by steel glints, afterimages, blooms and sound | Steel and poison-green; bone-white and Verge green |

- **In a packed horde the ground is hidden**, so a scar must also light the bodies standing on it from below. Then the line reads on them.
- **By day** the sun drowns the light, and the drain, the front and the scars carry the Flare. Every Flare is judged by day as well as by night.

### 1.4 Camera

- **Envelope:**
  - push in up to 12% at the press (pitch down 4° in 0.18 s, ease out);
  - pull out up to 15% (Deeper: 20%);
  - lift up to 10°;
  - lead up to 8° along a directional Flare's line;
  - roll up to 6°, once, on The Long Cut only;
  - orbit only on a boss kill (15°).
- **Never a cut.** She never leaves the center third of the screen.
- **The Hold is still:** no shake while she holds the key pose. The stillness is the anticipation.
- **Shake budget:**
  - one peak per Strike: at the Spend, trauma 0.5 to 0.8, starting on the transient frame, along the blow (vertical for slams, horizontal for sweeps), and decaying;
  - lesser blows: up to 0.2;
  - Stands: up to 0.15 a beat, and never above 0.4 in total.
- **Slow time happens only three ways:**
  - the press: the world at 8% until the Spend;
  - a boss killed by a Flare: 0.6 s at 20%, with the orbit;
  - the clutch: its Hold is 0.06 s longer.

  A Flare that kills two hundred things never slows; the ripple does that work.
- **Two cameras:** arenas frame at 64° and 31 m, the story at 56° and 23 m (`docs/feel/AUDIT.md`). Every image is judged at both.
- **Settings:** Motion off means no slowed time, no hitstop, no shake and no roll (the game's rule today). Reduced means half the push and shake, and no roll.

### 1.5 The screen

- **The drain:** at the press, the world (ground, crowd, props) desaturates 70% and darkens 25% over 0.12 s. She, the Flare's own effects, enemy missiles and every danger mark keep their full color. The likely way: global shader uniforms (drain, center, front radius) read by the world's materials, so nothing needs a mask.
- **The repaint:** at the Spend, color comes back with the front, from her outward, across a soft 6 m band. The band has no line and no light: only saturation returns. The player watches the Flare paint the world back.
- **The Flare owns the frame:** her other skills' effects dim to 40% from the press until 0.3 s after the Spend.
- **The HUD:**
  - It dims to 35%, except her health, the Flare lamp (which pours empty at the press) and a boss's bar.
  - From the press until 0.5 s after the Spend, ordinary damage numbers and enemy health bars are hidden. Champions' and bosses' numbers still show.
  - Everything is back after 0.4 s.
- **Sound** ducks and filters with the drain (§2.2).

### 1.6 Readable in a packed horde, and never blinding

What must read, in order, every frame: danger marks, then her, then the Flare's front, then the dead, then the ground.
- **The front travels.** Every Spend crosses its reach in 0.25 to 0.4 s. A clear never happens in one frame.
- **The deaths ripple.** They fall behind the front at its speed, each falling away from the source. This is view only: the game logic may kill everything at once, and the crowd's view holds each body in its hit pose for up to 0.3 s.
- **A crowd is told by its first few.** The white-flash cap still holds (two elites and three ordinary bodies). Every other struck body takes a 2-frame rim in the calling's hue, shaded, never a cut-out. This answers the skills page's open question about white, for Flares.
- **The last word:** when a boss or champion is in reach, the Flare's last beat lands on it with the main hitstop, so the player sees the Flare choose it.
- **The luminance budget** (the skills lead measures it from recorded frames):
  - at the Spend, the frame's mean luminance stays under 1.5 times the pre-press frame's, for 4 frames at most, once per Strike;
  - no more than 3% of pixels sit above the tone curve's knee in any frame;
  - no more than 2 whole-frame swings a second (WCAG 2.3.1's limit is 3). Repeated blows (Bell's tolls, Storm's bolts) are told by sound, air, rims and local light, never by the whole frame;
  - no saturated red ever flashes over an area. The Butcher's reds are dark and steady;
  - a "Flashing" setting halves the Spend's peak and removes the sky flashes.
- **Every layer earns its place:** it tells the reach, the power, the cause or the aftermath. If it tells none of these, it goes. More is not better.

### 1.7 The empty press

A Flare spends into the world, not into its enemies. With nothing near, it still draws, holds, spends and returns in full:
- its light and shadows;
- its sound;
- its scar on the ground;
- the world answering: grass laid flat outward, dust lifted, banners snapping, puddles shivering, and every lamp in reach flaring with her, then guttering after (lamps burn ember).

The Flares that choose targets have their empty form stated in §3.

### 1.8 The clutch, banking, boss kills and Stands

- **At the edge** (below a quarter: it mends 20% and reaches 25% further):
  - the Draw rushes, with twice the motes, faster;
  - the Hold is 0.06 s longer, and the core is one step whiter (still under the knee);
  - the low-health heartbeat stops dead for the Hold;
  - at the Return, the spent light doesn't sink. It runs back into her over the mend's second, and the heartbeat comes back slower. **The light comes home**: the save is seen.
- **Banked** (Banked Flame, both charges spent): the Draw doubles, the Hold is 0.05 s longer, the Spend is one step brighter, and the shake is 0.1 stronger.
- **A boss killed by a Flare:** 0.6 s at 20% with the 15° orbit. Its own light lifts out of it as an ember column, which hands over to the victory.
- **Stands breathe the same way, shorter:**
  - the world is at 8% for 0.15 s and the Hold lasts 0.2 s at most;
  - she can move at once, and moving blends the key pose into her run (the upper body finishes it);
  - their Spend is an opening statement (§3);
  - while a Stand holds, she wears it: her weapon lit, her own light, its own layer;
  - in its last second it gutters: the light flickers and thins, and so does its sound. The end is felt with no bar;
  - it ends on a small exhale: its light sinks into the ground at her feet.

### 1.9 Changes to CLASSES §3.5 and §3.6 (look only; no number of theirs changes)

1. **Her clock:** from the press to the Spend, the world runs at 8% and she runs at 100%. The first blow's motion starts on the Spend frame. Today the game logic fires `Release` at the key in its own time, so the experience lead and classes align the two clocks.
2. **The Draw's web** shows the reach, and **the Return** sinks the light.
3. **The repaint** comes from her outward.
4. **A shadowed light** at the Spend.
5. **The Flare owns the frame:** her other effects at 40%.
6. **The deaths ripple** (view only).
7. **Flare blow events bypass the hitstop cooldown** (`WorldScene.Weigh` allows one hitstop per 0.3 s; the Bell needs 4, 4 and 8 frames, 0.25 s apart). In hitstop she runs at 10% and the struck shudder.
8. **The Hold's tempo** varies by calling.
9. **The looks** of the clutch, banking, and the Stands' Hold and guttering end.
10. **The empty forms** (§3).
11. **Sixty on the Wall's bearers rise out of the ground** (in §3.6 they step in from the sides). **Through and Through ends on a sheath.**

---

## 2. Sound and feel: the intangibles

### 2.1 What the best do

| Principle | Seen in | Here |
|---|---|---|
| A game you can play by sound: VO, a clear mix, pinpoint position, information, and a "Pavlovian response" | Overwatch's "Play by Sound" (GDC 2016) | One ready sound whose core never changes. Every Flare is known blind (§3) |
| Loudness is priority: the loudest event plays in full and everything else gives way, by design | DICE's HDR audio (Battlefield) | The Flare is the loudest thing in the mix. Today the master compressor pumps by accident when booms land (`feel/AUDIT.md` §5); the Flare's duck is designed instead |
| Fewer voices make a clearer mix; quiet sounds quieter, so loud ones can cut through | Battlefield 1 and V | A Flare's kills are played as its first few, plus one bed |
| An impact is layers, with their transients aligned: the transient sets the timing, the body comes from the material, the sub gives weight, the tail is the room | Sound-design practice | §2.2 |
| Quiet before the hit gives it something to land against | Sound design; film's drop-out before the blast | The gap |
| Chains that rise in scale steps and resolve feel rewarding; microtones don't | Peggle, Balatro (`feel/AUDIT.md` §5) | Multi-hit Flares climb the music's scale and land on its home note |
| Two motors: a heavy low thud and a light high buzz, on the same frame as sight and sound | Controller haptics practice | §2.4 |
| A sound heard hundreds of times must not tire | Game audio practice: repetition is the enemy | Several takes, never the same one twice running, plus the 500th-time rules (§2.3) |

### 2.2 The BOOM's anatomy (every Flare)

- **Confirm (frame 0).** A short, bright transient made from the Flare's own material: a flint catching, an ember popping. It peaks within 30 ms, so the hand knows the button worked.
- **Inhale (the Draw and the Hold).**
  - The riser is made from the Flare's own Spend, reversed and pitched up a fifth over its length, so the riser and the BOOM are one sound.
  - A sub-drop sits under the press: an ember catching.
  - The calling's stinger plays on top: short, in the music's key.
  - The music ducks 9 dB and the world 12 dB, both low-passed toward 500 Hz.
- **The gap.** The last 80 to 120 ms of the Hold are near-silent, and the inhale cuts off clean. It must read as a held breath, never as a dropout.
- **The Spend.** Four layers start on one frame, with their transients aligned:
  - *transient* (0 to 10 ms): the material's crack: steel ringing, ice snapping, a chain snapping, a bowstring's whip;
  - *body* (to about 400 ms): the material's mass (bronze, rock, ice, iron, flesh), never a generic boom;
  - *sub* (300 to 600 ms): a pitched drop from 60 to 30 Hz. It is kin to the elite kill's 70 to 28 Hz, deeper and longer;
  - *tail:* the place's reverb, kept apart from the dry layers so every place colors it. At night in the open, **the valley answers**: one filtered echo off the hills, 0.3 to 0.6 s later.
  The filters open and the music returns over 0.3 s.
- **Debris (0.5 to 3 s):** whatever settles. Stones patter, ice tinkles, embers crackle, steam hisses.
- **The crowd's deaths, without mud.** The first few deaths (the nearest and the biggest) play their own sounds. The rest are one designed bed, a rolling crumple of the field falling, scaled in length and weight by the count and mixed under the Flare. During a Flare, the hit gate lets its blows in first, by importance rather than arrival (`feel/AUDIT.md` §5).
- **The mix.** The Flare's bus sidechains the others: the world −12 dB and the music −9 dB, back over 1 s after the Spend. Nothing clips. It is measured with `--wav`, and **the owner listens**: a spectrogram is not a verdict.
- **Music.** It ducks and filters at the press and returns at the Spend. The stinger is in the music's key, so it never clashes. If the music system allows it, the next phrase lifts one step in intensity.
- **Her voice: effort, not words.** Every Flare gets a breath in the Draw and a shout or grunt on the Spend: six to eight takes per hero, never the same one twice running. Words are rare: one line for a boss killed by a Flare, or for a clutch save, at most once in ten minutes, written by the story lead in `VOICES.md`'s voice. A catchphrase every minute grates.

### 2.3 The ready sound, and the 500th time

- **The catch.** It plays once, when the meter fills: a soft wick catching ("fwmp") over a warm low tone, under 0.4 s long.
  - Soft attack, on the home note or the fifth of the music's key.
  - Centered on her, about 18 dB under the fight's peaks.
  - The core never varies, because it is learned. The tail varies over three or four takes.
  - No loop: the visual breathing carries the "ready" state.
- **When the ember answers** (filled at low health), the same catch plays louder, with a rush. It is the one cue that means *press now*.
- **Why it won't tire:** it is short, soft-edged, consonant and quiet, and it means something every time.
- **A press with no charge** gets a dull, muted tap, never a buzzer.

### 2.4 Feel: frames, the punch, the hands

- **Hitstop at 60 fps:**
  - the main blow: 6 to 8 frames;
  - lesser blows: 2 to 3;
  - chops and multi-hits: 1 to 2;
  - a Stand's opening: 4;
  - the last word on a boss: 8.

  During hitstop she runs at 10% and the struck shudder along the blow, decaying. The camera's shake starts inside the hitstop.
- **One frame for everything:** the transient, the first hitstop frame, the shake's onset, the rumble's hit and the light's peak all land on the same frame. A sound or a rumble one frame late feels like lag.
- **The punch** is the push in at the press and the release out at the Spend. The shake rides the release.
- **Rumble** (`Haptics`; two motors). Each call to the pad replaces the last, so `Haptics` composes them.

| Moment | Low motor | High motor |
|---|---|---|
| Press | none | a 40 ms tick (the confirm) |
| Draw | a swell rising with the inhale to 20%, cut for the gap | none |
| Spend | full on the transient frame for 120 ms, decaying with the tail over 400 ms | 60 ms on top |
| Repeated blows (tolls, chops, embers) | none until the last, which plays as a Spend | a tick each |
| Stands | a texture at 10 to 15% (rain, frost, the drum) | ticks on its beats |

  Rumble has its own strength setting; Motion off doesn't silence it.

### 2.5 Sourcing: ours first, CC0 logged, the owner's own recordings

- **We make** (in `Synth.cs`, as the game does now): sub drops, risers (reversed, pitched Spends), the inhale and the gap, FM bells (chimes, the catch), electric snaps, filtered-noise whooshes, the war-drum pulse, the valley echo (a delay), and granular ice creaks from short recordings.
- **The owner could record** these with a phone or small recorder, held close, outdoors at night when it's quiet. Ten takes of each; each is about ten minutes' work:
  - **a real bronze bell or large handbell** (Bell of the Morning: the most important single recording);
  - a hardware-store chain, whirled, dropped, and dragged over gravel and dirt;
  - ice: freezer trays cracked, a sheet of ice shattered on stone, ice dropped into water;
  - a long knife drawn from a leather sheath, a blade run on a sharpening steel, a sheath's click;
  - a dowel or cane swung past the mic;
  - a heavy sheet or coat snapped;
  - a bow's creak and release (or a bent green branch);
  - a sharpened dowel thrown into a hay bale or a stack of cardboard (arrows planting);
  - stones crunched in a bucket;
  - a fireplace bellows;
  - dry chops into a log (the axes).
- **CC0, logged** in `docs/legal/ASSET_PROVENANCE.md` the way Kenney and OpenGameArt are: Freesound filtered to CC0 only, OpenGameArt CC0, Kenney. Royalty-free bundles that aren't CC0 (Sonniss's GDC bundles, for example) need the owner's OK first.
- **Voices:** her efforts, his, and the rare lines go through the voice pipeline the owner uses (ElevenLabs) or a performer. The owner decides which.

---

## 3. The sixteen

Roles (classes confirms each one):
- **Clear:** the room.
- **Save:** her life.
- **Single:** the one that matters.
- **Context:** clears a crowd, and chooses the boss when one is near.

That makes six Clears, four Saves, two Singles and four Contexts. §3.6's timings stand unless a Flare below says otherwise. The poses are her poster frames. Each is built on one clear line of action through her body (an arch, a twist or a long stretch), lit by her own light, with hair and cloth lifted by the Draw. They are powerful first and attractive always, and never awkward: no stiff wrists, and no weapon or shield through her body. He gets the same beats and contact frames, so the effect sockets line up, with his own weight.

| Calling | Strike | Stand |
|---|---|---|
| Warden, Sunderer | The Long Cut (Clear) | Dawn in the Steel (Context) |
| Warden, Bulwark | Bell of the Morning (Save) | Sixty on the Wall (Save) |
| Reaver, Butcher | The Butcher's Bill (Single, with a save in it) | Butcher's Hour (Clear) |
| Reaver, Chainbound | Drag Them Under (Clear) | Storm on the Chain (Context) |
| Arcanist, Kindler | Burns Twice (Clear) | Hard Winter (Save) |
| Arcanist, Moonweaver | The Branding (Clear) | The Drowned Moon (Context) |
| Stalker, Roadknife | The Road's Toll (Single) | Through and Through (Clear) |
| Stalker, Verge-Hunter | One Arrow (Context) | Pinning Rain (Save) |

### Warden: the Order's morning

Dawn-gold on steel. The brightest light, and the only calling with a column. Hold 0.3 s. Its sounds are bronze, steel and men's voices.

#### The Long Cut · Strike · Clear
*The image:* a seam of morning opened across the night. The cleave splits the ground in a 24 m line, light shines up through the crack as if the morning were under it, and every shadow on the field swings away from the line.
- **Pose:**
  - her: the blade low behind, in both hands, weight on the back foot, her torso wound away from the line so her back and waist make one long twist, head turned to look down the line over her shoulder;
  - the rise (0.1 s) peaks in a full arch with the blade overhead: the second poster;
  - the recovery kneel is the aftermath's image: one knee down, both hands on the hilt buried in the seam, head bowed, lit from below;
  - him: the same, wider and lower, shoulders square.
- **Layers:**
  - the sweep's 12 m blade is told by what it lights (a knee-height smear across the ground, and the rims of everything it passes) and by heat shimmer. A thin hot core runs only along the real steel;
  - the seam: a crack glowing from below, dust jetting up along it in sequence (a running fuse, 0.4 s), chunks thrown out;
  - the seam's light throws shadows away from it on both sides;
  - Return: it cools from gold to red to dark, under a curtain of smoke.
- **Sound:** a long steel draw that rings like a struck bell, the sweep's air-roar, then rock tearing down the line like a fuse, and the valley echoing it back.
- **Lamps:**
  - *Second Cut:* a counter-sweep; two smears cross at knee height;
  - *Line of Morning:* low dawn-fire stands along the seam for 4 s (the fed deadfall's flame, pressed to a line), with embers rising;
  - *Through the Wall:* the fuse runs off the screen's edge, the camera leads after it, and the tearing goes on into the distance.
- **Empty:** unchanged. The seam is the proof.

#### Dawn in the Steel · Stand · Context
*The image:* morning carried in the hand. Light pours down the blade like molten metal, and every swing throws a thin crescent that skims the ground and lights each face it passes.
- **Pose:**
  - her: the blade raised flat overhead, one hand on the hilt, the other's fingertips along the flat, chin up, light pouring down the blade onto her face and chest;
  - him: the blade held level overhead at arm's length, legs planted.
- **Layers:**
  - the edge: a white-gold core shedding sparks;
  - the crescents: thin, sharp and seen to travel, lighting the ground under them as they go (a moving light, not a lit object), gone at 10 m;
  - she stands in a small pool of her own morning, with motes rising at her feet, which also finds her in the horde;
  - the last second gutters.
- **Opening:** the light pours down the blade (4 frames), and a gust of motes blows out from her.
- **Sound:** a low hummed note under everything (the evening call's melody, no words), each swing ringing clear, and each crescent a whetstone hiss traveling away.
- **Lamps:**
  - *High Morning:* the light climbs from gold toward noon-white, and her pool widens;
  - *Crescents Through:* the crescents never break on what they cut, and they leave lines of rim-lit bodies;
  - *Mending Light:* a crescent kill sends one gold mote drifting back to sink into her (threads belong to the Butcher).
- **Empty:** the lit blade and her pool; the crescents fly as she swings.

#### Bell of the Morning · Strike · Save
*The image:* the screen stops three times. She strikes her shield like a bell, the air ripples out, and the whole horde stops mid-step, every rim touched with gold. On the third toll, a short column of morning pours up out of the shield.
- **Pose:**
  - her: the shield raised to her face, her eyes over the rim, the pommel drawn back. She holds it high, so her body stays open to the camera. The third strike is full-bodied: a step in, with the whole torso behind it;
  - him: the shield square in front, shoulders hunched behind it.
- **Layers:**
  - each toll's pressure wave is air and dust only: a refraction front, a sheet of dust lifting off the ground outward, grass laid flat;
  - each lesser thing's rim catches gold as the wave passes, and it stops in its pose, a tableau;
  - **no toll flashes the screen** (there are three in 0.5 s);
  - the third toll: the column, motes raining down, and the 8 m blast throwing the near ones back;
  - Return: the stopped hold a beat, and the motes settle into the ground.
- **Sound:** a real bronze bell, recorded close, three times. After each toll the world cuts to silence for 80 ms, and the decay rings on under the fight for 4 s.
- **Lamps:**
  - *Fourth Toll:* a fourth and deepest strike, with the flat of the blade. Its ripple reaches the screen's edge, and the column is taller;
  - *Bell for the Dead:* after the last toll the note bends down into a knell, and the stopped turn their backs and pull away, like a tide going out;
  - *Healing Peal:* each toll's motes fall onto her instead of the ground.
- **Empty:** the three tolls, the dust lifting, and the column.
- It must stay distinct from Path of Exile 2's Tempest Bell (a summoned bell and its shockwaves): ours has no bell object and no ring.

#### Sixty on the Wall · Stand · Save
*The image:* the Watch's dead come up out of the ground to stand with her. Fifty-nine lamp-smoke shield-bearers lock shields in an arc, she is the sixtieth, and the horde breaks on them.
- **Pose:** her: the sword raised high, the shield planted, her mouth open on the call (form up). Him: the same, the shout from the chest.
- **Layers:**
  - the web lights along the arc first, and the bearers rise out of it in a 0.4 s ripple from her outward;
  - they are dark, cold-gold figures in Watch mail, backlit as if by lamps in smoke, helms down, faces never seen, never pale ghosts;
  - their shield rims catch the light, so from above the wall reads as a line of men and rims, not a ring;
  - a block flashes on the struck shield only; missiles break in sparks; the press is shoved back in dust;
  - at the end they lower their shields and sink back into the ground as smoke.
- **Opening:** the lock (4 frames).
- **Sound:** fifty-nine shields locking in a rolling thunder of thuds, under a murmur of men, and each block a shield-crack. Story confirms whether the murmur carries the evening call: "Lamps are lit. Stay where they reach."
- **Lamps:**
  - *Shield-Brothers:* once a second the wall shoves forward in a ripple, with a shout;
  - *The Wall Walks:* they march with her, boots in step;
  - *Night Watch:* every third bearer carries a lamp-iron burning blue (ember burns blue in an iron), and the wall's light turns cold.
- **Empty:** the wall forms and holds.

### Reaver: take it out of them

Butcher: blood-red on iron. Chainbound: storm-blue on dark iron. Low, dark light. Hold 0.2 s (Butcher), 0.25 s (Chainbound). Its sounds are breath, growl, iron and thunder. She stays near-naked, so the poses are about her body's power.

#### The Butcher's Bill · Strike · Single (with a save in it)
*The image:* the bill collected. She lands on the biggest thing on the screen and takes it apart, chop by counted chop, and every chop pulls a thin red thread of its life back into her.
- **Pose:** her: crouched low and coiled like an animal, both axes drawn back, teeth bared, eyes ember-red, back arched, the red light running along her thighs and shoulders. Him: the same crouch, broader.
- **Layers:**
  - the leap trails red smoke;
  - dark red arcs hang a beat, then fall as droplets;
  - each chop draws a thread back into her, and her health globe fills a step with it;
  - the last chop, two-handed from a jump, bursts into blood mist;
  - her light stays low and red.
- **Sound:** a grunt on the leap, wet chops climbing a minor scale, a bone-crack to end, her breath ragged.
- **Lamps:**
  - *Running Tab:* the chops go on twice, and each vault leaves a red smoke arc;
  - *Wide Chops:* every chop throws a fan of blood arcs into the crowd around her;
  - *Feast:* a kill's light leaves it in a red gust, and she breathes it in, head back.
- **Empty:** she leaps 6 m along her aim and drives both axes into the ground in the last chop's overhead: a red-lit crack and a spray of dirt. With no target there is no mend; classes confirms.

#### Butcher's Hour · Stand · Clear
*The image:* she throws her head back and roars, and red breath pours off her shoulders like steam off a body in winter. For eight seconds she is a red blur, and the field keeps time with her pulse.
- **Pose:** her: head thrown back in the roar, axes out wide, chest up, back arched. Him: the same.
- **Layers:**
  - red smoke trails from the axes, and pours off her shoulders and mouth;
  - the world is a step warmer, and her eyes burn;
  - executions burst in short, dark sprays (by the gore setting);
  - each kill thickens the smoke; in the last second it thins.
- **Opening:** the roar's breath shoves the near ones back in a gust of red smoke (4 frames).
- **Sound:** her roar, then a war-drum pulse that tightens with each kill, and chops dry and close. It is a drum, not the low-health heartbeat, which stays the warning.
- **Lamps:**
  - *Overtime:* each kill's added time is a deeper drum beat and a thicker breath;
  - *Red Mist:* a low red fog rolls 5 m off her, and the lesser things back away from it;
  - *Not Today:* when it holds her at 1 health, she staggers, catches herself and snarls, with a crack of ember around her feet.
- **Empty:** the roar and the smoke.

#### Drag Them Under · Strike · Clear
*The image:* a net of hooked chain thrown over the horde and hauled in. The screen's edge slides across the ground into one knot at her feet. She drives the chain into the earth, and the ground takes them under.
- **Pose:**
  - her: the chain whirling overhead in one hand (dark iron and motion blur), the other arm reaching out with fingers spread, her body wound with the whirl, hair whipping;
  - the haul is the second poster: leaning far back, heels dug in, the chain taut across her body;
  - him: the same, heavier.
- **Layers:**
  - the chain splits into many hooked lines, dark iron catching the light, with storm-blue sparks only where they bite;
  - the hauled slide in dust wakes, all converging on her;
  - the slam throws up a cone of dirt and stone, the ground buckles, and the knot sinks half into it as it dies (the view lowers them);
  - a cold blue flash, low at the slam, throws shadows outward;
  - Return: a crater, with chain furrows running into it.
- **Sound:** the whirl's hum, the ratcheting rush of many chains, bodies scraping, then one iron-and-earth slam and a deep sub as the ground takes them.
- **Lamps:**
  - *Deeper:* the hooks reach off the screen's edges, and the camera pulls out to 20%;
  - *Grinder:* the chains spin the knot like a millstone for a breath before the slam, in sparks and spray;
  - *Hold Him:* a taut chain stays from the crater to the boss for 3 s, crackling.
- **Empty:** the hooks bite the ground and she hauls the earth itself: furrows torn toward her, turf and stones dragged in, then the slam.

#### Storm on the Chain · Stand · Context
*The image:* she raises the chain like a lightning rod, and the night answers. Rain comes down around her, and at the end of every lash a bolt runs down the iron into everything it touched.
- **Pose:** her: the chain raised skyward in one arm, face up into the rain, the other arm out; then a walking lash (sweep, return, sweep). Him: the same.
- **Layers:**
  - the chain is dark iron with motion blur, never a lit circle;
  - bolts drop with a short local flash on the ground: never the whole sky, and no more than 2 a second;
  - the current shows as fine forks running down short lengths of chain;
  - rain streaks fall around her, and the ground turns dark and wet, catching each flash;
  - scorch marks are left where the sweeps ended;
  - in the last second the rain thins.
- **Opening:** the first bolt strikes the raised chain (4 frames).
- **Sound:** thunder cracked with an electric snap down the iron, rain hiss rising, the chain's whir.
- **Lamps:**
  - *Second Length:* a chain in each hand, the figure-eights alternating;
  - *Earthing:* after each strike the current runs down her into the ground, which lights blue under her feet for a frame;
  - *Wide Lash:* a longer chain and wider sweeps.
- **Empty:** the sky answers anyway, and the storm rains on her.

### Arcanist: the ford's cold, the valley's ember, the drowned moon

Kindler: ember-amber with ford-blue. Moonweaver: moonlight silver-blue with moonfire violet. Bright, cold against hot. Hold 0.3 s. Its sounds are glass, ice, chimes and fire's roar.

#### Burns Twice · Strike · Clear (the slice: §4)
*The image:* a fire lit on ice burns twice. The whole field glazes with the ford's frost in a breath, then twelve embers fall out of the night and shatter it: ice, flame and steam.
- **Pose:**
  - her: the staff raised overhead in both hands, body long, up on the balls of her feet, the updraft lifting her hair and robe, ember in her eyes;
  - the drive down;
  - head up and held as the embers fall: the third poster, her face to the sky, lit amber from above as they come;
  - a sweep down on the last;
  - him: the same, feet wider.
- **Layers and beats:** §4.1.
- **Sound:** ice creaking out fast as the wind drops away, a roar falling out of the sky, then staggered hiss-and-glass shatters, and steam.
- **Lamps:**
  - *More Embers:* eighteen, a denser and faster fall;
  - *Black Ice:* the frost is dark and glassy, not pale, and the frozen below half health crack apart in a ripple before any ember lands;
  - *Called Down:* every ember falls on one target, a converging sheaf of streaks and one great impact.
- **Empty:** the frost races over empty ground, and the embers burst on it.

#### Hard Winter · Stand · Save
*The image:* the ford's cold comes up out of the ground. The horde slows, its breath smokes, and it glazes over and stands frozen, a silent army, until the thaw breaks every one of them at once.
- **Pose:** her: both hands on the staff, driven into the ground, head bowed, frost crawling up her bare arm to the shoulder and into her hair. Him: the same.
- **Layers:**
  - rime spreads over the ground as crystalline frost, never a ring;
  - diamond dust hangs glinting in the air;
  - the enemies' animation is visibly slowed, the beasts' breath smokes, and at 2 s they glaze;
  - this is the only Flare whose drain stays, a cool one, for its whole length;
  - in the last second the frost draws back down her arm and the ice creaks louder;
  - the thaw: cracks run through everything frozen, with meltwater spray and a shatter on each.
- **Opening:** the staff's strike and the rime's first rush (4 frames).
- **Sound:** the world goes quiet but for a high glassy ring and creaking ice. The thaw is a chorus of cracks.
- **Lamps:**
  - *Deep Winter:* the glaze comes at 1 s, thicker and whiter, but still mid-value;
  - *Thaw-Burst:* each shatter cracks the frozen near it, a cascade;
  - *Winter Keeps:* a fine rime keeps her too, glinting as it mends.
- **Empty:** the cold rises anyway: frost, hush and diamond dust.

#### The Branding · Strike · Clear
*The image:* she closes her hand, and every enemy on the screen wears a silver crescent at once, like a sky of new moons over the horde. Then they burst outward from her in a rolling peal.
- **Pose:**
  - her: one hand raised with the fingers spread, hair lifting, the other hand at her breastbone. The raised hand closes slowly into a fist, with a small turn of the wrist as the bursts start;
  - him: the same, the fist heavier.
- **Layers:**
  - the brands: small silver crescent glints (soft points, never lit squares), all appearing in one frame;
  - the bursts: violet moonfire tongues (Moonbrand's crisp jets), rippling out from near to far;
  - a passed mark: a thin silver arc hopping on;
  - the boss's brand bursts last and largest: the last word.
- **Sound:** one high chime as every brand lands, then a peal of soft detonations rolling from near to far, descending the scale and resolving on the boss's burst.
- **Lamps:**
  - *Second Brand:* the crescents come again a second later, and the peal echoes, quieter;
  - *Branded Deep:* wider, taller tongues;
  - *The Eye:* the boss's brand opens into a silver eye that flares each time a mark arcs into it.
- **Empty:** with nothing to brand, the crescents print on the ground across the reach and burst there, in the same ripple.

#### The Drowned Moon · Stand · Context
*The image:* the moon comes up in the ground. A pool of still black water opens at her feet, holding a moon that isn't in the sky, and silver motes rise out of it like fish to the surface.
- **Pose:** her: arms drawn down and apart, palms to the ground, head bowed, hair falling forward, lit from below by the pool; then a slower, gliding walk. Him: the same.
- **Layers:**
  - the pool lies flat on the ground: black water holding a pale moon, lit from below, its edge fading softly, ripples moving through the reflection as she walks;
  - motes rise as crescent glints with violet trails;
  - each marked thing carries a small crescent;
  - in the last second the reflection dims and breaks up.
- **Opening:** the pool opens (4 frames).
- **Sound:** a low swell like a breath held under water, each mote a soft chime, piling into a shimmering chord.
- **Lamps:**
  - *Full Moon:* a full round moon in the pool, and twice the motes;
  - *Moonset:* it ends by rising, a column of silver water lifting 8 m around her and falling back as glittering rain;
  - *Silver Tide:* each passed mark forks into three.
- **Empty:** the pool and the motes, which circle her slowly, like a shoal.

### Stalker: never there when it lands

Roadknife: steel with poison-green. Verge-Hunter: bone-white with Verge green. The darkest light, told by afterimages, lines, blooms and sound. Hold 0.15 s. Its sounds are steel, cloth, the bowstring and the click of a sheath.

#### The Road's Toll · Strike · Single
*The image:* twelve of her. She's gone in road dust, and steel-gray afterimages hang across the field, each frozen mid-cut beside something falling, until she's back where she stood, sheathing.
- **Pose:**
  - her: blades crossed at the chest, half crouched, one heel lifted, cloak and hair swept back;
  - then twelve held strike poses (cut, back-cut, thrust, spin, vault-cut). Each is its own frame and its own poster: the gallery is the image;
  - the finish: a low crouch, then the sheath;
  - him: the same set.
- **Layers:**
  - the vanish: a burst of dark smoke and dust;
  - the afterimages hang 0.2 s, fading steel-gray, joined by a thin smoke line between strikes;
  - a green-black poison bloom on each target;
  - the last cut lands on the strongest.
- **Sound:** twelve slices climbing in quick steps, resolving on the last, then the click of a sheath.
- **Lamps:**
  - *Toll Doubled:* eighteen cuts, faster, with more afterimages;
  - *Last Cut:* the last is a cross-cut finisher whose afterimage holds longest, over a bigger bloom;
  - *Gone:* for 3 s she comes back only as a shimmer in smoke.
- **Empty:** she cuts the air at twelve points along her aim, a kata of afterimages, and returns.

#### Through and Through · Stand · Clear
*The image:* a scribble of knife-lines through the horde, with every body she passed carrying a pale tally mark. She sheathes, and the whole scribble opens on the click.
- **Pose:** her: a blade flicked out to each side, cloak snapping, head down and eyes up; at the end, both blades sheathed in one move. Him: the same.
- **Layers:**
  - each dash scores a fading steel-gray line on the ground;
  - a notch is a small pale tally mark over the notched;
  - the end: every notch opens in one frame as a thin bright cut-line with a green bloom. The lines are thin, so the whole frame never flashes.
- **Opening:** her afterimage stays standing at the press point while she is already moving.
- **Sound:** whip-quick swishes, a tally of small knife-scores on wood, then, on the sheath's click, one huge layered slice.
- **Lamps:**
  - *Deeper Notches:* double tallies;
  - *Wake of Blades:* the scored lines stand as Cutting Wake's blades for 2 s;
  - *Free Hands:* pressing again is the sheath: she sheathes early and everything opens.
- **Empty:** the scored lines, and the sheath.

#### One Arrow · Strike · Context
*The image:* one arrow, drawn to the ear. It bends the air down the length of the screen and raises a seam of dust, and everything in its line kicks back in sequence, on into the dark.
- **Pose:**
  - her: at full draw, the string at her cheek, the bow canted, the drawing elbow high, her back drawn tight and her chest open, her eye down the shaft;
  - the bow arm snaps forward, and the follow-through is held 0.3 s;
  - him: the same, with a heavier draw.
- **Layers:**
  - a long, thin pressure wake (shimmer), with a line of dust raised along it;
  - each split: a quick bright fleck;
  - whatever is struck kicks back, in order;
  - Return: the dust seam hangs, then settles.
- **Sound:** the long creak of the draw, a whip-crack release, a tearing rush down the screen, and impacts receding into the distance.
- **Lamps:**
  - *Split Thrice More:* a fan of green streaks at every split;
  - *Pinned to the Earth:* the struck are pinned to the ground by pale shafts;
  - *Through the Heart:* it stops dead in the first champion or boss, and its three splits curve back into it: three arcs closing on one point.
- **Empty:** it flies anyway. The seam is the proof.

#### Pinning Rain · Stand · Save
*The image:* the Verge's rain. Arrows fall like a squall on the ground she marked until it stands as a field of planted shafts with pale fletching, and nothing crosses it.
- **Pose:** her: the bow aimed at the sky with a fan of arrows on the string, her body arched back, face up; three loosings, fast. Him: the same.
- **Layers:**
  - the arrows fall as dark streaks with pale fletching glints, thin, never bars;
  - they stay planted, so the field fills over 5 s, and its edge is only where the arrows stop;
  - the rooted flash green-white at the rim;
  - at the end the shafts go dark and fall.
- **Opening:** the first wave (3 frames).
- **Sound:** a rising whistle, then a squall of thuds, dense and rhythmic, like hail on a roof.
- **Lamps:**
  - *Follow the Hunter:* the rain moves ahead with her and leaves a trail of planted shafts behind;
  - *Iron Rain:* darker, heavier arrows that spark and thud;
  - *Thorned Rain:* Thornbloom's thorns curl up the planted shafts.
- **Empty:** the rain falls on empty ground.

---

## 4. The slice: Burns Twice

**Why this one** (the most wow for the least):
- It is what the owner asked for first: a room-clearing, planned BOOM for the arenas.
- It has the biggest contrast of any Flare: a hush of frost, then fire falling, two beats from one press.
- Its game logic is staged already: the frost, then the embers seeking the thickest frozen packs, four on a boss, and all three lamps.
- Its art is all its own (the owner: "flares should be unique"): no spell's flames, ice or steam are reused; only the engine's tools are shared.
- The arcanist's staff grip exists, so it needs one new clip.
- It carries a saying of this world.
- It proves the whole grammar on the hardest case, a frost that covers the screen without blinding it.

After it:
1. Bell of the Morning: already staged; the warden's save, and the stop.
2. The Road's Toll: already staged; the afterimages.
3. The Long Cut: the warden's showpiece, once its greatsword grip exists.

### 4.1 Beat sheet

The game logic's beats are key 0.15 s, frost 0.3, first ember 0.55 and last 1.05. The real times below assume her clock, with the world held for 0.52 s. The experience lead maps the two.

| Real time | Beat | What happens |
|---|---|---|
| 0.00 | Press | The confirm (a flint catching over a glassy shimmer), the pad ticks, the world drops to 8%, missiles within 6 m burst into embers, and the staff's head flares |
| 0.00 to 0.22 | Draw | The web lights within 14 m. Motes stream into the staff's head. She swings the staff up in both hands into the key pose, her hair and robe lift, and her breath smokes once at night |
| 0.22 to 0.52 | Hold | The staff's head is the brightest thing on the screen: an amber flame with a blue heart, lighting her face and the line of her body from above. The riser climbs, and from 0.42 there is silence |
| 0.52 | Release | The world's clock returns, and she drives the staff down (0.15 s) |
| 0.67 | Frost | The butt meets the ground: a 3-frame hitstop, a deep thud and a 0.2 vertical shake. The frost races to the reach in 0.4 s with an irregular, fingered front, and bodies glaze as it reaches them. Color returns cold (ford-blue first; the warmth is held back). The wind drops out. A cold, low bounce light, and no flash |
| 0.67 to 0.92 | The look up | Her head comes up and holds. The camera lifts 8° and pulls out 15%, and a roar grows in the sky |
| 0.92 to 1.42 | Embers | Twelve impacts with 2-frame hitstops. Each ember is a molten streak at one shared angle with a smoke trail, and the first three or four carry moving lights, so the shadows swing as they fall. Each impact: flame jets turned along their way on the screen, ice shards, a burst of steam, and the frozen near it shattering into ice and ember. Char splashes onto the wet frost. The pad ticks with each |
| 1.42 | The last word | The last ember lands on the toughest thing in reach (a boss takes four): a 6-frame hitstop, shake 0.6, the full BOOM (§2.2), and her sweep down |
| 1.42 to 6 | Return | Steam rises in columns and drifts. The frost melts back from its edges, leaving charred, wet ground with meltwater glints. The web glows amber under the melt, then sinks dark, and sparks lift off the shattered. The camera settles over 0.6 s. The scars are gone by 6 s |

### 4.2 What is built

- **The grammar, once:**
  - her clock and the world's 8%;
  - the camera envelope;
  - Flare hitstop;
  - the drain and the repaint;
  - the web;
  - the shadowed Spend light;
  - the death ripple and the hue rims;
  - the HUD dim and the damage-number rule;
  - the catch, the confirm, the inhale, the gap, the four-layer Spend, the crowd's bed, the designed duck and gate priority;
  - rumble;
  - the clutch, banking and the empty press;
  - the settings.
- **Burns Twice:**
  - her clip on the staff grip: wind-up, key pose, drive, the held look up, the sweep, the recovery. His comes when the owner releases the hero;
  - a frost growth shader. The front is a growth-time map: distance, plus low-frequency noise, plus fingers that race ahead. The crystal comes from two multiplied panning layers, so it never visibly repeats (Diablo III's method), using frost plates we make ourselves through ComfyUI gpu turns, logged;
  - the body glaze in the crowd's view;
  - ember streaks with smoke, three or four of them carrying moving lights;
  - the impact set, made new for it: its own flame jets, an ice-shard atlas, steam;
  - shatter deaths;
  - char and wet ground;
  - all three lamps.
  - Its sound set: the staff's thud, the ice creak, the sky's roar, the hiss-and-glass impacts, the steam. The owner's ice recordings (§2.5) would lift it most.

### 4.3 What "done" looks like

Done is seen at full resolution, at 1920×1080 and at the owner's own screen size, at both cameras (story 56° and 23 m; arena 64° and 31 m), in each of these:
1. a packed night (tier 3, at least 250 on screen): the main shot;
2. an empty field;
3. by day;
4. at the edge (below a quarter);
5. with a boss in reach;
6. each of the three lamps;
7. Banked.

It is also:
- **captured:** a 60 fps capture of each for the owner, plus a frame strip at the named beats (ready, press +1 frame, the Draw's end, the Hold, frost +0.1 and +0.3 s, the first impact, the last, Return +1 s and +3 s);
- **heard** by the owner, and **felt** on a pad;
- **measured:** the luminance budget (§1.6), and the frame time during the Spend in the packed night.

### 4.4 Judge checklist (a fresh max judge, at full resolution)

1. Ready reads on her in a packed horde without the HUD.
2. The press answers on frame 1: the sound, the staff's flare, the burnt missiles, the pad.
3. The web shows the reach and fades at its edge: no ring and no hard edge.
4. The key pose is a poster at a 100% crop:
   - a clear line through her body;
   - the staff never through her body, hair or hands, and her wrists natural;
   - her face lit by the staff, her hair and robe lifting;
   - powerful and attractive, never awkward.
5. In the Hold the world waits (the enemies near-still), and nothing shakes.
6. The gap is heard as a held breath, never as a dropout.
7. The frost:
   - is crystalline, and travels;
   - has an irregular front, with no repeat visible;
   - is a mid-value glaze, never white, and its frozen bodies are glazed, not cut-outs.
8. Color returns from her outward, with no visible line.
9. The embers:
   - are angled molten streaks with smoke, never vertical bars;
   - have their cores under the knee;
   - swing the shadows with their light.
10. Each impact shows turned flame jets, ice shards, steam, and char on the wet frost. The shatters ripple, and no frame empties the crowd at once.
11. The last ember lands on the toughest thing in reach with the big hitstop. The transient, the hitstop, the shake, the rumble and the light's peak share one frame.
12. A boss's danger marks read through every frame.
13. The luminance budget holds (the numbers are attached).
14. The Return shows steam, melt, char and the sinking web, and the scars are gone by 6 s.
15. An empty field still gets a BOOM.
16. The clutch:
   - the Draw rushes;
   - the heartbeat stops, then returns;
   - the light comes home into her.
17. Each lamp is told at a glance by its shape, not its number.
18. By day it still reads.
19. The sound:
   - all four layers are there;
   - nothing clips;
   - the crowd's deaths aren't mud;
   - **the owner has listened**.
20. The frame time is measured and within the performance budget.
21. The bar: is this the best version of this moment in any game? Would the owner say "oh shit"?

---

## 5. Who makes what

**Experience: camera and time** (the lead the coordinator names)
- Owns: her clock against the world's 8%; the Spend frame, aligned with classes; the camera envelope; Flare hitstop (the cooldown waived, her at 10%); shake on the transient frame; the settings; the rumble envelopes in `Haptics`; the HUD dim hooks, with UI.
- For the slice: all of it, built once.

**Skills VFX**
- Owns:
  - the drain and the repaint (global uniforms);
  - the web;
  - the Spend light and its shadows;
  - the front;
  - the hue rims under the white cap;
  - the dark beds;
  - each Flare's layers (§3);
  - textures, made through ComfyUI gpu turns or procedurally, logged in provenance;
  - a frame-luminance measuring script.
- For the slice: §4.2's Burns Twice layers.

**Animation, including the crowd's view**
- Owns, for each Flare and both heroes:
  - the wind-up, key pose, release and recovery, with shared contact frames;
  - the inhale, and the updraft on hair and cloth;
  - the face for each calling: the warden's set jaw, the reaver's bared teeth, the arcanist's parted lips, the stalker's calm;
  - The Road's Toll's twelve poses;
  - the sheath (The Road's Toll, Through and Through), as part of the owner's sheathing system;
  - the death ripple and the struck shudder in the crowd's view;
  - the shield-through-body measure, applied to every Flare.
- New grips come with their roads.
- For the slice: her Burns Twice clip.

**Sound** (the skills lead's `Sfx`, or a sound lead)
- Owns all of §2.
- For the slice: the shared sounds, plus Burns Twice's set.

**Classes** (the numbers stay theirs)
- Owns: confirming the roles; the empty forms for the Flares that choose targets (The Butcher's Bill, The Road's Toll, The Branding, Drag Them Under); the Stand's move-blend; the Flare's own clock in the game logic.
- For the slice: aligning the clock.

**Story**
- Owns: confirming four touches:
  1. the light drawn up out of the ground and returned to it;
  2. her one smoking breath at night;
  3. the Watch's dead rising, and whether they murmur the evening call;
  4. the knot sinking under.
- For the slice: the first two.

**UI**
- Owns: the HUD's Flare lamp (the ready breath, the banked second wick, the pour on the press, the ember answering); the dim; the damage-number rule.
- For the slice: the lamp and the dim.

**Arena art**
- Owns: lamps in reach flaring and guttering with a Flare; grass, banners and puddles answering the Spend.
- For the slice: lamps and grass.

**Performance**
- Owns: one shadowed light for 0.4 to 0.6 s in a packed horde; particle overdraw at the Spend; the decal count over a minute of Flares.
- For the slice: measure the Spend.

**The owner**
- Owns: listening; the bronze bell and the ice recordings, if he likes (§2.5); any royalty-free audio that isn't CC0.
- For the slice: watch the 60 fps capture, listen, and hold the pad.

---

## Sources

- Final Smash staging ("Standby Mode": screen darkens, aura, glowing eyes): https://www.ssbwiki.com/Final_smash
- Sakurai on hitstop (the struck shake more, along the blow, decaying; the attacker keeps moving a little): https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/
- Path of Exile, Vaal skill retrospective: https://www.pathofexile.com/forum/view-thread/952058
- Diablo IV's ultimates as the weakest skills: https://mein-mmo.de/diablo-4-ultimative-skills-sind-schwach/
- Diablo III VFX methods (multiplied textures, blend-add in crowds): https://jangafx.com/insights/diablo-3-vfx-experiments
- Riot's VFX style guide (clarity, visuals matching hitboxes, importance by size, value, saturation): https://nexus.leagueoflegends.com/wp-content/uploads/2017/10/VFX_Styleguide_final_public_hidpjqwx7lqyx0pjj3ss.pdf
- Vampire Survivors' Flashing VFX option, and the pentagram flash brought under it: https://vampire.survivors.wiki/w/Options, https://www.gonintendo.com/contents/25984-vampire-survivors-updated-to-ver-1-6-108
- WCAG 2.3.1 (three flashes): https://www.w3.org/WAI/WCAG21/Understanding/three-flashes-or-below-threshold
- Responsiveness over anticipation for player actions: https://www.gamedeveloper.com/programming/feature-programming-responsiveness-
- Path of Exile 2's Tempest Bell (kept distinct from ours): https://poe2wiki.net/wiki/Tempest_Bell
- Overwatch, "Play by Sound": https://pcgamesn.com/overwatch/overwatch-devs-on-creating-a-game-you-can-play-by-sound-and-announcing-dolby-atmos-support, https://audiokinetic.com/en/blog/overwatch-game-audio-using-wwise-1
- DICE's HDR audio, and Battlefield's clearer mixes: https://frostbite.com/frostbite/news/how-hdr-audio-makes-battlefield-bad-company-go-boom, https://designingsound.org/2013/06/21/finding-your-way-with-high-dynamic-range-audio-in-wwise/, https://www.asoundeffect.com/?p=41471
- Impact layering and space before the hit: https://sounddesign.irpr.agency/guides/how-to-add-weight-to-impacts/, https://violetrecording.com/how-to-make-impact-sounds/
- Rumble (two motors; each call replaces the last): https://wiki.libsdl.org/SDL2/SDL_GameControllerRumble, https://devdocs.xbox.com/reference/input/gameinput/structs/gameinputrumbleparams.md
- In the repo: `CLASSES.md` §3, `STORY_BIBLE.md` §1 (ember, the lamps, the Unchained's hours), `docs/feel/AUDIT.md` §5 and §7, `docs/team/skills.md`, `docs/handoff/skills.md`.

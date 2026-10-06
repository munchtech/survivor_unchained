# The owner's notes waiting for the leads

Every lead reads this after RESUME.md. When you take a note into your work, mark it done here with your commit. The main session keeps it current.

## 5 October 2026 (from playing the build; the leads were stopped by the weekly limit, so these wait)

### UI design and UI art: the HUD is the keystone

The owner: "the bottom skill bar and health globes and stuff need to be incredible, its a keystone of that kind of game." The bottom area with the abilities "is a relic of our old garbage ui".

- **Ember bar to the bottom** (or somewhere else). The boss's health bar then moves up to the top, where the ember bar was, so it never overlaps help text or a boss's banner. "ember on the bottom sliding the boss stuff up."
- **Timer and stats** (the clock, kills, gold) move to a lower corner, out of the top centre.
- **The skill bar, the draught, the dash and the art in hand need revisiting,** with symmetry: one composed group, not loose pieces. Health globe, skill slots, art, draught and dash must read as one designed instrument.
- **The minimap** needs the same pass.
- **"We still have bad texture bordering on a lot of UI elements"**: the skill bar's frame and the health globe's ring especially. Remake them in the restrained, soulful style (iron, chain, ember), with no muddy textured borders.
- **Journal and Map** should not resize the panel to full screen ("feels bad"). Keep them in the same half-window panel as the rest of the book, with an option to expand. Cut their dead space; centre what's in them.
- **The tab chain:** "I love the direction just needs polish."
- **Help text** (the tips): no shrinking from big to small; "more distracting not less". Show it at its full size from the start. It shouldn't come up at bad times anyway; if it does, that gets revisited later.
- **Liked:** "I'm a giant fan of some of the hexes or just lines you put on indicators for dodging. nice work." (Combat and skills VFX: keep that language for danger marks.)

### Combat and animation: moving through the crowd

- **"Pushing mobs by running into them seems awkward."** Rethink body-blocking and push as she runs into the horde: how the best survivors and ARPGs handle it (slip through, soft separation, brief knock-aside on a dash).
- **"We don't look very smooth while running, a little blurry pixelated."** Find out why: TAA or motion-blur smearing, a low-resolution shadow or a crowd LOD near her, the camera's follow judder, or the run clip itself. Fix it so her run is crisp and smooth at the game camera. Performance, animation and the experience director share this.

### Story: the writing needs emotional power

The owner: "we need better writing", "we need emotional power", "a mind breaking twist dosn't exist at the moment, and gut wrenching stuff dosn't hit too hard."

- **Maeca:** drop "Barefoot"; she is just Maeca. Her reason for wanting Holloway dead must be a real failing, far beyond "didn't get boots". "The barefoot thing is a little silly."
- **Holloway:** he was a good man. Through great writing, he did something that got them all killed. Now he's a drunkard trying his best to forget, who still protects, because he is a GOOD man.
- **Brannoc:** his arc, that he made the very thing that got his daughter killed, "needs to hit HARD. so hard."
- **Generally:** some beats are good already, but the gut-wrenching ones must land. Find the moments that should break the player's heart and build them up. Plant, pay off, let silence work.
- **A twist:** the story needs a mind-breaking twist, one that re-reads what came before. Propose one or two that fit the Ember Watch, the Order of the Morning Light and her past, with where each is planted, for the owner's choice. Don't bolt one on.

### The heroine's face, paints and hair: the order (5 October, later)

- **Order:** the face to perfect first (v10, v11 and so on); then the face paints and sliders (the hand-drawn paints are "really bad": kohl lands on her forehead, ash is a smudge, and so on; the sliders "don't do enough"); then hair, over many rounds ("hair will need way more than 2-3 rounds").
- **The bar for "perfect":**
  - at the Look close-up, beside each face's reference, no obvious "this is a render" tell;
  - grain at least 0.9 of the photo's;
  - tones and irises within a few percent;
  - no seams, bands or blobs;
  - it holds at play distance.
- **Freckles as a Look choice** (paints and sliders pass): an amount from none to heavy, off by default on every face, her own included ("none is probably the preferred for most people but they are a fun rarity too"), so any face the player builds can have them or not. The face lead designs the freckles themselves from her_23 (sparse, soft, varied, sun-placed).
- **Distance:** "not seeing any face at long distance is tragic." When the book opens (Pack, Self, Arts), the camera comes in close enough that her face reads. At play zoom she always has SOME face: eyes, brows, a mouth.

### Animation: an artists' kit for later (after the face, paints and hair)

For the owner's post-build work with professional artists:
- animator-friendly Blender rigs for her and the hero: IK/FK, hands and fingers, face keys, jiggle bones, one shared skeleton;
- the round trip back into the game: FBX or glTF in, through our retargeting and import;
- a library of building blocks: standing, sitting, lying, kneeling and leaning, with transitions, and the vocabulary of romance (a kiss, an embrace, holding, lying entwined, sitting close, undressing to the game's existing nudity);
- a two-character staging scene with cameras and light, and documentation.

- **Asked for by name:** a paired "lift and kiss, then carry to the bed" sequence:
  - he lifts her (or she jumps up), her legs round his waist and arms round his neck, his hands under her thighs;
  - forehead to forehead, then a kiss, with a held loop;
  - a carry walk loop with matched steps and weight, through a door;
  - he lowers her onto the bed and leans over her, ending there.

  The pair animate as one synced pair, with contacts locked. The owner's reference was a stock photo (pose reference only, never an asset).

- **Undressing gestures, up to just before nudity beyond what the game already shows:**
  - reaching behind to unhook a clasp;
  - a strap slipping off a shoulder;
  - unlacing a corset;
  - unbuckling a belt;
  - a cloak or shirt coming off;
  - his or her hands at the fastenings.

  Each ends at the moment before exposure. This needs garment control bones on the outfits' clasps, straps and laces, so a piece can open, slip or loosen, in the rig for the artists too.

- **Cinematic versions** (the cinematics lead with animation): each romance sequence (the lift, kiss and carry; the undressing gestures; lying together) also staged in-engine in the game's cinematic system.
  - Shot lists, cameras, lighting, blocking and timing, each ending at the fade.
  - They serve as the game's own love-scene cinematics (which fade to black; "Warmed" only notes it happened) and as staged templates the owner's artists continue from: the same cameras and lights, exportable with the rigs.

Not made by us: poses or animation whose purpose is a sex act, or that show nudity beyond the game's own coverage rules. That's for the owner's artists.

### Sound

- Every skill now has its own sounds (skills VFX), but no agent can hear them. The owner will say which sound bad after playing.

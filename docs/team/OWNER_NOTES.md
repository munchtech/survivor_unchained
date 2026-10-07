# The owner's notes waiting for the leads

Every lead reads this after RESUME.md. When you take a note into your work, mark it done here with your commit. The main session keeps it current.

## 6 October 2026 (after the editor's notes 02 on Act 1)

### Story: love scenes and showing, not telling

- **Love scenes: B** (the lovers' own lines over black). Apply the editor's four conditions (notes 02 §10); A stays only as the fallback.
- **"Absolutely"** to the editor's verdict that the heaviest moments are told, not shown. Build them as cinematics.

### Cinematics: a second, storybook style

The owner: "lets introduce another cheaper, but stylisticly and artistically STILL PERFECT version of like a storybook type cinematic drawings that can show true anguish much better like a flip book."
- **Storybook (new):** the owner, correcting: "well not a flipbook, but I think you know the kind of cinematic i'm talking about". That is the illustrated story cinematic of the best ARPGs (Diablo III's drawn act cinematics are the touchstone): painted, inked illustrations in layers, with slow camera moves, parallax, and living touches (fire, smoke, cloth, rain, ink that spreads), cut and scored like film. Cheaper to make, never cheaper-looking. Its job is anguish that the realistic engine can't carry: faces drawn at the height of grief.
  - **Brannoc's realisation** (C14, the walk to the ford): storybook.
  - **Holloway locking everyone out** (the lid on the ladder, Ninety-two's night): storybook.
- **Realistic (as before):** **the burial** (C08, made a trunk scene) stays an in-engine cinematic.
- The drawings carry our own soul (rooted in the Ember Watch, not generic fantasy illustration), with no AI look; any generated art follows the provenance rules (ours, local, logged).

### Animation: joints and motion to perfection (6 October)

Rendering fixes how motion is drawn; joints and rig are animation's (next free slot, raised to `su-lead-max`). The owner: "the motions that get scuffed are ... bad, unnatural movements with respect to wrists - follow through motion joint to joint, some elbow pinching or arms going through body or breast, some sliding. a lot is GOOD but we want perfection."
- **Wrists:** unnatural bends and rolls.
- **Follow-through, joint to joint:** motion should flow and overlap down the chain (shoulder to elbow to wrist to fingers), not move as one stiff piece.
- **Elbows pinching** (skinning: weights, twist and helper bones, corrective shapes).
- **Arms through her body or breasts:** collision-aware arm paths in every clip, with jiggle on. Check with the outfits lead, because the same weights carry the garments.
- **Sliding:** planted feet that hold.
- Audit her and the hero in every clip at 1:1, in motion; keep what's good.

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

### Story: the owner's choices on the treatment (docs/story/TREATMENT.md §10)

The owner loved the editor's letter. On the treatment:
1. **The twists:** all four, yes. §3.1 "You did this", §3.2 and §4 "Ninety-two", §3.3 the woman with the lamp, §3.4 the voice.
2. **The narrator** recast as a woman of about sixty: yes.
3. **Love scenes under §3.4:** undecided. Write both, the narration as unvoiced text and the lovers' own lines, for the owner to choose on the page.
4. **Holloway risen at his own gate** the dusk after: keep.
5. **The nod** as the game's first choice: yes.
6. **The lamp-iron** as her night lantern: yes.
7. **The lie to Brannoc** (settled): "we can't get punished from gameplay perspective - he just talks to us like he hates us or ignores us but dosn't hamper gameplay core stuff with respect to crafting and maps." No gameplay cost at all: prices, commissions, masterworks, crafting and maps are as on the truth route. The cost is only in how he speaks to her: hatred or silence. *Done (9b0cd04f): every first answer gives the truth's best standing; a test plays all four answers through four nights and checks prices, the bed, shelves, commissions, his terms and maps match. Act 2 must change his "starting to trust you" label once he learns.*
- **Holloway risen at his gate:** on the fourth dusk, after three days of knocking (the editor's advice; the owner agreed).
- **The second crossing:** the harshest version. The Kiln Ford comes back in Act 2, after he has sold the irons (the grey mare, Jory's drowning, Aldo's widow). "the harshest versions are what were aiming for."
8. **"Wick"** for her, and the lamplings renamed (not "Wick" or "Wick-Mother"; the writer suggested "Stub"): yes.
- **Holloway's act (owner, after the editor's notes):** option (b): with the lamp in his eyes, he took the living on the ladder for the dead, and his lid made the dead he feared. A great man's true mistake: "its a decision we can make which makes it more horrifying". Cut boots from Holloway entirely.
- **"Wick" replaced** (players hear John Wick): "maybe something else like flame or spark". The main session suggests "Spark" ("Lamp's lit, Spark."); the writer reads Spark and Flame aloud in her lines and picks. The lamplings are renamed either way.
- **Boots:** nobody dies because of footwear. Holloway's act is a great man's terrible judgement call (the lid on the ladder; ninety-one counted). The editor checks that no boot detail still reads as silly.

### The heroine's face, paints and hair: the order (5 October, later)

- **Order:** the face to perfect first (v10, v11 and so on); then the face paints and sliders (the hand-drawn paints are "really bad": kohl lands on her forehead, ash is a smudge, and so on; the sliders "don't do enough"); then hair, over many rounds ("hair will need way more than 2-3 rounds").
- **The bar for "perfect":**
  - at the Look close-up, beside each face's reference, no obvious "this is a render" tell;
  - grain at least 0.9 of the photo's;
  - tones and irises within a few percent;
  - no seams, bands or blobs;
  - it holds at play distance.
- **Freckles as a Look choice** (paints and sliders pass): an amount from none to heavy, each preset follows its own portrait (freckles where the reference shows them, at its amount; "some of the presets can have freckles if they go with the reference"), a face the player builds starts at none ("none is probably the preferred for most people but they are a fun rarity too"), and the amount is always adjustable. The face lead designs the freckles themselves from her_23 (sparse, soft, varied, sun-placed).
- **Distance:** "not seeing any face at long distance is tragic." When the book opens (Pack, Self, Arts), the camera comes in close enough that her face reads. At play zoom she always has SOME face: eyes, brows, a mouth.
- *Taken up in face v11 (worktree-agent-a43570e07edbe40b2): tones and irises within a few per cent, her face at play zoom, freckle defaults per portrait; grain and the other faces' brows still short of the bar (docs/team/face.md).*

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

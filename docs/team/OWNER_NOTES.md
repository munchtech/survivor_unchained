# The owner's notes waiting for the leads

Every lead reads this after RESUME.md. When you take a note into your work, mark it done here with your commit. The main session keeps it current.

## 11 October 2026

### The twists

- Approved: A ("Not yet": Chid made you) and B ("Count's right": Holloway knew). Then "I'm still missing a WHAT THE FUCK kinda moment". Chosen from TWIST_WTF.md: option 1, "It takes less than it did" (every rise costs one life in the valley; the ledger past line 27 is the player's own deaths from the save). The owner chose it knowing that dying in the endless then costs a life.

### Neck length

- On the neck fixes (seam, grey jaw shade): "the neck might have been too long anyway, maybe the bug helps find the perfect". Then: "said might :) It could be perfect - and maybe a design boon that lets helmets be cool later without taking bust view". So it is an open question, not a change: the length may be right, and a long neck leaves room for helmets, gorgets and high collars without covering the bust. The face lead shows today's neck beside one or two shorter lengths (front and profile, at the Look and in play), with a helmet or gorget silhouette on each if one is to hand, and the judge weighs both looks. The owner picks; today's length is a full option. Outfits and animation are told before any change ships.

### Classes, trees and ultimates

- Each calling gets two types: warden two-hander and shield tank; stalker dual-wield melee and ranged; arcanist two caster styles; reaver two of its own.
- Skill trees: "as simple to figure out as just clicking and having fun, but as complex to master to have fun planning". Study PoE, Last Epoch, Diablo and Grim Dawn.
- In arenas, anyone can do anything (as in PoE), but on-calling choices are easier or better. More skills, mostly synergy.
- Q / right-click stops being a dash and becomes a customizable ULTIMATE: it charges up, works as a limit-break life-saver, and is the heart of class identity. "it should be AWESOME. it should look AWESOME."
- Plan first (docs/design/CLASSES.md); the owner approves before code.
- The plan (CLASSES.md: the Lamps tree, the Flare ultimates, two types per calling) was approved with "go with all 8 recommendations". Build order: phases 1 to 3 first (systems; the beat and one Flare per calling; the Lamps screen and HUD).

### Outfits: trim at the bust (an option, sent to the outfits lead)
"can add leather trim to ranger, and white feathery trim to arcanist parts of their clothing in the bust if it makes it easier to clean them up nicely - just only increase the skin we cover slightly if you do decide to do that route." Leather trim for the Ranger, white feathery trim for the Arcanist, on the bust edges, where it gives a cleaner edge; the extra coverage stays slight.

### Rendering: the heroine's triangle budget (approved, after the wolf fur)
The owner asked whether her detail (about 1M triangles and 95+ draws in Warden, at about 150 px tall in play) will lag with a full crowd, and suggested AAA-style models by distance that keep what matters. Their answer to the plan: "all those ideas seem worthwhile!" So: a gameplay LOD that keeps the bust, hips, gear effects and weapon dense and cuts elsewhere; body hidden under each outfit removed; the lowest LOD for shadows; pieces merged by material; fewer fur shells at range. Full detail always at the title, in creation, in conversations, close-ups and cinematics ("we worked very hard on these models so they show there no matter what"). No measuring phase (the owner: "we can skip measuring and move to implementing"); judged so play size looks the same. The rendering lead builds it as a post-export step.

### Story: a big twist, sophistication, and early lines settled for voicing
"lets fire up the writer - we need a big twist nobody sees coming, maybe chid being evil? and another pass of sophistication. also I would like to get some of the early lines mostly settled so I can truly begin my elevenlabs voices" The writer brings three twist options first (Chid evil among them), because a twist is planted in the early lines. Then the Prologue and the opening of Act 1 are locked for recording, after an editor's pass.

### Spelling
The owner is American: the "British spelling" rule is dropped. The game's player-facing text is being switched to American spelling (the voiced lines' audio is renamed to match).

## 10 October 2026

### Face lead (skin): neck discolouration on every face
The owner, with two crops (`docs/team/owner_crops/2026-10-10_neck_1.png`, `_2.png`): "leads are aware of neck discolorations on every face right?" Under the jaw and down the side of the neck the skin goes blotchy grey-violet, bruise-like, with a darker vertical band. Not yet tracked as such (the face list had only "neck grain" and "jaw-edge spots"; the hair judge saw shadow facets on Highborn's neck). Find the cause at the root on every face (likely candidates: the head-to-body paint graft or seam, the freckle-map blue that now carries the grain up her neck, AO or SSS tint, hair shadow), fix it, and judge each face's neck at 1:1 beside its portrait. Sent to the face lead; any shadow cause goes to rendering.

### Outfits: nipple show-through and boots (the owner's answers to judge 1's taste calls on g2)
- **Nipples:** "both arcanist and ranger could use less nipple poke through, and it should be equal on both". Reduce the nipple point through the cup on the arcanist and the ranger, and make left and right match. (Judge 1 saw the arcanist's uneven and the ranger's nipple point through its cup.)
- **Boots:** "boots need work reaver, and ranger". The reaver's and ranger's boots need work, and the arcanist's white boots too (judge 1 found them flat plastic; the owner: "improve arcanist boots too"). Material and shape to the AAA bar on all three.
- For the outfits lead; recorded with its "paused here" block (branch `worktree-agent-a5ca10091b08dc429`).

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

### Face lead (skin): speckles over her breasts (6 October)

The owner: "we removed specklage on our shoulder/upper chest before to success, but noticed in the face tests we have a lot of specklage over the breasts. we want smooth skin aside from pores / freckles. the specklage seemed unintended and still does - the breasts must look magnificent which they mostly do". Remove it at the root; keep the real pores and freckles. Sent to the face lead.

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
- *Taken up by UI design (worktree-agent-adba22c3df8f39418, docs/ui_review/build9): all seven built (her irons at the foot, the boss at the top, the tally in the lower right, the minimap's bezel, Journal and Map in the panel with "Open wide", tips full size, the chain polished). The iron is drawn until UI art's pieces land (the spec is in docs/team/ui_design.md).*

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

## 11 October 2026, late: answers to the wind-down questions

- **The Bulwark's rebuke:** "rebuke should probably do a little more damage than that yeah". Raise it above today's under 1% of its night damage, toward the judge's 8-15%, through more or wider rebukes (phase 5's Wider Rebuke, or sooner).
- **The home bonus:** "I think? what does design/theory say?" Design (CLASSES §2.7) says home is easier and better, at most ×1.25. The coordinator's reading: today's ×1.03 is temporary because only one of each road's three signature skills exists; phase 5 should bring it to a clear edge (about ×1.10-×1.25). Accepted for now.
- **Act 1 story bosses:** "yes". Raise their health to offset the Flare (they fall 14-29% sooner).
- **Sunborn's warm jaw and neck:** "judge reccomendation is ok": one try at keeping melanin-rich skin browner in shadow, to match her portrait.
- **Neck length:** "judge decide but consider benefits of long neck (that dosn't look stupid)". The judge picks the length, weighing what a long neck gives (elegance, helmets and gorgets without hiding the bust) as long as it never looks stretched.

## 12 October 2026: classes

- **Light my way and Banked Flame:** "sounds good": the suggested path never lights Banked Flame (its gift only pays if you change how you spend the Flare).
- **Banked Flame is too weak:** "0-5% faster is barely anything though, seems like its a lot of risk with not much reward." Played well, it must be a clear reward worth the 30% slower fill. Sent to the classes lead (options measured, judge picks).

## 12 October 2026: the male hero

- "Begin work on Hero, using the lessons we learned making Heroine to hopefully do it in a fraction of the time and effort and tokens."
- **His body may be remade:** "you can totally make a new one from scratch if ours is lame. but remember sex appeal. muscular defined, attractive". A judge rates the current body against that; if it falls short, rebuild (hero_male.md path A is the start). Replaces "the bodies stay" for him.

## 12 October 2026: the face, two marks

- "most have a double eyebrow thing and a like lip outline above the lip. the lip outline I think is intentional? to show definition/3d? the eyebrow thing might also be i'm not sure. curious about both". Crops in coordinator session ba85aba8's images (1.png eye, 2.png mouth). Sent to the face lead: diagnose (paint vs mesh: brow, lid crease, vermilion border), fix in skin round r12, both on judge j8's checklist at 2x.
- **Cause found (face lead, 12 Oct):** the lip line is the mesh's real upper-lip edge, 3-4 mm above the painted red, shaded on purpose by the shared AO; the double brow is the upper lashes seen from below at the Look. Waiting on the owner: move the paints' red up to the mesh lip (fuller lips, recommended) or soften the shading.

## 12 October 2026, night: lips and the get_up ponytail (answered)
- **Lip line:** the owner, on the fuller-lip recolor: "the fuller lips is probably not great ... it dosnt look so hot". Recolor (a) stopped. Soft lip AO (b) is the default floor (halves the line, keeps the portraits' lips). One solver try at the true fix from the mesh side: bring the sculpt's upper-lip border down to each paint's red. If it fails its judge, (b) ships alone.
- **get_up ponytail:** one more solver round with the braid's method (shoulder capsules in the chain solve, tip-last release); if it fails, today's ponytail (a 0.1 s cut at k46-48) ships. The braid fix is merged (6234da8b).
- **Lips, round 3:** the model-side fix (j8b) failed as a set (drawn-on on six faces; Saffron, Wildling, Sunborn beat today). The owner: "one more round on the lips sure". The last round: taper to the corners, own upper red, the leftover line, per-face size; else per-face or the soft AO alone, and lips close.

## 12 October 2026, night: waiting on the owner (classes)
- **Arena boss phases and Flare bursts:** each arena boss phase has a minimum length, so no Flare burst can speed up an arena boss today (Banked Flame, Called Down). The judge recommends letting Flare damage alone cut a phase's minimum by at most half, tuned so the Flare's share of a boss stays near 35%. If no, Banked Flame stays a story-boss and safety lamp.
- **Banked Flame:** now "Hold two Flares. Each fills 30% slower and strikes 40% harder" (bankers 7.1% faster on Act 1 bosses). The judge says it's the best option measured but not yet the clear reward asked for; the arena answer above decides the rest.
- **get_up ponytail residuals:** accepted (answers below).
- **Lips closed (12 Oct, night):** the last round's fix beat today at rest on five faces (Moonlit, Saffron, Wildling, Hardwon, Fey) but the confirm judge held it: in a smile or open mouth a pink stripe shows under the old line. Per the owner's last-round rule, only the soft-lip shading ships. Reopen only on the owner's word (it would need the red carried to the mouth line and the smile shapes corrected).
- **Neck (done, judged):** the far neck now reads as cool rim light, not discolored skin (judge jn1); ships with the next skin branch. Faint residuals written in RESUME.

## 12 October 2026, night: answers (to the new coordinator)
- The owner: "yes to both, accept ponytail and let arena phases shorten and tighter nipple shape suggestion".
- **get_up ponytail residuals:** accepted as shipped (k44-46 jaw tuft, k38-42 stiff flick, k50-51 drop); a later polish pass only.
- **Arena boss phases:** yes. Flare damage alone may cut an arena boss phase's minimum length, by at most half, tuned so the Flare's share of a boss stays near 35% (judge's narrow version). Sent to the classes lead; Banked Flame's reward is then measured in arenas too.
- **Nipple rise:** the judge's suggestion accepted: keep the owner's 1.5 mm height, give it a tighter, more defined shape so it reads. Sent to the outfits lead.
- **Nipple shape, later the same night:** "the new nipples i see testing are not great, if its adding a ton of work they were kinda ok before I think, if they don't vastly improve in the next pass just move on with how they were". One more pass at most, judged against the old shape; unless it's a big improvement, the old rise ships as it was. Sent to the outfits lead.

## 12 October 2026, night: the close-up camera and the hero
- On a test shot of her zoomed in in town: "i like this being a feature a great deal, allow for mousewheel to view our character like that when in town or when we go idle - its a great way to keep sex appeal when we get to endgame and don't see zoom ins much while farming tough stuff". A camera lead builds it on `camera-1` (wheel in safe zones; idle close-up anywhere with no enemy near; a setting to turn idle off).
- "start the hero too if/when a blender slot frees": the male hero starts when the first Blender lead (animation, face or outfits) stops.
- **Nipple shape: closed (12 Oct, night).** Judge 11 put the tighter 1.5 mm plateau (f2) beside the old shape (e2) and ruled REVERT (read as a rivet or bead with a hard rim; chips at the tips). The old shape ships exactly as it was (outfits fa8d70c8).

## 12 October 2026, night: the face at character select
- Double brow: the owner's crop came from character select during a test ("and were sure we fixed the double eyebrows?"). The face lead traces which build; the re-judge checks the brow at the Look, the play camera and a close-up.
- "some faces have nostril and ear issues - see the like lump in the nose" (crops in coordinator 33ad5b17's images, 3.png and 4.png). The ear is the ear lobe already on B2 (the owner: "thats it"). The nostril lump went to the face lead: cause, all ten faces at 2x, fixed before the face ships.
- **Priority today (12 Oct, night):** "yes, prioritize face and outfits, hold the hero". Face and outfits get the Blender turns (outfits may run parallel solvers); animation pauses after reach_coals merges; the hero stays held.

## 12 October 2026, night: the shield, the idle wrists, sheathing in town
- "the shield is awful ... the shield just completely goes into her body all the time - surprised nobody caught it yet. but we haven't gotten to asset management too hard yet"; "that idle pose - also seen in character select, has some really awkward wrist action going on"; "shield on back (weapons in general sheathed) in town is a great idea".
- Sent to the animation lead (after reach_coals, instead of pausing): a shield-and-weapon-through-body measure in the motion check, standing on every animation judge's checklist; fix the idle's wrists and shield arm; then the worst clips; then a plan for sheathed weapons in safe zones (sockets, a sheathe/draw, a town idle, the code hook).

## 12 October 2026, late night: waiting on the owner (classes)
- **Merged:** arena boss phases shorten by the Flare's share of the phase's health (at most half, never under 6 s); arena bosses fall 6-15% faster for everyone. Banked Flame is now "Hold two Flares. The second fills half as fast; a Flare fired with both held strikes 75% harder": saving both for a boss is 13-25% faster with no falls; lighting it without saving costs nothing.
- **Question:** should Act 1's story bosses also be shortened by the Flare? Today they aren't (they were tuned to within 3%).
- For the UI/codex lead later: teach players that a Flare shortens the boss phase it lands in.

## 13 October 2026: answers (to coordinator 59a43b82)
- **Act 1 story bosses and the Flare:** "why wouldn't flare shorten things? its supposed to be epic. an 'oh shit' button. a planned 'BOOM' button. a 'clear the whole room' button." Yes: the Flare cuts story-boss phases too (lift `StoryBoss.FlareCuts`), and more broadly it must feel like a planned BOOM that clears the room, not a quiet damage bump. Sent to the classes lead (measure story bosses with the cut, and check what one Flare does to a crowd).
- **Restart:** the owner's "go" for the new coordinator: face, outfits, animation and classes restarted; hero still held.
- **Sheathing in town (13 October):** "will that copy paste with new assets? - having to do it special everytime we add something is rough ... we can skip a visibible draw/sheathe motion for now thats extra icing polish later." Sent to animation: sockets keyed by weapon type, each asset carries a grip and sheath anchor (falls back to its bounds), clearance from the worn outfit, armscheck runs every type against every outfit; the anchor rule written for Marionette's export. No draw/sheathe clip for now.
- **Flares are specialized (13 October, later):** "flares in general don't need to be big boss hits - they are specialized. *most* are for arena mode type screen clears or saves etc - but some can be single target (or one or the other based on context). but pushing a flare should always do something visible." Sent to classes: a role per Flare (clear, save, single target, context), the crowd side measured first, every press visible.
- **Lips and the smile (13 October):** the owner invited a challenge on the lip call. The coordinator: the no to fuller lips stands (that recolor was poor), but the open-mouth smile (j8d smile5.jpg) is below the bar (no upper teeth, red interior with an orange glow, corner smudges). The owner: "yes queue the smile pass after the face ships". The pass: upper teeth, mouth interior, corner creases, and the at-rest lip fix for Moonlit, Saffron, Wildling, Hardwon and Fey carried into the smile shapes; the soft version ships unless it clearly wins.
- **Pace (13 October):** "how are we looking at getting either face or outfits done in the next 12 hours?" Face aimed at shipping first (rj3, then face/ship); outfits aimed at a first judged set, failing parts gated off rather than chased.
- **Not chasing, recalled (13 October):** "recall your order about not chasing. we want perfection remember, within reason. for example I think the ear / lobe area will fail and need fixing". No deadline: failing parts are fixed, not switched off to make time. The ear lobe moves from B2 into the face ship.
- **Flares, the look (13 October):** "I'm simply anxious to begin building super epic flare animations. like beyond anything we've done yet with effects and just awesomeness"; "lets squeeze that in at the next handoff, breaking the max rule just this once (especially if some will be finishing in the next day)". A max-effort look director writes docs/design/FLARE_LOOK.md now (fifth agent, within the cap); the skills VFX build lead starts at the next lead handoff as a one-time sixth lead.
- **Flares, answers (13 October):** story touches OK (the light drawn up and returned, her smoking breath at night, the Watch's dead rising, the knot sinking); the recording list "sure" (FLARE_LOOK §2.5: the bronze bell first). "is burns twice using our existing effects from spells? flares should be unique. I really want these to be epic, not to mention our existing effects aren't perfect yet imo." Rule written at the top of FLARE_LOOK: every Flare's art and sound are its own; only engine tools are shared. Spells get their own pass later.
- **Phase 6, the Flare plan (13 October):** "yes to the four questions" (owner lines in docs/handoff/classes.md). (1) Build the first wave: the Long Cut, Drag Them Under, the Branding, One Arrow, plus the Butcher's Bill for a new butcher. (2) Weapons not in the game yet (greatsword, hooked chain, longbow) form in her hands in the calling's color for the Flare and vanish after. (3) The four new modifiers: Thaw-Burst, The Eye, Free Hands, Through the Heart. (4) Each spec's second Flare (waves 6b, 6c) is a separate yes later. Also standing: one role per Flare (6 clear, 4 save, 2 single, 4 context), every press seen, balance never blunts a Flare; Act 1 baseline "pre-Flare 11 Oct", no re-tune.

## 13 October 2026, evening: waiting on the owner (classes, coordinator 1be2d2a9)
- **Merged:** classes-11@bf5963c7, all five wave-6a Flares (the Long Cut, the Butcher's Bill, One Arrow, Drag Them Under, the Branding) within ±2% of their stand-ins on Act 1; good use 14-21% shorter than pre-Flare. Drag Them Under now hooks everything in reach (100% of arena rooms cleared, about 60 chain lines a press).
- **Question (the judge's, not blocking):** should the single-target Flares (the Bill, the Road's Toll, One Arrow when a boss is near) hit a boss harder than the room-clearing ones? Today the Bill takes about a quarter of an arena boss, the same as the Long Cut, which clears 92% of rooms to the Bill's 26%. Yes: they rise until their share of an arena boss sits near 35%, and well-used story fights get shorter than today's 19-21%; a player who never presses is unchanged. The judge recommends yes (verdict item 2, 59a43b82 scratchpad cl11/verdict_6a.md). If no: the Bill and One Arrow still rise until Act 1 sits about 2% faster than plain (CLASSES §7.1: a bossMul never leaves a Flare slower than its stand-in).
- **Answered (13 Oct evening):** the owner: "yes to the single-target Flares hitting bosses harder - thats the whole point of giving up the aoe clear". The Bill, the Road's Toll and One Arrow (when a boss is near) rise until their share of an arena boss sits near 35%; well-used story fights get shorter; never-press unchanged. For the next classes lead.
- **Revised (13 Oct evening, supersedes the 35% line, including 12 Oct's "Flare's share of a boss stays near 35%"):** the owner: "35% is too much. lets nerf the aoe damage ones vs bosses, and buff the ST ones slightly. but 35% is rediculous. maybe 10-15% for the aoe ones. 15-20 for the st ones". Targets for a Flare's share of a boss: room-clearing (AoE) Flares 10-15%, single-target 15-20%. AoE Flares are cut against bosses (their crowd clear stays); single-target ones rise slightly. Re-measure Act 1 and the arena phase cut against these.
- **The floor under the bands (13 Oct evening):** the owner: "as long as the flares are still the hardest hitting abilities, if they aren't then all spells need to do less to bosses". A Flare must stay the hardest-hitting ability against a boss: measure each Flare's single-press boss damage against every skill's best single cast (and its damage in the same window); if any skill beats a Flare, cut skills' boss damage, never raise the Flare past its band.
- **Reversed the same evening: no hidden boss cuts.** The owner: "actually no thats bad. things should hit what their tooltips say"; "we need to just buff the bosses I guess". So every skill and Flare hits a boss for what its tooltip says: no hidden boss-damage multipliers (retire bossMul and any skill-vs-boss cut). The bands (AoE Flares 10-15% of a boss, single-target 15-20%) are reached by raising boss health, and by the Flares' own tooltip numbers (single-target Flares carry the bigger hit, which is their trade for the clear). The floor stands as a check: a Flare stays the hardest-hitting ability against a boss; if it isn't, change visible numbers, never a hidden multiplier.

## 14 October 2026: fuller lips, reopened
- The owner, on the face lead's clay mouth sheet: "the full lips in the face leads current work look nice. but they aren't painted so maybe they aren't idk. I've wavered back and forth on bigger lips". The earlier no to fuller lips is open again. Sent to face successor 20: say whether the clay lips are the shipped shape (if so, the paint is softening the border); then a painted A/B (shipped vs fuller, by paint or a 10-15% shape increase, never a recolour) at the Look camera and the game close-up, day and night, for the owner to pick.

## 14 October 2026: the gloves (from playing the build, Arcanist in town)
- The owner: "something about those gloves just looks bad. its like her hands are giant or going at a very weird angle at the wrists. they definitely aren't sexy female hands. should we drop the gloves and have more delicate hands?. like those fingers just look silly". Screenshot kept in coordinator scratchpad 34daaf5d images\2.webp.
- Sent to outfits successor 20: diagnose (bare hands in the same frame; hand size against her height and face; the glove's offset from the skin), then A = current, B = a thin second-skin glove (about 1 mm or less, tapered fingers, knuckles, slim wrist), C = bare hands, for the owner to pick. The coordinator leans B only if it truly reads delicate, otherwise C. Sent to animation: the hat-brim clip's hard wrist bend and stiff splayed fingers.
- The owner, later: "I don't mind skin tight gloves but I'm wondering if they should be white to match the stockings and maybe cut off at the fingers sexily". Sheet revised: A current; B1 thin fingerless white (the stocking bands' white, a loop or point over the hand, bare fingers with nails); B2 the same in black; C bare hands.

## 14 October 2026: lips sheet (A / B1 / B2) and the breasts
- Lips: the coordinator recommended B1 (red to the sculpt border); the owner: "they are just so big, shouldn't bottom lip be bigger than top lip?" Agreed: B1's upper lip is as tall as the lower. Next: B3 = upper red partway (upper about 2/3 of the lower), lower lip 10-15% fuller by shape, crisp border; sheet A | B3 with measured ratios (face successor 21).
- Breasts: "would another pass at perfecting the breasts cause a cascade of work? I notice in this arcanist testing there are still some indentations and lumps. I don't know if thats in the suit or the breast". Sent to outfits successor 20: diagnostic sheet (suited / suit flat / nude / curvature), which layer, and the fix's cost, before any change. A body change means refitting all four outfits, legal on all four and the jiggle clips.
- Arcanist (the owner, 14 Oct): "lets make the gloves elbow length, and lets sheer off the arm of her leotard leaving just the shoulders". Sent to outfits: shoulder caps, bare upper arm, elbow-length gloves, on every glove option (white or black fingerless, bare hands).
- Lips, decided (14 Oct): "yep b3-15 is a clear winner - however it also clearly needs refinement, it has smudges or missing paint". B3-15 (lower lip about 15% fuller by shape, upper red raised partway, lower:upper about 1.5) to all ten faces after a paint clean-up (even coverage, no gaps or smudges, the pale ridge line gone), judged with the smile pass.
- Hands and proportions (14 Oct): outfits measured her hand at 12.1% of her height (women 10-11%), fingers about 30% too thick; the breast lumps are the Arcanist suit, not her body. The owner: "we should fix it now sure. and other proportion issues like head size? - but we shouldn't need to legal thats nowhere near problem areas and dosn't effect clothing anywhere near them". Done as one body pass: a proportions audit (head, hands, feet, neck, shoulders, hips, limbs) first, then the hands slimmed and shortened to about 11%; no legal run for hands, a vertex diff proves nothing else moved; animation fits grips to the final hand.
- Proportions audit (outfits s21, 14 Oct): hand 12.2% H and 1.05x her forearm; forearm 57 mm short (her wrist hangs 9 cm above her crotch); head small (8.57 heads; ideal 7.75-8); the rest is in band. The owner chose: hands (11%, slimmer) + forearm (+50 mm) in one body pass now; head +0/+3/+6% A/B first, joining the rebuild if approved.

## 14 October 2026, wind-down: waiting on the owner (classes, paused)
- Classes (classes-12@aeba2930, NOT merged, paused for beautification): bossMul retired; the other boss multipliers are shown on the cards. Boss health alone can't reach the bands (the Flare meter fills from a share of boss health), so the fix is: arena boss health ×2.5, no kill-fill near a boss, the lamp growth gone, new Strike powers. Measured: room-clearing Flares 10.1-14.9% of an arena boss; Act 1 all in band; good use 15.8% shorter than pre-Flare. **The cost for the owner to weigh: arena boss fights go from about 65-85 s to about 83-153 s.**
- **A finding for the owner:** damage over time double-dips (each bleed, burn or poison tick re-applies every multiplier to an already-multiplied base), so tooltips undersell it (Whetstone, the roadknife's poison at about 5x the Toll). Fixing it moves every damage-over-time build; queued for phase 7 with a number solver.
- **Answered (14 Oct):** longer arena boss fights (about 83-153 s): "good". Damage over time: "the tooltip can easily say 'and each tick' - nothing is broken there". Keep the mechanic; tooltips state that every multiplier applies to each tick. Not a rebalance; drop it from phase 7's fix list (the hardest-hit check counts it as designed).

## 14 October 2026, night: waiting on the owner (coordinator d7e64ca2)
- **The Arcanist glove pick (ANSWERED 14 Oct, below):** A current black leather, B1 white satin fingerless, B2 black satin fingerless, C bare hands; all with shoulder caps and a bare upper arm. Sheets: `survivorsunchained_inputs\scratch_d7e64ca2\outfits_s23\gloves_options_play.jpg` and `gloves_options_detail.jpg`. Judge gl2 SEND, recommends B1 about 60/40 over B2; gl1 leaned B2. The coordinator recommends B1. The pick starts the one body build (RESUME "14 October, night").
- **Optional:** the title camera 15% closer, so she reads bigger (the title judge's suggestion; left as it is).
- **Noted:** the Ranger's light-brown pants read close to skin in warm light, and their outer seam looks like a line drawn on her thigh. It's designed, so changing it is a colour call.

## 14 October 2026, night: the glove pick (to coordinator 1cc516bc)
- The owner: "b1 with th gloves but give them style". **B1 is picked:** white satin, fingerless, elbow length, with shoulder caps and a bare upper arm. It becomes the Arcanist default (`ARC_HANDS`, `ARC_GLOVE_MAT`).
- **"Give them style":** B1 as built is a plain white tube (a straight top edge, a flat hand edge, little satin sheen), so it can read like a sleeve or a bandage. The outfits lead designs styled B1s, a taste solver or judge picks the best two or three, and the owner picks from a sheet built on the new body. The coordinator's starting points:
  - (a) a shaped top edge with a soft point over the outer elbow, piped in the leotard's amethyst;
  - (b) a finger cut that's sexy, not cropped: a point to the middle knuckle with a thin loop over the middle finger, piped too;
  - (c) embroidery on the back of the hand: classic three-line glove points, or a small arcane sigil (soul for the Arcanist);
  - (d) a lace band at the top that the stocking tops can match;
  - (e) real satin: a sheen that runs along the forearm, not flat white.
- The style doesn't change her body, so **the one body build starts now** with B1 as the default. The styled glove is shot on the new hand. Whatever style wins carries to the stocking tops.


## 14 October 2026, evening: the crossbow hold (to coordinator 1847d1a6)
- Animation found the crossbow mesh has no pistol grip (the stock sits 85-120 mm off her hand) and `Arms.Seat` skips pistol pieces. The owner picked **(a): add a pistol grip** so her fist seats as it does on the sword (not a stock-under-forearm hold). Animation lead: a grip on the mesh (ours, logged in ASSET_PROVENANCE), an `Arms.Seat` path for it, a WRAP fist and a PocketR line, then the wrist cap at crossbow_shoot; queued after the other weapons' wrist cap.

## 14 October 2026, night: the finish line (to coordinator 1847d1a6)
- The owner: "judge at max zoom seen in game but make sure its critically! it should still look 'perfect' just at those distances". Judges rule at the game's own cameras (play/town, the close-up at its closest zoom, the Look camera), critically, and it must look perfect there; marks only visible beyond them (Blender, 6x crops) are logged, not fixed. Round cap 2-3 per item, then closed as known unless the owner reopens. A fixed list per area per session. README "Working lean", "The finish line".

## 14 October 2026, night: the glove pick (to coordinator 1847d1a6)
- The owner: "louder top if you think its better, as is if not (g3 either way)". **G3 is picked.** The coordinator's call: **the louder top**, because at play zoom G3's piping is a 1 px edge and the owner asked for style. A deeper scallop and a thicker plum cord at the top only; the hand keeps G3's piped knuckle V, with no extra lines. One build, then a max judge at the game cameras (the finish line) on whether it reads in play AND stays elegant; if it reads costume-y, ship G3 as is. Then G3 becomes the Arcanist default; stockings take its ivory and trim.

## 14 October 2026, night: waiting on the owner (coordinator 1847d1a6)
- **ANSWERED (the owner): "if it was meant to be two-handed, then two handed".** Animation makes her left hand grip the chain in chain_strike (and check chain_haul). Was: **chain_strike's left hand:** the clip is meant to be two-handed, but her left hand sits 30-42 cm off the chain's handle. Keep it one-handed (the left free), or make her grip the chain with both hands? (animation lead 33)
- **The owner will check the axe swings in play** (pending). Was: **The axe swings:** the wrist sits at the rig's limit at contact in every axe swing; two solvers couldn't fix it without moving the forearm deeper into her body, so it's closed as known at the round cap. Reopen if it reads as a "weird angle" in play.

## 16 October 2026: project finish line (to coordinator 007ccb1a)
- The owner: "we are gonna move judges to extra instead of max, and were going to accept perfect for what the player can see, not at the big zoom." Judges spawn as `su-lead-max` with `effort: "xhigh"`. Perfect is judged on 1:1 game-camera frames (play/town, the close-up camera, the Look camera); enlarged sheets and crops no longer count, and marks only they show are closed. README "The finish line". The owner then restarted outfits and animation too ("restart them then"), so F1 can land.

## 17 October 2026: effort and focus (to coordinator 59f6a467)
- The owner: "for most coding concerns we can use medium, the leads can orchestrate on high, as can you, but most coding can probably be done on medium, and even more tasks considered menial should be capably done by sonnet or even haiku. Judging is probably importantly kept where it is, and on things that aren't seen all the time can go down to xhigh. we ran out of usage too quickly last week and we have now lowered our perfect standards to 'still AAA quality. still "perfect", just we aren't going in 2x++ zoom anymore. we lost a little bit of focus and our game isn't moving along well enough'". Restart all three; report how close each is to finishing so other parts can begin. README "Effort by kind of work", "Focus".

## 17 October 2026: the close-up turn (from playing, to coordinator 59f6a467)
- The owner: "in town when we zoom in far enough it turns our character around into the idle animation. would prefer to be able to stare at the butt so lets not do that. the idle animation should just be when we open menu like character info or bags (in areas that actually pause like arenas and town, not in the rpg areas of the game we can't pause that - you can't in poe type games as far as I know) and when we truly idle for like a minute. we will eventually have more than just 1 pose, some emotes etc but thats way down the line". Sent to a medium coder: zoom never turns her; the turn and idle pose only with a menu open in town or an arena, or after about 60 s idle (was 12 s). More poses and emotes: later.

## 17 October 2026: Cinematics, the warden into First Light (from playing; for the cinematics lead when it restarts)
- The owner: "we go straight from the warden cinematic into a 3 second cross the river playtime into another cinematic. that will make players lose interest - have defeating the warden and the stuff stolen by grim also end with the ember going back into the ground cinematic we get from crossing the river". So c03 "The Heart Goes Down" (godot/data/cinematics/c03.json: the warden falls, Grimtunnel steals) runs on into c04a "First Light"'s ember-into-the-ground beat (c04a.json, the north bank at dawn), with no 3-second ford crossing in play between them. The crossing becomes part of the cut (or a transition) and play resumes after the ember goes down.
- The owner will go back to cinematics after face and outfits finish: "there are some issues with it besides that". Not started; the cinematics area waits for a free slot.
- **18 October, hair at rest (face 29):** "they also know outside of the hair animations that some of the hair just looks bad right? bob for example looks like some is glued on the face". The look at rest is its own item, per style, the bob first; sent to face 29.
- **18 October, the run (animation):** "running still looks goofy, not natural at all. weird exagerated arm movements". Sent to animation 36 as part of its item 1 (the chicken-wing run): the swing's size too, checked against a real running reference.
- **18 October, the rest of the notes:** "rest of notes are the silly slide across the log at the end of the first cinematic, and some polish issues. a couple overly long pauses that end up making animations look silly - some pauses are for narrative reasons thats great but if they go too long it gives people time to critique. improvement passes kinda thing". So: (1) C01's ending, her slide across the log; (2) a pacing pass over every cinematic, trimming holds that outlast their beat (keep narrative pauses, but short enough that the motion isn't on display); (3) general polish passes. Sent to the cinematics lead (coordinator 77fe93b5), with the c03 into c04a merge above.

## 17 October 2026: Face lead, the hair (from playing, to coordinator 59f6a467)
- The owner: "current note for faces, hair physics are a mess, and hair styles even on creation screen clip through and stuff - unless I don't have the proper version. but like hair dosn't look good". The build was current (freshness.py passes on integration). Sent to face 28 as the top of its list: shoot every style at 1:1 at the Look, close-up and play cameras, at rest and in motion, one max judge, then the fixed list and an estimate.

## 17 October 2026: Animation, a grip standard (to coordinator 59f6a467)
- The owner: "we will be adding more weapons and armor along the way, will gripping other weapons require new animation tweaks every single time? that seems tedious and theres got to be a better way". Answer: fists are fitted per weapon type; each new mesh's grip is conformed at import to its type's spec (diameter, length, socket), checked by fistfit numbers with no judge, so new animation work is only for a new weapon type. Gauntlets: one thick-glove offset per type. Animation builds it with the staff fix after F1 (staff, then the viking sword and axe as the proof).
- Also the owner: animations rarely show fingers (runs are clenched or held together), so don't chase finger detail; a proper wrap hides them.

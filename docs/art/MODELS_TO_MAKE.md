# Models to make

What has to be modelled so that every character and creature in the game is ours, who makes each, and in what order. By the character models planner, 4 October 2026.

Sources: the provenance audit (`docs/legal/ASSET_PROVENANCE.md`, `REPLACEMENT_PLAN.md`), the legal lead's rulings (`docs/legal/LEGAL_BRIEF.md` 5(a), 5(b) and 5(g), on `worktree-agent-aab20546fe06daa89@3ddc7728`), the cast (`docs/STORY_BIBLE.md` §3 and §5, `docs/VO_CAST.md`, `docs/cinematics/README.md`), the creatures (`godot/logic/Content/Enemies.cs`, `docs/bestiary/ROSTER.md`, `docs/bosses`), and the code that builds them today (`godot/src/Actors`).

> **Update:** the owner says TRELLIS made the bodies, not Hunyuan, from a picture made with Krea 2 Turbo and/or a free LLM's image tool. Likely kept; the legal lead is re-ruling.
>
> **Hold (4 October 2026):** the owner wants to keep the heroine's and hero's current bodies if their Krea records clear them: the 3D model used (not Hunyuan3D), a paid plan, and their own input picture. Their rebuilds below are fallbacks; nothing is replaced without the owner's decision.

## 1. Summary

**23 models in all.** Everyone else is a reskin: one of these bodies with its own face, hair and outfit, which the team makes.

| | Models | Which |
|---|---|---|
| **Must-make: blockers** (legal: replace before launch) | 3 | **The heroine's body** and **the hero's body**: both came from Krea's website, probably Hunyuan3D underneath, and the records are deleted (legal 5(b)). The 26 creation cameos are re-shot with her. **The boar**: its page says "personal use only" (legal 5(a)) |
| **Must-make: critical path** | 3 | **The Ford-Warden**: the first boss, held in close-up in the prologue; today a stretched townsman whose hood reads white. **The average man** and **the average woman**: the base of every townsperson, Kerchief and Risen, and of 15 named characters |
| **Should-make** (Act 1 at full quality) | 12 | Six more generic builds; the wolf, the lampling and Grimtunnel; the Barrow Lord; Vonnra; Sella |
| **Later** (Acts 2 and 3, and proposals) | 5 | The Warden of the Kiln Ford, the Thing in the Barn, the Bone-Heap, carrion crows, the Morrow |

Nothing needs making for `woman.glb` or the anime body: both come out of the build.

**Who makes what, under the legal lead's rules (5(g)):**
- **People: the team builds every person on MakeHuman's free body** (CC0, so there are no conditions). All the generic builds share one mesh per sex, so every outfit and face fits every build. You don't have to make a person. Your part is the look: briefs, approval of renders, and drawings or photos wherever you want a say.
- **What you make with AI: creatures, and the shape of the few own-model characters.** Work only from pictures that are yours: your drawing, your own photo (with a release if a person is in it), or one of our renders that you paint over. Run them through **TRELLIS 2 on this PC** (`tools/comfy/graphs/trellis_img.json`, MIT licence).
- **A picture from Krea 2 is allowed**, but the model then counts toward Krea's US$1M revenue cap and its 30-day termination. By legal's test that's no cleaner than the free CC0 and CC BY models most of these replace. Keep Krea to new things, and only when nothing else gets the look.
- **Never:**
  - Hunyuan3D in any version. It is `tools/make3d`'s model and the default in Krea's website 3D tool, and its licence bars the EU and UK. **Don't use make3d for game models** until it runs TRELLIS.
  - Any web tool on a free plan.
  - Pictures of real people without a release, or of anyone else's art.
  - The `MysticXXX_KREA2_v1` LoRA.

**Paths** (used in every table below):
- **A:** the team makes it, in Blender or code, on a CC0 base (MakeHuman, the shared skeleton). No conditions.
- **B:** you make it, with TRELLIS 2 locally, from a picture that's yours. No conditions beyond the record (section 5).
- **C:** as B, from a local Krea 2 picture. Allowed, but under Krea's cap.

## 2. Generic people

**Recommendation: 8 bodies (4 men, 3 women, 1 child), 3 heads with 16 crowd faces, and 13 outfit sets for Act 1.** The team makes all of them (path A); none needs a sculpt from you.

| Body | Builds | Who wears it |
|---|---|---|
| Man | average, strong, heavy, old | average: townsmen, footpads, pillagers, Holloway, Chid, Pell. Strong: smiths, bruisers, Brannoc, Redcowl. Heavy: merchants, Harlan. Old: elders, the old dead |
| Woman | average (from slim to full, as today's figure slider), heavy, old | average: townswomen, footpads, Maeca, Keegan, Ysolde. Heavy: goodwives, Rook. Old: Wenna, Firepot Nan |
| Child | one, a boy or a girl by hair and clothes | Tam, the town's children, the Roost's children |

- **Heads:** MakeHuman's (CC0), a man's, a woman's and a child's, with the face sliders the heroes already have (`tools/assets/face_shapes.py`). There are 8 face presets per sex for the crowd, young to old, and each named character gets a face of its own.
- **Outfits:** 13 sets for Act 1, each modular (top, legs, feet, headwear), and dyed as today. That's 6 for the town, 2 for the Watch, 4 for the Kerchiefs and 1 for the Order. The list is in the appendix.
- **Hair:** 6 styles a sex and 4 beards, as cards like hers but at the crowd's budget.

**Why this many** (variety on screen against the work):
- **One mesh per sex makes builds cheap.** Every build is the same MakeHuman mesh in another shape, so an outfit made once fits every build of that sex, and builds blend into each other. The fourth build costs far less than the first. The crowd's real cost is the outfits, not the bodies.
- **The town multiplies its parts.** Each walker is put together from parts:
  - 4 builds × 3 outfits × 5 heads (hood, hat, kerchief, cap or bare hair) give about 60 shapes of man and 45 of woman;
  - that's before 8 dyes, 6 skin tones and the faces.

  The Waystation shows up to 8 walkers and a child by day, beside the named people, so no two need match. Today every man in town has the same body and one of 2 outfits.
- **The arena bakes each enemy kind once** (`Vat.cs`), so a horde of one kind wears one look. Its variety comes from the number of kinds, about a dozen human looks, all from these parts.
- **Silhouette is what reads** at the arena camera (64°, 31 m): build, outfit and headwear, not faces. So builds and headwear earn their keep, and more crowd faces don't. A fifth or sixth build a sex would add little that dye and headwear don't already give.

## 3. Named characters

Screen time is counted in recorded lines (`VO_CAST.md`) and cinematics (C numbers). **Own** means a body made for them alone, at the close-up budget. **Reskin** means a generic build with their own face, hair, outfit and props. **Generic** means they're made from the crowd's parts.

| Character | Who | Screen time | Call · priority · path | Built from, and why |
|---|---|---|---|---|
| **The heroine** | the survivor, a woman, 30 | every frame of her run; creation | **Own** · blocker · A | Rebuilt on MakeHuman to her brief (legal 5(b)). Her outfits, hair and face paint are ours, so they're refitted, not remade. Her head is already MakeHuman. The 26 creation cameos are re-shot |
| **The hero** | the survivor, a man, 32 | the male choice (behind a flag today) | **Own** · blocker · A | As hers. His head is already MakeHuman; his body is the tainted part. Stop polishing the current one |
| **The Ford-Warden** | the prologue's boss | C02, C03; the endless hour's last echo | **Own** · must · A or B | See below |
| **Vonnra Ash-of-Morrow** | toll-keeper, the last binder, 66 | 78 lines; C09 (2 min, her hands on your palm), C32, C41; all three acts | **Own** · should · A (B for her shape) | The story's other lead, and its longest close-up. She is tall and straight-backed; the old build is short and stooped |
| **Sella** | the blue room, 28 | 95 lines, the most of anyone; a romance from the first night | **Own** · should · A (B for her shape) | A romance lead whose figure is part of her trade, framed close upstairs. On the shared build she'd read as a townswoman in a better dress, and on the heroine's body as the heroine's twin in the same scenes |
| **Grimtunnel** | Boss of the Dig | C03 (the prologue), C12; arena boss; Act 3 | **Own** · should · B (or A) | Made on the lampling's skeleton: his bulk, an iron hat with three lamps, and a boss's silhouette in close-up. Today he's a scaled lampling |
| **The Barrow Lord** | the Seventh Legion's standard-bearer | C13; the Risen's arena boss | **Own** · should · A | A Legion dead in its armour, with the eagle pole. He becomes the Legion base: the Barrow Knight, the legionaries, the Decurion, the Signifer and Act 3's Centurion are reskins of him |
| **Maeca Barefoot** | hunter, 34 | 65 lines; romance; C23 | Reskin · woman, average (lean) | Her own face and hair, a hunter's leathers and bare feet; the base's feet must hold up in close-up. Her clothes carry her, not a shape of her own |
| **Captain Holloway** | Watch captain, 45 | 62 lines; C22 | Reskin · man, average | The Watch set with a captain's cloak |
| **Harlan Coyle** | merchant, 55 | 59 lines; C24 | Reskin · man, heavy | A merchant's coat |
| **Rav Cutwell** | physician of a sort, 54 | 52 lines; romance in Act 2 | Reskin · man, average | A worn coat and hood, a knife, an older face |
| **Brannoc** | smith, 52 | 50 lines; C07, C14, C27 | Reskin · man, strong | A smith's apron over bare arms |
| **Dame Keegan Orme** | probationary knight, 24 | 44 lines; C21; Act 2 day boss; romance in Act 2 | Reskin · woman, average | The Vigil's argent plate, which then dresses the Vigil's knights |
| **Mother Rook** | innkeeper, 60 | 43 lines | Reskin · woman, heavy | An innkeeper's dress and apron, her mug |
| **Redcowl (the Red Hand)** | Kerchief chief, 45 | 43 lines; C06, C11, C26; arena boss at 1.9× | Reskin · man, strong | A red brigandine, a red hood thrown back, a greataxe. One model as man and boss: the cinematics need them to match, and today they're two. The Enforcer wears his kit without his face |
| **Chid** | priest of the Order, "32", near 200 | 40 lines; C08, C42; carries you home after every death | Reskin · man, average | The Order of the Morning Light's robes, which the Grave-Caller wears rotten |
| **Pell Varrow** | factor, 40 | 32 lines; C25 | Reskin · man, average | A factor's coat |
| **Old Wenna** | herbalist, 74 | 30 lines | Reskin · woman, old | A herbalist's shawl and hat, a staff, the blightward mask |
| **Ysolde Marrow** | the Wayfinder, 55 | 27 lines; Act 2; romance in Act 2 | Reskin · woman, average | A cartographer's coat, spectacles, a map case, an older face |
| **Tam Penhale** | farm boy, 9 | 16 lines; Act 2 | Reskin · child | Farm clothes |
| **Jory Coyle** | teamster, 17 | 15 lines | Reskin · man, average | A carter's set from the crowd, and the youngest face |
| **Nell** | Brannoc's daughter | C08, C14: seen risen and dead | Reskin · woman, average | Her own face, in grave paint |
| **Snib** | self-appointed foreman of the Dig | 14 lines; the Dig, the Slurry Engine | Variant of the lampling | His own head paint, and a foreman's props |
| **Greymuzzle** | the old dog-wolf | C05 (a wordless minute), C10; herald | Variant of the wolf | A grey muzzle, scars, a torn ear, larger. A sculpt from you only if the shared wolf can't look old enough in close-up |
| **Lord-Exchequer Orrin Sallow** | Act 2's antagonist | Act 2 | Reskin · man, average · later | A gentleman's clothes, and silver ink |
| **Edric Marrow** | Ysolde's caged brother | Act 2 | Reskin · man, average · later | Rags, and the cage |
| **The Keeper of the Silver Cages** | Act 2 day boss | Act 2 | Reskin · man, strong · later | Vigil plate |
| **The Silver Penitent** | Act 2 boss | Act 2 | Reskin · man, strong · later | Vigil plate, with a faceless ledger-plate helm |
| **The Warden of the Kiln Ford** | Act 2 boss, if that ford is lit | Act 2; echoes | **Own** · later · A or B | A drowned giantess in the Order's mail, with a lamp in each hand. She shares the Ford-Warden's paint, eye-lights and lamp |
| **The Centurion** | Act 3 boss | Act 3 | Reskin of the Barrow Lord · later | A centurion's crest |
| **The survivor's mother** | Act 3 (C43) | Act 3 | Reskin · woman, average · later | Only if her face is shown: decide with Act 3's script |

**Generic** (crowd parts, no call needed): the Watchman and Watchwoman at the gate, the Kerchief woman at the cages (C06), the dead Watchman, Wat (a risen carter, C14), Corran, Dannet, Jessop, the Penhales and the babbling lampling.

### The Ford-Warden

- **The call:** an own model, must-make. He is the first boss every player meets, and the prologue holds him in close-up: rising out of the river (C02), his face under the hood lit from below (C02 shot 9), and the last blow on his hood (C03).
- **Today:**
  - he is the kit's townsman (Quaternius), in the Ranger outfit and hood, stretched to 2.6 times a man;
  - he carries a Sketchfab zweihänder;
  - the cinematics lead reports that the hood reads white under the moon and won't take its dye.
- **What he is** (the C02 brief):
  - a hooded giant, with a long beard heavy with river water and weed;
  - two points of cold blue light for eyes, deep under the hood;
  - the old Watch's kit, soaked;
  - a greatsword in his right hand, and in his left fist a square cage-lamp of new black iron with a cold pale blue flame.

  He needs no face rig: the hood, the beard and the eye-lights carry him. "Every movement is a tired man's, made enormous."
- **What he needs:**
  - his lamp on its own bone, so it can be lifted to a face (the cinematics README, item 15);
  - a hood that takes its dye, or is painted dark;
  - a man's proportions on the shared skeleton, scaled in the game as today, so every clip plays on him;
  - the close-up budget.
- **The path:** A, the strong man with a hood, mail, beard and weed made by the team; or B, your drawing of him dressed, through TRELLIS 2, rigged as the hero was. His greatsword goes with the weapons (`REPLACEMENT_PLAN.md` 4.1).
- **What he shares:** the Kiln Ford Warden and the drowned Risen use his drowned paint.

## 4. Creatures and enemies

The arena bakes one look per kind, so a **variant** (new paint, a shape key, props or scale on a model) is cheap, and a model of its own is reserved for a new shape. "Not ours" is from the audit.

**The Pack.** Today: one wolf (CC BY, Roo) and one boar (**blocker**).

| Kind | Call |
|---|---|
| Longtooth Wolf | **Own: the wolf** · should · A or B. On one four-legged skeleton shared with the boar |
| Blight-Sick Wolf, Ridge-Runner, Howler, Whitethroat, Old Blue, Greenbelly, the Pack-Mother's yearling | Variants of the wolf: paint (blighted, pale, old), the yearling leaner, scale |
| Greymuzzle (herald and story), the Pack-Mother (arena boss: a she-wolf, blind in one eye) | Variants of the wolf, with paint and scars of their own |
| Spirit Wolf (ally) | The wolf in a shader; nothing to make |
| Thicket Tusker | **Own: the boar** · blocker · A (from our drawings, `REPLACEMENT_PLAN.md` 1.1) or B. If it isn't ready by launch, buy the Fab version and keep the receipt |
| Slurry Sow, Old Tusk, the Outflow Sow | Variants of the boar: a bloated sow's shape key and slurry paint; an old boar's paint |
| Carrion Crows (proposed) | **Own** · later · A |

**The Risen** (the valley's dead, so the town's own people). Today: Quaternius townsfolk (CC0) in grave paint, with Sketchfab weapons.

| Kind | Call |
|---|---|
| Risen, Risen Servant (ally) | Reskins: the generic builds in town sets, under a grave-rot paint layer |
| Risen Bowman, Risen Shieldman, the Scorpion | Reskins: the Watch set, rotten, with a crossbow or a shield |
| Grave-Caller, Horn-Blower | Reskins: the Order's robes, rotten; a horn |
| Drowned, the Weed-Wife | Reskins under the Warden's wet-and-weed paint |
| Bone-Heap, the Heap | **Own** · later · A or B: a mound of the dead moving as one. Today it's a big risen |
| Barrow Knight (champion and herald), Bone Knight (ally), Legion Shield-Rusher, the Decurion, the Signifer, the Barrow Lord's Hornblower | Reskins of the Barrow Lord's Legion base |
| The Barrow Lord (arena boss) | **Own** · should · A |
| The Ford-Warden (the prologue's boss) | **Own** · must · A or B |

**The Lamplings.** Today: "Goblin Ghoul" (CC BY, Rodrigo Bento); their hats, lamps and satchels are made in code and are ours.

| Kind | Call |
|---|---|
| Lampling Tunneler | **Own: the lampling** · should · B (or A). An original design this world owns, so a design of yours suits it best |
| Sapper, Wick, Fuse-Runner, Lamp-Thrower, Ganger of the Dig, Glimmer-Thief; the Wick-Mother, the Chucker, the Lamplighter, the Perfect of Fuses, the Gaffer, the Sapper-Foreman; Gutterwick (arena boss); Snib | Variants of the lampling: props in code, paint, scale |
| Grimtunnel (story and arena boss) | **Own** · should · B (or A), on the lampling's skeleton |
| Blasting-Cart, Lamp-Pole (proposed); the Slurry Engine (day boss) | Props and set pieces for arena art, not characters |

**The Kerchiefs.** Today: Quaternius bodies and clothes (CC0) dyed red, with Sketchfab weapons.

| Kind | Call |
|---|---|
| Footpad; Cutpurse (proposed) | Reskins: woman (average) or man (average) in the road set, with knives |
| Pillager | Reskin: man (average), the road set with its hood, firepots |
| Bruiser, Barn-Door | Reskins: man (strong), bare-chested with belts and a red sash, a shield and an axe |
| Enforcer, the Toll-Taker, the Drum-Major | Reskins: man (strong) in Redcowl's brigandine, without his face |
| Levy Crossbow, Levy Pikeman, Levy Drummer, the Pike-Captain, the Levy Sergeant | Reskins: man (average) in the levy set |
| Goodwife (proposed), Firepot Nan | Reskins: woman (heavy or old), a town set and a kerchief |
| The Red Hand (arena boss) | Redcowl's model |

**The rest.**

| Kind | Call |
|---|---|
| The Ember-Core | Drawn in code; nothing to make |
| The Reflection | The survivor; nothing to make |
| Act 2: the Fevered | Reskins: town sets under a fever paint layer |
| Act 2: the Vigil | Reskins: the argent plate set |
| Act 2: the Thing in the Barn | **Own** · later · A or B |
| Act 3: the Legion's dead | Reskins of the Barrow Lord |
| Act 3: the Morrow | **Own** · later: a set piece as much as a creature; make it with Act 3's script |

## 5. What to hand the team

This is what the heroes' tools take today (`tools/assets/build_heroine.py`, `hero_male_body.py`, `wrap_sculpt.py`), with the sizes of what ships today. The team reduces, unwraps, bakes and rigs; you hand over what the generator made.

| | Close-up (the heroes, own-model characters, bosses in cinematics) | Play distance (crowd people, creatures) |
|---|---|---|
| **Pose: people** | A-pose: standing straight, facing the camera, arms 30 to 45° out with a clear gap under the armpits, hands open and clear of the thighs, legs apart, feet flat. Whole body, plain background, one character | Same |
| **Pose: creatures** | Standing square, legs straight and apart, head level, mouth closed, tail clear; nothing touching or crossing | Same |
| **Triangles** (after the team's reduction) | Body 50k to 110k, with the head 90k to 145k (the heroine is 92k, the hero 143k) | People about 30k dressed, with hair (today's kit man). Creatures 4k to 12k (the lampling 4k, boar 8.5k, wolf 12k). The arena bakes every vertex of every frame, so this is memory |
| **What you give** | The generator's full output with its paint, unreduced (TRELLIS 2 gives about 700k triangles) | Same |
| **Textures** | The team bakes 4K colour and 4K normal from your sculpt (as for the hero) | The team's call: today the crowd uses 2K for bodies and hair and a shared 4K clothes atlas |
| **Scale** | Metres, +Y up, front to +Z, feet on the ground. Say the height you mean; the team sets it (the hero is 1.98 m, the heroine 1.87 m, the kit's folk 1.78 to 1.82 m, the Warden a man scaled 2.6×) | Same |
| **Rig** | The shared skeleton (Quaternius UAL: 65 bones; the heroine has 69, with soft-tissue bones for the breasts and glutes), so every clip plays. The team folds the weights on. If you rig in AccuRIG, as for the hero, hand over its FBX too | Four-legged creatures share one skeleton; lamplings keep their own |

**Also, for people:**
- Keep hair short or tied, off the neck and shoulders: the team adds hair as cards. Sculpted hair melts into the neck; both heroes' leads fought this.
- Leave the hands empty: weapons, lamps and tools are separate models.
- Use a neutral face with the mouth closed. Talking characters get our MakeHuman head with its expressions.
- Say so for robes and long skirts: they need their own weighting.

**The record:** keep the picture, the prompt and seed if any, and the tool. Every model gets a ledger line before it lands: file, tool, model, licence, input and date (legal 5(g)). The team's own changes (the rig, retopology, repaint, sculpting) are what make an AI-made model ours in law (legal §16), so they're kept with it.

## 6. Order of work: the first five

Blockers come first. Within them, the most-seen comes first, and work for leads who can run side by side.

1. **The heroine's body** (path A; the heroine face lead with the main session).
   - She is the most-seen model in the game, and a launch blocker.
   - Her outfits, hair, face paint and the creation cameos all wait on her, so she has the longest chain.
   - Her face lead is rebuilding her head now, which is the right moment to change the body under it.
2. **The boar** (A or B; arena art for the model, animation for the rig and clips).
   - It is a launch blocker, and it runs in parallel with 1 under other leads.
   - Its four-legged skeleton is the one the wolf will share.
   - The Fab purchase covers launch if it runs late.
3. **The hero's body** (A; the male hero lead).
   - It is a blocker, though players don't see him yet.
   - His lead is polishing the tainted body right now: every day on it is lost work.
4. **The Ford-Warden** (A or B).
   - He is the first boss, and the prologue cinematics (C02, C03) can't be finished without him.
   - What's on screen now is broken.
5. **The average man and woman** (A).
   - Every townsperson, Kerchief and Risen, and 15 named characters, are built on them.
   - Every outfit set waits on them.

Next come the other six builds and the outfit sets, then the wolf and the lampling (both credited CC BY, legally fine until replaced), Grimtunnel, the Barrow Lord, Vonnra and Sella.

---

## Appendix (for the team)

### A. The generic kit, in detail

- **Builds** are MakeHuman settings plus hand sculpting in Blender. `tools/assets/heroes.py` already builds a MakeHuman man and woman. Its age macro, weight, muscle and height give the builds; add folk presets beside the heroes' presets.
  - Adults stay at or over MakeHuman's age 0.5 (25), as `heroes.py` sets.
  - The child is a separate preset. It is clothed only, and appears in no adult content.
- **Faces:** 8 presets a sex, spread over age, built from `face_shapes.py` sliders (the face lead's set). Each named character gets one preset of its own, judged in close-up.
- **Outfit sets for Act 1 (13):**
  - Town, men (3): a labourer (shirt, breeches, apron); a carter (smock, gaiters, hat); a townsman (coat).
  - Town, women (3): a working kirtle and apron; a farm dress with a shawl; a townswoman's gown.
  - The Watch (2, a man's and a woman's): a gambeson in Watch blue, a hood, a pauldron and boots. Holloway's is a captain's version; the Risen Bowman and Shieldman wear it rotten.
  - The Kerchiefs (4): a road set (leathers, a red kerchief, a hood; the bruiser's bare chest with belts and a red sash) and a levy set (a red gambeson and a kettle hat), each for a man and a woman.
  - The Order (1): the Order of the Morning Light's robe, for Chid, and for the Grave-Caller rotten.
  - Headwear, shared across sets: a hood, a hat, a kerchief and a cap.
- **Later sets:** the Vigil's argent plate (for a man and a woman: Keegan, the knights, the Keeper, the Silver Penitent). The Legion's armour comes with the Barrow Lord.
- **Named characters' outfits:** about 15 for Act 1. Most are a set with a few pieces of their own (section 3).
- **Paint layers,** as shader layers shared by all: grave rot, drowned (wet and weed, the Warden's too), blight and fever.
- **Hair:** 6 styles a sex and 4 beards, cut like `heroine_hair.py`'s cards. Keep them near the kit's 3k triangles for the crowd: her long hair is 173k.

### B. Variety, and what it costs

- **Town walkers** are built one by one from parts (`Folk.Person`, `People.Build`), so every choice multiplies.
- **Arena kinds** are baked once each into vertex-animation textures (`Vat.cs`), with each instance varying only in tint and scale. A new look for a kind is a new bake: memory and first-run time (307 MB of bakes today, `docs/PERF_AUDIT.md`).
- Today's kit woman's body alone is 52k triangles, and the man's 14k. The new bases should come in at the play-distance budget, with the close-up budget kept for the characters who are held in close-up.

### C. What the blockers carry, and what they don't (legal 5(b))

- **Tainted, so remade:**
  - the heroine's body mesh and its paint;
  - the hero's body;
  - the 26 creation cameos (`godot/art/ui/create/female/*`), re-shot on the new body.
- **Ours, so refitted rather than remade:**
  - her four outfits, her hair cards and her face paint;
  - both heroes' heads (MakeHuman, CC0).
- **Dropped, with nothing to make:** `woman.glb`, `anime_female.glb` and `her_Hair_*.glb`.

### D. Open questions

1. **For legal:** which local picture generator, if any, counts as path B's "an image we generated ourselves"? Only Krea 2 (path C) runs here today. Clearing one would let the owner make creature pictures by AI without Krea's cap.
2. **For the main session:** who owns the Ford-Warden? He has no lead; the cinematics lead needs him, and the male hero lead's pipeline fits him.
3. **For the male hero lead and the animation lead:** MakeHuman bodies go onto the shared skeleton the `build_heroine.py` way (their weights folded onto UAL's bones). Confirm that this holds for the game-engine rig `heroes.py` makes.
4. **For the owner:** look for Krea receipts from the days the bodies were made (legal 5(b) action 3). A paid plan lowers the risk until launch, but it doesn't change the plan to replace them.

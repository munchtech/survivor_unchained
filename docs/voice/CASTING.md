# Casting

Every voice in the game, for the local TTS and for anyone casting real actors. Rendered from `tools/voice/voices.json` by `tools/voice/extract.py`: edit that file, not this one. How each person talks on the page is `docs/VOICES.md`; who they really are is `docs/STORY_BIBLE.md` §5.

The **voice design** paragraph of each is written for a model that builds a voice from a description (Qwen3-TTS VoiceDesign): one paragraph, physical and concrete, no names. Generate several candidates from it, audition them on the **audition lines**, and keep the winner as the reference clip (`tools/voice/refs/<voice>.wav`) so every later take is cloned from the same voice. Audition lines come from the script where it shows the range; a few are written for the audition alone and are not in the game.

| Voice | Who | Takes | Shares with |
|---|---|---|---|
| `narrator` | The narrator | 113 | Nobody: the narrator is heard more than anyone, and must be his own voice. |
| `rook` | Mother Rook | 42 | Could lend her voice, lighter and quicker, to a townswoman variant if the pool needs a second woman. |
| `holloway` | Captain Holloway | 59 | His voice, younger and less worn, can stand in for the watchman pool if needed. |
| `maeca` | Maeca Barefoot | 36 | Nobody. |
| `wenna` | Old Wenna | 30 | Tam's Pa (Act 2) is her county and could borrow her direction, not her voice. |
| `tam` | Tam | 16 | The town's children could take his voice with lighter direction if a separate child voice will not come right. |
| `brannoc` | Brannoc | 38 | Nobody. |
| `harlan` | Harlan Coyle | 51 | Jory is family and should sound it: cast Jory first, then build Harlan as his older, rounder self (or the other way round). |
| `jory` | Jory Coyle | 11 | Family likeness with Harlan. |
| `pell` | Pell Varrow | 30 | Lord-Exchequer Sallow (Act 2) is a softer, older cousin of this casting; keep them distinct. |
| `rav` | Rav Cutwell | 35 | Redcowl is his brother: let them share a grain (both Scots) without sharing a voice. |
| `chid` | Chid | 35 | Nobody. |
| `vonnra` | Vonnra Ash-of-Morrow | 73 | Nobody. |
| `keegan` | Dame Keegan Orme | 28 | Nobody. |
| `sella` | Sella | 40 | Nobody. |
| `redcowl` | Redcowl | 32 | Brother to Rav: both Scots, different men. |
| `wayfinder` | Ysolde Marrow, the Wayfinder | 25 | Edric Marrow (Act 2) is her brother: the same accent, quieter. |
| `snib` | Snib | 11 | The babbling lampling can take his voice, whispered and slower. Grimtunnel is his family: build him from Snib's design, bigger and lower. |
| `grimtunnel` | Grimtunnel | 2 | Built from Snib's voice, pitched down; two lines in Act 1. |
| `lampling` | The babbling lampling | 2 | Snib's voice, whispered. |
| `ford_warden` | The Ford-Warden | 2 | Two lines: any deep male voice, processed. Could be the watchman's voice pitched down an octave. |
| `dead_watchman` | The dead Watchman | 1 | With the bones in the Verge: one 'dead' voice for both. |
| `bones` | The bones | 1 | The dead Watchman's voice. |
| `townsman` | A townsman | 100 | If one voice repeats too often, add a second townsman (a design with an older, rougher voice) and split the folk lines between them by line number. |
| `townswoman` | A townswoman | 103 | As the townsman: a second design if one voice wears thin. |
| `child` | A child | 7 | Tam's voice, lighter, if a second child voice will not come right. |
| `watchman` | A watchman | 12 | The townsman's voice with a sterner direction, if the budget is short. |
| `watchwoman` | A watchwoman | 12 | The townswoman's voice with a sterner direction, if the budget is short. |

## The narrator (`narrator`)

Tells the player what happens and what can be seen, in the present tense and the second person: captions in the world, the silences in conversations, the notice board, the chapter's last page.

- **Apparent age:** 50s
- **Origin and accent:** Neutral RP, unshowy; nothing regional to place him.
- **Timbre:** Low, close, a slight gravel; a voice that sits near the microphone.
- **Pace:** unhurried
- **Range:** Narrow on purpose: from dry and plain to quietly grave. Never theatrical; horror is said flat, which is what makes it land.
- **Verbal habits:** One image per line; lets the full stop do the work. Reads quoted speech without acting it.
- **At rest:** plain, close, unhurried
- **Never:** Never cute, never names a feeling the scene has already shown, never performs.
- **Can share a voice with:** Nobody: the narrator is heard more than anyone, and must be his own voice.

**Voice design:**

> A man in his fifties with a low, close, slightly gravelled voice and neutral southern English Received Pronunciation. Calm, warm and unhurried, like someone telling a winter's tale by a fire to one listener; quiet, dry, and plain, with no theatrical colour. Recorded close to the microphone in a dry room.

**Audition lines:**

1. The fire has burned low. Out in the dark, the ground is moving.
1. The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.
1. Under the silence you hear it, for as long as a held breath: slow, patient, enormous. Not breathing. Praying.

## Mother Rook (`rook`)

Keeper of the Last Lamp, the inn. Knows everyone's business and admits to most of it; Vonnra pays her for news of the ford road, and paid double for the survivor.

- **Apparent age:** about 60
- **Origin and accent:** Yorkshire, broad but tidy; 'pet' is hers.
- **Timbre:** Warm, dry, chesty; a laugh that lives on the out-breath.
- **Pace:** brisk
- **Range:** From bossing a room to a rare, low tenderness she covers at once; cold and short when crossed.
- **Verbal habits:** Short sentences, imperatives, kindness said sideways ('Sit down before you fall down'). Counts beds and debts.
- **At rest:** dry, bossy warmth
- **Never:** Never says please or sorry; never cries in front of anyone.
- **Can share a voice with:** Could lend her voice, lighter and quicker, to a townswoman variant if the pool needs a second woman.

**Voice design:**

> A sturdy woman of about sixty with a warm, dry, slightly husky voice and a Yorkshire accent. Brisk and bossy, mid-low pitch, quick to command and quick to laugh on the out-breath; underneath it, an unshowy kindness. Plain, practical, working-class, a landlady used to being obeyed.

**Audition lines:**

1. Wipe your boots.
1. If you're bleeding, bleed outside.
1. You told Brannoc about his girl. ... Good. Somebody had to, and it was never going to be me.

## Captain Holloway (`holloway`)

Captain of the Waystation Watch: a quartermaster made a captain. Was the Ashford garrison's quartermaster who signed for the boots that never came.

- **Apparent age:** about 45
- **Origin and accent:** Lancashire flattened by the army.
- **Timbre:** Hoarse from shouting, mid-low, worn at the edges.
- **Pace:** clipped
- **Range:** Tired patience to anger held one notch below the surface; very quiet whenever Ashford or Maeca comes up. Swears rarely, and it lands.
- **Verbal habits:** Numbers and lists, what things cost; says 'proof', never 'evidence'. Contractions.
- **At rest:** tired, clipped, contained
- **Never:** Never says sorry; the nearest he gets is paying for something.
- **Can share a voice with:** His voice, younger and less worn, can stand in for the watchman pool if needed.

**Voice design:**

> A man in his mid-forties with a hoarse, slightly rough mid-low voice, a northern English Lancashire accent worn flat by years in the army. Clipped, tired, practical; speaks in short counted phrases with anger held just under the surface. Sounds like an officer who has shouted too much and slept too little.

**Audition lines:**

1. Eleven men, and four of them can hold a spear the right way round.
1. Grey beard, proud of it? Bad hip? ...Corran. He had that post before I had this one.
1. Mine. From the north, about the north. ... Read your own post, if anybody writes to you.

## Maeca Barefoot (`maeca`)

Hunter, last of the Ashford garrison; the Pack kept her alive after the Fall. A possible lover.

- **Apparent age:** mid-30s
- **Origin and accent:** Welsh borders: a soft lilt kept short.
- **Timbre:** A hunter's half-voice: low, quiet, a hard edge on it.
- **Pace:** level, unhurried, present tense
- **Range:** Flat and watchful to a quiet, final contempt; on the morning after, an unguarded softness she shuts again.
- **Verbal habits:** Few words, all about ground, tracks, weather and animals. 'The Pack', or 'them'.
- **At rest:** level, watchful, few words
- **Never:** Never raises her voice; never says more than three words about Ashford.
- **Can share a voice with:** Nobody.

**Voice design:**

> A woman in her mid-thirties with a low, quiet, slightly husky voice and a light Welsh borders accent. Speaks barely above a murmur, as a hunter does in a wood: level, spare and watchful, with a hard edge under the calm. Never raises her voice.

**Audition lines:**

1. Tracks. Big ones. Going east, and none coming back.
1. Some. ... Fed some of them, once. Buried more. ...Ask me about wolves.
1. The Pack found me, after Ashford. Three days in a cave mouth with the garrison dead round me.

## Old Wenna (`wenna`)

The herbalist. Nursed the fever year; has suspected for a decade that it came out of the ground.

- **Apparent age:** 70s
- **Origin and accent:** Somerset, rolled r's.
- **Timbre:** Cracked, reedy, quick.
- **Pace:** brisk, speeding up when interested
- **Range:** Impatient scolding to a breathless rush of interest; a flash of something guarded when the fever year comes near.
- **Verbal habits:** Lists of plants and symptoms; interrupts herself with a dash; calls everyone 'child'. Very rude, very kind.
- **At rest:** brisk, cracked impatience
- **Never:** Never admits to being frightened; never names the fever year's dead.
- **Can share a voice with:** Tam's Pa (Act 2) is her county and could borrow her direction, not her voice.

**Voice design:**

> A small, sharp woman in her seventies with a cracked, reedy voice and a West Country Somerset accent with rolled r's. Brisk and impatient, rude and kind at once; she speeds up and her pitch climbs when something interests her. An old herbalist who has seen everything and suffers no fools.

**Audition lines:**

1. Sit. No, there. Feverfew, woundwort, a little willow: chew it, don't swallow it, child.
1. Green. Warm. Smells like a chapel lamp. Ember slurry, child: the dust of the stones, cooked and watered.
1. I've no time for heroes. I've time for patients. Which are you?

## Tam (`tam`)

Tam Penhale, the farm boy, nine. Nobody believes him; he is right every time.

- **Apparent age:** nine (a young voice)
- **Origin and accent:** Somerset farm boy.
- **Timbre:** Light, eager, a little breathless.
- **Pace:** quick, run-on
- **Range:** Earnest excitement to indignation at not being believed; small and frightened once or twice.
- **Verbal habits:** Sentences joined with 'and'; 'Pa says'; the exact thing he saw, in order, with the wrong word for the important part. Pleased with an overheard swear word.
- **At rest:** eager, earnest
- **Never:** Never sarcastic.
- **Can share a voice with:** The town's children could take his voice with lighter direction if a separate child voice will not come right.

**Voice design:**

> A nine-year-old English farm boy with a light, eager, slightly breathless voice and a soft Somerset accent. Earnest and excitable, talking quickly in long run-on sentences, pitch rising when he is not believed. A real child's voice, not a cartoon.

**Audition lines:**

1. And I saw it and it was a wolf but it was all thin and Pa says wolves aren't thin but it was.
1. I SAID it was wolves.
1. There's knocking. Under the top field. Pa says it's the frost. It isn't the frost.

## Brannoc (`brannoc`)

The smith. Forged the Low Ford's lamp-irons for a buyer who paid in square coin; his daughter Nell drowned at the ford and rose in the ditch.

- **Apparent age:** about 50
- **Origin and accent:** Cornish, slow and deep.
- **Timbre:** Very deep, slow, a little rough; the hammer under everything.
- **Pace:** slow, fragments, long gaps
- **Range:** Narrow and immovable, until Nell: then the stillness of a man who has put the hammer down.
- **Verbal habits:** Fragments, two sentences at most. Talks about iron as others talk about weather. His only question is about Nell.
- **At rest:** slow, deep, few words
- **Never:** Never small talk; never thanks anyone in words, except once (brannoc.nell_quick).
- **Can share a voice with:** Nobody.

**Voice design:**

> A big man of about fifty with a very deep, slow, slightly rough voice and a Cornish accent. Speaks in short heavy fragments with long pauses between them, plain and unmoved, like a smith between hammer strokes. Few words; each one set down like iron on an anvil.

**Audition lines:**

1. Steel or fur?
1. Twelve ordered. Ten went down to the ford, at night, square coin on the anvil.
1. Thank you. ... Forge is shut. Go on.

## Harlan Coyle (`harlan`)

Of the Coyle Company. A grieving uncle, and the man who has sold the Dig its blasting ember for two years.

- **Apparent age:** about 55
- **Origin and accent:** Bristol merchant.
- **Timbre:** Warm, round, salesman's; cracks under pressure.
- **Pace:** patter that over-explains, then stops dead
- **Range:** Bright patter to broken grief on 'Jory'; a too-quick change of subject when the crates come up.
- **Verbal habits:** Lists of goods and prices; 'friend'. Over-explains, then stops.
- **At rest:** warm patter with a crack in it
- **Never:** Never names the buyer of the B.E. crates.
- **Can share a voice with:** Jory is family and should sound it: cast Jory first, then build Harlan as his older, rounder self (or the other way round).

**Voice design:**

> A stout man in his mid-fifties with a warm, round, friendly voice and a Bristol West Country accent. A merchant's easy patter that runs on and over-explains, then stops dead; under the warmth, a crack that opens when he is frightened or grieving.

**Audition lines:**

1. Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road.
1. Three. In cages. ... Is one of them young? Fair, freckled, a mouth on him that'll get him— ... Get him out.
1. I sell salt to people who salt things. I don't ask the salt what it's for, friend.

## Jory Coyle (`jory`)

Harlan's nephew, seventeen, rescued from the Kerchiefs' cages. Did not know what he was carrying.

- **Apparent age:** seventeen
- **Origin and accent:** Bristol, like his uncle.
- **Timbre:** Young, quiet, a little hoarse.
- **Pace:** short sentences, halting
- **Range:** Shaken and flat to a brittle laugh; once, a slow betrayed understanding.
- **Verbal habits:** 'Uncle'. The cage in every other thing he says.
- **At rest:** quiet, shaken
- **Never:** Never brave about it.
- **Can share a voice with:** Family likeness with Harlan.

**Voice design:**

> A seventeen-year-old English youth with a quiet, slightly hoarse young man's voice and a Bristol accent. Shaken and subdued, speaking in short halting sentences, trying to sound steadier than he is.

**Audition lines:**

1. I'm all right. ... Uncle's counting crates that aren't there.
1. Every rut in Thornhollow. I took them over every rut. ... Uncle knew. Didn't he.
1. Right. Right. ...Thank you. I think. I'll know when I've stopped feeling sick.

## Pell Varrow (`pell`)

Factor. Paid the Kerchiefs to take the caravan; lost his sister in the Ashford Fall. 'I'm not a good man. I'm a careful one.'

- **Apparent age:** about 40
- **Origin and accent:** Precise London RP.
- **Timbre:** Soft, a little nasal, smiling.
- **Pace:** measured, complete sentences
- **Range:** Smiling courtesy to a frightened, ever more polite precision; once, a dry grief for his sister.
- **Verbal habits:** The vocabulary of ledgers: terms, considerations, accounts.
- **At rest:** soft, precise, smiling
- **Never:** Never raises his voice, never swears, never makes a threat that could be repeated to the Watch.
- **Can share a voice with:** Lord-Exchequer Sallow (Act 2) is a softer, older cousin of this casting; keep them distinct.

**Voice design:**

> A slim man of about forty with a soft, precise, slightly nasal voice and crisp London Received Pronunciation. Smiling, courteous and exact, speaking in complete sentences like a clerk reading terms; when frightened he becomes even more polite.

**Audition lines:**

1. Ah. You. What can I do for you today, specifically?
1. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire.
1. My sister kept the books in Ashford. I came up to collect them, after.

## Rav Cutwell (`rav`)

The Crooked Flagon's doctor and drinker; Redcowl's brother, though he never says so.

- **Apparent age:** 50s
- **Origin and accent:** Glaswegian.
- **Timbre:** Gravel, wry; a bedside calm under the cant.
- **Pace:** loose, half-drunk music
- **Range:** Wry cant and filth to a doctor's steady frankness; one line of grief (rav.cb_killed_redcowl).
- **Verbal habits:** 'Pal'. Frank about bodies. Funny about everything except his brother.
- **At rest:** wry, gravelly, loose
- **Never:** Never sentimental; never names his brother but once.
- **Can share a voice with:** Redcowl is his brother: let them share a grain (both Scots) without sharing a voice.

**Voice design:**

> A man in his fifties with a gravelly, wry voice and a Glasgow accent, loose and musical as if a few drinks in; under the banter, the calm, steady bedside manner of a doctor. Frank, funny and unshockable.

**Audition lines:**

1. Drop your trousers or don't, pal. I've seen worse and I've seen better.
1. A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds.
1. Get out of my light for a bit, pal. Come back tomorrow. I'll be a doctor again tomorrow.

## Chid (`chid`)

'The Fool', last priest of the Order of the Morning Light; an Unchained near two hundred years old who does not know he lets it show.

- **Apparent age:** sounds 30s
- **Origin and accent:** Irish-tinged.
- **Timbre:** Light, bright, breathless.
- **Pace:** quick, running on and doubling back
- **Range:** Delight that catches in the throat, to an old stillness he slips into without noticing.
- **Verbal habits:** Exclamations; theology in plain words; now and then a line far older than he looks.
- **At rest:** light, delighted
- **Never:** Never cynical; never says how old he is.
- **Can share a voice with:** Nobody.

**Voice design:**

> A man who sounds in his thirties, with a light, bright, slightly breathless tenor voice and a soft Irish lilt. Joyful and quick, words tumbling over each other, the voice catching on delight; now and then a sudden quiet, older stillness.

**Audition lines:**

1. You're awake! Good. Good! A carter found you on the Old Road and brought you here.
1. A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, who—
1. She was very light. ...Sit down a minute. Not there. There.

## Vonnra Ash-of-Morrow (`vonnra`)

Toll-keeper and far seer: the last binder, who lit the lamps and made the survivor. Her 'sight' is old lore and bought talk. The most important casting in the game.

- **Apparent age:** 60s
- **Origin and accent:** Clipped and unplaceable: old empire, no region.
- **Timbre:** A low alto with a little air in it.
- **Pace:** very slow, long pauses
- **Range:** Stillness to a stillness that frightens; almost never louder, only slower.
- **Verbal habits:** No contractions. Talks of payment, of seeing, of what is 'arranged'. Calls the survivor 'traveller', and after the fortune perhaps their name.
- **At rest:** still, slow, certain
- **Never:** Never answers yes or no; never hurries; never says what she wants.
- **Can share a voice with:** Nobody.

**Voice design:**

> A woman in her sixties with a low alto voice with a little breath in it and a clipped, cultivated, unplaceable accent, as if from an old empire's court. Extremely still and slow, every word chosen and set down, with long silences between phrases. Calm, certain and quietly unsettling; she never hurries and never raises her voice.

**Audition lines:**

1. Traveller. The road was quiet tonight. It will not always be. Payment, always.
1. Gone south. On the toll's business. ... Clerks go south, traveller. It is the direction they fall in.
1. Sit down. I have not finished reading.

## Dame Keegan Orme (`keegan`)

Of the Argent Vigil, probationary; the last true knight of an order that is gone, though she does not know it. Chapter four of her handbook is about the survivor.

- **Apparent age:** 20s
- **Origin and accent:** Oxbridge RP.
- **Timbre:** Clear, bright, projected.
- **Pace:** brisk, over-articulated
- **Range:** Lecturing earnestness to flustered contractions when she forgets herself; once, real fear.
- **Verbal habits:** No contractions on duty; cites the probationary handbook by chapter; names rhetorical figures.
- **At rest:** earnest, projected
- **Never:** Never admits the Vigil is gone; never says what chapter four is about.
- **Can share a voice with:** Nobody.

**Voice design:**

> A young woman in her twenties with a clear, bright, well-projected voice and crisp Oxbridge Received Pronunciation. Earnest and over-articulated, like a keen lecturer reciting from a handbook; comic but sincere, and flustered when she slips into ordinary speech.

**Audition lines:**

1. Dame Keegan Orme, of the Argent Vigil. Probationary. That is a technicality.
1. The probationary handbook, chapter two, is very clear on the matter of taverns.
1. You look well. You look extremely well. ...I've got to go and read something.

## Sella (`sella`)

The blue room at the top of Rook's stairs. Sells company and talk, and sells what is said upstairs; Vonnra outbids everyone. A possible lover.

- **Apparent age:** late 20s
- **Origin and accent:** Softened Cockney.
- **Timbre:** Low, amused, intimate.
- **Pace:** easy, unhurried
- **Range:** Teasing warmth that is also work, to a plain, unguarded tenderness she does not trust.
- **Verbal habits:** Heavy contractions; 'love'. Frank about sex and money and about which is which.
- **At rest:** low, amused warmth
- **Never:** Never coy, never pitiful, never sorry for her work. Adult; never breathy.
- **Can share a voice with:** Nobody.

**Voice design:**

> A woman in her late twenties with a low, warm, amused voice and a softened London Cockney accent. Easy and intimate, frank and funny, with a smile always audible; grown-up and direct rather than breathy or coy.

**Audition lines:**

1. Evening. The lamp's lit upstairs, if you're asking. You look like you're asking.
1. Put your purse away. Tonight I'm not working. ...Don't look at me like that.
1. Chapel lamps, with nobody to see them but you, and you lit them anyway.

## Redcowl (`redcowl`)

Chief of the Kerchiefs: Dunstan Cutwell, Rav's brother, leader of Ashford's dispossessed, who feeds forty-one mouths off the road.

- **Apparent age:** 40s
- **Origin and accent:** Hard Scots.
- **Timbre:** A big chest voice.
- **Pace:** loud, then cold and slow on a turn
- **Range:** Booming laughter that comes before a threat, to a sudden cold quiet; a flicker of the brother.
- **Verbal habits:** 'Ha! HA.' 'Lad' or 'lass' as the survivor is; 'my lot'. Talks about feeding people the way chiefs talk about gold.
- **At rest:** booming, dangerous good humour
- **Never:** Never says please; never says Ashford, and never lets anyone say it twice.
- **Can share a voice with:** Brother to Rav: both Scots, different men.

**Voice design:**

> A big man in his forties with a deep, booming chest voice and a hard Scottish accent. Laughs loudly before he threatens, then turns cold and quiet in an instant; a bandit chief with real authority and real menace.

**Audition lines:**

1. Talk or bleed. Your choice.
1. Ha! A little bird. Sings for its drink. ... Birds don't have names, lass. Not in my camp.
1. Don't. ... You get to say that once in my camp. You've said it.

## Ysolde Marrow, the Wayfinder (`wayfinder`)

Cartographer of the night arenas; writes down who comes back and sells the list north, to keep her risen brother fed.

- **Apparent age:** 50s
- **Origin and accent:** Edinburgh.
- **Timbre:** Crisp, dry, bookish.
- **Pace:** brisk
- **Range:** Gallows humour to a precise, guarded vagueness about her buyers.
- **Verbal habits:** Talks of the dead as entries in a margin; contractions; precise about maps.
- **At rest:** brisk, dry, bookish
- **Never:** Never says who buys her notes.
- **Can share a voice with:** Edric Marrow (Act 2) is her brother: the same accent, quieter.

**Voice design:**

> A woman in her fifties with a crisp, dry, precise voice and an educated Edinburgh Scottish accent. Brisk and bookish with a gallows sense of humour, like a cartographer who has outlived a great many customers.

**Audition lines:**

1. Maps. Places the road forgets. Pick one.
1. Name first; I'm a tidy woman. ... Speaking of which. How do I put you down?
1. Nobody. ... You'd be surprised how often Nobody comes back.

## Snib (`snib`)

Self-appointed foreman of the Dig, a lampling. Exactly what he looks like. Survives everything.

- **Apparent age:** ageless, small
- **Origin and accent:** None you could place; a goblin's scrape.
- **Timbre:** Small, fast, pitched up; a tinny lamp ring on stressed words (add in post).
- **Pace:** fast, panicked
- **Range:** Panic to more panic; pomposity collapsing into contradiction.
- **Verbal habits:** Third person; capitals on the stressed word; contradicts himself in the next breath. 'Boss'.
- **At rest:** panicked, fast
- **Never:** Never calm.
- **Can share a voice with:** The babbling lampling can take his voice, whispered and slower. Grimtunnel is his family: build him from Snib's design, bigger and lower.

**Voice design:**

> A small creature with a high, fast, reedy, slightly scratchy voice, panicky and self-important, words tumbling out in bursts with sudden loud stresses. A comic goblin foreman, nervous and pompous, speaking about himself in the third person.

**Audition lines:**

1. OI! No surface-meat past the pump!
1. The pump does not pump itself. It does, actually.
1. Snib does not want to talk about pipe-lads. Snib wants you to LEAVE.

## Grimtunnel (`grimtunnel`)

Boss of the Dig; a believer, carrying the Warden's heart down to the god he thinks he is freeing.

- **Apparent age:** ageless
- **Origin and accent:** Snib's family.
- **Timbre:** Bigger and lower than Snib, oily; a cackle; cave reverb (add in post).
- **Pace:** gleeful, quick
- **Range:** Gloating to possessive delight.
- **Verbal habits:** 'Nobody's!', 'surface-meat'.
- **At rest:** oily glee
- **Never:** Never afraid of you.
- **Can share a voice with:** Built from Snib's voice, pitched down; two lines in Act 1.

**Voice design:**

> A squat goblin boss with a lower, oily, gloating voice that breaks into a cackle; gleeful, greedy and possessive, speaking quickly with relish, as if from inside a cave.

**Audition lines:**

1. Oho! A Warden's heart, still warm! Nobody's, is it? Nobody's!
1. Finders keepers, surface-meat. The Deep Dig thanks you!

## The babbling lampling (`lampling`)

A lampling at the edge of the pit, who saw the dark move.

- **Apparent age:** ageless
- **Origin and accent:** Snib's people.
- **Timbre:** Whispered, dry, close.
- **Pace:** uneven, repeating
- **Range:** Dazed to terrified.
- **Verbal habits:** Repetition, broken grammar, the same three facts in a different order.
- **At rest:** whispered, dazed
- **Can share a voice with:** Snib's voice, whispered.

**Voice design:**

> A small creature whispering in a dry, cracked, close voice, dazed with fear, repeating itself in broken phrases, as if it cannot stop seeing something.

**Audition lines:**

1. It moved. The dark moved. We dug, and we dug, and it MOVED.
1. Kell's lamp came back up on its own, still lit. Still lit.

## The Ford-Warden (`ford_warden`)

The drowned thing that kept the Low Ford, woken by the lamps; the prologue's boss.

- **Apparent age:** ancient
- **Origin and accent:** None: a voice from under water.
- **Timbre:** Huge, slow, drowned; pitch down and a wet reverb in post.
- **Pace:** slow, proclaimed
- **Range:** A proclamation, nothing else.
- **Verbal habits:** Speaks in capitals.
- **At rest:** vast, slow, proclaiming
- **Can share a voice with:** Two lines: any deep male voice, processed. Could be the watchman's voice pitched down an octave.

**Voice design:**

> An enormous, ancient, inhuman voice, very deep and slow, booming as if from under deep water; a drowned guardian proclaiming a law.

**Audition lines:**

1. NONE CROSS AFTER DARK.
1. RISE, YOU WHO DROWNED HERE.

## The dead Watchman (`dead_watchman`)

Corran, dead at his post on the Low Ford road; his jaw moves once, for the survivor alone.

- **Apparent age:** 60s, dead
- **Origin and accent:** Northern, faint.
- **Timbre:** Dry, cracked, barely voiced.
- **Pace:** slow
- **Range:** One line.
- **At rest:** dry, dead whisper
- **Can share a voice with:** With the bones in the Verge: one 'dead' voice for both.

**Voice design:**

> An old man's voice, dry and cracked and barely above a whisper, as if from a throat long dead; slow, flat and close.

**Audition lines:**

1. It shatters its own lamps when it charges. Make it charge.

## The bones (`bones`)

A legionary's skeleton by the vault door in the Verge.

- **Apparent age:** dead
- **Origin and accent:** None.
- **Timbre:** Dry, hollow whisper.
- **Pace:** slow
- **Range:** One line.
- **At rest:** hollow whisper
- **Can share a voice with:** The dead Watchman's voice.

**Voice design:**

> A dry, hollow, ancient whisper, slow and toneless, as if spoken through an empty skull.

**Audition lines:**

1. It was never locked from the outside.

## A townsman (`townsman`)

Any man of the Waystation in passing: carters, stall-keepers, drinkers, the grumbling, the gossiping and the bawdy.

- **Apparent age:** 30s to 50s
- **Origin and accent:** Northern or West Country English, ordinary.
- **Timbre:** Ordinary, a working man's voice.
- **Pace:** off-hand
- **Range:** Grumbles, gossip, fear and filthy jokes, all said in passing.
- **Verbal habits:** Said to the air, not performed.
- **At rest:** off-hand, ordinary
- **Can share a voice with:** If one voice repeats too often, add a second townsman (a design with an older, rougher voice) and split the folk lines between them by line number.

**Voice design:**

> An ordinary working man in his forties with a plain, slightly rough northern English voice, speaking off-hand in passing as he walks by, conversational and unperformed.

**Audition lines:**

1. Bread's up again. It's always up.
1. Holloway couldn't find his own arse with a lantern and a map.
1. Came up the Low Ford at night? You're brave or daft.

## A townswoman (`townswoman`)

Any woman of the Waystation in passing.

- **Apparent age:** 30s to 50s
- **Origin and accent:** West Country or northern English, ordinary.
- **Timbre:** Ordinary, brisk.
- **Pace:** off-hand
- **Range:** As the townsman's.
- **Verbal habits:** Said to the air, not performed.
- **At rest:** off-hand, ordinary
- **Can share a voice with:** As the townsman: a second design if one voice wears thin.

**Voice design:**

> An ordinary working woman in her forties with a plain, brisk West Country English voice, speaking off-hand in passing as she walks by, conversational and unperformed.

**Audition lines:**

1. Two coppers for a turnip. Two!
1. My husband went out to the Verge a month back. Some days I hope he stays out.
1. Is that blood? Don't tell me.

## A child (`child`)

The town's children at play.

- **Apparent age:** about eight
- **Origin and accent:** Local English.
- **Timbre:** Light, quick.
- **Pace:** quick
- **Range:** Play and dares.
- **At rest:** playful
- **Can share a voice with:** Tam's voice, lighter, if a second child voice will not come right.

**Voice design:**

> A young English child of about eight with a light, quick, playful voice, calling out mid-game.

**Audition lines:**

1. You can't catch me!

## A watchman (`watchman`)

The Waystation Watch on the gate and on the rounds.

- **Apparent age:** 30s
- **Origin and accent:** Northern English.
- **Timbre:** Plain, a little official.
- **Pace:** steady
- **Range:** Warnings and boredom.
- **At rest:** dutiful, plain
- **Can share a voice with:** The townsman's voice with a sterner direction, if the budget is short.

**Voice design:**

> A watchman in his thirties with a plain, steady northern English voice, a little official and a little bored, giving warnings at a gate.

**Audition lines:**

1. Keep your weapon sheathed in town.
1. East road. Mind the wolves.

## A watchwoman (`watchwoman`)

The Waystation Watch on the gate and on the rounds.

- **Apparent age:** 30s
- **Origin and accent:** Northern English.
- **Timbre:** Plain, firm.
- **Pace:** steady
- **Range:** Warnings and boredom.
- **At rest:** dutiful, plain
- **Can share a voice with:** The townswoman's voice with a sterner direction, if the budget is short.

**Voice design:**

> A watchwoman in her thirties with a plain, firm northern English voice, steady and a little official, giving warnings at a gate.

**Audition lines:**

1. Dawn arrivals. We do not get many that live.
1. Lamps are lit. Stay where they reach.

## Pronunciation

For every voice. Respell in the text sent to the TTS only if a take gets one wrong (`say` in `tools/voice/directions.json`); the subtitle keeps the spelling.

- **Vonnra**: VON-ruh (short o, as in 'on')
- **Ash-of-Morrow**: ASH-of-MORR-oh
- **Morrow**: MORR-oh
- **Maeca**: MAY-kuh
- **Brannoc**: BRAN-uck
- **Wenna**: WEN-uh
- **Harlan**: HAR-lun
- **Coyle**: COIL
- **Jory**: JOR-ee (as in 'jolly')
- **Pell Varrow**: PEL VARR-oh
- **Varrow**: VARR-oh
- **Rav**: RAV (rhymes with 'have')
- **Cutwell**: CUT-well
- **Chid**: CHID (rhymes with 'did')
- **Keegan Orme**: KEE-gun ORM
- **Sella**: SEL-uh
- **Redcowl**: RED-cowl ('cowl' rhymes with 'owl')
- **Snib**: SNIB
- **Grimtunnel**: GRIM-tun-ul
- **Ysolde**: ih-ZOLD-uh
- **Greymuzzle**: GRAY-muzz-ul
- **Thornhollow**: THORN-holl-oh
- **Ashford**: ASH-fud
- **Jessop**: JESS-up
- **Dunstan**: DUN-stun
- **Corran**: KORR-un
- **Dannet**: DAN-it
- **Penhale**: pen-HAIL
- **Penhales**: pen-HAILZ
- **Low Kiln**: LOH KILN
- **Aldo**: AL-doh
- **Oswin**: OZ-win
- **Ashe**: ASH
- **Kerchiefs**: KER-chifs
- **Silverstair**: SIL-ver-stair
- **Argent Vigil**: AR-junt VIJ-il
- **Waystation**: WAY-stay-shun

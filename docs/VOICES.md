# Voices

How each named person in Survivor Unchained talks, for whoever writes the
next line. Every line in `godot/data/content/dialogue.json` and the barks in
`npcs.json` is written against these sheets. The casting notes are for the
voice pass (local TTS or actors); the accents are a palette, not a
caricature: northern and West Country English for the town, RP for the old
orders, a rougher Scots edge for the Kerchiefs.

Rules for everyone:

- Most people use contractions. Only **Vonnra** and **Keegan** speak in
  full, and for each of them it means something (Vonnra is old and careful;
  Keegan is reciting, and slips when she forgets herself).
- Nobody explains a mechanic. People talk about wolves, money, the dead and
  each other; the interface says what a choice does.
- Retired, for everyone: "mostly", "Hm.", "I will not forget", "nobody
  listens". If a line wants one of them, it wants a better line.
- Each person has something they are not saying (see `STORY_BIBLE.md`).
  They never say it. They talk around it, and the shape of the hole is the
  hint.
- A "never" below is a rule with at most one written exception in the whole
  game, placed where breaking it is the scene: Rav names his brother once
  (`rav.cb_killed_redcowl`), Brannoc says thank you once
  (`brannoc.nell_quick`), Redcowl says "Ashford" once, dying, to the one who
  said it to him (`cin_raid_on_the_roost.last`), and Holloway's one "sorry" is
  kept for Act 2, said to his own counting as he hands the survivor over
  (`docs/cinematics/act2_outline.md`, C22). Do not spend those again.
- Families sound alike under stress: Harlan and Jory both say "Thank you. I
  think. I'll know when I've stopped feeling sick." Redcowl and Rav both
  reach for their mother when something is unbearable.
- The player's lines are short, plain and a little dry. They never make a
  speech.
- The game is written for adults. Swearing, crude jokes and frank talk
  about sex belong to the mouths below that have them (Rav, Sella,
  Redcowl, the Flagon's regulars, the Watch on a bad night); Holloway
  swears rarely and it lands; Vonnra, Keegan, Chid and Tam never do.
  Violence is said in one plain line, where it lands, and not dwelt on.
  Intimate scenes are written in full before and after, with a cut-away
  for the moment itself and an `[explicit scene: ...]` slot for the
  owner's writer (`STORY_BIBLE.md`).

---

**The narrator.** Present tense, second person, plain nouns and working
verbs; one image per line, never two adjectives where one will do. Says
what happens and what can be seen, never what it means. Never theatrical,
never cute, never names a feeling the scene has already shown. *Casting:*
50s, neutral RP, low and close; a winter's tale told by the fire, slight
gravel, unhurried.

**Mother Rook** (the Last Lamp). Short sentences, bossy imperatives, kindness
said sideways ("Sit down before you fall down"). Yorkshire turns: "love" is
Sella's, Rook's is "pet". Counts beds and debts; knows everyone's business
and admits to most of it. Never says please, never says sorry, never cries
in front of anyone. Laughs on the out-breath. *Casting:* 60, Yorkshire,
warm, dry, bossy.

**Captain Holloway** (the Watch). A quartermaster who was made a captain:
numbers, lists, what things cost ("eleven men, four can hold a spear the
right way round"). Clipped, tired, contractions, anger held one notch below
the surface. Says "proof", never "evidence". Never says sorry; the nearest
he gets is paying for something. Goes very quiet whenever Ashford or Maeca
comes up. *Casting:* 45, Lancashire flattened by the army; hoarse from
shouting.

**Maeca Barefoot** (the Ashford Garrison). Few words, all of them about
ground, tracks, weather and animals. Level, quiet, present tense. Calls the
wolves "the Pack" or "them", never "beasts" or "monsters". Contempt is
quiet and final. Never raises her voice; never talks about Ashford except
in three words or fewer. *Casting:* 30s, Welsh borders, a hunter's
half-voice with a hard edge.

**Old Wenna** (herbalist). Brisk, cracked, impatient; lists of plants and
symptoms; interrupts herself with a dash when she gets interested, and
speeds up. Calls everyone "child". Very rude, very kind. Never admits to
being frightened, and never names the fever year's dead. *Casting:* 70s,
Somerset.

**Tam** (farm boy). Nine. Run-on sentences joined with "and"; "Pa says";
the exact thing he saw, in order, with the wrong word for the important
part. Earnest. Repeats a swear word he has overheard and is pleased about
it. Never sarcastic. *Casting:* a young adult voice lightly pitched up, or
very short lines.

**Brannoc** (smith). Fewest words in town: fragments, two sentences at the
most, the hammer under everything. Talks about iron the way other people
talk about weather. Never small talk, never thanks anyone in words (once:
when he is told his daughter's end was quick). The only question he ever
asks is about Nell; when he stops hammering, the narrator says so, because
it is the loudest thing he does. *Casting:* 50, Cornish, deep and slow.

**Harlan Coyle** (the Coyle Company). A salesman's patter with a crack in
it: lists of goods, prices, "friend". Over-explains, then stops dead.
Breaks on "Jory". Never names the buyer of the B.E. crates, and changes the
subject a beat too fast when anyone tries. *Casting:* 55, Bristol merchant,
warm and cracking.

**Pell Varrow** (factor). Soft, precise, smiling; complete sentences with
contractions; the vocabulary of ledgers ("terms", "considerations",
"accounts"). Never raises his voice, never swears, never makes a threat
that could be repeated to the Watch. When he is frightened he gets more
polite. *Casting:* 40, precise London RP, a little nasal.

**Rav Cutwell** (the Crooked Flagon). Gravel and cant; a doctor's frankness
about bodies ("drop your trousers or don't"); a half-drunk music in the
rhythm; "pal". Funny about everything except his brother, whom he never
names (once: "Dunstan", the day he hears Redcowl is dead). Never
sentimental, never says no to a drink. *Casting:* 50s, Glaswegian, wry; the
bedside calm under the cant.

**Chid** ("the Fool"). Light, breathless, delighted; exclamations; sentences
that run on and double back. Theology in plain words, and now and then a
line that is far older than he looks, which he does not notice saying.
Never cynical; never says how old he is. *Casting:* sounds 30s, Irish-
tinged; the voice catches on joy.

**Vonnra Ash-of-Morrow** (toll-keeper, far seer). No contractions. Very
still, long pauses, few questions. Talks of payment, of seeing, of what is
"arranged". Never answers yes or no; never hurries; never says what she
wants. Calls the survivor "traveller" until the fortune; if the survivor
tells her there that she lit the lamps, she answers with their name, and
uses it from then on. That is the only answer she gives. Her "seeing" is
what she has bought: say it as sight, and let the narrator notice where her
eyes are. *Casting:* 60s, clipped and unplaceable (old empire), a low alto
with a little air. The most important casting in the game.

**Dame Keegan Orme** (the Argent Vigil, probationary). Over-articulated and
earnest, a lecturer's projection; no contractions while she is on duty,
and they slip out when she forgets herself (which is the joke, and later
the tell). Cites the probationary handbook by chapter. Names rhetorical
figures. Never admits the Vigil is gone; never says what chapter four is
about. *Casting:* 20s, a woman, Oxbridge RP; comic but sincere.

**Sella** (the blue room). Low, amused, intimate; heavy contractions;
"love". Frank about sex and money and about which is which; never coy,
never pitiful, never sorry for her work. Sells talk as well as company and
says so. *Casting:* late 20s, softened Cockney; warmth that is also work.
Adult, never breathy.

**Redcowl** (the Kerchiefs). A big chest voice that laughs before it
threatens ("Ha! HA."), and goes cold on a turn. "Lad" or "lass" as the
survivor is (write both variants), "my lot".
Talks about feeding people the way other chiefs talk about gold. Never
says please; never says the name Ashford, and never lets anyone else say
it twice. *Casting:* 40s, hard Scots.

**Snib** (self-appointed foreman). Third person, panic, capitals on the
stressed word, and the gag where he contradicts himself in the next
breath ("The pump does not pump itself. It does, actually."). Loyal to
"Boss" and terrified of him. *Casting:* small and fast, pitched up, a tinny
lamp ring on stressed words.

**Grimtunnel** (Boss of the Dig). Oily, gleeful, possessive: "Nobody's!",
"surface-meat", "downstairs" for the deep. Under the greed, faith: he is
carrying a god its heart, and when anything touches that he goes toad-still
and very nearly bows, then covers it with a grin. He believes the thing below
will be grateful, and says so. *Casting:* Snib's family, bigger, lower, a
cackle, a cave reverb that gets wetter as he goes down.

**The Ford-Warden.** The Order's keeper of the Low Ford, older than the Watch.
Speaks rarely, in capitals and orders: the dead are told to rise, the living to
lie down, nobody to cross. Sings the Order's evening call under the water. His
last line is in another voice: the tired man under him, asking if it is morning.
*Casting:* a very low bass with no age and no accent that belongs to the valley
now, a long cave reverb with water in it; the last line a plain man of sixty,
dry, no reverb.

**The Barrow Lord** (the Seventh Legion). Speaks only the old empire's tongue,
one word at a time, like orders given a thousand times ("Nondum", "Redi").
Translated in the subtitles only for a survivor who can read it. *Casting:* a
dry, enormous whisper, close to the ear.

**The Waystation's watchmen.** Tired men with colds; they say to each other what
they always say and watch the survivor too long after.

**The Kerchiefs.** Scots like their chief, rougher; few words to strangers, and
those flat.

**The babbling lampling.** Repetition, broken grammar, the same three
facts in a different order. *Casting:* whispered, dry, close.

**Jory Coyle.** Seventeen and shaken: short sentences, "Uncle", the cage
in every other thing he says without saying "cage". *Casting:* Bristol,
like Harlan, quiet.

**Ysolde Marrow** (the Wayfinder). Brisk, bookish, gallows humour; talks
about the dead as entries in a margin; contractions. Precise about maps,
vague about who buys her notes. *Casting:* 50s, Edinburgh.

**Greymuzzle.** Never speaks. Everything he says is the narrator watching
what he does.

**Tam's Pa** (Penhale). Heard, not yet met: "He calls you several things on
the way, and one of them is a fool." A farmer who swears at whoever saves
him. When he speaks (Act 2): short, profane, grateful only by accident.
*Casting:* 40s, Somerset like Wenna, louder.

**Nell, Wat, Corran.** The dead. They never speak; they are spoken of. Nell
is "Mine." to her father and "Brannoc's girl" to the town. Corran speaks
only in his belt-book, three lines in a hand that worsens.

**Jessop** (Act 3, on the stair, risen and kept by the Legion's dead). A
clerk's phrases with nothing behind them: tolls, receipts, "the road is
shut", over and over. *Casting:* 30s, thin, a clerk's careful vowels gone
slack.

**Lord-Exchequer Orrin Sallow** (Act 2). The Vigil's paymaster: courteous,
unhurried, a collector's pleasure in completeness. Speaks of people as
entries and arrears; never raises his voice; apologises often and means
none of it. Contractions, unlike Keegan. *Casting:* 60s, soft RP, a little
amused.

**Edric Marrow** (Act 2, in a silver cage). Ysolde's brother, twelve years
risen. Her bookishness without her humour; asks about the corners of the
barrow she keeps drawing. *Casting:* 40s, Edinburgh like his sister,
quieter.

**The notice board.** Notices in notice voice: capitals for the important
word, initials for signatures, and the town's graffiti underneath.

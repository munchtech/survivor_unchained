# 06: The Ineffable. What players mean when ARPGs and survivors-likes "just feel good"

Research brief for a dark-fantasy survivors-like (auto weapons, hordes, level-up drafts, boss at 30 min).
Compiled 2026-10-03.

---

## 0. Method, corpus, and a caveat

**Why the evidence looks the way it does.** Reddit was the planned main source, but it blocks this research crawler outright: both search and fetch return "domains not accessible to our user agent". I didn't try to get around the block. The main player-language corpus is instead **Steam user reviews pulled through Steam's public `appreviews` endpoint**. After de-duplication that is **34,543 English reviews** across 14 titles:

- Survivors-likes (16,548 reviews): Vampire Survivors, Megabonk, Brotato, Halls of Torment, 20 Minutes Till Dawn, Deep Rock Galactic: Survivor, Soulstone Survivors, Death Must Die.
- ARPG and action-roguelite comparators (17,995 reviews): Hades, Hades II, Diablo IV, Path of Exile, Path of Exile 2, Last Epoch.

The rest comes from press and essays, Steam forum threads, developer statements, the canonical game-feel talks (titles verified by oEmbed), and perception research.

**Quote rules.** Every quote is verbatim, shortened with "…" where needed, and kept under about 30 words. Typos are left as written. A Steam review URL has the form `steamcommunity.com/profiles/<id>/recommended/<appid>/`, which links to that reviewer's review of that game.

**What the vocabulary shows.** Rates are mentions per 1,000 reviews, from regex counts over the corpus.

| Term family | Survivors-likes | ARPGs + Hades | Ratio |
|---|---|---|---|
| "addict-" | 124 | 52 | 2.4x |
| "dopamine" | 19.3 | 5.9 | 3.3x |
| "brain off" / "turn my brain off" | 6.4 | 1.4 | 4.6x |
| "relax" / "chill" / "cozy" | 24.8 | 8.3 | 3.0x |
| "crack" (as in the drug) | 7.6 | 2.3 | 3.3x |
| "AFK" / "plays itself" | 3.8 | 1.6 | 2.4x |
| "responsive" / "smooth" / "snappy" | 9.9 | 30.8 | 0.32x |
| "impactful" / "weighty" / "crunch" / "punchy" / "visceral" | 4.3 | 8.3 | 0.52x |
| "satisf-" | 32.0 | 35.5 | about 1x |

**Headline finding.** Both groups use "satisfying" at the same rate. They don't mean the same thing by it:

- ARPG and action players talk about their **hands**: responsiveness, impact, weight.
- Survivors-like players talk about their **state of mind**: addicted, relaxed, brain off, dopamine.

So "feels good" in a survivors-like is mostly a claim about an altered state, and only partly about the controls. Hand-feel is the floor (its absence fills negative reviews), but the state is what people are paying for.

---

## 1. The phrase families: usage and what is underneath

### 1.1 "Crunchy / punchy / weighty / meaty" vs "floaty / wet noodle / hitting air"

**Usage (positive):**
- "Every swing, spell, and explosion feels weighty, visceral, and incredibly polished." (Diablo IV reviewer, https://steamcommunity.com/profiles/76561198163771977/recommended/2344520/)
- "the combat feels satisfyingly crunchy. Smashing demons into loot-filled piñatas never really gets old." (Diablo IV reviewer, https://steamcommunity.com/profiles/76561199753705177/recommended/2344520/)
- "The combat is weighty, the bosses hit like a truck carrying another truck" (PoE2 reviewer, https://steamcommunity.com/profiles/76561198965459009/recommended/2694490/)
- "Skeleton bone crunch ASMR for all ye dungeon dweebs and dark fantasy dorks." (Halls of Torment reviewer, https://steamcommunity.com/profiles/76561198039045576/recommended/2218750/)

**Usage (negative):**
- "some hits are just wet sponges and theirs no physicality to anything… you may as well be swinging a pool noodle." (Last Epoch reviewer, https://steamcommunity.com/profiles/76561197970993705/recommended/899770/)
- "My eyes are constantly bombarded with rainbows, but the audio has no weight and inputs are inconsistent" (Last Epoch reviewer, https://steamcommunity.com/profiles/76561198041802448/recommended/899770/)
- "Everything explodes but nothing has serious oomph to it." (Soulstone Survivors reviewer, https://steamcommunity.com/profiles/76561198095722522/recommended/2066020/)
- "it feels unsatisfying and "floaty". It doesn't really feel like I'm landing any hits. The monsters are just like sponges" (Soulstone reviewer, https://steamcommunity.com/profiles/76561198053854269/recommended/2066020/)
- "Floaty refers to combat that lacks feedback and commitment." (user "Panic Fire", Nightingale Steam forum, https://steamcommunity.com/app/1928980/discussions/0/7221029098485809053)

**What is underneath.** The complaints split in a revealing way. "Bombarded with rainbows… but the audio has no weight" and "everything explodes but nothing has oomph" both say that **more visual effects don't produce weight**. Weight is a mass inference. The brain judges an object's mass from how other things react to it, not from how bright it is. Concretely:

1. **Time dilation at contact.** Hit-stop freezes the frame for a few frames. Vlambeer's Nijman freezes "for about 10-20 milliseconds whenever you hit something" (Tom Armitage's notes on *The Art of Screenshake*, https://infovore.org/?p=5275; talk at https://www.youtube.com/watch?v=AJdEqssNZ-U). A pause says "resistance happened."
2. **Reaction of the struck body.** That means knockback, a flash, a squash, a stagger. Sponge enemies that don't react read as "hitting air", whatever the numbers say.
3. **Low-frequency, transient-rich sound placed at the contact frame.** "Audio has no weight" is literal. Perceived heaviness tracks low-frequency energy and a sharp attack. Bright, sustained whooshes read as light.
4. **Permanence.** Nijman's "props are there to add some permanence to the battles" (Armitage, same URL). Corpses, gore, decals and craters are evidence that the event *happened*.

The one controlled study on this agrees. Lin, Duan, Wen and Cai tested a 19-feature framework against well- and poorly-reviewed Steam action games. Their conclusion: "A lack of dedicated design on one of these three features [hit stop, sound coherence, camera control] may ruin players' impact feel" (https://arxiv.org/abs/2208.06155v1). Note that the feature is sound **coherence**, not sound volume.

**Survivors-like twist.** In an auto-attack game you can't apply hit-stop to *every* hit. With 300 enemies on screen, that would be a slideshow. The crunch has to move to **kills, crits, elites and evolution-tier weapons**, and to the *aggregate* sound of many deaths (see 1.6).

---

### 1.2 "Brain off / zen / trance / mindless in a good way / meditative"

**Usage:**
- "it's just become my go-to shut my brain off and vibe game." (Vampire Survivors reviewer, https://steamcommunity.com/profiles/76561198271936568/recommended/1794680/)
- "A simple, chill game to turn your brain off with as you effortlessly evaporate thousands of monsters." (20 Minutes Till Dawn reviewer, https://steamcommunity.com/profiles/76561199105508651/recommended/1966900/)
- "Total chaos, but cozy chaos. Like meditation, if meditation involved becoming a walking health-and-safety violation." (Megabonk reviewer, https://steamcommunity.com/profiles/76561199036548398/recommended/3405340/)
- "it can be relaxing in a zen sort of way" (Haikal Fernandez, The Vibes, https://www.thevibes.com/articles/lifestyles/53373/vampire-survivors-an-escalating-dopamine-rush-disguised-as-a-retro-game)
- "a brain-tingled, barely-conscious cretin, gently slaughtering the hordes of the underworld." (Halls of Torment reviewer, https://steamcommunity.com/profiles/76561198180778439/recommended/2218750/)

**The failure modes on either side of the trance:**
- *Too much thinking:* "This was the perfect "turn my brain off and relax" game until I realized I had to actually had to think about making a coherent build." (Death Must Die reviewer, https://steamcommunity.com/profiles/76561197984865906/recommended/2334730/)
- *Too little engagement:* "the game has become something I could use as a sleep aid." (Death Must Die reviewer, https://steamcommunity.com/profiles/76561198177953455/recommended/2334730/)
- *Self-awareness breaks the spell:* "the most mask-off dopamine drip in the shape of a video game I've ever encountered. It makes me hyper aware of every minute" (Halls of Torment reviewer, https://steamcommunity.com/profiles/76561198091583642/recommended/2218750/)

**What is underneath.** "Brain off" doesn't mean the brain is off. It means the *verbal, deliberative* channel is idle while the *perceptual-motor* channel is busy. "Turn your brain on but not too hard" is the most precise phrasing in the corpus. It describes a low-load flow state. Several of the classic flow components (Csíkszentmihályi and Nakamura, summarised at https://en.wikipedia.org/wiki/Flow_(psychology)) map directly:

| Flow component | Survivors-like mechanism |
|---|---|
| "Merging of action and awareness" | One input channel (movement). There's nothing to decide in the hands. |
| "Loss of reflective self-consciousness" | No aiming, no reading. Players' accounts describe dropping into autopilot. |
| "Immediate feedback" | Constant gem chimes and kills, with a continuous trickle of reward. |
| "Distortion of temporal experience" | The "where did 3 hours go" reports (1.8). |

The trance breaks at the three failure points quoted above: deliberation spikes (a build puzzle or dense draft), under-stimulation (unkillable = "sleep aid"), and meta-awareness ("mask-off"). The design job is to keep load in a narrow band: perceptual and spatial engagement stays high, symbolic engagement stays low and brief.

Positional play gives the hands just enough to do. Removing aiming frees attention for positioning and build choices (the argument of the Tampere PlayLab essay, https://blogs.tuni.fi/playlab/game-related-media/vampire-survivors-a-humble-game-that-took-the-video-game-industry-by-storm/). Steering through a crowd is a continuous, low-symbolic motor task, much like driving an empty road.

---

### 1.3 "Power fantasy / turning into a god / the tables turn / becoming the monster"

**Usage:**
- "It starts with you throwing a single whip at a bat and ends with you becoming a literal god of death, surrounded by a thousand flashing lights" (VS reviewer, https://steamcommunity.com/profiles/76561197972251798/recommended/1794680/)
- "you start the run extraordinarily weak, struggling to overcome groups of rats, bats, and slimes, and end the run as a demigod" (anewson, GamingOnLinux, https://www.gamingonlinux.com/2022/09/a-genre-is-born-horde-games)
- "in VS the game pretty much says "hey, here, take this nuke. Go wild with it". It's both the attitude and tone that matters" (20MTD reviewer, https://steamcommunity.com/profiles/76561198027357658/recommended/1966900/)
- Galante himself: "It's absolutely not balance; balance is completely out of the window. I just want to make stuff that is fun." (Pocket Tactics interview, https://www.pockettactics.com/vampire-survivors/interview)

**When the fantasy is withheld:**
- "You never reach a true "god run" power fantasy… You're rarely ahead of the power curve" (DRG: Survivor reviewer, https://steamcommunity.com/profiles/76561197985061559/recommended/2321470/)
- "The whole premise under this kind of game should be fast paced free movement and power fantasy" (Death Must Die reviewer, https://steamcommunity.com/profiles/76561197994443475/recommended/2334730/)

**When the fantasy goes hollow:**
- "you can eventually clear an entire screen of mobs with what you created, but it just doesn't feel impressive or cool or memorable. You feel… nothing really." (Halls of Torment reviewer, https://steamcommunity.com/profiles/76561198042115865/recommended/2218750/)
- "let the enemies run into my death circle for 30 minutes" (Boss Rush review, https://bossrush.net/2022/12/game-review-vampire-survivors/)

**What is underneath.** Players don't describe power as a *level*. They describe it as a **slope**, and specifically an inversion. Every account has two ends: "single whip at a bat" → "god of death"; "struggling… rats, bats" → "demigod". Three things make the slope felt:

1. **The pressure direction flips.** Early on the horde is the hunter and you flee. Late, the horde is "running into my death circle". The *same* enemies change meaning. Survivors-likes stage this reversal better than ARPGs because the player's *motion* changes: from kiting away to walking *into* the crowd. That bodily change is the "I'm the monster now" moment.
2. **The baseline matters (Weber-Fechner).** A noticeable change in sensation scales with the existing intensity, and "the intensity of our sensation increases as the logarithm of an increase in energy" (https://en.wikipedia.org/wiki/Weber%E2%80%93Fechner_law). A flat +10 damage feels huge at minute 3 and invisible at minute 25, and a +5% upgrade sits below the noticeable threshold at any time, hence "boring stat increases". To stay *felt*, power growth has to be roughly multiplicative, and it has to show up in new **kinds** of effect (new shapes, new screen coverage), not just bigger numbers.
3. **Generosity as attitude.** "Take this nuke. Go wild" is a statement about the designer's *intent*, as players read it. Stingy, careful upgrades read as distrust ("the dev thinks he is being both cautious and generous" in the same 20MTD review).

The Halls of Torment "you feel nothing" review shows that **power without a witness is empty**. Clearing a screen only means something if the screen could, a moment ago, have killed you. When it can't, there's nothing for the power to push against.

---

### 1.4 "The build came online / it clicked / broke the game / busted"

**Usage:**
- "This is about finding combinations that break the game." (Megabonk reviewer, https://steamcommunity.com/profiles/76561199212803046/recommended/3405340/)
- "One of my favorite runs involved a cast that bounced repeatedly between enemies, slamming poison mobs into walls until they melt" (Hades reviewer, https://steamcommunity.com/profiles/76561198056271409/recommended/1145360/)
- A first-session VS reviewer's reaction log: "uhhh" "oh, okay" "wtf" "woah you can evolve items" (https://steamcommunity.com/profiles/76561198173127898/recommended/1794680/)

**The downside:**
- "The moment you discover weapon evolutions you solve the entire game" (VS reviewer, https://steamcommunity.com/profiles/76561198153018810/recommended/1794680/)
- "I usually know if I'll die to the final boss within the first 5 minutes" (Megabonk reviewer, https://steamcommunity.com/profiles/76561198043767317/recommended/3405340/)
- "I don't get any dopamine hit in my brain for playing a more challenging assassin build than I do an AFK ranger build." (Death Must Die reviewer, https://steamcommunity.com/profiles/76561198217546487/recommended/2334730/)

**What is underneath.** "Came online" is a **phase transition**,, felt as one event though it builds gradually. Three things are true at that moment:

1. **Expectancy confirmation.** The player made a *prediction* while drafting ("if I get X and Y…"), and the game paid it off. The payoff is credited to the player's own foresight.
2. **Discontinuity.** Synergies that multiply (bounce × poison × wall-slam) produce a visible change in *behaviour*, not just in numbers. The Hades reviewer remembers a **choreography**, not a DPS figure.
3. **Surprise beyond prediction.** "Busted" and "broke the game" mean the outcome went past what the player expected. That is positive prediction error.

The downside quotes add a timing constraint. An outcome settled at minute 5 leaves 25 minutes with no prediction error. The evolution moment has to come **mid-run**, roughly in the 10-20 minute band, so that it is both earned and still uncertain.

---

### 1.5 "Screen full of… / fireworks / visual noise / can't see what killed me"

**As praise:**
- "I spent most of my playtime looking like a sentient fireworks display screaming "WHAT IS EVEN HAPPENING" with a grin." (Soulstone reviewer, https://steamcommunity.com/profiles/76561198149913527/recommended/2066020/)
- "An immensely satisfying stimulus overload that's just a bit over-repetitive." (Mo, Retromo, https://retromo.substack.com/p/vampire-survivors-pc-2022/comments)

**As complaint:**
- "your character often gets lost in the deluge of bullets, effects, enemies" (20MTD reviewer, https://steamcommunity.com/profiles/76561198031574827/recommended/1966900/)
- "your spells will eventually cover your entire screen, essentially becoming a photosensitive epilepsy inducing headache." (Soulstone reviewer, https://steamcommunity.com/profiles/76561198037084966/recommended/2066020/)
- "getting oneshotted by an attack from offscreen that you had no way of seeing coming." (Soulstone reviewer, https://steamcommunity.com/profiles/76561198023384828/recommended/2066020/)
- "staring at your screen wondering what exactly killed you this time." (PoE2 reviewer, https://steamcommunity.com/profiles/76561198244648960/recommended/2694490/)

**The synthesis players offer themselves:**
- "fights are not just a fireworks show. Sure, things explode, burn and go off everywhere, but underneath that there is substance." (PoE2 reviewer, https://steamcommunity.com/profiles/76561198087287602/recommended/2694490/)
- "Razor-sharp art direction, buttery smooth animations, instantly readable visual language" (Hades II reviewer, https://steamcommunity.com/profiles/76561198093621729/recommended/1145350/)

**What is underneath.** The same visual density gets praised or condemned depending on **what role the player is in at that moment**:

- When the player is a **spectator of their own power** (safe, winning), density is *spectacle*. Attention can relax into the fireworks, and that relaxation is part of the trance.
- When the player is a **survivor needing information** (threat present), density is *noise*. Attention has to pull the signal (threats, self, pickups) out of the noise, and anything that hides it reads as unfair.

Players praise the spectacle and complain about the lost information, but in both cases they are describing the same density in different moments. The fix isn't "less stuff". It is **channel separation**: give threats, the player, pickups and the player's own effects visual features that never overlap, in hue, value, motion signature and layer order.

---

### 1.6 "That sound when…" / ASMR / "the vacuum" / "the chest music"

**Usage:**
- "the lil ding-sounds from getting XP crystals are satisfying, especially when u run through an entire field of them" (VS reviewer, https://steamcommunity.com/profiles/76561198067330202/recommended/1794680/)
- "a certifiable symphony of sounds as you suck up these gems like an industrial grade vacuum cleaner" (Haikal Fernandez, The Vibes, URL above)
- "triggers a chorus of chimes as your xp bar fills, reminiscent of a jackpot of coins clattering out of an old slot machine." (Mechanics of Magic, https://mechanicsofmagic.com/?p=31948)
- "the sound of an attack going off, enemies being hit, picking up the little green pellets on the ground, the level up sound, all of it is so satisfying." (Brotato reviewer, https://steamcommunity.com/profiles/76561198380776248/recommended/1942280/)
- "My dopamine levels spike as soon as the treasure chests start rolling and the music starts playing." (VS reviewer, https://steamcommunity.com/profiles/76561198205158969/recommended/1794680/)
- A player quoted by Mechanics of Magic: "Why would I skip the animation? That's the best part of this game!" (https://mechanicsofmagic.com/?p=31948)

**The counter-evidence:**
- "Because your game is mainly automatic you still want the players to have a sense of achieving something. The sound effects lack power and the satisfaction of killing something." (Brotato reviewer, https://steamcommunity.com/profiles/76561199566655073/recommended/1942280/)
- "the music and strobe that plays for every single one of those 20+ chests per level is annoying as hell" (VS reviewer, https://steamcommunity.com/profiles/76561198011142637/recommended/1794680/)

**What is underneath.**

1. **Sound is where an auto-attack game puts its agency.** The negative Brotato review spells it out: *because* the attacks are automatic, sound has to carry "a sense of achieving something." When the hands aren't pressing attack, sound is how the game says "you did that."
2. **Granular texture.** A field of gems isn't heard as N separate events. It is heard as one *texture*, a granular cloud: the "symphony", the "chorus", the "vacuum". The most satisfying pickup sounds are short, pitched, slightly randomised, and rising in pitch through a streak. The cloud then reads as a crescendo the player conducts by walking. Dense, soft, high-frequency transients are also classic ASMR triggers, hence "bone crunch ASMR".
3. **Rhythm and entrainment.** Weapon cooldowns are periodic. Periodic sound events invite entrainment, "the synchronization… of organisms to an external perceived rhythm" (https://en.wikipedia.org/wiki/Entrainment_(biomusicology)). Movement falls into the weapon's beat, which feeds the trance (1.2).
4. **Hedonic adaptation.** The chest fanfare is beloved, but only while it is rare and variable. Played "for every single one of those 20+ chests" with predictable contents, it becomes "annoying as hell". The hedonic treadmill, "humans quickly return to a relatively stable level of happiness" (https://en.wikipedia.org/wiki/Hedonic_treadmill), works on a scale of minutes inside a run.
5. **Audiovisual binding.** Sound reinforces impact only if the brain fuses it with the visual event. For simple flash-beep stimuli the temporal binding window is about 100 ms (Frontiers in Neuroscience 2023, https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.1067632/pdf). Average windows run wider: Powers, Hevey and Wallace measured a baseline of "343 ms", narrowing to "231 ms" with training (https://pmc.ncbi.nlm.nih.gov/articles/PMC3366559). Practised players' windows narrow, so **experienced players are more sensitive to sound/visual misalignment**. An 80 ms-late hit may pass with a novice and feel "mushy" to a veteran.

---

### 1.7 "Dopamine / slot machine / crack / goblin brain / monkey brain"

**Usage:**
- "It's the video game equivalent of crack cocaine" (Megabonk reviewer, https://steamcommunity.com/profiles/76561198045508815/recommended/3405340/)
- "This constant drip of dopamine is only amplified by the sheer amount of flashing colors and sounds." (VS reviewer, https://steamcommunity.com/profiles/76561198173127898/recommended/1794680/)
- "Software engineer for slot machines here—the flashing lights, the upbeat sounds, and the suspense of a "multi-item" pull make every chest feel like a jackpot." (VS reviewer, https://steamcommunity.com/profiles/76561198256897471/recommended/1794680/)
- "hunched over like a goblin, whispering "one more run" to nobody." (Megabonk reviewer, https://steamcommunity.com/profiles/76561199036548398/recommended/3405340/)
- Press framing: Galante "has applied his previous experience in the gambling industry" (Peter Howell, The Conversation, https://theconversation.com/vampire-survivors-how-developers-used-gambling-psychology-to-create-a-bafta-winning-game-203613). The chest screen: "The potential rewards cycle past you, just like a slot machine." (Mechanics of Magic, URL above)

**What is underneath.** "Dopamine" is folk shorthand for **reward-prediction error under variable reinforcement**. On a variable-ratio schedule a payoff arrives "on average every nth response, but not always", which produces "both the highest rate of responding and the greatest resistance to extinction" (https://en.wikipedia.org/wiki/Reinforcement). In a survivors-like, several schedules of this kind run at once:

| Schedule | Interval |
|---|---|
| Gem pickups | Continuous (micro) |
| Level-ups | Rising interval |
| Chests | Variable, with a variable *quantity* (1/3/5 items) |
| Evolutions | Rare, partly predictable |
| Unlocks | Meta |

Layering them means **some reward is always about to land**. "Goblin brain" is the player's own word for knowing they're being worked on and enjoying it anyway, until the "mask-off" point (1.2).

The ethical line: this grammar draws no resentment while it costs nothing real. The Conversation notes Poncle "actively avoided the monetisation tactics so often employed on mobiles".

---

### 1.8 "One more run / just one more / where did 3 hours go"

**Usage:**
- "You always say, 'Let's do one more run' and then 2 ½ hours disappear" (Boss Rush review, https://bossrush.net/2022/12/game-review-vampire-survivors/)
- "at 30min its "game over" so even if you lose you win… when death comes there is no loss" (VS reviewer, https://steamcommunity.com/profiles/76561198173127898/recommended/1794680/)
- When it fails: "After a while you stop thinking "one more run" and start thinking "do I really have to do this again?"" (Hades II reviewer, https://steamcommunity.com/profiles/76561198074667492/recommended/1145350/)

**What is underneath.**

1. **Open loops at the moment of death.** A run ends with unfinished business: an unlock *just* reached, a build idea not yet tried, a near miss. Peter Howell describes the near-miss effect: "every run in which players don't reach the 30 minute mark will elicit this feeling" (The Conversation, URL above).
2. **Loss doesn't sting.** "When death comes there is no loss": meta-currency and unlocks convert defeat into progress. Hades' design language was "take the sting out of failure" (Greg Kasavin, per Inven Global's interview summary, https://www.invenglobal.com/datalab/articles/14783/supergiant-games-how-indie-developers-made-goty-hades). If death costs nothing, there's no reason to stop.
3. **Short commitment, distorted time.** Each "one more" is only 20-30 minutes, and flow hides how many have stacked up.
4. **Failure mode:** when the next run promises nothing new (Hades II's "do I really have to"), the pull is gone.

---

### 1.9 "Responsive / tight / snappy / buttery" vs "sluggish / floaty movement / mud"

**Usage:**
- "The game is incredibly responsive and the sound design and visuals make a very satisfying experience zapping, cleaving, or shooting your way through hordes of skeletons" (Halls of Torment reviewer, https://steamcommunity.com/profiles/76561198031768732/recommended/2218750/)
- "Characters feel very floaty, moving longer than they should after you stop moving." (PoE2 reviewer, https://steamcommunity.com/profiles/76561198385960763/recommended/2694490/)
- "Every direction change feels sluggish and unresponsive" (PoE2 reviewer, https://steamcommunity.com/profiles/76561198107987055/recommended/2694490/)

**What is underneath.** In a survivors-like, **movement is the only verb**. All of Swink's "aesthetic sensation of control" (game feel as "real-time control of virtual objects in a simulated space, with interactions emphasised by polish", https://en.wikipedia.org/wiki/Game_feel) therefore sits in one stick. "Floaty" in movement has a precise meaning: *deceleration after input release*, i.e. "moving longer than they should after you stop". Weight on *enemies* is good. Inertia on the *player avatar* is bad, because it breaks the comparator loop: what the player predicted from their own input doesn't match what happens on screen.

Responsiveness also feeds agency through *intentional binding*: when an action is self-caused, "the perceived time between related events is decreased" (https://en.wikipedia.org/wiki/Sense_of_agency). Lag stretches that gap, and the action feels less like your own. GMTK's Celeste analysis (https://www.youtube.com/watch?v=yorTG9at90g) lays out the related "forgiveness" toolkit: input buffering, coyote time, corner correction.

The survivors-like version: dodge and contact hitboxes slightly generous to the player, near-zero acceleration ramps, and instant direction reversal.

---

### 1.10 "Fair" vs "cheap deaths / bullshit / one-shot out of nowhere"

**Usage:**
- "I had many moments where I went from overpowered to being one-shot out of nowhere." (Megabonk reviewer, https://steamcommunity.com/profiles/76561198051360649/recommended/3405340/)
- "There's a difference between testing skill and testing patience." (Soulstone reviewer, https://steamcommunity.com/profiles/76561198068000482/recommended/2066020/)
- On the earned version: "you will remember your first boss kill way longer than your first Reaper kill in VS… Here, you actually did something for it" (Halls of Torment reviewer, https://steamcommunity.com/profiles/76561199628604843/recommended/2218750/)

**What is underneath.** "Fair" means **the cause of death was readable before it happened, and the death could be pinned on something the player did**. "Cheap" deaths come from off-screen threats, hitboxes that outlive their visuals, or an instant jump from god to dead with no warning gradient. The last is the most damaging: it breaks the power fantasy (1.3) and the fairness contract at once, and leaves no near-miss tension.

---

### 1.11 "Empty / lifeless / soulless / asset flip / just a clone"

**Usage:**
- "It clearly draws inspiration from it without understanding what made VS so fun to play to begin with." (20MTD reviewer, https://steamcommunity.com/profiles/76561198027357658/recommended/1966900/)
- "the game lacks the charm and depth of both VS and RoR2" (Megabonk reviewer, https://steamcommunity.com/profiles/76561199132866589/recommended/3405340/)
- "like every weapon is just an animation prop, and everything else… are stat sticks that have close to no impact until they are legendary." (Megabonk reviewer, https://steamcommunity.com/profiles/76561198074248932/recommended/3405340/)
- "it doesn't REALLY grasp that Diablo vibe and feel. It's more like 50-70% there" (Halls of Torment reviewer, https://steamcommunity.com/profiles/76561198042115865/recommended/2218750/)
- "You are largely a spectator to whatever the f*** the game wants to do" (Megabonk reviewer, https://steamcommunity.com/profiles/76561198007359613/recommended/3405340/)

**What is underneath.** "Soulless" turns out to be a cluster of specific absences. Five recur:

1. **Weapons that are props rather than verbs.** Weapons differ only by numbers, with no distinctive motion, sound or kill signature.
2. **Upgrades that change numbers but nothing you can see or hear.** The "stat sticks": +5% is below the noticeable threshold.
3. **No designer intent visible in the upgrade pool.** No jokes, no secrets, no "take this nuke". Players read the *personality* of a ruleset.
4. **No spectator/actor rhythm.** The player watches and is never pulled back into acting.
5. **No congruence across channels.** Big VFX with weak SFX ("rainbows… audio has no weight").

The clones aren't missing *effects*. They're missing **correspondence**: a sound for each kind of event, a visible change for each choice, a behaviour for each weapon. "Soul" is the felt sense that every element was *authored to mean something*.

---

## 2. The moments players retell

Players don't summarise a whole run when they talk about it. They retell **peaks and endings**, consistent with the peak-end rule: people judge an experience "largely based on how they felt at its peak… and at its end" (https://en.wikipedia.org/wiki/Peak%E2%80%93end_rule). The retold moments in this corpus fall into five types:

- **The first evolution / discovery.** "woah you can evolve items" (VS, https://steamcommunity.com/profiles/76561198173127898/recommended/1794680/). "The moment you discover weapon evolutions…" (VS, https://steamcommunity.com/profiles/76561198153018810/recommended/1794680/).
- **The choreographed synergy.** "a cast that bounced repeatedly between enemies, slamming poison mobs into walls until they melt" (Hades, URL above). "From becoming a living lawnmower to zapping the entire screen with chain lightning." (Death Must Die, https://steamcommunity.com/profiles/76561197987200278/recommended/2334730/)
- **The jackpot chest.** The slot-machine engineer's "suspense of a 'multi-item' pull" (VS, URL above). Megabonk's "truely satisfying PING , PING , PING!" (https://steamcommunity.com/profiles/76561198089331648/recommended/3405340/).
- **The earned boss kill.** "you will remember your first boss kill way longer than your first Reaper kill" (Halls, URL above).
- **The extreme-rarity drop in ARPGs.** Mirror and Zod rune stories have the same structure on a lifetime scale. When a speedrunner sold his first-ever Zod rune, a viewer shouted "OMFG HE VENDORED IT" (TechSpot community, https://www.techspot.com/community/topics/diablo-2-speedrunner-scores-legendary-zod-rune-trolls-audience-by-immediately-selling-it.284355/). Rarity counts only when it has a *witnessable moment*: a distinctive drop sound, a beam of light, an audience.

What they share: the player *recognised* the moment as rare while it happened, it had a unique sensory signature, and it carries a causal story ("I took X, then Y…"). Moments without a story, like an unremarkable Reaper kill, don't get retold.

---

## 3. A taxonomy of the ineffable

Each entry gives the felt phrase, then the mechanism, then a test. The supporting quotes are in Section 1.

| # | Felt as | Mechanism | Test |
|---|---|---|---|
| T1 Congruence | crunchy, crisp, "it hits" / floaty, "rainbows but no weight" | Contact visual, transient SFX and target reaction must fuse inside the audiovisual binding window (about 100 ms for simple stimuli, narrower with practice). Hit-stop, sound coherence and camera each, alone, can ruin impact (Lin et al.). | Blind A/B with hit SFX offset by 0/40/80/120 ms. Expect "hits harder" to collapse at 80-100 ms, sooner for veterans. |
| T2 Mass cues | weighty, meaty, bone crunch | Mass is inferred from the struck body's reaction and from time stretched at contact: knockback, stagger, hit-stop, low-frequency transients, permanence. Brightness and particle count don't convey mass. | Hold VFX constant and vary the enemy response (none / flash / +knockback / +corpse). Rate weight. |
| T3 Rhythm and entrainment | hum, trance, symphony, ASMR | Periodic weapon cycles and granular pickup clouds invite motor synchronisation. Low symbolic load plus a rhythmic motor task gives a meditative state. | Beat-quantised vs free-running cooldowns. Measure an absorption scale and session length. |
| T4 Effort → effortlessness | power fantasy, tables turn, "I'm the monster now" | The felt quantity is the inversion (flee → wade in), not the power level. Weber-Fechner means growth must be multiplicative and change the *kind* of effect. Power with no residual threat goes empty. | Telemetry on the sign of the movement vector relative to the horde centroid. It should flip between minutes 10 and 20. |
| T5 Agency under auto-attack | "a sense of achieving something" / spectator, idle game, AFK | Agency moves to movement, drafts, and SFX/VFX that mark consequences as player-caused. | "AFK fraction": the share of time where 10 s with no input wouldn't change the outcome. |
| T6 Earned vs given | clicked, came online, busted / "solved the game", "decided in 5 minutes" | A reward feels earned when the player predicted it and it beat the prediction. A guaranteed or purely random reward has no felt cause. | Distribution of the minute of first evolution: centred mid-run, with variance. |
| T7 Contrast | chest = "best part" → "annoying as hell" after 20 | Hedonic adaptation plus Weber: peaks need valleys. | Excitement rating per chest across a run, with ceremony scaled to rarity. |
| T8 Signal/noise and role | fireworks (praise) / "what killed me" (complaint) | Density is spectacle while safe and noise while the player needs information. Channel separation lets both coexist. | Can a naive viewer locate self, nearest threat and nearest pickup in 300 ms on a minute-25 frame? |
| T9 Layered variable reinforcement | dopamine, slot machine, goblin brain | Overlapping variable schedules mean a reward is always about to land. Turns sour on meta-awareness or monetisation. | Chart the gaps between reward events: none over about 20 s mid-game. |
| T10 Fairness as legibility | fair / cheap, one-shot out of nowhere | A death is fair when its cause was perceivable and the player's own action contributed. | Share of deaths whose source began off-screen or after the hitbox faded. Target close to 0. |
| T11 Open loop | one more run, where did 3 hours go | Near-miss, plus progress that survives death, plus a short commitment unit, plus flow-distorted time. | Rate of restarts within 10 s of death. |
| T12 Authored meaning | charm, "attitude and tone" / soulless, prop weapons, stat sticks | Players read intent from correspondence: every distinct thing looks, sounds and behaves distinctly. | Can a blind player name each weapon from its SFX alone, or from a silent clip alone? |

---

## 4. The canon, and what this corpus adds

The canonical talks are Nijman's *The Art of Screenshake* (https://www.youtube.com/watch?v=AJdEqssNZ-U), Jonasson and Purho's *Juice it or lose it* (https://www.youtube.com/watch?v=Fy0aCDmgnxg), and GMTK's *Secrets of Game Feel and Juice* (https://www.youtube.com/watch?v=216_5nu4aVQ) and *Why Does Celeste Feel So Good to Play?* (https://www.youtube.com/watch?v=yorTG9at90g). They all treat feel as a layer separate from the rules: in *Juice it or lose it*, the Breakout game's rules never change, yet it ends up feeling like a different game. Their unit of analysis is **one hit**. A survivors-like delivers **ten thousand hits at once**, so its feel lives mostly in *aggregate textures*, *phase changes*, and *how attention shifts between acting and watching*. The taxonomy above extends the canon in that direction.

---

## 5. Implications: 18 testable takeaways for a dark-fantasy survivors-like

1. **Spend crunch on kills, not hits.** Reserve hit-stop (2-4 frames, a 30-60 ms equivalent) for elite kills, crits above a threshold, and evolved-weapon procs. Give ordinary hits a 1-frame white flash and a 2-4 px knockback only. *Test:* blind A/B of "hits harder?" against frame-time stability at 300+ enemies.

2. **Make bone the signature sound.** Use a dry, low-mid, transient-rich "crunch" per kill with ±3 semitone randomisation, and voice-limit it into a granular bed so mass deaths read as a *texture*. Halls of Torment players literally call this "bone crunch ASMR". *Test:* SFX-only clip, ask players to rate "satisfying" and "heavy".

3. **Keep audio and visual tight.** Hit and kill SFX must fire on the contact frame, with an audio-latency budget of ≤40 ms end to end, so congruence survives the narrower binding windows of practised players. *Test:* inject 40/80/120 ms offsets and ask veteran testers which build feels "mushy".

4. **Make the gem vacuum a crescendo.** Raise pickup pitch through a streak (resetting after 0.5 s idle), and cap overlapping voices so the XP bar *sings* rather than clatters. Avoid the "constant and absurd" failure. *Test:* rating of pickup audio at minute 5 vs minute 25.

5. **Movement has zero float.** Use ≤2-frame acceleration, instant stop on release, and generous player-favouring contact hitboxes. Movement is the only verb, so give it Celeste-grade forgiveness. *Test:* PoE2-style "sluggish" complaints in playtest surveys should be zero.

6. **Stage the flip from fleeing to wading in.** Tune so that between minutes 10 and 18 a typical build *walks into* the horde. Mark the moment by switching the music layer to a heavier variant when kill rate exceeds spawn rate for 20 s. *Test:* telemetry of the sign of the movement vector toward the horde centroid.

7. **Power must change kind, not just number.** Each weapon gets two or more *visible behavioural* breakpoints (e.g. a scythe that orbits, then reaps in arcs, then leaves soul-fire trails). Retire flat +5% upgrades or bundle them into chunks of at least 20%. *Test:* can players name an upgrade's effect from a 3-second silent clip?

8. **Keep the evolution moment mid-run.** Target the median first evolution at 11-16 min, with the variance a pity timer allows. Give it a unique 1.5 s cinematic beat: freeze, flash, a choir sting in the dark-fantasy key, and the old weapon "shattering" into the new one. *Test:* recall interviews: "describe your best moment" should name evolutions.

9. **Keep residual threat alive to the end.** Power without a witness feels empty. Keep a lethal element present in every minute band: elites that scale, ground hazards, an encroaching darkness. That way a full-screen clear still *means* survival. *Test:* "AFK fraction" (from T5) under 25% in the last 10 minutes.

10. **Ration the fanfare.** Scale chest ceremony to contents: a 1-item chest gets a 0.4 s chime, while a 3- or 5-item chest gets the full reliquary-opening sequence with bells. That way the jackpot stays a jackpot. *Test:* excitement ratings per chest across a run should not decline.

11. **Separate the visual channels by rule.** Enemy threats get warm red/orange plus a hard outline; the player is a constant-luminance silhouette with a rim light; pickups are cold blue-white with a bob animation; player FX are desaturated and drawn *under* enemies at ≤60% opacity after a density threshold. Dark fantasy makes this harder, so budget it. *Test:* the 300 ms "find self / nearest threat / nearest pickup" check on minute-25 screenshots.

12. **Make every death legible.** No off-screen one-shots (edge-of-screen indicators for threats inbound within 1 s). Hitboxes may never outlive their visuals. Show a 2-second "slain by" vignette on the death screen. *Test:* zero deaths per 100 runs whose source began off-screen or after the hitbox faded.

13. **Keep the draft fast and readable.** Use three cards, icon first, one line of text, and show synergy with an evolution glow. Keep median decision time under 3 s, so the draft is a quick choice rather than a reasoning task that pulls the player out of the trance. *Test:* decision-time telemetry plus "felt interrupted" survey items.

14. **Keep a rhythmic bed.** Lock weapon cooldowns to subdivisions of the music tempo, e.g. 120 BPM with cooldowns at 0.25/0.5/1.0 s, so fire patterns sit on the beat and invite entrainment. *Test:* absorption scale (or session length) of beat-locked vs free-running builds.

15. **Design the 30-minute boss as the peak and the end.** Under the peak-end rule, the boss *is* the run's memory. Give it a telegraphed, readable kit that rewards the build the player made: the boss should take visibly more damage from the run's signature synergy. Make the kill a big, distinct beat (silence, then a cathedral bell, then the screen bleeding to black). Never let it pass unremarked. *Test:* "describe your last run" interviews should mention the boss and the build together.

16. **Make death not hurt.** Show progress and near-misses on the death screen ("3 kills short of unlocking the Ossuary Knight"), and make restart a single button press within 1 s. *Test:* restart-within-10-s rate.

17. **Give players a dial for density, not just an opacity slider.** Offer "Spectacle" vs "Clarity" presets that change particle *count and layering*, not just alpha. Soulstone reviewers describe fighting an opacity slider all run. *Test:* proportion of players who change the setting, and their subsequent session length.

18. **Write designer intent into the pool.** Include at least a few absurdly generous "take this nuke" items, secret combos and dark jokes (a cursed relic that is *obviously* broken), so players feel the designer is *on their side*. *Test:* community discovery threads and "charm" mentions in reviews; aim for a "lacks charm" rate below the genre baseline.

---

### Data

Steam review corpus pulled via `store.steampowered.com/appreviews/<appid>?json=1` on 2026-10-03. The raw review JSON was kept out of the repo; the same endpoint and a regex over the review text reproduce any count or quote. All other URLs are inline above.

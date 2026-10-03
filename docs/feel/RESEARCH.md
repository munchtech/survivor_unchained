# What makes ARPGs and survivors-likes feel good: the research

Findings for Survivor Unchained, organised by what produces the feeling:
impact, power growth, reward and anticipation, flow and escalation, sound,
sight, touch, and the ineffable. Each finding names its source. Numbers are
given wherever a source gives them, and marked when they are an estimate.

**How to read the labels.**
- **[S]** a number or claim from the cited source.
- **[E]** an estimate, a conversion or a recommendation (usually derived
  from sourced numbers, but not stated by anyone).
- **(secondary)** from a write-up of the source rather than the source.
- **(unverified)** widely repeated, but not confirmed this session.

The web research hit a shared search budget partway through; some primary
pages (Maxroll, Icy Veins, PoE Wiki, Hades wikis) could not be fetched and
were read through search summaries. Where that matters it is marked. All
quotes are short and attributed; everything else is paraphrase.

The full working notes (about 30,000 words, every claim and quote with its
URL, including the Steam review links) are in `notes/`, one file per
research strand; this file condenses them. The most important sources are
listed at the end of each section.

---

## 0. The ten findings that matter most

1. **Juice is an inverted U, and it works only when it is tied to the
   player's success.** In the largest study of juiciness (Kao 2020, n =
   3,018, an action RPG in four versions), *medium* and *high* juice beat
   both *none* and *extreme* on play time, motivation, experience and even
   performance. A follow-up (Kao et al. CHI 2024, n = 1,699) found that
   feedback that depends on success raised every motive measured, while
   blanket amplification lowered them. [S]
2. **Hit-stop, sound in sync with the visual, and camera control** are the
   three features that most separate games players praise for impact from
   those they call "soft and powerless" (Lin et al. 2022, from Steam
   reviews of 44 action games). [S]
3. **Dopamine follows surprise and suspense, not receipt.** Responses move
   to whatever predicts a reward, and ramp during a wait over an uncertain
   outcome, peaking at even odds (Schultz 1997; Fiorillo 2003). The
   reveal is worth more than the reward. [S]
4. **Perceived growth is logarithmic.** +50 damage feels like a lot at 100
   and nothing at 5,000 (Weber–Fechner; Dehaene 2003). Power must grow by
   *ratios* to feel like growth. [S]
5. **The genre's core promise is ease, not volume.** Vlambeer's second
   step of thirty was "lower enemy HP: no bullet sponges" (Nijman 2013).
   Vampire Survivors' late game is described by players as the horde
   "evaporating". (§2 for how far Survivor Unchained is from this.) [S]
6. **Anticipation needs a staged delay with escalating cues**: the VS
   chest (built by a designer from the slot-machine industry), Diablo's
   item sounds and beams, PoE's filter alerts, Hades' door icons. [S]
7. **Every sound is important, but not at the same time** (DICE's HDR
   audio). Big moments must duck the small ones; reserved signals must
   stay rare (Diablo III removed the legendary beam from rift keys
   because it diluted it). [S]
8. **Rising pitch makes "number go up" audible.** One semitone per chain
   step is the textbook figure; Peggle maps the steps onto the music's
   scale. Reset after a pause. [S]
9. **Players remember a run by its peak and its end** (Kahneman 1993,
   peak-end; duration neglect). Design the climax and the death screen;
   padding the middle adds little. [S]
10. **Habituation is beaten by variation, novelty and rationing**
    (Rankin 2009): vary every repeated sound, keep rare variants, and
    give big stingers rest so they recover. [S]

---

## 1. Impact: making a blow feel like a blow

### 1.1 Foundations

- **Steve Swink, *Game Feel* (2008):** game feel is "real-time control of
  virtual objects in a simulated space, with interactions emphasized by
  polish". Polish is anything that enhances the interaction without
  changing the simulation, and for players, simulation and polish are
  indistinguishable: the flash *is* the hit. Feedback must arrive within
  about **100 ms** to feel instant; the perceive–decide–act cycle is
  about **240 ms**. [S]
- **"Juice it or lose it"** (Jonasson and Purho, 2012) turns a dull
  Breakout clone into a joyful one in eleven steps, in order: colour,
  tweening on every motion, squash and stretch, sound, music, particles,
  screen shake, faces on things, more action, the environment pulsing to
  the music, screen flash. Juice is "maximum output for minimum input". A
  counterpoint (Folmer Kelly) warns that juice must fit the context: for a
  dark fantasy, weight and gore, not wobble. [S]
- **"The Art of Screenshake"** (Jan Willem Nijman, Vlambeer, 2013): thirty
  steps applied to a dull shooter. Note what comes *before* any polish:
  **lower enemy HP**, higher rate of fire, more enemies, bigger bullets.
  Then: muzzle flash, faster bullets, spread, impact effects, hit
  animation, **enemy knockback**, **permanence** (corpses, shells,
  debris), camera lerp and lead, **screen shake**, player recoil, **sleep
  (hit-pause)**, gun kick, more permanence, **more bass**, super weapons,
  random explosions (a third of enemies explode harmlessly on death),
  even more enemies, **camera kick toward the shot**, bigger explosions,
  even more permanence, and last, meaning. Permanence appears three times.
  [S]

### 1.2 Hit-stop

- **What it does** (critpoints; Sakurai's Famitsu columns): it shows the
  collision, gives the eye time to confirm it, and in fighting games opens
  cancel windows. Without it hits feel weak and are harder to read. [S]
- **Numbers.**
  - Smash Ultimate: about **6 frames + 0.65 per % damage, capped at 30**
    (a 15% hit ≈ 15 frames, 250 ms). Melee caps at 20. [S]
  - Guilty Gear Xrd: **7 frames light, ~10 heavy** (117/167 ms). [S]
  - Dead Cells: crits freeze **one frame**, then slow motion "for several
    tenths of a second". [S]
  - God of War (2018) holds Kratos and the target in the first frame of
    the hit pose "for a short duration". [S]
  - A Tokyo Denki University study (Fukuda et al. 2023) found the optimal
    hit-stop for a launching blow at **0.1–0.2 s**, and optimal slow motion
    at **0.2–0.4 s**. [S]
  - Engine tutorials: weak 0–30 ms, strong 50–80 ms, crit/ultimate
    100–150 ms. [S, secondary]
- **Sakurai's refinements:** shake the victim more than the attacker;
  decay the shake over the freeze; let the attacker keep moving a little;
  scale per move (a sword's tip gets more than its blade). [S]
- **Why too much hurts.** Monster Hunter World players called its hit-stop
  "too strong"; Smash limits it in free-for-alls because a third player
  can strike while two are frozen. Doom's glory kills are held to
  "hundreds of milliseconds" to keep the player moving. **In a horde the
  arithmetic is brutal:** 40 hits a second × 33 ms of global pause is
  1.3 s of pause per second. Per-hit stops must be local (the victim
  only); global pauses are a rationed resource. [S + E]

### 1.3 Screen shake

Squirrel Eiserloh, "Juicing Your Cameras With Math" (GDC 2016), slides:
- A **trauma** value in [0, 1]; hits **add 0.2 or 0.5**; trauma decays
  **linearly**; **shake = trauma² or trauma³** (at trauma 0.3/0.6/0.9, the
  cubic gives 3%/22%/73% shake), so small additions are barely felt and
  big ones are unmistakable. [S]
- **Smooth noise, not random**: it feels better and works with slow motion.
  [S]
- In 3D, **rotational shake is good and translational shake is "VERY
  BAD"**; in 2D, both together are best. [S]
- "Camera shake is like salt." The slides give no maximum; a widely copied
  implementation uses roll ≤ 0.1 rad. For a far, high camera, about 1.5%
  of screen height and ≤ 1.5–2° of roll. [S + E]
- Directional shake says more than noise: kick the camera *toward* the
  player's outgoing blow and *away from* incoming damage (Nijman's camera
  kick; Guilty Gear's vertical shake on knockdowns). [S]
- Vampire Survivors ships toggles for weapon screen shake, flashing VFX and
  damage numbers. [S]

### 1.4 Flash, squash, knockback

- **Hit flash** is the most common highlight; a tutorial-standard white
  flash lasts **0.08 s** and should be a hard impulse, not a fade. Set it
  per instance, never on a shared material. [S, secondary]
- **Squash and stretch** along the hit axis for 2–4 frames, then spring
  back. [E, from Disney's principles]
- **Knockback** (Nijman step 11) is where mass becomes visible. Diablo III
  fires an impulse along the blade's direction on the contact frame, so
  bodies fly the way the swing went (Erin Catto, GDC 2012). No source
  gives canonical distances; starting points: 0.3–0.6 body widths for
  ordinary hits over 100–150 ms, 1.5–3 for heavy hits and crits (they
  bowl into neighbours), a quarter of that for elites, none for bosses.
  Cap the total per enemy per second, or stacked auto-weapons make the
  horde jitter. [S + E]

### 1.5 Death, gore and permanence

- **Diablo III's ragdolls** exist to "make the world feel more interactive
  and make the player feel more powerful", and give death variety cheaply.
  Bodies are flung, torn apart by crits, shattered when frozen. "It's not
  about the action, it is about the reaction" (BlizzCon 2013). [S]
- **Element-specific deaths** (frost shatter, fire char, crit gib) are the
  cheapest strong variation in an ARPG. [S]
- **Death effects must never lie or kill.** Diablo IV's lingering
  post-death hazards killed players in dense packs and had to be fixed. [S]
- **Doom 2016's push-forward combat**: kills drop what the player needs, so
  juice and reward arrive in the same beat and the player is pulled
  *into* the fight (Loudy and Campbell, GDC 2018). [S]

### 1.6 The kill, not the hit, is the unit of satisfaction

No single source states this outright; it is the convergent reading of
the sources above and of the player language in §8. [E, strongly
supported]
- Nijman's list escalates kills (random explosions, permanence) more than
  hits.
- Diablo's design loop was "click, click, kill, click, click, kill —
  loot" (Diablo II's sound team), and Brevik's "kill/reward" loop.
- Doom puts its reward on the kill (glory kills, drops).
- Survivors players describe hordes "evaporating", "melting", "popping";
  they describe *deaths*, not hits.

The implication for a horde game is a **feedback budget in tiers**, each
more restrained the more often it fires (§1.7).

### 1.7 Budgeting juice when hundreds of hits land a second

No primary talk covers this exact problem. The principles that follow
from the sources:
1. **Tier events, not hits.** Per hit: cheap, local, always on (flash,
   squash, a spark). Per kill: medium, pooled, rate-limited (the death,
   the decal, the drop, a pooled sound). Per event (a crit kill, an elite,
   a level, a boss phase): expensive, global, rare (shake, slow motion,
   bass, a big number). "The more restrained your weak tier, the harder
   the strong tier lands." [S, secondary + E]
2. **Pool and clamp every shared channel**: trauma clamps at 1; Smash caps
   hitlag; do the same for voices, particles and numbers. [S → E]
3. **Biggest hit wins per window**: within ~66 ms, only the largest
   event gets the global effects. [E]
4. **Local over global** for time effects. [S → E]
5. **Toggles** for shake, flashing and numbers are expected. [S]

Sources (selection): Swink (http://mycours.es/gamedesign2014/files/2014/10/Game-Feel-Steve-Swink-chapter-1.pdf);
Jonasson & Purho and Nijman lists (https://rpgplayground.com/research-making-a-juicy-game/,
https://www.youtube.com/watch?v=AJdEqssNZ-U); SmashWiki hitlag (https://www.ssbwiki.com/Hitlag);
Sakurai (https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/);
Lin et al. 2022 (https://arxiv.org/abs/2208.06155); Fukuda et al. 2023 (https://ken.ieice.org/ken/paper/20230315OCSt/eng/);
Eiserloh 2016 (http://www.mathforgameprogrammers.com/gdc2016/GDC2016_Eiserloh_Squirrel_JuicingYourCameras.pdf);
Catto 2012 (https://box2d.org/files/ErinCatto_Ragdolls_GDC2012.pdf); Dead Cells (https://80.lv/articles/interview-with-the-developers-of-dead-cells);
Doom (https://gdcvault.com/play/1024940/Embracing-Push-Forward-Combat-in); Diablo IV death effects (https://diablofilter.com/news/blizzard-on-death-effects);
Pichlmair & Johansen survey (https://arxiv.org/abs/2011.09201).

---

## 2. Power growth

### 2.1 Growth is perceived in ratios

- **Weber–Fechner**: the smallest noticeable change scales with the size of
  what is already there; numerosity sits on a log-compressed mental number
  line (Dehaene 2003). A +50 damage upgrade is large at 100 and nothing at
  5,000. [S]
- **Idle-game maths** (Anthony Pecorella, Kongregate): costs grow
  exponentially (×1.07 per purchase in AdVenture Capitalist), production
  polynomially, with **multiplier milestones** (×2 at 25 and 50 owned) that
  make old things worth buying again. When only the newest generator
  matters, "interesting decisions" vanish. [S]
- **Players say the same**: flat +5% upgrades are "stat sticks… that have
  close to no impact" (Megabonk review); power must change **kind**, not just
  number (new shapes, new screen coverage). [S, §8]

### 2.2 The promise is ease, not volume

- Vlambeer's second step of thirty, before any polish: **"lower enemy HP"
  — no bullet sponges.** [S]
- The genre's players describe the arc as an *inversion*: "It starts with
  you throwing a single whip at a bat and ends with you becoming a literal
  god of death" (VS review); "you start the run extraordinarily weak,
  struggling to overcome groups of rats, bats, and slimes, and end the run
  as a demigod" (GamingOnLinux). The horde "evaporates". [S]
- When it is withheld, players name it exactly: **"You never reach a true
  'god run' power fantasy… You're rarely ahead of the power curve"**
  (Deep Rock Galactic: Survivor review). DRG:S has the second-lowest
  positive rating of the ten survivors-likes studied (86%). [S]
- Luca Galante: "It's absolutely not balance; balance is completely out of
  the window. I just want to make stuff that is fun." Players read this as
  an attitude: "the game pretty much says 'hey, here, take this nuke. Go
  wild with it'" (20 Minutes Till Dawn review, comparing it unfavourably). [S]
- **But power needs a witness.** "You can eventually clear an entire screen
  … but it just doesn't feel impressive … You feel… nothing really" (Halls
  of Torment). The threat must remain, as elites, hazards and the boss,
  so that the clear still means survival. [S]
- **Enemy health must still grow geometrically**, but slightly *behind* the
  player at power spikes and slightly ahead before the next draft: that gap
  is what drives the build–wall–breakthrough rhythm. [E, from §2.1]

### 2.3 Curves in practice

- **Diablo III**: multiplicative stacking took damage from millions to
  trillions and quadrillions; patch 2.4.0 had to abbreviate numbers
  ("31.5T") and colour the biggest hits; players reported that big numbers
  "lost their emotional appeal because they didn't stand out". Seasonal
  sets raised DPS 2–5× each. [S, secondary]
- **Diablo IV** began against big numbers ("We don't want big numbers
  clogging up the screen", Joe Shely), drifted back into billions, and
  later squished. [S + unverified]
- **Diablo IV Masterworking** is a clean breakpoint rhythm: 12 ranks, about
  **+5%** per rank, with **+25%** to one affix at ranks **4, 8 and 12** and
  a colour shift (blue → yellow → orange). Small steps, a jackpot every
  fourth. [S]
- **Vampire Survivors' XP curve** is close to linear: level 2 costs 5 XP,
  then +10 per level to 20, +13 to 40, +16 after; levels 20 and 40 carry
  one-off taxes of 600 and 2,400 offset by +100% growth for that level.
  "100+ level-up choices per game." Late levels never take minutes. [S]
- **Risk of Rain 2** makes time the difficulty dial and shows it as a
  threat ladder on screen (Easy → … → "HAHAHAHA"), about +0.1 per minute
  on Rainstorm. [S]

### 2.4 The build coming online

- What players retell is a **phase transition**: one item or boon joins two
  separate effects (a Hades Duo boon, a D3 six-piece set, a PoE unique that
  enables a build, a Last Epoch legendary at full potential, a VS
  evolution). "One of my favorite runs involved a cast that bounced
  repeatedly between enemies, slamming poison mobs into walls until they
  melt" (Hades review): a choreography, not a number. [S]
- It feels earned when the player **predicted** it while drafting and it
  **exceeded** the prediction (a positive prediction error). [S + E]
- **Timing.** VS enables evolutions from chests only after **10:00**, and its
  first big spike (300 alive, 0.1 s spawn tick) comes at **11:00**: the
  build comes online exactly as the escalation arrives. "The moment you
  discover weapon evolutions you solve the entire game" (VS) and "I usually
  know if I'll die to the final boss within the first 5 minutes" (Megabonk)
  are the failure modes of a payoff that comes too early or too surely.
  **Mid-run, minutes 10–20.** [S]
- **HoloCure** makes fusion a *visible recipe with a physical drop*: two
  weapons at level 7+ can fuse at a Golden Anvil that drops at 1/100 base,
  rising 1/2000 per minute. Players chase what they can see. [S]
- **Hades** has 28 Duo boons needing boons from two gods; finding one
  shows the player a synergy they built half by accident. [S]

Sources (selection): Pecorella (https://www.gamedeveloper.com/design/the-math-of-idle-games-part-i);
Dehaene (https://homepage.uni-tuebingen.de/andreas.nieder/Dehaene(2003)TICS.pdf); VS level-up and growth
(https://vampire.survivors.wiki/w/Level_up); Mad Forest waves (https://vampire.survivors.wiki/w/Mad_Forest);
D4 Season 4 (https://news.blizzard.com/en-us/article/24077223/4); masterworking (https://primagames.com/gaming/all-masterworks-ranks-and-effects-in-diablo-4);
HoloCure collabs (https://holocure.wiki.gg/wiki/Collabs); RoR2 difficulty (https://riskofrain2.wiki.gg/wiki/Difficulty);
Galante (https://www.pockettactics.com/vampire-survivors/interview); Steam reviews as cited in §8.

---

## 3. Reward and anticipation

### 3.1 Wanting, surprise and the wait

- **Reward prediction error** (Schultz, Dayan and Montague 1997):
  dopamine neurons fire for *unexpected* rewards; once a cue predicts the
  reward, the burst moves to the cue; a predicted reward that fails to come
  dips below baseline. A fully expected reward produces little. [S]
- **Suspense is coded** (Fiorillo, Tobler and Schultz 2003): a sustained,
  ramping response during the ~2 s wait between cue and outcome, **largest
  at even odds**. A short reveal over a truly uncertain outcome is "live"
  time; a reveal over a certain outcome is only waiting. [S]
- **Play releases dopamine** (Koepp et al. 1998: 8 men, a −13% change in
  raclopride binding, roughly double the dopamine; correlated with
  performance). A small study with money at stake; it does not make games
  drugs. [S]
- **Wanting is not liking** (Berridge): the drive to pick up the next chest
  and the pleasure of using what is in it run on different systems. Cues
  can inflate wanting without liking, which players feel as "compulsive but
  hollow". Pay wanting off with liking: the item must change how you play. [S]
- **Anticipation is pleasurable in itself**: waiting for experiences is
  more pleasant than waiting for possessions (Kumar, Killingsworth and
  Gilovich 2014); holidaymakers were happiest *before* the trip (Nawijn et
  al. 2010, n = 1,530). [S]
- **A bar about to fill is a cue.** By the RPE account, the predictive
  response sits on the XP bar nearing full, the chest dropping, the champion
  walking in "carrying something". The cue deserves as much craft as the
  reward. [E, from Schultz]

### 3.2 The chest

- **Vampire Survivors**: gameplay pauses; lights swirl in and out of the
  chest; candidate rewards cycle "like a slot machine reel"; music surges;
  the gold counter ticks up. Galante: "I put a lot of work into making a
  super rewarding and over-the-top treasure chest animation that matches a
  catchy little sound." (He wrote it after noticing that a slot game he had
  worked on had a good jingle that did not match its animation.) [S]
- **Odds**: 1 item 50%, 3 items 10%, 5 items 3%, multiplied by luck (only
  quality is affected); gold 100–200 / 300–600 / 500–1,000; **three
  jingles, one per tier**; usually **one evolution per chest**, and
  evolutions only after 10:00; skippable after the first few. [S]
- Players: "My dopamine levels spike as soon as the treasure chests start
  rolling and the music starts playing"; "Why would I skip the animation?
  That's the best part of this game!"; a slot-machine engineer: "the
  suspense of a 'multi-item' pull make every chest feel like a jackpot".
  And the limit: "the music and strobe that plays for every single one of
  those 20+ chests per level is annoying as hell". **Scale the ceremony to
  the contents.** [S]

### 3.3 The language of loot

- **Kill, then reward.** Diablo's team called the loop "Kill/Reward";
  Brevik: "We were basically making a slot machine where every time that you
  killed a monster, you were pulling that lever." Unidentified items let you
  "unwrap it twice" (Brevik); "If we could have added a third step, we
  would've" (Erich Schaefer). [S]
- **Colour.** Blue for magic and gold for "special" are nearly universal
  (Schaefer: gold "looked more important. It looked cooler"); beyond that
  ladders differ (D2 white–blue–yellow–gold–green; Grim Dawn white–yellow–
  green–blue–purple; Hades white–blue–purple–red). Pick one ladder and use
  it everywhere: drops, card frames, beams, minimap. [S]
- **Three channels for the top tiers** (Diablo III's Loot 2.0): a clang, an
  orange beam, a minimap star. Beams were taken off rift keys because a false
  positive diluted the signal. **Reserved signals must stay rare.** [S]
- **Fewer, louder drops.** Diablo III's Loot 2.0 aimed at "quantity with
  quality" (85% of drops for your class, a hidden bad-luck timer, legendary
  rate doubled and kept). Diablo IV's Season 4: "fewer items will drop
  overall"; legendaries cut to three affixes. Each studio that over-dropped
  had to add filters or scarcity. Players complain of "zero excitement about
  loot", a "loot piñata", "Legendaries doesnt feel like legendaries". [S]
- **Scarcity as reward**: in Path of Exile's Ruthless mode "each ring you
  find represents a huge power boost". [S]
- **A reference item.** Players judge a session by one item (PoE's Divine
  Orb: "the thing that people use as their way of comparing loot", Jonathan
  Rogers). Have one deliberately, give it its own sound. [S]
- **Pity.** Diablo III hides a timer that raises the legendary chance until
  one drops; Lost Ark shows a meter (Artisan's Energy) that guarantees
  success at 100%, and shows the gain before you commit. Too early a
  guarantee kills the chase ("Let it actually be special", D4 forum). [S]
- **Show the reward on the door** (Hades): each door shows the kind of
  reward behind it, giving choice and anticipation; each boon comes with a
  god's voiced line, so every reward is a story beat. [S]

### 3.4 The draft

- **Size**: Galante settled on **three to four** ("I really don't like only
  having two options… more than three to four felt overwhelming"); Hades
  offers three; HoloCure four with reroll ×10, hold ×5, eliminate ×10;
  VS caps banish at 10 across 100+ choices. [S]
- **Frequency matters more than size**: choice overload replicates poorly
  (a meta-analysis found an average effect near zero), but **drafting
  often, under threat**, competes with dodging for the same attention, and
  each choice matters less (decision fatigue). "This was the perfect 'turn
  my brain off' game until I realized I had to actually think about making
  a coherent build" (Death Must Die). Median decision under ~3 s. [S + E]
- **The draft is player-driven difficulty** (Jenova Chen's flow via
  choice): risk-for-power options let skilled players raise their own
  challenge without hidden rubber-banding. [S]
- **Discoverable, not hidden, not spelled out**: tags and "fits your
  build" on cards (recognition is the pleasure); leave the *size* of the
  combo to be experienced. LocalThunk on Balatro: more fun "when you set up
  your Rube Goldberg machine and watch it go before knowing whether or not
  the hand will win". [S]
- **Separate verbs from tuning**: Halls of Torment gives new abilities from
  map loot and elites, and stats from level-ups; VS gives rule-bending
  Arcanas at 11:00 and 21:00 apart from the normal draft. [S]

### 3.5 Gems and the vacuum

- VS gem tiers by colour (blue ≤ 2 XP, green ≤ 9, red above); a cap of
  **400 gems** on the map, above which new XP goes into one red gem whose
  pickup fires **a chain of level-ups**: a performance cap and a jackpot at
  once. [S]
- The vacuum pickup cashes in the whole board: "a certifiable symphony of
  sounds as you suck up these gems like an industrial grade vacuum
  cleaner"; "triggers a chorus of chimes as your xp bar fills, reminiscent
  of a jackpot of coins clattering out of an old slot machine". [S]

### 3.6 What makes rewards cheap

- **Reward inflation**: constant rewards become predicted, so their signal
  fades; cutting them back then feels like punishment (Hopson's
  behavioural contrast). [S]
- **Hedonic adaptation** within a run (the 20th chest). [S]
- **Celebration out of proportion to value** is the slot machine's "loss
  disguised as a win" (Dixon 2010, 2013): it works, and it devalues real
  wins. [S]
- **Expected extrinsic rewards crowd out intrinsic interest**
  (overjustification, Lepper et al. 1973); surprise rewards do not. [S]
- **Stat sticks**: upgrades that change nothing visible (§2.1). [S]

### 3.7 The ethics line

Our chests, near misses and jingles use the same machinery as slots
(Clark 2009 on near misses; Dixon on sound). Loot-box spending is linked to
problem gambling (Zendle and Cairns 2018, n = 7,422). The line: no
real-money randomness; no rigged "almost" outcomes; celebration honest to
value; and Hopson's test: a contingency is ethical if the player has more
fun fulfilling it than not. Players accept being "worked on" by spectacle
that sells them nothing. [S]

Sources (selection): Schultz 1997 (https://www.gatsby.ucl.ac.uk/~dayan/papers/sdm97.html); Fiorillo 2003
(https://pubmed.ncbi.nlm.nih.gov/12649484/); Koepp 1998 (https://pubmed.ncbi.nlm.nih.gov/9607763/); Berridge
(https://sites.lsa.umich.edu/berridge-lab/research-overview/neuroscience-of-linking-and-wanting/); Kumar et al. 2014
(https://bpb-us-e1.wpmucdn.com/blogs.cornell.edu/dist/b/6819/files/2019/12/KumarKillingswothGilovich.14.pdf);
VS chest (https://vampire.survivors.wiki/w/Treasure_Chest, https://mechanicsofmagic.com/2024/05/22/critical-play-vampire-survivors/);
Galante on the chest and draft (https://www.androidpolice.com/vampire-survivors-developer-interview/); Brevik and Schaefer
(https://kotaku.com/why-video-game-loot-is-so-addictive-according-to-the-c-1846695147); Loot 2.0 and beams
(https://games.softpedia.com/blog/Next-Diablo-3-Patch-Removes-Legendary-Beam-from-Greater-Rift-Keys-458391.shtml);
D4 forum (https://us.forums.blizzard.com/en/d4/t/i-hate-the-itemization/114952); PoE Divines
(https://www.pcgamesn.com/path-of-exile-2/return-of-the-ancients-divine-orbs); Lost Ark honing
(https://maxroll.gg/lost-ark/resources/gear-honing-system); Hades doors (https://shacknews.com/article/122186/door-symbol-meanings-hades);
HoloCure draft (https://holocure.wiki.gg/wiki/Level_Up); VS banish (https://gmdq.substack.com/p/vampire-survivors-banish-mechanic);
Clark 2009 (https://pmc.ncbi.nlm.nih.gov/articles/PMC2658737/); Dixon 2010
(https://uwaterloo.ca/reasoning-decision-making-lab/sites/default/files/uploads/files/DixFugetal_10c.pdf); Zendle & Cairns
(https://eprints.whiterose.ac.uk/139116/); Hopson (https://www.gamedeveloper.com/design/behavioral-game-design).

---

## 4. Flow and escalation

### 4.1 Flow

Csikszentmihalyi's components as games use them (Jenova Chen, "Flow in
Games", 2007): clear goals, immediate feedback, challenge matched to skill,
concentration, a sense of control, loss of self-consciousness, altered time,
an activity worth doing for itself. Chen's point: one fixed difficulty
keeps only the average player in flow; **choices that let players set their
own difficulty** keep more of them there. A screen too full to see what
killed you breaks feedback and control. [S]

The survivors version is a **low-load flow**: "brain off" means the verbal
mind idles while the perceptual-motor mind works (§8.2).

### 4.2 The interest curve, peaks and valleys

- **Jesse Schell** (*The Art of Game Design*): a hook, **rising peaks
  separated by strategic valleys**, a climax. Valleys let tension drain so
  the next peak registers as escalation, not noise. [S]
- **Tension and release**: a screen-clear is cathartic *because* of the
  pressure before it; its value is the threat it relieves. [S]
- **Self-Determination Theory** (Ryan, Rigby and Przybylski 2006):
  autonomy and competence each predict enjoyment; power satisfies when the
  player feels they caused it. Kao et al. 2024: success-dependent feedback
  raised every motive; unconditional amplification lowered them. [S]

### 4.3 Vampire Survivors' 30 minutes, measured

From the Mad Forest wave table ("min alive" is what the spawner keeps on
the field) [S]:

| Phase | Minutes | Min alive | Spawn tick | Set pieces |
|---|---|---|---|---|
| Onboarding | 0–1 | 15 → 30 | 1.0 s | first boss and treasure at 1:00 |
| First pressure | 2–4 | 30–50 | 0.25–1.0 s | bat swarm at 2:00, treasure at 3:00 |
| Set pieces | 5–9 | **10–100** | 0.5–1.5 s | flower wall at 5:00, boss, swarms at 7–8 |
| Build online | 10 | **10** | 0.5 s | evolution treasure from 10:00 |
| **Spike** | 11 | **300** | **0.1 s** | skeleton flood and an Arcana boss |
| Escalation | 12–20 | 20–150 | 0.1–1.0 s | treasure almost every minute; giant bosses at 15 and 20 |
| Endgame | 21–29 | 200–300 | 0.1 s | Arcana boss at 21, bosses at 25, swarms at 27 and 29 |
| Cap | 30:00 | — | — | screen cleared to silence; the Reaper |

What it shows: an event (boss or treasure) **every 1–2 minutes, almost
every minute after 10:00**; **density swings, it does not ramp** (a quiet
minute of 10 next to a flood of 300); the build comes online (10:00) just as
the escalation hits (11:00); and the run ends by **clearing the screen to
silence** before the Reaper. Critics describe the same rhythm: "periods
where players comfortably dominate enemies are followed by periods of
increased tension". [S]

Other rhythms: **Brotato** runs 20 waves of 20–60 s (90 s for the last)
with a shop pause between, about 17–18 minutes of fighting; the pause is a
breather and a planning step. **Megabonk** stages are about 10 minutes,
then a Final Swarm. [S]

### 4.4 Thirty minutes is long

- Only **Halls of Torment**, the other 30-minute benchmark, draws repeated
  "too long" complaints (9 per 1,000 reviews, the most of the ten games):
  "30 minute rounds are like torture. There is eventually a item that turns
  them into 20 min rounds which is clutch". Vampire Survivors runs the same
  length with few complaints, probably because its density swings and its
  near-constant treasures keep the half hour varied. [S + E]
- VS ships 15-, 20- and 30-minute stages; 20 Minutes Till Dawn a 10-minute
  quick play. [S]
- "Boring" is 7–18% of negative reviews in every survivors-like studied,
  usually as "autopilot once the build is done". [S]

### 4.5 Peak and end

- **Peak-end** (Kahneman et al. 1993): people judge an experience by its
  most intense moment and its end, neglecting duration; 69% chose to repeat
  a longer cold-water trial that ended slightly warmer. A run is remembered
  by its peak and its end: **engineer peaks**, **make the boss kill the
  loudest moment of the run**, and **design the death screen** (the cause,
  how close you came, what you earned). Padding the middle adds little. [S]

### 4.6 One more run

- Near-miss: "every run in which players don't reach the 30 minute mark will
  elicit this feeling" (Peter Howell); near misses raise the urge to play on
  only when the player had control (Clark 2009). [S]
- Loss that does not sting ("at 30min its 'game over' so even if you lose
  you win"; Hades' aim to "take the sting out of failure"), a short
  commitment, open loops, and the promise of something new. [S]
- The Zeigarnik effect (interrupted tasks are remembered better) is often
  cited; replications are mixed. Do not lean on it. [S]

Sources (selection): Chen (https://khoury.northeastern.edu/~lieber/courses/csu670/f08/materials/p31-chen-flow-in-games.pdf);
Schell (https://notesbylex.com/interest-curve); SDT (https://selfdeterminationtheory.org/player-experience-of-needs-satisfaction-pens/);
Kao 2020 (https://www.sciencedirect.com/science/article/pii/S1875952118300879); Kao et al. 2024 (https://dl.acm.org/doi/10.1145/3613904.3642656);
Mad Forest (https://vampire.survivors.wiki/w/Mad_Forest); Brotato waves (https://brotato.wiki.spellsandguns.com/Waves);
Halls of Torment themes (https://vaporlens.app/app/2218750/halls_of_torment); Kahneman 1993
(https://ius.uzh.ch/dam/jcr:5ae9adc9-61ec-4174-b37c-4b752f36c23b/Kahnemann%20et%20al.%20-%20When%20More%20Pain%20is%20Preferred%20to%20Less%20(1993).pdf);
Howell (https://theconversation.com/vampire-survivors-how-developers-used-gambling-psychology-to-create-a-bafta-winning-game-203613).

---

## 5. Sound

### 5.1 Layering

- **Diablo III** used "up to 10–15 randomized sound layers" on a single
  action, to avoid fatigue over long sessions. Its target: a click should
  sound "like you're actually physically hitting or breaking something
  with your mouse, and that feels good" (Joseph Lawrence). [S]
- **Diablo II**: a club on leather sounds different from a club on chain;
  the gore was watermelons in plastic, for "the meaty yet hollow sound";
  the gem drop was found by tapping wine glasses until the note was
  right. [S]
- **Diablo IV** named its systems for a chaotic mix: skill and foley
  layering for repetitive play, monster voice limiting with an
  "Importance System", and ducking between SFX, voice and music. [S]
- **The common layer model** [E, industry practice]:
  - transient or click, 0–5 ms (carries contact; survives a dense mix);
  - body, 5–80 ms (the material: flesh, bone, metal);
  - tail or sweetener, 80–400 ms (debris, ring, a shimmer on crits);
  - **sub thump**, 40–80 Hz with a fast downward sweep, **only on big
    events** (on every hit it muddies the mix and tires the ear);
  - **crunch**: saturation or bitcrush on transient and body.
- **Doom 2016**'s signature instrument was a **pure sine** run through
  parallel chains of distortion, bitcrushing, fuzz, tape echo and
  compression (Mick Gordon). It is exactly what a runtime synthesiser can
  afford. [S]

### 5.2 Variation and voice management in hordes

- Pitch: one semitone is ×1.0595. Footsteps ±20–50 cents; weapon hits
  ±1–2 semitones; small deaths ±2–3 semitones; also randomise gain
  ±1.5 dB and filter cutoff ±15%. Randomising the transient and the tail
  independently "can drastically reduce the machine gun effect". [S + E]
- FMOD's per-event model: a cap of 1–64 instances, a steal rule (oldest,
  furthest, quietest, virtualise, none) and a cooldown. [S]
- A survivors-like devlog (Cozy Space Survivors) fixed "too loud when many
  play" by refusing a duplicate of the same sound within **0.03 s**. [S]
- A better merge than dropping: duplicates within the window become one
  voice at **+3 dB × log2(n), capped at +9 dB**, so the player hears that
  forty died, not that one did. [E]
- Vampire Survivors players call late-game gem collection "a certifiable
  symphony of sounds": the gem sound is allowed to stack. [S]

### 5.3 Rising pitch: ladders, chains and combos

- "Successively increasing the pitch … can help reinforce the length of
  the chain and increase satisfaction", at **one semitone per step**
  (Game Developer, "The Power of Pitch Shifting"). [S]
- **Peggle**: peg hits climb a scale tuned to the music underneath; the
  "Ode to Joy" fever began as a placeholder and was kept because players
  loved it. "When you hear that 9th it's just so gratifying" (John Vechey).
  [S]
- **Mario's coin** is a rising fourth (B5 then E6, the second held). The
  stomp chain escalates in score (100, 200, 400 … 8,000, then extra lives),
  a ladder with a terminal reward. [S]
- **Tetris Effect** syncs every move to the beat, making the player "both
  player and conductor". [S]
- **Balatro**: scoring steps play one at a time, each with its own sound,
  climbing in pitch; the score catches fire and burns hotter with each
  multiplication; shake grows with magnitude. LocalThunk: the game is more
  fun "when you set up your Rube Goldberg machine and watch it go". (Exact
  notes and pixel values are from one unofficial write-up: unverified.)
  [S + secondary]
- **Reset rule**: reset after 0.6–1.0 s of silence; clamp at about one
  octave; then hold the top note and add a shimmer. Map steps to a
  **pentatonic** scale in the music's key so long ladders stay musical
  (the Peggle principle). [E]

### 5.4 Loot and kill stingers

- **Diablo I/II**: rings were hard to see, so "you'd hear it. So the sound
  became kinda emblematic of 'Something cool has dropped'" (Erich
  Schaefer). D2's "fwip-fwip" item tumble was carried into Diablo III for
  continuity. [S]
- **Diablo III**: a legendary drops with a loud clang, an orange beam and
  a minimap star; the beam was removed from rift keys because a false
  positive diluted it. [S]
- **Diablo IV**: fans voted the Mythic Unique drop sound the **best sound in
  the game**, though some have never heard it. [S]
- **Path of Exile** filters formalise rarity audio: 16 alert tones, volume
  0–300, positional alerts, custom files, 11 beam colours, minimap icons;
  players are advised to mute the cheap and keep loud alerts for the
  Divines. [S]
- **Vampire Survivors**' chest opening is a full jingle (six variants)
  that replaces the stage music while coins and items spill out. [S]

### 5.5 Mixing chaos

- **DICE's HDR audio** (Battlefield: Bad Company): each sound is tagged with
  a real-world loudness; a sliding window maps the loudest current sounds
  into the output range and culls what falls below. "Every sound is
  important, but not at the same time." [S]
- **Doom 2016** drops the music *out* during a glory kill and slams it back
  after: ducking as drama. [S]
- **Starting values** [E]: big stingers (level, boss, legendary) duck the
  horde by **8 dB** (10 ms attack, 400 ms release) and music by 4 dB;
  player-hurt ducks the horde 6 dB (5/250 ms); keep small hits about
  **12 dB** below the reserved level of big events. A **hurt filter**: on
  damage, low-pass the SFX bus from 18 kHz to 1.2 kHz in 20 ms, recovering
  over 350 ms.

### 5.6 Adaptive music

- **Hades** splits each track into stems (drums, bass, "everything else");
  drums engage in combat; stems are picked semi-randomly per chamber "to
  keep things fresh"; changes land on the bar; boss music was often
  written from the end backwards. "We … try to have the music feel like
  it is scoring your playthrough" (Darren Korb). [S]
- **Doom 2016** cut its songs into small sections for re-sequencing so
  "it's nearly impossible to hear a song played the exact same way twice",
  tempo matched to gameplay; music as "reward and motivation". [S]
- **For a procedural score** [E]: four stems (pad, bass, drums, lead),
  driven by an intensity value from enemies *and damage dealt*, rising
  over 2 s and falling over 6 s; thresholds around 0.15 bass, 0.4 drums,
  0.75 lead; quantise to the bar; pull the music down 6–10 dB for half a
  second on an "execution" moment, then slam back.

### 5.7 Sound and the perception of reward

- Celebratory sound on a slot machine raised players' estimate of how
  often they had won from **15% to 24%**, and raised arousal (Dixon et al.
  2013, n = 96); "losses disguised as wins" aroused players like real wins
  (Dixon 2010). Sound **changes remembered generosity**. Two consequences:
  it works, and celebrating trivial events like real wins dilutes the
  real ones (and is the slot machine's trick, not a game's). [S]

Sources (selection): Diablo III audio (https://www.pcworld.com/article/465972/scoring_sanctuary_the_sound_design_of_diablo_iii.html);
Diablo II audio (https://www.gamedeveloper.com/audio/how-audio-design-enhances-diablo-2);
Doom (https://everythingisnoise.net/features/sound-test-doom-2016/); FMOD (https://www.fmod.com/docs/2.03/studio/event-macro-controls-reference.html);
Cozy Space Survivors (https://simonschreibt.itch.io/cozy-space-survivors/devlog/634575/update-61-sound-regulation);
pitch shifting (https://www.gamedeveloper.com/audio/the-power-of-pitch-shifting); Peggle (https://www.gamezebo.com/news/peggle-how-a-spark-started-a-fever/);
PoE filters (https://www.pathofexile.com/item-filter/about); VS music (https://vampire.survivors.wiki/w/Music);
DICE HDR (https://www.frostbite.com/frostbite/news/how-hdr-audio-makes-battlefield-bad-company-go-boom);
Hades (https://gameplay.co/hades-game-music-sound-design-darren-korb-supergiant-games/); Dixon 2013 (https://www.sciencedaily.com/releases/2013/07/130702100348.htm);
D4 sounds poll (https://mein-mmo.de/die-besten-sounds-in-diablo-4-laut-fans/).

---

## 6. Sight

### 6.1 One colour language

- A school, a rarity or a threat should be the same hue everywhere it
  appears, so the screen reads by colour alone. Only "blue = magic" and
  "gold/orange = special" are close to universal (§3.3). [S]
- Keep **hostile** in a reserved band that no friendly effect may use. "your
  character often gets lost in the deluge" (20 Minutes Till Dawn); the
  palette complaint "same color as the monsters" is a textbook overlap. [S]

### 6.2 Damage numbers

- Damage numbers and the health bar are the UI elements most tied to
  combat; crits are commonly bigger and warmer (Lin et al.). [S]
- Practice: a small random offset; white with an outline; pooled; life
  **0.5–1 s**; **merge area ticks into one number**; offer **"crits only"**;
  one MMO cut number sizes by 23–50% and confined them to a quadrant of
  the enemy. Vampire Survivors and others ship a toggle. [S, secondary]
- HoloCure's negative reviews name "excessive damage numbers and effects
  obstruct character visibility" (27% of negative themes are clutter). [S]
- Diablo III's inflation forced abbreviation and highlighting the top hits
  in colour (§2.3). [S]
- Starting points [E]: merge hits on one target within 150–250 ms into one
  number that pops (scale 1.0 → 1.2 → 1.0) as it grows; a cap of 30–40 live
  numbers, dropping the smallest non-crit first; crits ×1.4–1.6 with a
  warm colour and a small shake; size and colour stepping per ×10; a
  three-way setting (all / crits and big hits / off).

### 6.3 Readability in chaos

- The genre's loudest complaint after grind: "LET US TURN DOWN OR TURN OFF
  WEAPON EFFECTS I CANT SEE A DAMN THING" (VS review, positive); Clock
  Lancet "blots out the entire screen"; Soulstone has the most "can't see"
  mentions (20 per 1,000) despite an effects slider; "a circus of red
  circles" at its hardest difficulty. Megabonk and Brotato draw almost none:
  readable silhouettes, low effect density. [S]
- RPS: most clones separated the player from the clutter worse than VS,
  whose flat sprites and limited palette still read at high density. [S]
- Diablo IV's VFX goal: huge effects "while keeping the game clear and
  readable, even when there are many players and monsters on the screen". [S]
- Kao 2020: *extreme* juice reduced **performance**, not only enjoyment. [S]
- **Channel separation** (§8.2): threats, the player, pickups and the
  player's own effects each own a hue, value, motion and layer. Draw
  hostile projectiles and telegraphs on top in reserved colours; fade the
  player's effects by density (~60–70% opacity in the late game); give the
  player an always-visible silhouette. Offer "Spectacle" and "Clarity"
  presets that change particle *count and layering*, not only alpha. [S + E]
- **Death effects must never hide or become a threat** (Diablo IV). [S]
- **Darkness**: 20 Minutes Till Dawn's dark palette is praised for mood but
  draws eye-strain complaints. Use darkness as a radius, keep threats and
  pickups lit everywhere. [S + E]

### 6.4 The reward on screen

- **Beams**: a vertical light in the rarity colour (Diablo III's orange,
  Diablo IV's purple Mythic beam). Reserved, rare, three channels with sound
  and minimap (§3.3). [S]
- **The level-up**: VS stops the world and shows the cards; the HUD bar
  that fills is the cue (§3.1). Brotato's level-ups queue to the end of the
  wave, a breather. [S]
- **Permanence** (Nijman three times): corpses, blood, scorch, so that after
  thirty minutes the arena looks like a battlefield. [S]
- **"Brightness is not weight"** (§8.2): adding effects does not add impact.
  [S]

Sources (selection): Lin et al. (https://arxiv.org/abs/2208.06155); floating text practice
(https://www.wayline.io/blog/unity-floating-combat-text); VS options (https://vampire.survivors.wiki/w/Options);
VS clutter thread (https://steamcommunity.com/app/1794680/discussions/0/4631482569784862180); HoloCure themes
(https://vaporlens.app/app/2420510/holo_cure_save_the_fans.md); Soulstone themes (https://vaporlens.app/app/2066020/soulstone_survivors.md);
D4 VFX (https://www.gamebanshee.com/x6uhx); 20MTD (https://vaporlens.app/app/1966900/20_minutes_till_dawn).

---

## 7. Touch

### 7.1 Rumble

- **Xbox**: the left motor is "rough, high-amplitude"; the right "gentler,
  more subtle"; the left cannot reach the right's high frequencies.
  Mapping: **low motor for weight** (damage taken, explosions, kills of
  big things), **high motor for texture** (rapid small events, ticks). [S]
- **Switch HD Rumble** is felt most strongly at about **100–250 Hz**. [S]
- **Returnal** (Housemarque) synthesises some haptics at runtime (rain),
  designs haptics like audio, and **reserves maximum intensity**: a
  middle-ground baseline so key moments can spike. [S]
- Constant rumble "can become background noise"; haptics need an
  intensity slider and an off switch (accessibility guidelines). [S]
- **For hordes** [E]: never rumble per kill. A starting vocabulary:
  - crit or a 10-kill milestone: high motor 0.2 for 30 ms;
  - damage taken: low 0.6 + high 0.3, 120 ms, decaying;
  - level-up: low 0.4 for 80 ms, a 60 ms gap, 0.5 for 80 ms;
  - elite kill: low 0.7 for 150 ms;
  - boss kill and death: low 1.0 for 400 ms;
  - ceiling 0.8 for everything but those two; at most one non-damage
    rumble per 250 ms.

### 7.2 Latency, buffering and forgiveness

- Motor-visual delay is detected about half the time near **200 ms**, but
  some people spot **under 50 ms** (Raaen and Eg 2016); local latency hurts
  about **twice** as much as network latency, with effects visible at
  100 ms (Liu, Claypool et al. 2021). Target: under 50 ms input to photon,
  audio within one frame of the visual. [S + E]
- **Celeste's source**: 0.1 s coyote time; full run speed in 0.09 s; dash
  0.15 s with a 0.2 s cooldown. "Everything is fudged a tiny bit in the
  player's favor" (Maddy Thorson, "Celeste & Forgiveness"). [S]
- **Input buffers** of **100–150 ms** are standard: a press just before an
  action becomes legal executes on the first legal frame. Over ~200 ms
  they misfire (Souls players complain of queued rolls). [S + community]
- **Dodges in ARPGs**: Path of Exile 2's roll covers 3.7 m with no
  cooldown, i-frames only briefly at the start; Diablo IV's evade has one
  charge and a 5 s cooldown; Hades' dash is immune for its duration and
  a dash-strike comes out of it (exact frames unverified). [S]

### 7.3 Movement and camera

- Vampire Survivors moves at constant speed, instant start and stop.
  Megabonk is the outlier: Source-engine momentum, slides and bunny hops,
  and its movement is the reason it stands out. [S + observation]
- Top-down starting point: full speed in 0.08–0.10 s, stop in 0.06–0.08 s,
  instant reversal, momentum only from dashes and skills. [E from Celeste]
- **Cameras** (Itay Keren, "Scroll Back", GDC 2015): windows, snapping,
  lerp smoothing, forward focus (Defender leads ~25% of the screen). For
  survivors-likes, where threats come from all sides, a smaller lead of
  12–18%. [S + E]

Sources (selection): Xbox vibration (https://learn.microsoft.com/en-us/windows/uwp/gaming/gamepad-and-vibration);
Returnal (https://blog.playstation.com/2021/05/13/how-housemarque-created-returnals-immersive-dualsense-controller-effects/);
Raaen & Eg (https://mmsys2016.itec.aau.at/papers/MMSYS/a28-westerdals.pdf); Liu & Claypool (https://web.cs.wpi.edu/~claypool/papers/csgo-net-local-21/paper.pdf);
Celeste source (https://raw.githubusercontent.com/NoelFB/Celeste/master/Source/Player/Player.cs);
Celeste & Forgiveness (https://maddymakesgames.com/articles/celeste_and_forgiveness/); Keren (https://www.gamedeveloper.com/design/scroll-back-the-theory-and-practice-of-cameras-in-side-scrollers);
game accessibility guidelines (https://gameaccessibilityguidelines.com/?p=3182).

---

## 8. The ineffable: what players can't quite say

### 8.1 Method

Reddit blocks automated reading, so the player-language corpus was built
from **Steam reviews: 34,543 English reviews across 14 games**, pulled from
Steam's public review endpoint (16,548 for eight survivors-likes: Vampire
Survivors, Megabonk, Brotato, Halls of Torment, 20 Minutes Till Dawn, Deep
Rock Galactic: Survivor, Soulstone Survivors, Death Must Die; 17,995 for
Hades I and II, Diablo IV, Path of Exile 1 and 2, Last Epoch), plus press,
essays and developer statements. Vocabulary was counted per 1,000 reviews.

| Words | Survivors-likes | ARPGs + Hades | Ratio |
|---|---|---|---|
| "addict-" | 124 | 52 | 2.4× |
| "dopamine" | 19.3 | 5.9 | 3.3× |
| "brain off" | 6.4 | 1.4 | 4.6× |
| "relax", "chill", "cozy" | 24.8 | 8.3 | 3.0× |
| "AFK", "plays itself" | 3.8 | 1.6 | 2.4× |
| "responsive", "smooth", "snappy" | 9.9 | 30.8 | 0.32× |
| "impactful", "weighty", "crunch", "punchy", "visceral" | 4.3 | 8.3 | 0.52× |
| "satisf-" | 32.0 | 35.5 | ~1× |

**The headline.** Both groups say "satisfying" equally often, but they
mean different things. **ARPG players talk about their hands**
(responsiveness, impact, weight). **Survivors players talk about their
state of mind** (addicted, relaxed, brain off, dopamine). In a
survivors-like, hand-feel is the floor (its absence shows up in negative
reviews) but **the state is what people are paying for.**

Survivor Unchained is both: a dark-fantasy ARPG by day and a survivors
arena by night. It has to meet both vocabularies.

### 8.2 The phrases, and what is underneath each

**"Crunchy, weighty, meaty" vs "floaty, wet noodle, hitting air".**
"Everything explodes but nothing has serious oomph to it" (Soulstone
review); "My eyes are constantly bombarded with rainbows, but the audio has
no weight" (Last Epoch review); "the monsters are just like sponges"
(Soulstone review). *Underneath:* **more effects do not make weight**.
Weight is a *mass inference*: the brain judges mass from how other things
react, not from brightness. Four cues produce it: time stretched at
contact (hit-stop); the struck body reacting (knockback, flash, stagger);
low-frequency, sharp-attack sound at the contact frame; and permanence
(the corpse, the decal). "Sponge" enemies that take hits without reacting
read as "hitting air" however big the numbers.

**"Brain off", "zen", "trance", "meditative".** "A simple, chill game to
turn your brain off with as you effortlessly evaporate thousands of
monsters" (20 Minutes Till Dawn review). *Underneath:* the verbal,
deliberative mind is idle while the perceptual-motor mind is busy: a
low-load flow state (merging of action and awareness, immediate feedback,
time distortion). It breaks three ways, each quoted: **deliberation
spikes** ("until I realized I had to actually think about making a
coherent build", Death Must Die), **under-stimulation** ("something I
could use as a sleep aid", Death Must Die), and **meta-awareness** ("the
most mask-off dopamine drip … It makes me hyper aware of every minute",
Halls of Torment). Keep perceptual load high and symbolic load low and
brief.

**"Power fantasy", "turning into a god", "the tables turn".** "It starts
with you throwing a single whip at a bat and ends with you becoming a
literal god of death" (VS review). When withheld: **"You never reach a true
'god run' power fantasy… You're rarely ahead of the power curve"** (Deep
Rock Galactic: Survivor review). When hollow: "you can eventually clear an
entire screen … but it just doesn't feel impressive … You feel… nothing
really" (Halls of Torment). *Underneath:* players describe power as a
**slope**, an *inversion*: early the horde hunts and you flee; late you
**wade into it**. The same enemies change meaning, and the player's body
(the stick) changes direction. The inversion must be felt (Weber–Fechner:
growth must be multiplicative and change the *kind* of effect), and
**power needs a witness**: a screen-clear means nothing unless the screen
could have killed you a moment ago.

**"It clicked", "the build came online", "busted", "broke the game".** A
first-time VS player's notes: "uhhh" "oh, okay" "wtf" "woah you can evolve
items". *Underneath:* a **phase transition** perceived as one event:
the player *predicted* it while drafting (earned), the behaviour changes
visibly (not just numbers: a Hades player remembers "a cast that bounced
… slamming poison mobs into walls until they melt", a choreography, not
a DPS figure), and it exceeds the prediction (a positive surprise). If the
outcome is decided "within the first 5 minutes" (Megabonk review), the rest
of the run carries no surprise. **The evolution belongs mid-run, about
minutes 10–20.**

**"Screen full of fireworks" vs "can't see what killed me".** Praise:
"looking like a sentient fireworks display screaming 'WHAT IS EVEN
HAPPENING' with a grin" (Soulstone). Complaint: "getting oneshotted by an
attack from offscreen" (Soulstone); "staring at your screen wondering what
exactly killed you" (PoE2). *Underneath:* the same density is **spectacle
when the player is safe and noise when they need information**. The fix
is not less stuff but **channel separation**: threats, the player, pickups
and the player's own effects each own a hue, value, motion and layer that
never overlaps the others. Then the noise can be total without hiding the
signal.

**"That sound when…", "ASMR", "the vacuum", "the chest music".** "the lil
ding-sounds from getting XP crystals are satisfying, especially when u run
through an entire field of them" (VS); "a certifiable symphony of sounds as
you suck up these gems like an industrial grade vacuum cleaner" (The
Vibes); "Why would I skip the animation? That's the best part of this
game!" (on the VS chest). Against: **"Because your game is mainly
automatic you still want the players to have a sense of achieving
something. The sound effects lack power"** (Brotato review); "the music
and strobe that plays for every single one of those 20+ chests per level is
annoying as hell" (VS); "The sound of picking up XP is constant and
absurd" (Soulstone). *Underneath:* (1) **sound is where an auto-attack game
puts its agency**: with no attack button, the ears are how the player
feels the consequences of their choices; (2) a field of gems is heard as
one **granular texture** that rises in pitch, a crescendo the player
conducts by walking; (3) periodic weapon sounds invite **entrainment**;
(4) **hedonic adaptation** works within minutes: rationed fanfare stays
loved; (5) sound and sight fuse only inside the **audiovisual binding
window**, about 100 ms for simple stimuli, wider for most people (343 ms
untrained, 231 ms trained), so **practised players feel misalignment
sooner**.

**"Dopamine", "slot machine", "crack", "goblin brain".** "Software engineer
for slot machines here — the flashing lights, the upbeat sounds, and the
suspense of a 'multi-item' pull make every chest feel like a jackpot" (VS
review). *Underneath:* several variable reward schedules running at once
(gems continuous, levels at a rising interval, chests variable in *quantity*,
evolutions rare, unlocks meta), so **some reward is always about to land**.
Players know and enjoy it ("goblin brain") as long as it costs nothing real
and does not tip into "mask-off".

**"One more run", "where did 3 hours go".** "at 30min its 'game over' so even
if you lose you win… when death comes there is no loss" (VS). Fails when
"you stop thinking 'one more run' and start thinking 'do I really have to
do this again?'" (Hades II). *Underneath:* open loops at the moment of death
(an unlock almost reached, an idea untried, a near miss); loss that does not
sting; a short commitment; flow's distortion of time; and fresh information
promised by the next run.

**"Responsive", "snappy" vs "floaty", "sluggish".** "Characters feel very
floaty, moving longer than they should after you stop moving" (PoE2). In a
survivors-like **movement is the only verb**, so all of Swink's sensation of
control lives in one stick. "Floaty" is precise: deceleration after release.
Weight on enemies is good; inertia on the avatar is bad.

**"Fair" vs "cheap", "one-shot out of nowhere".** "I had many moments where I
went from overpowered to being one-shot out of nowhere" (Megabonk). Fair
means the cause was readable beforehand and pinned on something the player
did. The god-to-dead transition breaks the power fantasy and fairness at
once.

**"Empty", "soulless", "a clone".** "like every weapon is just an animation
prop, and everything else… are stat sticks" (Megabonk); "It's more like
50-70% there" on the Diablo vibe (Halls of Torment); "You are largely a
spectator" (Megabonk). *Underneath:* not missing effects but missing
**correspondence**: weapons that differ only in numbers, upgrades with no
visible change, no designer personality in the pool ("take this nuke. Go
wild" is read as an *attitude*), no rhythm between watching and acting,
big visuals with weak sound. "Soul" is the felt sense that every element
was authored to mean something.

### 8.3 Twelve mechanisms under the ineffable

| # | Felt as | Mechanism | How to test it |
|---|---|---|---|
| 1 | Congruence: "crunchy", "it hits" / "rainbows but no weight" | The contact visual, the transient sound and the target's reaction fuse within the binding window (~100 ms; narrower for veterans) | Blind A/B with the hit sound offset 0/40/80/120 ms |
| 2 | Mass: "weighty", "bone crunch" | Mass is inferred from the reaction and from time stretched at contact, not brightness | Hold VFX constant; vary none / flash / knockback / corpse; rate weight |
| 3 | Rhythm: "the hum", "trance", "symphony" | Periodic weapon cycles and granular pickup clouds invite motor entrainment | Beat-locked vs free cooldowns; absorption and session length |
| 4 | Effort to effortlessness: "the tables turn" | The *inversion* (flee → wade in), multiplicative growth that changes the kind of effect, and a residual threat | Sign of movement relative to the horde's centre should flip between minutes 10 and 20 |
| 5 | Agency under auto-attack: "a sense of achieving" / "spectator" | Agency moves to movement, drafts, and to sound and sight that mark consequences as caused by the player | "AFK fraction": share of time where 10 s of no input would not change the outcome |
| 6 | Earned vs given: "it clicked" / "decided in 5 minutes" | A reward feels earned when predicted and then exceeded | Distribution of the minute of first evolution: centred mid-run, with variance |
| 7 | Contrast: chest "best part" → "annoying" after 20 | Hedonic adaptation; peaks need valleys | Excitement per chest across a run should not decline |
| 8 | Signal and role: "fireworks" / "what killed me" | Density is spectacle when safe and noise when threatened; channels must separate | Can a naive viewer find self, nearest threat and nearest pickup in 300 ms on a minute-25 frame? |
| 9 | Layered variable rewards: "dopamine", "goblin brain" | Overlapping schedules mean a reward is always about to land | No gap over ~20 s between reward events mid-run |
| 10 | Fairness: "fair" / "out of nowhere" | Cause perceivable, player's action contributed | Share of deaths whose cause began off screen: near zero |
| 11 | Open loop: "one more run" | Near miss + progress that survives death + short commitment + time distortion | Restarts within 10 s of death |
| 12 | Authored meaning: "charm" / "soulless", "prop weapons" | Every distinct thing looks, sounds and behaves distinctly | Can a player name each weapon from its sound alone, or a silent clip alone? |

### 8.4 What this adds to the canon

The canonical talks (Nijman, Jonasson and Purho, GMTK's game-feel videos)
take **one hit** as the unit. A survivors-like delivers ten thousand hits
at once, so its feel lives mostly in **aggregate textures** (the granular
sound of a crowd dying, the gem crescendo), in **phase changes** (the build
coming online, the inversion) and in **how attention shifts between acting
and watching**.

### 8.5 The moments players retell

People retell peaks and endings, not runs (peak-end). In this corpus the
retold moments are: the **first evolution**; the **choreographed synergy**
("from becoming a living lawnmower to zapping the entire screen with chain
lightning", Death Must Die); the **jackpot chest** (Megabonk's "PING, PING,
PING"); the **earned boss kill** ("you will remember your first boss kill
way longer than your first Reaper kill in VS… Here, you actually did
something for it", Halls of Torment); the **extreme-rarity drop** (a
speedrunner's first Zod rune; a viewer's "OMFG HE VENDORED IT"). What they
share: the player **recognised the moment as rare while it happened**, it
had **a sensory signature of its own**, and it came with **a causal story**
the player could tell ("I took X, then Y…"). Moments without a story, like
an unremarkable Reaper kill, are not retold.

Sources: Steam review corpus (review URLs for every quote above are in the
working notes); flow (https://en.wikipedia.org/wiki/Flow_(psychology));
audiovisual binding windows (https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2023.1067632/pdf,
https://pmc.ncbi.nlm.nih.gov/articles/PMC3366559); Lin et al. 2022 (https://arxiv.org/abs/2208.06155);
Weber–Fechner (https://en.wikipedia.org/wiki/Weber%E2%80%93Fechner_law); Howell, The Conversation
(https://theconversation.com/vampire-survivors-how-developers-used-gambling-psychology-to-create-a-bafta-winning-game-203613);
Mechanics of Magic on VS (https://mechanicsofmagic.com/?p=31948); The Vibes on VS
(https://www.thevibes.com/articles/lifestyles/53373/vampire-survivors-an-escalating-dopamine-rush-disguised-as-a-retro-game);
Galante (https://www.pockettactics.com/vampire-survivors/interview); Kasavin via Inven Global
(https://www.invenglobal.com/datalab/articles/14783/supergiant-games-how-indie-developers-made-goty-hades).

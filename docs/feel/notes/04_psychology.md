# 04 — The Psychology of Why ARPGs and Survivors-likes Feel Good

Research brief for a dark-fantasy survivors-like hybrid (30-minute runs, level-up drafts, boss at minute 30).
Each claim has a source. Numbers are in **bold**. Where a claim is a designer's opinion or a secondary summary rather than a primary study, it says so. Where I could not check a primary text this session, I mark it "(not re-verified)".

---

## 1. Dopamine: prediction, surprise and "wanting", not pleasure

**Reward prediction error (RPE).** Schultz, Dayan & Montague (1997, *Science*) showed that primate midbrain dopamine neurons fire for *unexpected* rewards. Once a cue reliably predicts the reward, the burst moves to the cue. When a predicted reward is withheld, firing dips below baseline at the moment the reward should have come. The paper ties this pattern to temporal-difference learning signals ("signals changes or errors in the predictions of future salient and rewarding events").
- https://www.gatsby.ucl.ac.uk/~dayan/papers/sdm97.html
- PDF: https://www.its.caltech.edu/~jkenny/nb250c/papers/Schultz-1997.pdf

*Design reading:* a reward the player fully expects produces little phasic response when it arrives. The response sits on the *signal that predicts it* (the chest dropping, the XP bar nearly full) and on outcomes that *beat* expectation. A promised reward that fails to arrive is actively negative, not neutral.

**Uncertainty itself is coded.** Fiorillo, Tobler & Schultz (2003, *Science*) varied reward probability. Phasic responses tracked prediction error. They also found a **sustained, ramping** activation during the **~2 s** wait between cue and outcome. It was **maximal at p = 0.5**, higher than at **p = 0.25 or 0.75**. Uncertainty is therefore "maximal at P = 0.5", and the brain responds to the *suspense* period itself.
- https://pubmed.ncbi.nlm.nih.gov/12649484/

*Design reading:* a short reveal delay (a spinning chest, rolling numbers) over a genuinely uncertain outcome is neurally "live" time. A delay over a certain outcome is just waiting.

**Dopamine is released during video-game play.** Koepp et al. (1998, *Nature*) scanned **8 male volunteers** with [11C]raclopride PET while they played a tank game. Players collected flags, avoided enemy tanks and earned **£7 per level**. Raclopride binding in the ventral striatum fell by a mean of **−13%** (range +8 to −42%). That is comparable to IV amphetamine (−16%) or methylphenidate (−23%) in other studies. The authors note that a 1% decrease reflects "at least an 8% increase" in extracellular dopamine, which implies roughly a doubling. The drop correlated with performance level.
- https://pubmed.ncbi.nlm.nih.gov/9607763/

Caveat: this was a small sample with a monetary reward, so it shows goal-directed play *can* release dopamine. It does not show that games are "like drugs".

**Wanting vs. liking.** Berridge and Robinson separate *incentive salience* ("wanting") from *hedonic impact* ("liking"). "Wanting" runs on large, robust mesolimbic dopamine systems. "Liking" depends on small "hedonic hotspots" (about 1 mm³ in rats) that use opioids and endocannabinoids, and does *not* depend on dopamine. "Dopamine is no longer widely regarded as a pleasure transmitter." In incentive-sensitization theory, cues can inflate "wanting" without raising "liking".
- https://sites.lsa.umich.edu/berridge-lab/research-overview/neuroscience-of-linking-and-wanting/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC5171207/

*Design reading:* the drive to pick up the next chest (wanting) and the satisfaction of using the item you got (liking) are separate systems. A game can create a lot of wanting (glowing chests, jackpot jingles) without delivering liking. Players feel that gap as "compulsive but hollow". Good design pays off the wanting with actual liking: the item changes how you play.

---

## 2. Variable rewards, near-misses and the slot-machine toolkit

**Variable-ratio schedules.** Hopson's "Behavioral Game Design" (Gamasutra, 2001) applied Skinner's schedules to games: "variable ratio schedules produce the highest overall rates of activity of all the schedules". Fixed-interval schedules produce a post-reward pause, then acceleration. Hopson also warns about *behavioral contrast*: when a reward rate drops sharply, the frustration is out of proportion to the cut ("Violation of expectations is perceived as an aggressive act").
- https://www.gamedeveloper.com/design/behavioral-game-design

In a later piece, Hopson argued that "a Skinner Box is completely unnecessary to create operant conditioning" and proposed an ethics test: a contingency is ethical "if the designer believes the player will have more fun by fulfilling the contingency than they would otherwise".
- https://www.gamedeveloper.com/design/there-is-no-skinner-box-says-bungie-user-research-lead

**Near-misses.** Clark, Lawrence, Astley-Jones & Gray (2009, *Neuron*) ran a behavioural study (**n = 40**) and an fMRI study (**n = 15**) on a slot task:
- Near-misses were rated **less pleasant** than full misses but **increased the desire to play**.
- This happened only when the player had **personal control** over the choice. Computer-chosen near-misses *reduced* desire to play.
- Near-misses recruited **ventral striatum and anterior insula**, the same circuitry that responds to wins. Insula activity correlated with self-reported urge to keep playing.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC2658737/

*Survivors-like application:* Howell (University of Portsmouth, *The Conversation*) argues that every Vampire Survivors run ending before the **30-minute** mark works as a near-miss ("just one more go"). He also notes that Luca Galante drew on his slot-machine industry background for the chest animations. Treat this as a secondary analysis, not a primary study.
- https://theconversation.com/vampire-survivors-how-developers-used-gambling-psychology-to-create-a-bafta-winning-game-203613

**Losses disguised as wins (LDWs).** Dixon, Harrigan, Sandhu, Collins & Fugelsang (2010, *Addiction*) studied multi-line slots, where a "win" smaller than the stake still triggers celebratory lights and sounds. With **40 novices**, skin conductance responses to LDWs were **similar to real wins** and **significantly larger than to losses**. The paper also describes the "repeated chiming sound as the machine 'counts up'".
- https://uwaterloo.ca/reasoning-decision-making-lab/sites/default/files/uploads/files/DixFugetal_10c.pdf (doi:10.1111/j.1360-0443.2010.03050.x)

**Sound is part of the disguise.** Dixon et al. (2013/2014, *Journal of Gambling Studies*, "The impact of sound in modern multiline video slot machine play") ran **96 gamblers** through sound-on and sound-off sessions:
- Skin conductance was **significantly higher with sound**.
- Players **overestimated** how often they had won by **24% with sound vs 15% without**.
- "The majority of players preferred the playing session where wins were accompanied by sounds."
- https://www.sciencedaily.com/releases/2013/07/130702100348.htm
- https://uwaterloo.ca/news/news/music-gamblers-ears

*Sound-design reading:* celebratory audio does more than decorate a reward. It **changes how players remember their reward rate** and raises arousal on its own. Two consequences:
1. It works, and our game will feel more generous if we celebrate.
2. If we celebrate trivial pickups the way we celebrate real wins, we are using the LDW mechanism. That inflates *wanting* and dilutes the signal value of real wins.

**Loot boxes.** Zendle & Cairns (2018, *PLOS ONE*, **n = 7,422**) found that loot-box spending is linked to problem-gambling severity, more strongly than other in-game spending.
- https://eprints.whiterose.ac.uk/139116/

This is relevant as an ethical boundary. Our chests should be paid for with play, never with money.

---

## 3. Flow, difficulty and the interest curve

**Flow.** Csikszentmihalyi's flow components, as used by Chen (2007, *Communications of the ACM*, "Flow in Games"), are:
1. clear goals
2. immediate feedback
3. challenge–skill balance
4. concentration
5. sense of control
6. loss of self-consciousness
7. altered sense of time
8. autotelic experience

Chen's practical argument: a single static difficulty curve keeps only the average player in flow. Instead, embed **player-driven choices** that let players move their own difficulty, rather than relying only on hidden automatic DDA, so that different players stay inside their own "Flow Zones".
- https://khoury.northeastern.edu/~lieber/courses/csu670/f08/materials/p31-chen-flow-in-games.pdf
- https://en.wikipedia.org/wiki/Jenova_Chen

*Survivors-like reading:* the level-up draft *is* player-driven difficulty adjustment. Picking defense vs. greed, and opting into curses or elite fights, lets skilled players raise the challenge without hidden rubber-banding. Flow also needs *clear goals* and *immediate feedback*. A screen so full of particles that you cannot see the bullet that killed you breaks components 2 and 5.

**Interest curve.** Schell (*The Art of Game Design*, chapter "Experiences Can Be Judged by Their Interest Curves") describes a good experience as:
- a **hook** (early spike)
- then **rising peaks** separated by **strategic valleys** (rest that makes the next peak register)
- ending in a **climax**

Relevant lenses: Lens of the Interest Curve, Lens of Surprise, Lens of Pleasure, Lens of Reward, Lens of Flow, Lens of Meaningful Choices.
- https://notesbylex.com/interest-curve
- https://www.routledge.com/The-Art-of-Game-Design-A-Book-of-Lenses/Schell/p/book/9781138632059

*30-minute run reading:* the boss at minute 30 is the climax. The minutes 0–2 power spike is the hook. Elite waves or mini-bosses at, say, 10 and 20 are the rising peaks. **Deliberately quieter 20–40 s lulls** after big waves are the strategic valleys. They let tension drain so the next swarm registers as escalation, not noise.

---

## 4. Self-Determination Theory: competence, autonomy and the power fantasy

Ryan, Rigby & Przybylski (2006, *Motivation and Emotion* 30(4):347–363) ran four studies on SDT and games. Main findings:
- Perceived in-game **autonomy** and **competence** predicted enjoyment, preference and short-term well-being change.
- **Intuitive controls** and presence supported these needs.
- Autonomy, competence and relatedness each independently predicted enjoyment and intention to keep playing.
- Ryan's summary: "the psychological 'pull' of games is largely due to their capacity to engender feelings of autonomy, competence, and relatedness."
- https://www.sciencedaily.com/releases/2006/12/061226134706.htm
- https://selfdeterminationtheory.org/player-experience-of-needs-satisfaction-pens/

PENS describes competence as coming from "controls that were easily mastered; feedback that was clear and consistent", and autonomy from "choices regarding goals and strategies".

*Power-fantasy reading:* a survivors-like delivers competence in two channels:
1. **Earned skill competence**: dodging, positioning, kiting.
2. **Granted build competence**: the numbers. The "power fantasy" is the moment the second channel visibly overtakes the threat.

SDT predicts this satisfies only if the player feels *they caused it*, through their draft choices (autonomy) and their survival (competence). Random, unchosen power is weaker. Kao et al. (2024), in section 9, support this: success-*dependent* feedback raised motivation, while unconditional amplification lowered it.

---

## 5. "Number go up": exponential growth and logarithmic perception

**Idle-game math.** Pecorella (Kongregate, *AdVenture Capitalist*), "The Math of Idle Games":
- Costs grow **exponentially**: cost = base × rate^owned, with a growth rate of **1.07** for the Lemonade Stand.
- Production grows **linearly or polynomially**, with periodic **multiplier milestones** (for example **×2 at 25 and 50 owned**). These make old generators worth buying again.
- Exponential cost "will eventually catch and far exceed any polynomial growth", which creates the walls that **prestige** resets past.
- When only the newest generator matters, that "removes any interesting decisions."
- https://www.gamedeveloper.com/design/the-math-of-idle-games-part-i

**Log perception.** By Weber's law, discrimination thresholds scale with magnitude. Fechner's account turns that into a **logarithmic internal scale**. Numerosity is represented on a log-compressed "mental number line" in humans (Dehaene 2003, *TICS*) and in other animals (crows, pigeons).
- https://homepage.uni-tuebingen.de/andreas.nieder/Dehaene(2003)TICS.pdf

Children's number-line estimates start logarithmic and only become linear with schooling, and only for familiar ranges (Siegler & Opfer 2003, *Psychological Science*, doi:10.1111/1467-9280.02438) (not re-verified this session).

*Design reading:*
- Under log perception, a +50 damage upgrade feels large at 100 damage and like nothing at 5,000. **Perceived growth tracks ratios, not differences.**
- To feel like steady growth across 30 minutes, power must climb roughly **geometrically**, by multiplicative steps.
- Enemy health must climb geometrically too, *slightly behind* the player at "power spike" moments and *slightly ahead* before the next draft. That gap is what drives the build–wall–breakthrough rhythm.
- Damage numbers should be displayed so that magnitude reads at a glance: digit count, size and colour tiers by order of magnitude. A "1.2K" vs "12K" vs "120K" step ladder is the visual form of a log scale.

---

## 6. Synergy discovery and the "build comes online" moment

**Balatro.** LocalThunk's stated design goal: "My personal belief is that the game is more fun when you set up your Rube Goldberg machine and watch it go before knowing whether or not the hand will win the round." He therefore did *not* show a score preview. Mark Brown (GMTK) discusses the tension: players compute scores externally anyway. He compares it to Edmund McMillen calling hidden item descriptions "the biggest flaw" in *The Binding of Isaac*, because players went to wikis.
- https://gmtk.substack.com/p/balatros-cursed-design-problem
- https://rogueliker.com/balatro-interview/

The scoring presentation is the payoff: cards and jokers step forward **one at a time**, chips and mult tick up with **rising-pitch** sounds, and big multipliers set the score **on fire**, burning hotter with each multiplication (secondary descriptions in the GMTK piece and a design breakdown at https://blakecrosley.com/zh-Hans/guides/design/balatro).

In psychological terms this combines:
- the Fiorillo **uncertainty ramp**: outcome unknown until the end
- **sequential RPE**: each joker is a small surprise that beats the running expectation
- **escalating sound**: the pitch ladder is an audible "number go up"

LocalThunk also describes "interlocking mechanics that allow you to score more chips as you progress", with "synergies that steer you in interesting directions", and says players "come up with strategies and scores I never would be able to do myself". That is emergent discovery, which supports autonomy and competence.

*Design reading for drafts:* the strongest pleasure is **recognising** that pick A + pick B multiply. That moment gives competence (I figured it out), autonomy (I chose it) and an RPE (output beyond expectation). Choices therefore need to be **legible enough to plan** but **open enough to surprise**. Fully hidden numbers send players to wikis. Fully spelled-out interactions remove discovery.

---

## 7. Anticipation: chests, doors and drafts

**Anticipation is pleasurable in its own right.**
- Kumar, Killingsworth & Gilovich (2014, *Psychological Science*, "Waiting for Merlot") found that waiting for *experiences* is more pleasurable and exciting than waiting for *possessions*. They used questionnaires, a large experience-sampling study and archival analysis.
  - https://bpb-us-e1.wpmucdn.com/blogs.cornell.edu/dist/b/6819/files/2019/12/KumarKillingswothGilovich.14.pdf
- Nawijn et al. (2010) surveyed **1,530** Dutch adults, of whom **974** were vacationers. Vacationers were happier *before* the trip than non-vacationers, but generally not happier after it, unless the trip was very relaxed.
  - https://www.sciencedaily.com/releases/2010/02/100218125204.htm
- Together with Fiorillo's ramp, this suggests the **wait before a reveal** carries a large share of the total pleasure.

**Slot-style reveal in the genre.** Vampire Survivors' chest screen pauses the game. Swirling lights, cycling candidate rewards and a ticking gold counter appear while special music swells, based on the developer's slot-machine background (Howell, *The Conversation*, link above).

**Showing the reward before choosing (Hades).** Hades puts reward symbols on chamber doors, so the player picks the *kind* of reward (boon god, coin, health, upgrade) but not its exact roll. This turns each door into an autonomy-supporting choice point and an anticipation phase. Supergiant's Greg Kasavin frames the genre's appeal as "the thrill comes from the idea that the game can surprise you over and over again."
- https://gamespot.com/articles/hades-changes-what-it-means-to-be-a-roguelike/1100-6483420/

**The level-up draft as a choice point.** Each draft is a small anticipation → choice → reveal loop:
- XP bar nearly full: cue, which carries the predictive dopamine response
- Pause and present cards: the uncertainty window
- Pick: autonomy
- New power visible on the next wave: liking

**Choice overload caution.** Iyengar & Lepper (2000): **24** jam flavours drew more shoppers (**60% vs 40%**) than **6**, but only **3%** of them bought, against **~30%** with 6.
- https://www.chronicle.com/article/to-choose-or-not-to-choose/

The effect replicates poorly. Scheibehenne, Greifeneder & Todd's (2010) meta-analysis of about 50 experiments found a mean effect near zero, with overload appearing under specific conditions such as hard-to-compare options and no prior preferences (doi:10.1086/651235, not re-verified). Draft sizes of **3–4** (Slay the Spire's 3-card rewards, Vampire Survivors' 3–4 level-up options) sit in the comfortable range. The bigger risk is **decision fatigue from frequency**. Drafting every 20 seconds while dodging competes for the same attention as survival.

---

## 8. Catharsis, escalation and the peak-end rule

**Peak-end.** Kahneman, Fredrickson, Schreiber & Redelmeier (1993, *Psychological Science*):
- Subjects held a hand in **14 °C** water for **60 s**, and on another trial for **60 s + 30 s** while the water warmed to **~15 °C**.
- About **69%** chose to repeat the *longer* trial.
- Retrospective evaluations follow the **peak** and the **end**, with "duration neglect".
- https://ius.uzh.ch/dam/jcr:5ae9adc9-61ec-4174-b37c-4b752f36c23b/Kahnemann%20et%20al.%20-%20When%20More%20Pain%20is%20Preferred%20to%20Less%20(1993).pdf

*Run-design reading:* players will remember a 30-minute run by (a) its most intense moment and (b) how it ended. Three consequences:
1. **Engineer peaks**: the screen-clear, the build-online moment, the boss phase change.
2. **Control the end**, including on death. A run that ends in a muddy, unreadable death colours the whole run. A run that ends with a clear "you were killed by X at 24:13; you were 6 minutes from the boss; here is what you unlocked" ends on a readable, motivating note.
3. On victory, **make the boss kill the loudest event of the run**.

Duration neglect also means padding the middle of the run adds little to remembered quality.

**Tension and release.** Screen-clearing effects (nukes, the "Rosary" type) are cathartic because they are *release after tension*. Their value depends on the tension before them. In Schell's terms, a peak with no valley flattens out.

---

## 9. Juice: what the user studies actually say

**Kao (2020, *Entertainment Computing* 34, 100359).**
- **n = 3,018**, four versions of an identical action RPG: **None, Medium, High, Extreme** juiciness.
- None and Extreme produced "significantly decreased play time, … player experience, … intrinsic motivation, and … performance" compared with Medium and High.
- Described as the largest juiciness study to date.
- https://www.sciencedirect.com/science/article/pii/S1875952118300879
- https://www.goodreads.com/author_blog_posts/19932694-the-effects-of-juiciness-in-an-action-rpg-new-study

**Kao, Ballou, Gerling, Breitsohl & Deterding (2024, CHI), "How does juicy game feedback motivate?"**
- Pre-registered, **n = 1,699**, 2×2 + control design varying amplification, success-dependence and variability.
- **Curiosity** was the strongest predictor of enjoyment and the only predictor of playtime. Competence pathways were supported.
- **Success-dependent feedback raised all motives.** **Amplification reduced them**, possibly because it impeded agency.
- Conclusion: effective juice depends on "legible action-outcome bindings and graded success."
- https://spiral.imperial.ac.uk/entities/publication/253c32f5-d124-4a23-88b5-9aaaf114608d
- https://dl.acm.org/doi/10.1145/3613904.3642656

**Hicks et al.**
- *Juicy Game Design: Understanding the Impact of Visual Embellishments on Player Experience* (CHI PLAY 2019).
- *Understanding the Effects of Gamification and Juiciness on Players* (IEEE CoG 2019).

As summarised by Hicks, Rogers, Gerling & Nacke (2024):
- Combined visual and audio juice improved experience over a plain baseline and was "equal" to gamification. Combining both gave a "slight improvement".
- Across action, arcade and FPS games, juice raised meaning and curiosity but **did not change performance or behaviour**.
- Juul & Begy (2016): players *said* juice mattered, but it did not move the measured experience constructs.
- The 2024 paper interviewed **12 audio designers** and identified the pillars of juicy audio as **emphasis/augmentation, cohesion/coherence, synesthesia**.
- https://eprints.staffs.ac.uk/8527/1/3677084.pdf
- https://dl.acm.org/doi/10.1145/3311350.3347171

**Impact feel: hitstop, sound and camera.** Lin, Duan, Wen & Cai (2022) ranked Steam action games by impact feel, using an NLP model trained on player reviews. They proposed a 19-feature framework and found that **hit stop, sound coherence and camera control** separated high- from low-ranked games:
- Games without hit stop were described as "soft and powerless", with an "IF attitude" below **70%**.
- Audio–visual desync and repetitive SFX hurt ratings.
- https://arxiv.org/abs/2208.06155

**Hitstop duration.** Fukuda, Inoue & Tetsutani (Tokyo Denki University, IEICE 2023) found that for attacks that launch enemies off-screen, the optimal hit-stop was **≈0.1–0.2 s** and the optimal slow-motion **≈0.2–0.4 s**.
- https://ken.ieice.org/ken/paper/20230315OCSt/eng/

A 2024 follow-up suggests matching hit-stop length to how long the player is *looking* at the target improves game feel.
- https://scitepress.org/PublishedPapers/2024/124614

**Survey.** Pichlmair & Johansen, "Designing Game Feel: A Survey" (IEEE ToG), warn that juice can obscure "what aspects of interactivity have mechanical importance", for example "when the whole screen is filled with wobbling particle effects". They also describe hit stop as "maybe the best researched phenomenon" in impact feedback.
- https://arxiv.org/abs/2011.09201

**Industry canon.** Jonasson & Purho, "Juice It or Lose It" (GDC Europe 2012), https://www.gdcvault.com/play/1016487/Juice-It-or-Lose; Nijman, "The Art of Screenshake" (2013); Swink, *Game Feel* (2008).

**Synthesis:** juice is an **inverted U**. Moderate-to-high juice beats both none and extreme (Kao 2020). Juice tied to *success* and *legible cause and effect* motivates, while blanket amplification can backfire (Kao et al. 2024). Hit stop and sound coherence are the measurable, high-leverage pieces (Lin 2022).

---

## 10. Mastery, readable danger and fair failure

- **Attribution.** In Weiner's attribution theory, failure attributed to *controllable, internal* causes ("I mis-positioned") keeps motivation up. Failure attributed to *uncontrollable, external* causes ("the game cheated") drains it (https://en.wikipedia.org/wiki/Attribution_(psychology), not re-verified). Juul (*The Art of Failure*, MIT Press 2013) argues that games are where we seek out failure, and that it stays tolerable when it reads as information we can learn from (https://mitpress.mit.edu/9780262529952/the-art-of-failure/).
- **Telegraphs** turn deaths into controllable attributions. They need wind-up, a distinct colour or shape language, an audio cue, and a ground marker for area attacks. This is the competence channel of SDT: "feedback that was clear and consistent" (PENS).
- **Readability vs. juice** is the direct trade-off. Kao's Extreme condition hurt *performance* as well as experience, and Pichlmair & Johansen warn about particles obscuring mechanics. In a survivors-like, player-damage sources and hostile projectiles must stay readable on top of every friendly effect.
- **"One more run."** The Zeigarnik effect (1927) holds that interrupted tasks are recalled better than completed ones. The popular "90% better" figure comes from secondary sources, and later replications are mixed. The idea that an *open loop* (half-finished unlock, quest within one or two runs of completion) pulls people back is plausible but should not be over-claimed.
  - https://www.psychologyofgames.com/2017/01/3613/
- **Short sessions** lower the cost of "one more". 30-minute runs are long for a roguelite. Mid-run save and quit, plus a clear run summary, help.
- **Meta-progression.** It keeps a failed run from feeling wasted. The standard critique is that strong permanent upgrades turn "learn to win" into "grind to win" and make the game easiest at the end, an inverted difficulty curve.
  - https://bugnet.io/blog/how-to-design-a-roguelite-meta-progression
  - Mark Brown, "Roguelikes, Persistency and Progression" (GMTK)
  - Hades' answer: progress through **story, variety and new options** as well as stats, so even a lost run delivers *novelty*.

---

## 11. Cheap rewards and fatigue

- **Hedonic adaptation.** Brickman, Coates & Janoff-Bulman (1978) found that lottery winners returned roughly to control-group happiness and rated everyday pleasures *lower*. Big rewards reset the reference point.
  - https://en.wikipedia.org/wiki/Hedonic_treadmill
- **RPE implies reward inflation.** Rewards that arrive constantly become *predicted*, so their phasic signal fades. Cutting them back then produces negative prediction error, which matches Hopson's behavioral-contrast warning. A loot piñata (gold everywhere, everything glowing) trains the player to expect it, and anything less then feels like punishment.
- **Overjustification.** Lepper, Greene & Nisbett (1973): preschoolers who already liked drawing and were promised a "Good Player Award" later drew *less* in free play than children given a surprise award or no award. Expected extrinsic rewards can crowd out intrinsic interest. Unexpected rewards largely did not.
  - https://www.psychologynoteshq.com/overjustification-effect/
  - JPSP 28(1):129–137

  *Reading:* "Kill 1,000 skeletons for a badge" achievement lists can turn play into labour. Surprise rewards are safer.
- **Habituation.** Rankin et al. (2009, "Habituation revisited") define habituation as a response decrement with repeated stimulation, with three relevant properties:
  - **stimulus specificity**: a different stimulus restores the response
  - **dishabituation**: a novel stimulus restores the response to the old one
  - **spontaneous recovery**: withholding the stimulus restores the response
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC2754195/

  These map directly onto audio and VFX fixes: variation (round-robin samples, roughly ±5–10% pitch and rate jitter; https://sounddesign.irpr.agency/guides/why-is-my-game-audio-repetitive/), novelty (rare variant sounds), and **rationing** (silence or cooldowns between big stingers so they recover).
- **Sensory overload and decision fatigue.** Kao's Extreme condition and Kao et al.'s amplification result are the empirical warnings. Sequential, frequent drafting under threat taxes the same attention as dodging.
- **Ethics line.** Our chests, near-misses and jingles use the same machinery as slots (Dixon; Clark). The mitigations are:
  - no real-money randomness (Zendle & Cairns)
  - honest reward displays: do not celebrate a net loss like a win, which is the LDW pattern
  - Hopson's test: the contingency must make the game *more fun*, not just more compulsive

---

## Implications for design

1. **Put the reveal delay only where the outcome is truly uncertain.** Mechanism: Fiorillo 2003, where the ramp is maximal near p = 0.5. Use 0.6–1.5 s chest and evolution reveals with cycling candidates for genuinely random rewards. Skip or shorten them (or make them tap-to-skip) when the outcome is determined. Never make the player sit through a reveal of a known result.

2. **Scale celebration to actual value, in tiers, and never celebrate a net loss.** Mechanism: Dixon 2010/2013 LDWs, where sound inflated perceived wins from 15% to 24%. Use three or four audio/VFX tiers (common pickup, upgrade, evolution, jackpot). The top tier must be rare enough to stay a positive prediction error.

3. **Build an escalating pitch ladder for chained events.** Mechanism: sequential RPE and the Balatro scoring presentation. XP-gem streaks, multi-kill counters and evolution reveals should step up in pitch and intensity per step, then *reset*. The rise is audible "number go up".

4. **Make power and HP grow geometrically, and show numbers in order-of-magnitude tiers.** Mechanism: Weber–Fechner log perception, and Pecorella's exponential-vs-polynomial structure. Upgrades should be mostly multiplicative, roughly +15–30% effective DPS per draft. Damage numbers should change size and colour per ×10.

5. **Script the 30-minute interest curve explicitly.** Mechanism: Schell's hook, rising peaks, valleys and climax, plus peak-end. Give an early power spike by minute 2, elite peaks around minutes 10 and 20, and 20–40 s breather valleys after each peak. Minute 30 is a boss whose kill is the loudest moment of the run.

6. **Design the ending of every run, including death.** Mechanism: peak-end rule and duration neglect. The death screen should show the cause of death (attributable), time reached vs. boss (a framed near-miss), highlights (peak damage, biggest clear) and unlocks earned. Victory gets a separate, bigger celebration.

7. **Treat each level-up draft as player-driven difficulty.** Mechanism: Chen's flow via choice, and SDT autonomy. Offer 3 cards, with a reroll or banish economy. Regularly include risk/reward options (curse for power, greed for defense) so skilled players can raise their own challenge.

8. **Keep draft frequency humane.** Mechanism: decision fatigue, plus mixed choice-overload evidence. Pause the game during drafts. Cap level-ups per minute late in the run, or bank them, so drafting does not compete with dodging. Keep card text scannable: icon, one line, a number.

9. **Make synergies discoverable, not hidden and not spoon-fed.** Mechanism: competence and RPE from recognising combos (Balatro, the Isaac lesson). Show tags or keywords on cards ("Fire", "Projectile", "On-Kill") and highlight cards that synergise with the current build. Leave the *magnitude* of combos to be experienced.

10. **Keep juice in the medium-to-high band, never extreme, and tie it to success.** Mechanism: Kao 2020 inverted U (n = 3,018) and Kao et al. 2024 (success-dependent feedback helps, blanket amplification hurts). Add an accessibility slider for shake, flash and particles, defaulting to "high", not "max". Bigger effects should come from bigger player achievements, not ambient intensity.

11. **Spend juice budget on hit stop, sound coherence and camera first.** Mechanism: Lin 2022 impact-feel features, and Fukuda's 0.1–0.2 s optimum. Use micro hit-stop of 30–60 ms on crits and elite hits and ~0.1–0.2 s on boss-phase or elite kills. Never apply global hit-stop on every swarm kill. Sync audio to the frame of impact.

12. **Protect threat readability above all effects.** Mechanism: competence and fair attribution (SDT, Weiner), and Kao's Extreme condition hurting performance. Draw hostile projectiles and telegraphs on a top layer with reserved colours that no friendly VFX uses. Fade friendly particles by density. Every boss attack gets a wind-up, ground marker and audio tell.

13. **Fight audio habituation with variation, novelty and rationing.** Mechanism: Rankin 2009 stimulus specificity, dishabituation and spontaneous recovery. Use 4–8 round-robin variants with ±5–10% pitch jitter on high-frequency sounds (hits, gem pickups), voice limits per sound, and cooldowns on big stingers so they recover.

14. **Ration screen-clears as release after tension.** Mechanism: tension and release, and Schell's valleys. Nukes and screen-wipe pickups should appear after peak density, not at random in calm moments. Their payoff scales with the threat they relieve.

15. **Create wanting with visible previews of reward type.** Mechanism: anticipation research (Kumar 2014, Nawijn 2010) and Hades doors. Elites, shrines and chests should show what *kind* of reward they hold (weapon, passive, gold, heal) so the player chooses a route toward something.

16. **Use meta-progression for breadth more than stats.** Mechanism: SDT competence and the "grind to win" critique, plus the Hades novelty model. Unlocks should mainly add new weapons, characters, curses and story fragments. Keep permanent stat bonuses small and capped, so wins still feel earned.

17. **Prefer surprise rewards to contingent badge rewards for intrinsic play.** Mechanism: overjustification (Lepper 1973). Use achievements as discovery signposts ("evolve X to unlock Y") rather than grind quotas, and occasionally give unannounced bonuses.

18. **Hold an explicit ethics line.** Mechanism: near-miss and LDW machinery (Clark 2009, Dixon), and loot-box harm (Zendle & Cairns 2018, n = 7,422). No real-money randomness, no fake near-misses (rigged "almost" outcomes), honest reward displays, and Hopson's test applied to every compulsion loop.

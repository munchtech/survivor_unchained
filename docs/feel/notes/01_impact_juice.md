# 01 — Impact & Juice: research notes for a dark-fantasy survivors-like / ARPG hybrid

Scope: how action games make hits *feel* like hits (hit-stop, shake, flash, knockback, death, permanence, numbers), with the numbers sources actually give, and how to budget all of it when hundreds of hits land per second over a 30-minute run.

**Legend:** **[SRC]** = number or claim taken from the cited source. **[EST]** = my own estimate, conversion or recommendation. Frame→ms conversions assume 60 fps (1 f = 16.7 ms) and are marked [EST] when I did the conversion.

Research caveat: the shared web-search budget ran out partway through. Some items in the brief (Street Fighter per-strength hit-stop tables, a Hades/Supergiant primary source on hit-stop, Diablo III's damage-number spec) could not be confirmed from a primary source. Those gaps are flagged inline rather than filled from memory.

---

## 1. Foundations: Steve Swink, *Game Feel* (2008)

**Definition.** Swink defines game feel as "real-time control of virtual objects in a simulated space, with interactions emphasized by polish" (*Game Feel* ch. 1, PDF excerpt: http://mycours.es/gamedesign2014/files/2014/10/Game-Feel-Steve-Swink-chapter-1.pdf; also https://en.wikipedia.org/wiki/Game_feel).
- **Real-time control:** a continuous loop of intent → action → feedback → correction, which Swink compares to driving a car more than to a conversation (ch. 1).
- **Simulated space:** physical interaction (collision, mass) that the player *actively* perceives.
- **Polish:** "any effect that artificially enhances interaction without changing the underlying simulation". Strip it out and the game still works, but players find it "less perceptually convincing". He also says that **for players, simulation and polish are indistinguishable** (ch. 1). This is the core argument for juice: a hit-flash counts as part of the hit.

**Six components** (Swink, Gamasutra 2007, https://www.gamedeveloper.com/design/game-feel-the-secret-ingredient): input, response, context, polish, metaphor, rules.

**Perceptual thresholds.** These come from his "Game Feel and Human Perception" chapter, which builds on Card, Moran & Newell's Model Human Processor (chapter listing: https://www.taylorfrancis.com/chapters/mono/10.1201/9781482267334-10/game-feel-human-perception-steve-swink). I could not read that chapter directly. The figures below come from secondary summaries:
- **~10 fps** is the floor for the *impression of motion*. Below it, players see a slideshow [SRC, summary: https://kirsturino.github.io/home/blog/gamefeel1.html].
- **~100 ms** is the ceiling for *perceived instantaneous response*. Feedback must arrive within about 100 ms or the player feels they are waiting [SRC, same summary; the 100 ms correction-cycle definition is also in the Pichlmair & Johansen survey, https://arxiv.org/pdf/2011.09201].
- MHP phases: perceptual processor **~100 ms (range 50–200)**, cognitive **~70 ms (30–100)**, motor **~70 ms**. That puts a full perceive→decide→act cycle at **~240 ms** [SRC, kirsturino summary + survey].
- The "50 ms" in the brief matches the *lower bound* of the perceptual-processor range (50–200 ms). It is not a separate Swink rule [SRC for the range; [EST] for the interpretation]. A separate 50 ms figure in the literature: Disc Room delays newly-activated lethal hitboxes by **up to 50 ms** as an accessibility/fairness measure (survey, https://arxiv.org/pdf/2011.09201).

**Implications [EST]:** Every impact cue (flash, sound, number, shake) should start **on the same frame** as the damage event. Never put it more than ~100 ms late. "Sound coherence" (audio in sync with the visual) is one of the three features most correlated with good impact feel (see §5).

---

## 2. "Juice it or lose it" — Martin Jonasson & Petri Purho (2012)

First given at Nordic Game Jam / Nordic Game in 2012 (https://rpgplayground.com/research-making-a-juicy-game/). Game Developer later published the video as a GDC Europe talk (https://www.gamedeveloper.com/design/video-is-your-game-juicy-enough-). The demo starts from a plain Breakout clone and adds, **in order** [SRC, rpgplayground transcript list]:

1. Colour
2. Tweening / easing on every motion
3. Squash & stretch on events; wobble on bounce
4. Sound
5. Music
6. Particles ("you can't have too many": smoke, shatter, trails)
7. Screen shake on impact
8. Eyes and a smile on everything (objects react to their surroundings: eyes track the ball, blink)
9. More action (more balls)
10. Environment pulses to the music
11. Screen flash

Key quotes [SRC, Game Developer]: Jonasson calls juice "maximum output for minimum input". Purho says a juicy game is "way more fun to interact with… feels more professional."

Counterpoint [SRC]: Folmer Kelly ("Indies: resist the urge to juice it or lose it", https://gamedeveloper.com/design/video-indies-resist-the-urge-to-juice-it-or-lose-it-) argues that layered polish can *cost* immersion and that juice should fit the context. For a dark-fantasy tone this is a useful check: wobble and googly eyes are wrong, weight and gore are right [EST].

---

## 3. "The Art of Screenshake" — Jan Willem Nijman, Vlambeer (INDIGO Classes / Control Conference, 2013)

About 45 minutes, about 30 tweaks to a dull side-scrolling shooter (https://www.gamedeveloper.com/design/vlambeer-co-founder-shares-advice-on-building-better-action-games; video: https://www.youtube.com/watch?v=AJdEqssNZ-U; archive: https://archive.org/details/the-art-of-screenshake). **The list, in order** [SRC, rpgplayground transcription, https://rpgplayground.com/research-making-a-juicy-game/]:

1. Basic animations & sound
2. Lower enemy HP (no bullet sponges)
3. Higher rate of fire
4. More enemies
5. Bigger bullets
6. Muzzle flash
7. Faster bullets
8. Less accuracy (spread → dynamism)
9. Impact effects
10. Hit animation
11. Enemy knockback
12. Permanence (shells, corpses, debris stay)
13. Camera lerp
14. Camera position (lead toward aim/action)
15. Screen shake ("just do it")
16. Player knockback (recoil on the player)
17. Sleep (hit-pause)
18. Gun delay
19. Gun kick
20. Strafing (facing locked while firing)
21. More permanence
22. More bass
23. Super weapons / extreme variants
24. Random explosions
25. Even more enemies
26. Even higher rate of fire
27. Camera kick (toward the shot direction)
28. Bigger explosions
29. Even more permanence
30. Meaning: win/lose consequences

Specific numbers and details reported in write-ups:
- Shake goes in the direction **opposite** the player's fire (gun kick on the camera) [SRC, Game Developer].
- **33% chance** an enemy explodes harmlessly on death ("random explosions") [SRC, Game Developer]. A cheap way to vary deaths in a horde.
- "Sleep": the game pauses briefly on a bullet hit. One secondary write-up gives **~0.2 s** [SRC: https://victorweidar.wordpress.com/2016/10/06/the-art-of-screenshake/]. *Treat 0.2 s as unreliable.* At a high fire rate a 200 ms pause per hit would freeze the game permanently. In the talk the pause is applied on *kills/big hits* and is much shorter [EST, unverified].

Three points from Nijman matter most for a horde game [EST]: **lower TTK + more enemies** (steps 2, 4, 25) come *before* polish; **permanence** appears three times; and **meaning** comes last. Juice amplifies a loop that already works.

---

## 4. Hit-stop / hitlag / "sleep"

### 4.1 What it is and why it works
- Both parties freeze at the moment of contact to emphasise the power of the impact. More damage gives a longer freeze. Sakurai, Famitsu column vol. 490 (https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/).
- Functions [SRC, critpoints.net, https://critpoints.net/2017/05/17/hitstophitfreezehitlaghitpausehitshit/]: (1) shows the collision clearly, (2) gives the eye time to confirm the hit, (3) in fighting games, creates input-buffer/cancel windows. In SF2, the ~5-frame cancel window on normals is extended to **~10 frames** by hit-stop. Without it (critpoints cites Dark Souls 2) hits feel weak and are harder to read.
- An empirical study of Steam action-game reviews (Lin, Duan, Wen, Cai 2022, https://arxiv.org/abs/2208.06155) found **hit stop, sound coherence and camera control** are the three features that most separate well-reviewed from poorly-reviewed impact feel. The two games in the sample without hit-stop (Sacred Citadel, Draw Slasher) ranked 39th and 40th of 44, and players called their hits "soft and powerless" [SRC].

### 4.2 Numbers by game
| Game | Hit-stop | Source |
|---|---|---|
| Smash 64 | ⌊d/3 + 4⌋ (JP) / ⌊d/3 + 5⌋ (intl) frames; no cap | [SRC] SmashWiki https://www.ssbwiki.com/Hitlag |
| Melee | ⌊d/3 + 3⌋; **cap 20 f** | [SRC] same |
| Brawl / Smash 4 | ⌊(d·0.3846 + 5)·h·e⌋; **cap 30 f** | [SRC] same |
| Ultimate | ⌊(d·0.65 + 6)·h·e·s⌋·p; cap 30 f | [SRC] same |
| Smash, 15%-damage hit | 64: 10 f · Melee: 8 f · Brawl/4: 10 f · Ultimate: **15 f** | [SRC] same; ≈133–250 ms [EST conversion] |
| Smash modifiers | electric ×1.5; crouch-cancel ×0.67 (victim only); shield ×0.67 (Ult.); zero-damage hits → 0 hitlag | [SRC] same |
| Guilty Gear Xrd | light **7 f**, heavy **~10 f** (≈117 / 167 ms) | [SRC] Lin et al. 2022 PDF §B1.4; ms = [EST] |
| DBFZ | opponent frozen **~1 s** while Goku charges Spirit Bomb (a cinematic, not a per-hit stop) | [SRC] Lin et al. |
| Dead Cells | crits freeze **1 frame**, then slow-mo for "several tenths of a second" + blood spray + impact SFX; modelled on SF4, Garou: Mark of the Wolves, etc. | [SRC] 80.lv interview https://80.lv/articles/interview-with-the-developers-of-dead-cells |
| God of War (2018) | "pops the target to the hit pose and holds both Kratos and the target in that first frame for a short duration" (Christian Wohlwend, Naughty Dog, analysing GoW) | [SRC] https://blog.playstation.com/?p=370399 |
| Monster Hunter World → Wilds | World players said hit-stop was "too strong" and got in the way. Wilds beta made it "a little bit lighter", then raised it again for launch with extra hit SFX after players asked for "harder" hit-stop (Tsujimoto & Tokuda) | [SRC] https://gamingbolt.com/monster-hunter-wilds-weapon-hitstops-will-be-closer-to-what-people-are-looking-forward-to/amp |
| Street Fighter (per-strength table) | **not verified.** Sources only confirm "heavier attacks have longer hitstop" and that it freezes both characters | [SRC qualitative] https://srk.shib.live/w/Street_Fighter_6/Game_Data (page blocked on fetch) |
| Generic engine guidance | weak 0–0.03 s, strong 0.05–0.08 s, crit/ultimate 0.10–0.15 s; freeze on the exact impact frame | [SRC, secondary tutorial] https://uhiyama-lab.com/en/notes/unity/unity-game-feel-hit-feedback/ |
| Whole-screen "screen pause" | 100–300 ms, works with no camera motion | [SRC, secondary] http://www.davetech.co.uk/gamedevscreenshake |

**Scaling with damage.** The Smash formulas give the cleanest model: **base + k·damage, clamped**. Ultimate is about 6 f + 0.65 f per % up to 30 f [SRC]. Sakurai also adjusts per move on purpose: Marth's sword tip gets *more* hit-stop than the blade, and Ryu got exaggerated hit-stop to feel like SF2 [SRC, Source Gaming].

### 4.3 Attacker vs victim; shake during the freeze
Sakurai's eight hit-stop refinements [SRC, https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/]: shake the *victim* more; don't move the hitbox; shake horizontally on the ground and vertically in the air; let the shake decay over the freeze; control the amount per move; interpolate into the damage pose; **keep the attacker moving a little**; scale shake with camera distance. In Smash both sides freeze, and the attacker also vibrates slightly [SRC, Source Gaming]. Smash 4/Ult. cap the victim at 20 f when crouch-cancelling but leave the attacker's 30 f cap unchanged [SRC, SmashWiki], so the two sides *can* have different durations.

### 4.4 Why too much hurts, especially in hordes
- **Multiplayer precedent:** Smash limits hit-stop in free-for-alls because "a third player can move in and strike" while two characters are frozen [SRC, Source Gaming]. A horde is the extreme case of this: there are always more attackers.
- **Flow precedent:** MH World players disliked heavy hit-stop because it interrupted their play [SRC]. Doom 2016's glory kills are kept to "hundreds of milliseconds, just because you want to keep the player moving" (Robert Duffy, id CTO; https://bethesda.net/en-AU/news/the-guts-and-gore-of-doom-glory-kills).
- **Localised vs global:** the Pichlmair & Johansen survey separates *hit stop* (one or more objects drop out of the time flow) from *freeze frames* (the whole game halts) (https://arxiv.org/pdf/2011.09201). **In a horde game, per-hit hit-stop must be local** (freeze only the victim's sprite/animation, and maybe a 1–2 frame squash on the projectile). Reserve global freezes for rare events [EST].
- **Arithmetic [EST]:** 40 hits/s × 33 ms of global sleep = 1.3 s of freeze per second, so the game never runs. Even 1 global frame per kill at 20 kills/s removes a third of real time.

---

## 5. Screen shake: Squirrel Eiserloh, GDC 2016, "Math for Game Programmers: Juicing Your Cameras With Math"

Primary source, slides: http://www.mathforgameprogrammers.com/gdc2016/GDC2016_Eiserloh_Squirrel_JuicingYourCameras.pdf (video summary: https://www.gamedeveloper.com/programming/video-sprucing-up-cameras-with-math).

**The trauma model** [all SRC, slides]:
- Keep a `trauma` value in **[0, 1]**.
- Damage or stress *adds* trauma: **+= 0.2 or 0.5**.
- Trauma **decreases linearly** over time.
- **shake = trauma² or trauma³.** Two reasons on the slides: it feels right ("spring and damper") and escalation is perceptible. Example: **trauma 0.30 / 0.60 / 0.90 → 3% / 22% / 73% shake** (these are the cubic values).
- "Camera shake is like salt": too little is boring, too much is "OMG MAKE IT STOP".

**Translational vs rotational** [SRC]:
- 2D: rotational alone is "okay, but kinda lame"; translational is "nice"; **translational + rotational = awesome**.
- 3D: translational is "super lame"/"VERY BAD", rotational is "nice". In VR: "tread carefully".
- 2D implementation: `angle = maxAngle·shake·noise(seed,t)`, `offsetX/Y = maxOffset·shake·noise(seed+1/2,t)`. In 3D, apply yaw/pitch/roll and XYZ offsets, each on its own seed.

**Perlin, not random** [SRC]: smoothed fractal noise "is WAY better than random". It feels better, works automatically with pause and slow-mo, has adjustable frequency, and replays reproducibly.

**Max values.** The slides do *not* give maxAngle/maxOffset. A widely used implementation of the talk (KidsCanCode Godot recipe, https://kidscancode.org/godot_recipes/3.x/2d/screen_shake/) uses **trauma power 2 (range 2–3), decay 0.8/s, max offset (100, 75) px, max roll 0.1 rad (~5.7°)** [SRC, secondary]. For a zoomed-out horde camera, 100 px is huge. Use roughly 1–2% of screen height for the max offset and ≤2° for max roll [EST].

**Camera smoothing, same talk** [SRC]: asymptotic averaging `x += (target − x)·k`, with **k ≈ 0.01 = slow, 0.1 = reasonably fast, 0.5 = incredibly fast (at 60 fps)**. Multiply k by timeScale so it respects pause and slow-mo. Use separate (asymmetric) weights per axis or direction. "The camera is a character."

**Directional shake** [SRC, survey + Lin et al. + davetech]: an eased shake in a meaningful direction says more than random noise. Guilty Gear Xrd shakes vertically on knockdowns and horizontally on horizontal slashes. Kick the camera *toward* the player's attack and *away* from incoming damage (davetech).

**Horde rate-limiting** [SRC, secondary devlog summary]: when dozens of enemies die at once, shake should become a "consistent rumble" instead of stacking. The trauma model does this for free: trauma clamps at 1, and squaring keeps small additions nearly invisible. Vampire Survivors ships a **"Weapons ScreenShake"** toggle and a **"Flashing VFX"** toggle (https://vampire.survivors.wiki/w/Options) [SRC].

---

## 6. Impact frames, flash, squash, knockback, death, permanence

**Hit-flash.**
- Flashing the character on hit is "the most pervasive" form of colour-flash highlighting [SRC, Lin et al.].
- KOF XIII flashes the whole screen white/red for game-over [SRC, Lin et al.].
- Duration: a tutorial-standard white flash lasts **0.08 s (~5 frames)** [SRC, secondary: uhiyama-lab]. One busy-screen guideline says flashes should be a hard impulse, not a fade, and readable in a single frame [SRC, secondary, search summary of gamedev.net shaderlab].
- Implementation pitfall for hordes: set the flash per instance (MaterialPropertyBlock or per-sprite uniform), not on a shared material, or every enemy flashes at once [SRC, uhiyama-lab].

**Squash & stretch** is principle #1 of Disney's twelve (https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation) and step 3 of Juice it or lose it. On hit, squash the victim along the hit axis for 2–4 frames, then spring back [EST].

**Knockback.**
- Nijman step 11 (enemy knockback) and step 16 (player recoil) [SRC].
- God of War lets enemy reactions "break reality with huge pose changes, flips, and even air juggling" (Wohlwend) [SRC].
- Diablo III fires a *linear explosion* along the blade direction on the weapon's contact frame, so the ragdoll flies the way the swing went. Impulse is applied at the closest point on each collision shape, which adds spin, and is scaled by projected surface area (Erin Catto, GDC 2012, https://box2d.org/files/ErinCatto_Ragdolls_GDC2012.pdf) [SRC].
- No source gave canonical knockback distances. Starting points: 0.2–0.5 enemy body-widths on normal hits, decaying over ~100–150 ms; 1–3 body-widths for heavy/crit hits; no knockback for elites/bosses, which get flinch/flash instead [EST].

**Death and "the bigger they fall."**
- Diablo III goal, in Catto's words: ragdolls "make the world feel more interactive and make the player feel more powerful", give "lots of death variation and reduce the animator workload", and keep corpses on the terrain [SRC].
- D3 deaths are pre-animated, then become physical: bodies can be flung, torn apart by crits, shattered when frozen, or have their skeleton ripped out [SRC, search summary of diablowiki "Physics", https://diablowiki.net/Physics]. D3 also has a gibbing system for zombies [SRC, Catto].
- Diablo III's animators focused on the *reaction*: "it's not about the action, it is about the reaction… What does the flail do after the movement?" (BlizzCon 2013 panel, https://blizzplanet.substack.com/p/blizzcon-2013-diablo-iii-gameplay-systems-crusader-panel-transcript) [SRC].
- I could not find a specific Julian Love talk titled "the bigger they fall". His GDC panel was "Giant Toads and Zombie Bears: Technical Art Re-envisioned for Diablo 3". Treat the phrase as folklore, not a citation.

**Damage-type deaths.** Element-specific death states ("frozen shatter", "crit explode") are the cheapest strong variation in an ARPG [SRC, D3 above]. Nijman's harmless random explosion on **33%** of deaths is the 2D equivalent [SRC].

**Permanence.** Nijman lists it three times (steps 12, 21, 29) [SRC]. Corpses, shells and decals show how much damage the player has done to the space. A horde game can afford decals as a single render-texture "blood map" with near-zero per-kill cost [EST]. Watch the Diablo IV lesson: post-death hazards (lingering explosions, delayed projectiles) killed players in dense, fast packs, and Blizzard promised to fix it (https://diablofilter.com/news/blizzard-on-death-effects) [SRC]. **Death juice must never hide or become a threat.**

**Doom 2016: "push forward combat"** (Kurt Loudy & Jake Campbell, GDC 2018, https://gdcvault.com/play/1024940/Embracing-Push-Forward-Combat-in) [SRC]:
- No regenerating health, cover or reloads; the player "take[s] what they need from adversaries".
- Glory kills grew out of that idea, are position-dependent, and are capped at "hundreds of milliseconds".
- Lesson for a survivors-like [EST]: make kills *drop the resource* (XP, health orbs), so juice and reward arrive in the same beat and the player is pulled *into* the horde.

---

## 7. Animation: anticipation, follow-through, smears

- **Anticipation / follow-through / exaggeration / timing** are Disney principles (Wikipedia, above). God of War's swings "have very large arcs with powerful follow throughs" (Wohlwend) [SRC]. The D3 Crusader's Shield Bash "gathers that energy… holds it and then explodes forward" [SRC, BlizzCon 2013].
- **Smear frames** simulate motion blur between keys. They go back to 1912 and were standardised at Warner Bros. In games: Sonic's feet, Crash's spin, Jak & Daxter's elongated in-betweens over **1–2 frames** (https://en.wikipedia.org/wiki/Smear_frame) [SRC].
- **Snap, don't blend:** One Finger Death Punch, the best-liked game in Lin et al.'s sample, switches straight to the strike pose with *no interpolation*, holds it for frames 2–5, and lets the VFX carry the direction [SRC, Lin et al.].
- **Auto-weapons caveat [EST]:** players don't press a button per swing, so anticipation must be short (≤50–80 ms) or fully cosmetic. A long wind-up on an auto-attack reads as lag. Put the "weight" into follow-through, trails and the victim's reaction instead.

---

## 8. Damage numbers

**Evidence:**
- Lin et al.: the health bar and damage numbers are the UI elements most tied to combat. Crits commonly render **bigger and red** [SRC].
- Vampire Survivors: damage numbers are a player toggle (Gameplay/Favorites) [SRC, https://vampire.survivors.wiki/w/Options]. Players also report turning them off helps performance with many enemies on screen [SRC, search summary, low confidence].
- D3/RoS: Wyatt Cheng conceded very large numbers are "hard to process" but called inflation a distant concern [SRC, BlizzCon 2013]. History proved it a real one [EST].
- Practitioner guidance [SRC, secondary: https://www.wayline.io/blog/unity-floating-combat-text and search summaries of MMO/indie devlogs]: random spawn offset to avoid overlap; white text with outline; pool the objects; lifetime **0.5–1 s**; merge AoE ticks into one number; offer a "crits only" filter; one MMO reworked its numbers to sans-serif, cut sizes by **23–50%**, and confined outgoing numbers to the enemy's upper-right quadrant.
- Not verified here: exact Borderlands/Brotato/Diablo III styling specs. I'll describe them only qualitatively: D3 uses a larger, coloured crit pop; Borderlands uses comic-style bouncing numbers with elemental colouring.

**When numbers help vs clutter [EST]:** they help when they *teach* (new build, crit chance, elemental weakness) and when they mark rare events (crit, kill-shot, boss). They clutter when 200 white "12"s cover the enemies the player needs to dodge. In a horde, numbers should be aggregated, ranked, and capped.

---

## 9. Budgeting juice when hundreds of hits land per second

No primary GDC talk on this specific problem turned up. The evidence above combines into these principles:

1. **Tier events, not hits.** Split feedback into *per-hit* (cheap, local, always on), *per-kill* (medium, pooled, rate-limited), and *per-event* (crit-kill, elite kill, level-up, boss phase: expensive, global, rare). Supported by Lin et al. (distinguish light from heavy feedback) and the uhiyama tiers. "The more restrained your weak tier, the harder the strong tier lands" [SRC, uhiyama-lab].
2. **Pool and clamp shared channels.** Trauma clamps at 1 (Eiserloh); Smash clamps hitlag at 20–30 f and limits it in free-for-alls (Sakurai). Apply the same to SFX voices, particles and numbers [SRC principles → EST application].
3. **Biggest-hit-wins per window.** Within a time window (e.g. 50–100 ms), run only the largest event's global effect (shake impulse, sleep, bass hit) and drop the rest [EST].
4. **Local over global.** Per-hit stop goes on the victim only; global freeze is reserved (survey distinction, Smash FFA rule) [SRC → EST].
5. **Accessibility toggles are expected.** Vampire Survivors exposes shake, flashing and damage-number toggles [SRC].
6. **Death effects must not lie.** D4 post-death hazards in dense packs are a cautionary tale [SRC].

---

## 10. Implications for a horde survivors-like (design takeaways + numeric starting points)

All numbers below are **[EST] starting points** derived from the cited sources; tune in playtests.

1. **Zero-latency confirmation.** Flash, SFX and number start on the damage frame, and the whole pipeline stays under 100 ms from input/auto-fire to visible hit (Swink's ~100 ms ceiling [SRC]). Never queue impact feedback behind a hit-stop.

2. **Three-tier feedback budget.**
   - *Per-hit:* white flash, micro-squash, spark. No shake, no global sleep.
   - *Per-kill:* death animation/gib, decal, XP drop, pooled SFX.
   - *Per-event* (crit-kill, elite, boss, level-up, ult): shake, local slow-mo, bass, big number.

3. **Hit-flash: 50–80 ms (3–5 frames) of solid white, hard on/off.** Based on the 0.08 s tutorial standard [SRC] and "hard impulse, not fade". Per-instance uniform, never a shared material. Re-hits refresh the timer rather than stacking. Bosses: 2-frame flash + tint ramp to avoid strobing; respect a "Flashing VFX" toggle (VS precedent [SRC]).

4. **Local hit-stop only, damage-scaled, capped.** Victim-only freeze = `clamp(1 f + 0.15 f × (damage / enemyMaxHP × 10), 0, 4 f)`. That gives ≈0–67 ms for trash (cf. GG Xrd's 7/10 f for one-on-one [SRC]; Smash's base + k·d with cap [SRC]). Shake the victim's sprite ±1–2 px during the freeze and decay it (Sakurai [SRC]). Never freeze the player character or the world on a normal hit.

5. **Global sleep is a rationed resource.** Allow at most **1 global hit-pause per 1.5–2 s**, lasting **30–60 ms** (2–4 f), and only for crit-kills on elites, boss hits or the player taking a big hit. For "big moment" feel, use Dead Cells-style **1-frame freeze + 150–300 ms slow-mo at 0.3× time** [SRC pattern: 1 frame + "several tenths of a second"]. Boss deaths: 300–500 ms slow-mo (cf. davetech's 100–300 ms screen pause and the Smash 30 f cap [SRC]).

6. **Trauma-based shake, per Eiserloh.** `shake = trauma²` (try trauma³ for subtlety), Perlin noise on separate seeds, linear decay **~1.0–1.5 trauma/s** (cf. 0.8/s in the Godot recipe [SRC]), maxOffset **~1.5% of screen height** (≈16 px at 1080p), maxRoll **~1.5°** (2D: translational + rotational [SRC]). Trauma adds: normal kill **0**, elite kill **0.15–0.2**, player hit **0.2–0.3**, boss slam/ult **0.5** (Eiserloh's +0.2/+0.5 [SRC]). Clamp at 1 so mass kills become a steady rumble. Add a directional "camera kick" of 4–8 px toward big outgoing blasts (Nijman step 27 [SRC]). Ship a shake slider (0–100%).

7. **Biggest-hit-wins arbitration.** Collect events into a 66 ms (4-frame) window. Only the highest-priority event fires global effects (shake impulse, sleep, bass thump, announcer). Others fall back to their local-tier effects.

8. **Knockback as crowd control *and* feel.** Trash: 0.3–0.6 body-widths over 100–150 ms with ease-out, applied along the projectile/swing direction (D3's blade-direction impulse [SRC]). Heavy/crit: 1.5–3 body-widths, which can bowl into neighbours. Elites: 25% of that. Bosses: none, use flinch plus a stagger meter. Cap the total knockback velocity per enemy per second so stacked auto-weapons don't make the horde jitter.

9. **Death variety on a budget.** Each enemy type gets 1 normal death and 2–3 elemental/overkill deaths (fire char, frost shatter, crit gib: D3 [SRC]). Trigger overkill gibs when the final hit ≥ 2× remaining HP. Add Nijman's random-death-explosion idea at 10–33% for some enemy types [SRC 33%], but **cosmetic only, never damaging the player** (D4 lesson [SRC]).

10. **Permanence that scales.** Corpses persist 2–4 s then sink/fade (on-screen corpse cap ~150–250). Blood and scorch marks are stamped into a persistent ground render-texture that slowly fades over ~60–120 s. After a 30-minute run the arena should look like a battlefield (Nijman's three permanence steps [SRC]). Never let decals drop the contrast of enemy telegraphs.

11. **Damage numbers: aggregate, rank, cap.**
    - Merge hits on the same target within **150–250 ms** into one rising number that pops (scale 1.0→1.2→1.0) each time it grows.
    - Lifetime 0.6–0.9 s (cf. 0.5–1 s [SRC]).
    - Global cap **~30–40 live numbers**. When full, drop the smallest non-crit first.
    - Crits: larger (×1.4–1.6), warm colour, small shake of the digits. Kill-shots and elite damage get priority.
    - Offer three modes: All / Crits & big hits only / Off (VS ships a toggle [SRC]; "crits only" filter [SRC, secondary]).
    - Use compact formatting past 10k (12.3k) to fight D3-style inflation [EST].

12. **Audio does half the impact.** Sound coherence is a top-3 impact feature [SRC, Lin et al.]. Use voice limiting per sound type (e.g. max 6–8 simultaneous "flesh hit" voices), random pitch ±5–10%, 3–5 variants per sound (Lin et al. note random clip choice avoids fatigue [SRC]). Keep the low-frequency "bass" layer for per-event tier only (Nijman's "more bass" [SRC]; GoW's "low end… high frequency slash" [SRC]).

13. **Auto-weapon animation: short anticipation, heavy follow-through.** Wind-up ≤ 50–80 ms (well under the 100 ms responsiveness ceiling [SRC]). Snap to the strike pose (One Finger Death Punch [SRC]). Use a 1–2 frame smear/trail [SRC]. Give weapons a big follow-through arc and a 2–4 frame victim reaction (D3 "it's about the reaction" [SRC]).

14. **Resources come out of kills (push-forward).** As in Doom 2016 [SRC], tie XP/health drops to the kill juice, with gems bursting outward on the death frame. Occasional "glory" moments (elite execute, boss finisher) stay under ~300–500 ms so flow is never broken ("hundreds of milliseconds" [SRC]).

15. **Readability guardrails.** Keep enemy telegraphs and projectiles on a reserved high-contrast value band that no impact VFX may use. Cap per-frame additive particle overdraw. Test at the 25-minute mark with a maxed build. Diablo IV's VFX goal applies: huge effects "while keeping the game clear and readable, even when there are many players and monsters on the screen" [SRC, https://www.gamebanshee.com/x6uhx].

---

### Source list (primary first)
- Eiserloh GDC 2016 slides: http://www.mathforgameprogrammers.com/gdc2016/GDC2016_Eiserloh_Squirrel_JuicingYourCameras.pdf
- Catto, Diablo 3 ragdolls GDC 2012: https://box2d.org/files/ErinCatto_Ragdolls_GDC2012.pdf
- Swink ch. 1: http://mycours.es/gamedesign2014/files/2014/10/Game-Feel-Steve-Swink-chapter-1.pdf ; Swink 2007: https://www.gamedeveloper.com/design/game-feel-the-secret-ingredient
- Loudy & Campbell GDC 2018: https://gdcvault.com/play/1024940/Embracing-Push-Forward-Combat-in ; Bethesda glory kills: https://bethesda.net/en-AU/news/the-guts-and-gore-of-doom-glory-kills
- Sakurai: https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/ ; https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/
- SmashWiki hitlag: https://www.ssbwiki.com/Hitlag
- Lin et al. 2022: https://arxiv.org/abs/2208.06155 ; Pichlmair & Johansen survey: https://arxiv.org/pdf/2011.09201
- Nijman: https://www.youtube.com/watch?v=AJdEqssNZ-U ; https://www.gamedeveloper.com/design/vlambeer-co-founder-shares-advice-on-building-better-action-games ; list: https://rpgplayground.com/research-making-a-juicy-game/
- Jonasson & Purho: https://www.gamedeveloper.com/design/video-is-your-game-juicy-enough- ; Kelly counterpoint: https://gamedeveloper.com/design/video-indies-resist-the-urge-to-juice-it-or-lose-it-
- Dead Cells: https://80.lv/articles/interview-with-the-developers-of-dead-cells
- God of War: https://blog.playstation.com/?p=370399
- Monster Hunter Wilds: https://gamingbolt.com/monster-hunter-wilds-weapon-hitstops-will-be-closer-to-what-people-are-looking-forward-to/amp
- Diablo III BlizzCon 2013: https://blizzplanet.substack.com/p/blizzcon-2013-diablo-iii-gameplay-systems-crusader-panel-transcript ; D4 death effects: https://diablofilter.com/news/blizzard-on-death-effects ; D4 VFX: https://www.gamebanshee.com/x6uhx
- critpoints hitstop: https://critpoints.net/2017/05/17/hitstophitfreezehitlaghitpausehitshit/
- Vampire Survivors options: https://vampire.survivors.wiki/w/Options
- Secondary implementation guides: https://kidscancode.org/godot_recipes/3.x/2d/screen_shake/ ; https://uhiyama-lab.com/en/notes/unity/unity-game-feel-hit-feedback/ ; http://www.davetech.co.uk/gamedevscreenshake ; https://www.wayline.io/blog/unity-floating-combat-text
- Animation: https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation ; https://en.wikipedia.org/wiki/Smear_frame

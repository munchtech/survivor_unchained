# 05 — Sound and Touch: audio, haptics, input and movement feel for a procedural-audio dark-fantasy survivors-like / ARPG

Scope: what the shipped games and published research say about (a) layered impact sound, variation, voice management and mixing when hundreds of hits land each second, (b) rising-pitch reward ladders and loot stingers, (c) adaptive music, and (d) rumble, input latency, buffering, dodges, movement and camera. All sound in this project is synthesised at runtime, so every finding is turned into oscillator, noise, envelope and filter parameters in the final section.

**How to read the confidence labels.** **[S]** = the number comes from the cited source. **[E]** = my estimate or industry rule of thumb, not documented by the cited game. Where a widely repeated "fact" could not be confirmed from a primary source, it is labelled **unverified**.

---

## 1. Layered impact design

**Layering is how commercial ARPGs work, and the layer count is high.** Blizzard's Diablo III team told PCWorld that current tech allowed "up to 10-15 randomized sound layers" on a single action, specifically to avoid fatigue over long sessions. [S] Sound design supervisor Joseph Lawrence described the target feel: "when you click on something in Diablo III it sounds like you're actually physically hitting or breaking something with your mouse, and that feels good." https://www.pcworld.com/article/465972/scoring_sanctuary_the_sound_design_of_diablo_iii.html

**Material layers carry meaning.** On Diablo II, "the smack of a Fallen's club against a hero wearing leather armor sounds different than if that same club strikes a hero wearing chainmail." Jon Stone: "Little sonic layers could reinforce the reality of the objects in the world." The gore layer was watermelons wrapped in plastic, chosen for "the meaty yet hollow sound". The gem-drop "ding" was made by tapping wine glasses until the pitch was right. The design loop was summed up as "click, click, kill, click, click, kill, click—loot." https://www.gamedeveloper.com/audio/how-audio-design-enhances-diablo-2

**Diablo IV turned repetition management into systems.** Blizzard's Diablo IV quarterly update named three things: "Hero Skill and Foley SFX layering for repetitious gameplay", "Monster SFX voice limiting and Importance System", and "Voice/SFX/Music ducking to help manage a chaotic mix". The team also adds slight random variation so sounds "almost never play back exactly the same way twice". https://www.wowhead.com/news=378805/go-behind-the-scenes-with-the-art-of-sound-design-of-diablo-4 (via search summary), https://massivelyop.com/?p=357065. GDC session "Diablo IV Audio Systems Deep Dive: Living Audio": https://schedule.gdconf.com/session/diablo-iv-audio-systems-deep-dive-living-audio/899258

**The usual layer model (synthesis of common practice, [E]).**
- **Transient/click** (0–5 ms): a short noise burst or high-frequency click. It carries most of the localisation and "contact" information, and it is the layer that survives a dense mix.
- **Body** (5–80 ms): a pitched or band-passed thump that tells you the material (flesh, bone, metal, stone).
- **Tail/sweetener** (80–400 ms): debris, ring, reverb or a pitched shimmer for crits.
- **Sub thump** (40–80 Hz sine with a fast downward pitch sweep): used only on big events. Spending it on every hit muddies the mix and tires the listener.
- **Crunch**: saturation, waveshaping, bitcrush or sample-rate reduction on the transient and body. Doom's composer took this to an extreme. Mick Gordon's "DOOM instrument" fed a *pure sine wave* through four parallel chains of distortion pedals, bitcrushers, fuzz, tape echo, spring reverb and compressors. In his words, a sine is "our most pure representation of what sound can be", and the chains then "imprint" corruption on it. https://www.thumbsticks.com/mick-gordon-crafted-doom-soundtrack/, https://everythingisnoise.net/features/sound-test-doom-2016/ The approach suits procedural SFX well, because "sine + parallel distortion chains" is exactly what a runtime synth can afford.

**Kick-drum synthesis is the model for procedural impacts.** Kick generators start from a pure sine and shape it with a pitch envelope (attack and tonal drop) plus an amplitude envelope (body and decay). https://isotonikstudios.com/wp-content/uploads/rupture2-userguide.pdf. Retro SFX generators (sfxr/pyfxr, gb-synth) ship "hurt", "explosion", "coin" and "powerup" presets built from 4–5 waveforms plus noise and ADSR. https://pyfxr.readthedocs.io/en/stable/generating.html, https://hackage.haskell.org/package/gb-synth. Microsoft Research has shown modal synthesis of impact variations on consoles, which is the physically based route if metal or bone "ring" is needed. https://microsoft.com/en-us/research/?p=309038

## 2. Variation, voice limiting and horde audio

**Pitch randomisation.** The standard maths: one semitone = a 2^(1/12) ≈ 1.06 pitch multiplier, and 100 cents = 1 semitone. https://www.gamedeveloper.com/audio/the-power-of-pitch-shifting, https://www.oreilly.com/library/view/web-audio-api/9781449332679/ch04.html. Game Developer recommends random shifts so small that "the actual change to the pitch may not be noticeable". Forum practice for footsteps cites ±20 cents per step (https://adventurecreator.org/forum/discussion/9071/request-random-pitch-offset-on-footsteps). Common practice [E]:
- Footsteps and UI: ±20–50 cents.
- Weapon hits: ±1–2 semitones.
- Small "pop/splat" enemy deaths: ±2–3 semitones.

Randomising the transient and the tail *independently* "can drastically reduce the machine gun effect while still using just one sample" (https://www.kvraudio.com/forum/viewtopic.php?p=7232081). Round-robin means cycling through several variants in a fixed or shuffled order (https://steinberg.help/halion/v7/en/halion/topics/editing_programs_and_layers/sound_editor_variation_groups_section_r.html). With procedural synthesis, every trigger can be a fresh variant: randomise the seed, the filter cutoff and the decay.

**Per-event voice caps and stealing (FMOD's model) [S].**
- Max Instances is a per-event cap with a range of 1–64 or ∞.
- When the cap is hit, the stealing rule is one of: Oldest, Furthest, Quietest, Virtualize (the voice keeps playing silently until a slot frees) or None (new triggers are refused).

https://www.fmod.com/docs/2.03/studio/event-macro-controls-reference.html (FMOD also offers a per-event *cooldown*, a minimum retrigger interval, on the same panel.)

**Survivors-likes in practice.** A Cozy Space Survivors devlog solved "too loud when many of the same sound play" by keeping each played sound's path in a list for **0.03 s** and refusing duplicates. That is effectively **one instance per sound type per 30 fps frame**. [S] https://simonschreibt.itch.io/cozy-space-survivors/devlog/634575/update-61-sound-regulation. The general advice is the same: when many identical sounds would fire on one frame, play one. https://bugnet.io/blog/how-to-fix-overlapping-audio-and-sound-spam. FlatRedBall's engine has a built-in "don't play the same sound twice in one frame" option. https://docs.flatredball.com/flatredball/api/flatredball/audio/audiomanager/play. No primary dev post documents Vampire Survivors' or Brotato's exact caps (**unverified**). Vampire Survivors players describe late-game gem collection as "a certifiable symphony of sounds", which shows the gem sound is deliberately allowed to stack. https://www.thevibes.com/articles/lifestyles/53373/vampire-survivors-an-escalating-dopamine-rush-disguised-as-a-retro-game

**A better merge rule than "drop it" [E].** Merge same-frame duplicates into one voice whose gain rises with the log of the count:
- gain = base + 3 dB × log2(n), capped at +9 dB.
- Optionally widen the stereo spread or add a "crowd" noise layer.

The player then hears that 40 enemies died, not that one did.

## 3. Rising-pitch ladders, chains and combos

- **The principle.** "When several actions are chained together such as in a combo, successively increasing the pitch of the associated sound effect can help reinforce the length of the chain and increase satisfaction." The recommended step is **1 semitone per chain step**, a pitch multiplier of 1.06^N. [S] https://www.gamedeveloper.com/audio/the-power-of-pitch-shifting
- **Peggle.** Peg hits are tinkles "perfectly pitched to the serene melodies underneath" (Wikipedia summary, https://en.wikipedia.org/wiki/Peggle). In practice the notes climb a scale as the ball chains through pegs. "Extreme Fever" plus Beethoven's "Ode to Joy" began as a *placeholder*, and the team kept it because players responded to it. They then made the sounds "more airy" (an air cannon and a brief angelic chorus) so the effects sat inside the music. John Vechey: "When you hear that 9th it's just so gratifying." https://www.gamezebo.com/news/peggle-how-a-spark-started-a-fever/
- **Mario.** The coin is a two-note figure, B5 (988 Hz) then E6 (1319 Hz), with the second note held longer. That is a rising perfect fourth. https://themarysue.com/?p=153521. Stomp chains escalate in *score* (100, 200, 400, 500, 800, 1000, 2000, 4000, 5000, 8000, then 1-Ups), a ladder with a terminal reward. https://mariowiki.com/Point
- **Tetris Effect.** Moving and rotating pieces trigger sounds synced to the beat, so the player is "both player and conductor". Mizuguchi's team "cut the sound and synced them to each action". https://wccftech.com/interview-tetsuya-mizuguchi-synesthesia-tetris-effect-rez-lumines/amp/, https://www.gamerevolution.com/review/455063-tetris-effect-review-synesthetic-aesthetic
- **Balatro.** Numbers "tick up with escalating sound", and the score multiplier "will set on fire and start to burn hotter and hotter". LocalThunk on the core feeling: "the game is more fun when you set up your Rube Goldberg machine and watch it go". https://amp.kr-asia.com/how-balatro-became-2024s-indie-darling. A design write-up claims each scored card plays a rising note (C-D-E-F-G), multipliers add a "ka-ching" layer, and screen shake scales 2/4/8 px with score. https://blakecrosley.com/guides/design/balatro. **Unverified secondary source:** the exact notes and pixel values are not from the developer, and the game's source could not be checked from this environment. What is consistent across sources: each scoring step plays its own sound, the pitch climbs across the sequence, the flame and shake intensify with magnitude, and there is a final punctuation when the blind is beaten.
- **Survivors-likes.** The XP-gem pickup is the genre's ladder. A rising gem pitch that resets after a quiet period is common practice, but Vampire Survivors' and HoloCure's exact behaviour is **unverified**.

**Reset rule [E].** Reset the ladder after 0.6–1.0 s with no pickups, and clamp at about +12 semitones (one octave). After the clamp, either hold the top note or wrap with an octave-down plus an extra harmonic layer. Mapping steps to a pentatonic scale rather than chromatic semitones keeps long ladders musical against the score, which is the Peggle principle.

## 4. Kill and loot stingers

- **Diablo II/III.** The item-drop "fwip-fwip-fwip" whistle (the "flippy" sound) was kept from Diablo II in Diablo III for continuity, while the gold sound was redone. https://www.pcworld.com/article/465972/scoring_sanctuary_the_sound_design_of_diablo_iii.html, https://epicsound.com/2014/03/great-in-depth-feature-with-the-blizzard-game-audio-team. Diablo III legendaries drop with an orange light beam. A Greater Rift key patch removed the beam because it was a false positive. https://games.softpedia.com/blog/Next-Diablo-3-Patch-Removes-Legendary-Beam-from-Greater-Rift-Keys-458391.shtml. The lesson is that reserved rarity signals must stay rare.
- **Path of Exile loot filters** formalise rarity audio [S]:
  - `PlayAlertSound <Id 1–16> <Volume 0–300>`, default volume 50.
  - `PlayAlertSoundPositional`: the same, but placed at the item's 3D location.
  - `CustomAlertSound "file"`: several files play at random; volume 0–300, default 100.
  - `DisableDropSound`: mutes the standard drop sound.
  - `PlayEffect <Color> [Temp]`: light beams in 11 colours.
  - `MinimapIcon <0–2> <Color> <Shape>`.

  Players thus get about 16 distinct tones plus volume to sort loot by ear. https://www.pathofexile.com/item-filter/about
- **Vampire Survivors chests.** The treasure-chest opening is a full music jingle (six variants by Daniele Zandara, Filippo Vicarelli and William Davies, released on the OST). The jingle temporarily replaces the stage music and runs while coins and items spill out. https://vampire.survivors.wiki/w/Music, https://vip-develop.primagames.com/?p=74429

## 5. Mixing chaos: HDR, ducking, priority, readability

- **DICE's HDR audio** (GDC 2009, "How HDR Audio Makes Battlefield: Bad Company Go BOOM"):
  - Designers tag each sound with a real-world loudness in dB SPL across "the entire range of hearing".
  - A sliding window then maps the loudest current sounds into the living-room output range. The motto is "every sound is important, but not at the same time".
  - Sounds that fall below the bottom of the window are culled, which frees voices.

  https://www.frostbite.com/frostbite/news/how-hdr-audio-makes-battlefield-bad-company-go-boom, https://designingsound.org/2013/06/21/finding-your-way-with-high-dynamic-range-audio-in-wwise/ (Wwise's version: "loudness values should be seen as a measure of priority"; when the input exceeds the threshold, "the level of all sounds of the mixture drops by the same amount"; attack and release that are "too slow or too fast" cause pumping).
- **Diablo IV** explicitly ducks SFX, voice and music against each other and uses an "Importance System" for monster sounds (sources in section 1).
- **Doom 2016** fades the music *out* during glory kills and "snaps back in" afterwards, so the execution sounds get the stage. https://everythingisnoise.net/features/sound-test-doom-2016/ This is ducking used as dramaturgy.
- **Haptic and audio "peak reservation".** Housemarque set a middle-ground baseline so they could escalate for key moments (section 7). The same principle applies to the mix: keep small hits about 12 dB below the reserved big-event level [E].

## 6. Adaptive music

- **Hades (vertical layering plus randomised stems).**
  - Each area track is split into stems: "a drum stem, a base stem, and an everything else stem".
  - Drums engage in combat and drop out in exploration.
  - Stems are "selected programmatically at the start of each combat chamber" in semi-random combinations: sometimes only bass, sometimes bass and guitar, sometimes no instruments. Korb says this is to "keep things fresh and get some extra longevity out of the music."
  - FMOD advances sections at measure boundaries.
  - Boss music was often written "from the end and worked backwards".
  - Korb: "we definitely, deliberately try to have the music feel like it is scoring your playthrough".

  https://gameplay.co/hades-game-music-sound-design-darren-korb-supergiant-games/, https://www.lacedrecords.com/blogs/blog/how-rock-band-influenced-hades-soundtrack, https://www.wshu.org/culture/2020-12-04/darren-korbs-metal-inspired-soundtrack-for-hades
- **Doom 2016 (horizontal re-sequencing).** "Song sections were parsed out into much smaller parts so as to make it easy for the game's code to select the correct music tracks", so it is "nearly impossible to hear a song played the exact same way twice". Tempo was matched to gameplay footage, and the music was used as "reward and motivation". Gordon's GDC 2017 talk "DOOM: Behind the Music" covers the 9-string guitars, the giant synths and the interactive system. https://everythingisnoise.net/features/sound-test-doom-2016/, https://gdcvault.com/play/1024068/-DOOM-Behind-the
- **Diablo III music** used large orchestral and choir recordings (Abbey Road and others). GDC 2015 "Soundtracking Hell": https://www.gdcvault.com/play/1022258/Soundtracking-Hell-The-Music-of
- **Implication for a procedural game.** Vertical stems (pad / bass / drums / lead) driven by an intensity parameter, with changes quantised to the bar, are the cheapest robust approach and fit synthesis directly. Use horizontal re-sequencing only for boss phases.

## 7. Controller rumble and haptics

- **Xbox motors [S].**
  - Four motors. The left motor gives "rough, high-amplitude vibration"; the right gives "gentler, more subtle vibration". Each takes 0.0–1.0.
  - "Even at the maximum value, the left motor can't produce the high frequencies of the right motor".
  - The two impulse-trigger motors are identical and mechanically isolated, so they are felt independently.

  https://learn.microsoft.com/en-us/windows/uwp/gaming/gamepad-and-vibration. Mapping: **low = weight / damage taken / explosions; high = texture / rapid small hits / UI ticks.**
- **Nintendo HD Rumble.** The Joy-Con uses linear resonant actuators, similar to a loudspeaker voice coil.
  - Frequency range: about 41–1253 Hz.
  - The band that "really shakes the controller" is about 100–250 Hz.
  - SDL emulates classic dual rumble with strong = 141 Hz at amplitude ≤ 0.9 and weak = 182 Hz at ≤ 0.1.

  https://github.com/dekunukem/nintendo_switch_reverse_engineering/issues/11, https://git.axiodl.com/encounter/SDL/commit/fe2fe29049f2b2bc508edde9e98a254f721fa878 (search summary)
- **Returnal (DualSense).**
  - Rain uses "subtle raindrop haptic pulses that are procedurally synthesised at runtime".
  - Haptics are designed like audio, since the DualSense works "similar to that of a loudspeaker or headphones" (Harvey Scott).
  - The three pillars are Immersion, Communication and Power. Max intensity is *reserved*: a middle-ground baseline lets Killsight and big weapons spike.
  - Alt-fire: half-pull to aim, "feel the satisfying click", full pull to fire.

  https://blog.playstation.com/2021/05/13/how-housemarque-created-returnals-immersive-dualsense-controller-effects/
- **Fatigue and accessibility.** Constant rumble "can become background noise" (https://www.wayline.io/blog/haptic-feedback-less-is-more). Haptics can cause discomfort and pain for people with RSI or carpal tunnel, so they need an intensity slider and an off switch. https://gameaccessibilityguidelines.com/?p=3182. Academic typology: "A Typology of Rumble", DiGRA: https://dl.digra.org/index.php/dl/article/view/1069
- **For hordes [E].** Never rumble per kill. Use one short high-motor tick of 20–40 ms at about 0.15–0.25 for *the player's own crits or kill-streak milestones*, and send all per-kill feedback through audio and visuals. Use low-motor pulses (80–200 ms at 0.4–0.8) for damage taken, level-ups, elite or boss kills, and explosions. Sum all requests into a per-motor envelope with a ceiling of 0.8, and let the "max" tier through only for boss kills and death.

## 8. Input latency, buffering and forgiveness

- **Latency thresholds.**
  - Raaen and Eg (Westerdals/Simula, MMSys 2016) measured a motor-visual *discrimination threshold close to 200 ms*. Some people "can spot lags shorter than 50 ms, whereas others cannot notice delays that exceed 200 ms". Typical system floors are around 17–33 ms. https://mmsys2016.itec.aau.at/papers/MMSYS/a28-westerdals.pdf
  - Liu, Claypool et al. (2021) found that *local* latency hurts performance and QoE about **2x** more than equal network latency. Their test conditions were 0/25/50/75/100 ms, with effects already visible at 100 ms. https://web.cs.wpi.edu/~claypool/papers/csgo-net-local-21/paper.pdf
  - For exergames, which tolerate lag far better, the tipping point was about 400 ms. https://web.cs.wpi.edu/~claypool/papers/spaz-22
  - Claypool's broader line of work puts noticeable degradation in action games around 60 ms (search summary, https://web.cs.wpi.edu/~claypool/papers/csgo-net-22).
  - Practical target [E]: under 50 ms input-to-photon at 60 fps, which means at most 3 frames of pipeline. Never leave a hit's audio onset more than 1 frame (16.7 ms) behind its visual, and avoid mixer look-ahead limiters with long buffers.
- **Celeste source constants [S].**
  - Movement: `JumpGraceTime = 0.1f` (100 ms coyote time), `MaxRun = 90`, `RunAccel = 1000`, `RunReduce = 400` (px/s and px/s²).
  - Dash: `DashSpeed = 240`, `DashTime = 0.15f`, `DashCooldown = 0.2f`, `DashRefillCooldown = 0.1f`.
  - Jump: `VarJumpTime = 0.2f`, `WallSpeedRetentionTime = 0.06f`.

  https://raw.githubusercontent.com/NoelFB/Celeste/master/Source/Player/Player.cs. Maddy Thorson's "Celeste & Forgiveness" lists the systems: coyote time, jump buffering, half gravity at the jump peak, corner correction, wall-jump windows of 2 px (super wall-jump 5 px), and stamina refunds. "Everything is fudged a tiny bit in the player's favor." https://maddymakesgames.com/articles/celeste_and_forgiveness/
  - Celeste's MaxRun 90 with RunAccel 1000 means full speed in **0.09 s**, which is about 5 frames. Deceleration (RunReduce 400) applies only above max speed; stopping from normal running uses the same 1000 acceleration, so it takes about 0.09 s as well.
- **Generic buffer guidance.** Coyote time and jump buffer are commonly set at 0.10–0.15 s. https://bugnet.io/blog/coyote-time-and-input-buffering-explained, https://bugnet.io/blog/how-to-fix-platformer-jump-feels-unresponsive
- **Souls.** An attack or dodge pressed near the end of an animation executes immediately. Community measurements say DS1/Bloodborne buffers are short (about 0.3 s) and DS3's much longer. Over-long buffers cause unwanted queued rolls after stagger. https://steamcommunity.com/app/374320/discussions/0/357284131782825962. **Community-sourced, not developer-confirmed.**
- **Dodges in ARPGs.**
  - **Path of Exile 2** [S, wiki]: the roll moves **3.7 m**, has **no cooldown or cost**, and has i-frames only for "a few brief frames when the animation begins". It mainly dodges projectiles and non-AoE attacks, and can cancel almost any animation except another roll. Its speed scales with movement speed. https://sportskeeda.com/mmo/path-exile-2-poe2-dodge-roll-system-iframes, https://massivelyop.com/2023/07/28/exilecon-2023-path-of-exile-2-introduces-dodge-rolling-and-instant-weapon-skill-swapping/
  - **Diablo IV** evade: **1 charge, 5 s cooldown** at base; boots can add up to +3 charges. https://www.wepc.com/gaming/how-to-evade-in-diablo-4/, https://sportskeeda.com/mmo/how-get-evade-charges-diablo-4
  - **Hades**: Zagreus is "immune to all damage" while dashing. Attacking out of a dash gives a Dash-Strike, and casting or attacking mid-dash ends the immunity. Athena's boon extends the i-frames. https://hades.fandom.com/wiki/Unblockable, https://www.pcgamer.com/hades-guide-tips-and-tricks. No primary source gives exact frame or cooldown numbers (**unverified**). By feel, the dash is very short (about 0.15–0.2 s) and re-usable almost at once [E].
  - **Dead Cells**: generous i-frames, pushes the player through enemies, "ridiculously short cooldown". No published numbers. https://www.gamesradar.com/dead-cells-tips

## 9. Movement feel and camera

- **Vampire Survivors**: movement is instant start and stop at constant speed with no inertia (observation, [E]). Readability comes from the horde, not from the character.
- **Megabonk**: 3D, with "Source-engine" momentum. Sliding down slopes gains "massive speed", bunny-hopping preserves momentum, and turning at about 45° builds speed. Movement skill is a core pillar and the reason it stands out among survivors-likes. https://www.dtgre.com/2025/10/megabonk-advanced-movement-bunny-hop-sliding-guide.html
- **Takeaway for a top-down 2D hybrid [E].** Near-instant acceleration, like Celeste's 0.09 s to max speed. Slightly slower deceleration (0.06–0.10 s) to avoid a "stuck" stop. Turning at full speed should be instant, with no turn radius. Momentum should come only from dashes or skills, never from base walking.
- **Camera.** Itay Keren's "Scroll Back" (GDC 2015) catalogues four core techniques:
  - **Camera windows**: the camera stays still "until the character hits the edge".
  - **Position snapping**.
  - **Lerp smoothing**: `a + t*(b-a)` each frame. It can hide threats ahead of very fast characters.
  - **Forward focus**: Defender pushed the camera about 25% of the screen width ahead.

  For top-down games he cites position-averaging between actors and region anchors. https://www.gamedeveloper.com/design/scroll-back-the-theory-and-practice-of-cameras-in-side-scrollers, https://gdcvault.com/play/1022243/Scroll-Back-The-Theory-and. Squirrel Eiserloh's "Juicing Your Cameras With Math" (GDC 2016) covers smoothed motion types and camera shake. Its widely used recipe is a trauma value from 0 to 1, shake = trauma² or trauma³, Perlin noise rather than random jitter, linear trauma decay, and rotational shake preferred in 2D. https://gdcvault.com/play/1023557/Math-for-Game-Programmers-Juicing (the details of the recipe are from memory of the talk, [E]-level confidence).

---

## Implications: concrete starting parameters

Labels: **[S]** = directly from a cited source; **[S-derived]** = computed from a sourced number; **[E]** = estimate to tune in playtests.

### Sound

1. **Same-sound coalescing window: 33 ms (one 30 fps frame) per sound type** [S, Cozy Space Survivors]. Rather than discarding duplicates, merge them into one voice at +3 dB × log2(n), capped at +9 dB [E].
2. **Voice caps per category** [E, FMOD model S]:
   - Enemy-hit transients: 8.
   - Enemy deaths: 6.
   - XP pickup: 4, as a monophonic ladder voice plus 3 overlap voices.
   - Player weapon: 6.
   - Player-hurt, level-up, loot stinger and boss: 1–2 each, and these are never stolen.
   - Steal rule: Quietest for hordes, Oldest for weapons.
   - Global software voice budget: 48 [E].
3. **Per-type cooldowns** [E]:
   - Enemy hit: 15–25 ms.
   - Enemy death: 25–35 ms.
   - Player-hurt: 250 ms, matched to the i-frame window.
   - Low-HP heartbeat: no retrigger, as a loop.
4. **Pitch randomisation** [E, 2^(1/12) maths S]:
   - Small hits: ±1.5 semitones (±150 cents).
   - Deaths/splats: ±2.5 semitones.
   - UI and pickups: ±0 (the ladder supplies the movement).
   - Footsteps: ±30 cents.
   - Also randomise gain ±1.5 dB and filter cutoff ±15%.
5. **XP / combo ladder** [S for the 1 semitone step; rest E]:
   - +1 step per pickup on a major-pentatonic scale, starting around 880 Hz.
   - Clamp at 12 steps, then hold the top note and add an octave-up shimmer.
   - Reset 0.8 s after the last pickup.
   - Kill-streak ladder: the same scheme with a 1.5 s reset.
6. **Layer timing for impacts** [E]:
   - Transient 0–5 ms.
   - Body 5–80 ms.
   - Tail ≤ 300 ms for normal hits and ≤ 800 ms for crits and elite kills.
   - Sub thump (55 Hz → 35 Hz sweep, 120 ms) only on crits, explosions, elite or boss hits and player-hurt.
7. **Ducking (sidechain) amounts** [E, with the HDR principle S]:
   - Level-up, boss-spawn and legendary-drop stingers duck horde SFX by 8 dB with a 10 ms attack and 400 ms release, and duck music by 4 dB.
   - Player-hurt ducks horde SFX by 6 dB (5 ms attack / 250 ms release).
   - Use a simple HDR-style "loudest event sets the window" rule with a window of about 24 dB, culling anything below it.
8. **Hurt filter** [E]:
   - On damage, apply a 1-pole low-pass to the SFX bus (not the player's own hit sound): 18 kHz → 1.2 kHz in 20 ms, recovering over 350 ms.
   - Below 25% HP, hold a 3 kHz low-pass plus a 60 bpm heartbeat (Doom/Returnal convention).
9. **Loot rarity audio**, PoE-style [S for the concept and ranges]:
   - Common drops get no unique sound.
   - Each higher tier gets a distinct pitched bell or chord stinger, rising one interval per tier: fifth → octave → major chord → added 9th with a choir pad.
   - The top tier is reserved and rare, with a light beam plus a 1.2–2 s stinger.
   - Provide per-tier volume sliders (PoE exposes 0–300).
10. **Chest / level-up** [S for the Vampire Survivors jingle convention; timing E]:
    - Chest: a 2–4 s jingle that replaces the music, with music ducked by 12 dB, plus coin-ladder ticks.
    - Level-up: a 0.6–1.0 s rising arpeggio, with music ducked by 6 dB.
11. **Adaptive music** [S for Hades stems and bar quantisation, Doom fade-on-execution; rest E]:
    - Four synthesised stems: pad, bass, drums, lead/choir.
    - Intensity = smoothed (enemies on screen × damage dealt), with a 2 s rise and 6 s fall.
    - Stem thresholds: 0.15 bass, 0.4 drums, 0.75 lead.
    - Quantise changes to the bar.
    - Randomise which stems are present per wave, as Hades does.
    - Pull music down 6–10 dB for 0.5 s on boss-kill "execution" moments, then slam back.

### Touch and input

12. **Rumble vocabulary** [S for motor roles; values E]:
    - Light hit dealt: none.
    - Crit or 10-kill milestone: high motor 0.2 for 30 ms.
    - Damage taken: low 0.6 plus high 0.3 for 120 ms with exponential decay.
    - Level-up: low 0.4 for 80 ms, a 60 ms gap, then 0.5 for 80 ms.
    - Elite kill: low 0.7 for 150 ms.
    - Boss kill and death: low 1.0 for 400 ms.
    - Global ceiling 0.8 except for those last two events.
    - At most 1 non-damage rumble per 250 ms.
    - Ship an intensity slider and an off switch [S, accessibility].
13. **Latency budget** [S thresholds; E budget]: under 50 ms input-to-photon (at most 3 frames at 60 fps), audio onset within 1 frame of the visual hit, and audio buffer ≤ 512 samples at 48 kHz (10.7 ms).
14. **Input buffer**: hold attack/dodge/skill presses for 100–150 ms [S-derived from Celeste-style 0.08–0.15 s windows and the generic guidance], and execute them on the first legal frame. Do not exceed about 200 ms, because Souls-style long buffers cause unwanted queued actions [S, community].
15. **Dash/evade starting point** [S anchors; E blend]:
    - Speed about 2.7× run speed (Celeste: 240 vs 90).
    - Duration 0.15 s [S, Celeste DashTime].
    - I-frames for the full dash, plus 50 ms after it (Hades-like generosity).
    - Cooldown 0.2–0.4 s with 1 charge, or 2 charges on a 3 s recharge as a middle ground between PoE2 (no cooldown, 3.7 m) and Diablo IV (5 s, 1 charge).
    - Dash cancels attack recovery.
    - Allow a dash-strike within 150 ms of dash end.
16. **Movement curve** [S-derived from Celeste]:
    - Reach max speed in 0.08–0.10 s, i.e. accel = maxSpeed / 0.09 s.
    - Stop in 0.06–0.08 s.
    - Instant direction reversal: apply deceleration only toward zero when there is no input.
    - Thumbstick radial deadzone 0.1 [S, Microsoft sample], then rescale.
17. **Camera** [S for the techniques; values E]:
    - Exponential lerp with a frame-rate-independent factor: `1 - exp(-12·dt)`.
    - Look-ahead of 12–18% of screen height/width in the direction of movement, eased over 0.4 s. This is less than Defender's 25%, because threats come from all sides in survivors-likes.
    - A small dead window of about 2% of screen size.
    - Trauma shake: trauma 0–1, offset = maxOffset (8 px) × trauma², rotation ≤ 2° × trauma², Perlin noise at 20–30 Hz, decay 1.5/s.
    - Hits add 0.05, player-hurt 0.3, explosions 0.4, boss slam 0.6.
    - Shake strength is a player setting.

### How to do it with procedural synthesis (oscillators, noise, envelopes, filters)

18. **Generic impact voice** (each value randomised per trigger) [E]:
    - **Transient**: white noise → high-pass 2–4 kHz; amplitude envelope attack 0 ms / decay 4–8 ms, exponential.
    - **Body**: sine or triangle at 90–220 Hz (flesh) or 300–600 Hz (bone/wood), with a pitch envelope from ×2.5 down to ×1 over 25 ms; amplitude envelope attack 1 ms / decay 60–120 ms. Add band-passed noise (Q 2–4) at the same centre for "wet" flesh.
    - **Crunch**: tanh waveshaper with drive 2–6 on transient + body, *or* a bitcrusher at 8–10 bits and sample-rate reduction to 8–12 kHz on crits only. This is Mick Gordon's sine-into-distortion idea at miniature scale [S for the concept].
    - **Tail**: for metal, 2–3 inharmonic sine partials (ratios 1, 2.76, 5.4) with 200–600 ms decays (modal-synthesis-style ring); for gore, low-passed noise at 800 Hz decaying over 150 ms.
    - **Sub thump**: sine sweeping 60 → 35 Hz over 120 ms with an amplitude decay of 150 ms.
    - **Click guard**: a 1–2 ms fade on every voice end, and a DC-blocking high-pass at 20 Hz on the master.
19. **Pickups, ladder and stingers**:
    - **Gem tick**: two detuned sines (+7 cents) or a sine plus a 3rd harmonic at 0.3; attack 2 ms, decay 90 ms; pitch from the pentatonic ladder (item 5).
    - **Coin**: the Mario-style rising 4th, two notes about 60 ms + 200 ms apart, using square waves at 25% duty for brightness, through a low-pass at 6 kHz [S for the interval].
    - **Rarity stingers**: additive chords of sine + saw → low-pass 3 kHz, plus a reverb tail.
    - **Dark-fantasy colour**: minor or Phrygian chords and a low choir-like formant pad (saw through two band-passes at about 700 Hz and 1100 Hz).
    - **Musical stems**: from the same synth, with a step sequencer quantised to a bar clock that is shared with the ladder notes, so pickups land in key (Peggle/Tetris Effect principle [S]).
20. **Mixer and haptics from the same engine** [E, the Returnal precedent S]:
    - Implement buses: Horde, Player, Stingers, Music.
    - Each bus gets a gain smoother (5 ms) and a one-pole low-pass.
    - Ducking is a sidechain from the Stingers/Player envelopes into Horde/Music.
    - Use a master soft-clip limiter with no look-ahead (to keep latency down) rather than a brick-wall limiter with look-ahead.
    - Haptics: reuse the envelope generators. Each rumble event is an ADSR on "low" and "high" channels, summed and clamped per motor each frame. On LRA/DualSense hardware the same oscillators can drive the haptic stream directly at 100–250 Hz, the band the Switch research says is felt most strongly [S for the band].

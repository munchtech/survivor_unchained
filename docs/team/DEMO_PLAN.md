# The demo plan (3 November 2026)

**The goal:** a playable demo. Title, creation, the tutorial (the storybook intro and the prologue), the Waystation, queue into the arenas from the Wayfinder's table, fight, come back to town. Everything else waits.

**The owner, 2 November:** "I have been going through a lot of loops and circles and am struggling to feel like I'm making progress ... I keep getting lost in details that probably don't matter right now." And: things we build must be reusable, so the next use is cheaper.

## Phase 3 verdict (3 November, coordinator b6ad7e4e): it runs, it doesn't hook. The hook passes replace the beauty order

The owner played demo-rc1 start to finish (`DEMO_GATE.md` "Phase 3"). The loop is proven; the player isn't held: "A new player would probably not really want to play more." So `demo` is not tagged, and the "After the demo" order below (her at the cameras, the HUD's soul, the Warden at boss tier, ...) does not start: it is beauty, area by area, the same shape that produced a game with no one look. **The next tag is `demo-rc2`, earned when the owner plays again and wants another night.**

**Why it doesn't hook, in order of weight (the coordinator's read of the notes):**
1. **The fight isn't a fight.** One-shot enemies, no foe health, no danger, so dash and Flare are movement keys, bosses are the same blob and the arena is a big empty field. Seven of the notes share this cause. The harness measured the bot's win rate and the callings' spread (x1.25) and never whether a human sweats; the bot never does.
2. **No one look.** Painterly realism was picked (20 Oct) and reached the screen a third of the way, then went in by remakes one asset at a time, while she stayed realistic, the HUD went bronze, the storybook ink, and each VFX its own palette. Every area judged its own sheet against "AAA"; nothing judged a frame against "one game".
3. **Sound is tones.** Every effect is synthesized; no lead ever owned audio. Half of "satisfying" is sound, and it is the cheapest of the four.
4. **Seams.** The cuts out of cinematics, the Warden pan and walk-up, the wheelbarrow, the skill flash, the missing head: craft marks a player sums up as "clunky".
5. **Her arm**, now seen in play the whole time.

### The hook passes (the owner's next playtest is the exit of the set; three to five leads at once)

| Pass | Lead(s) | Scope | Exit |
|---|---|---|---|
| **H1 Combat teeth** | combat design (max: taste) + combat sim (sonnet: numbers) + arena layout (high) | Tier 1 for a human: foes take 2-4 auto-attacks, elites 8-12; a careless night ends under 50% life and a tier-1 death is possible (the harness gets a "human" bot that reacts late, and 1 in 4 careless nights falls); foe health pips under 70% and elite bars; every wave past minute 3 carries a telegraph that must be dashed (an expanding ring that slows at its edge and roots at its center, a line charge, a pull), and the Flare is designed as the save of a named wave shape; hover = priority target (click-to-move: Owner decides); each arena boss one silhouette, one color, one signature attack that must be dodged; the Deep Shaw sized to its crowd and given a board (lanes, a lamp to hold, chokepoints) so position is a decision. Keep the corpse pops and the skills the owner liked. | the owner plays one tier-1 night: "I was scared once and I had a plan" |
| **H2 One look** | art director (max, one session), then restyle leads (high, GPU) | Step 1, the lock: judge demo-rc1's twelve frames (title, SB00, C01, the Verge day, the Ford night, the Warden, the Waystation, the Lamps screen, the Deep Shaw night, the Pack-Mother, the result, the HUD over play) as one game, and write the look bible in one page: palette and value structure, surface treatment at one brush scale, light, line, and what is off-style in each frame in the player's order. No new style frames: the direction (painterly realism, colorful light) stands. Step 2: restyles, not remakes, in that order, each judged against the bible with the frame question "is this the same game as the other eleven?". Her forms never change; her surfaces take the same light ramp and painted treatment only if the owner says so (Owner decides). The HUD's soul, the Warden at boss tier and the painted remakes fold into this pass under the bible. | the owner sees the twelve frames before/after: "one game" |
| **H3 Sound** | audio lead (a new area; high) | A palette: her hits and kills, the corpse pop, the dash, each Flare, the lamps, UI, footsteps by ground, foe tells (H1's telegraphs each have a sound), the boss, ambience beds by zone and time, the result. Route: ElevenLabs sound generation on the owner's account (output owned, no credit) plus CC0 beds, or CC0 only (Owner decides); the synth stays for nothing a sample does better. Mixed with the music (`godot/src/Audio/Music.cs`). Judge: a listening sheet (ten moments, before/after), one max. | the owner plays a night with headphones: "it sounds like a game" |
| **H4 Seams** | experience (high) with cinematics (high) and a UI worker | One rule for every cinematic-to-play cut (the camera eases into the play camera over about a second, her pose carries across, the HUD fades in; `Prologue.cs` and the C0x cue data); the Warden intro pan; C03's walk-up (with Cinematics 12's list); C04's wheelbarrow; the three lamps readable (a three-mark count on his bar, the pylons spaced and lit); tier-1 nights at the story-night shape (Owner decides); the way out from the win as a banner with a sound plus the arrow; the skill ready cue; the inventory head (plus a check that the figure is whole). | a replay of the demo path: every cut passes a motion judge; the owner's next run has no "clunky" |
| **H5 Her arm, route D** | body (high) + Marionette | A new source arm (Meshy generator, Marionette fixer) that bends and hangs right at the game cameras, bare and in each kit; the owner sees the bare shape first (the 23 Oct gate). Animation 62's route A ships meanwhile. | a max whole-frame judge at the play camera and the Look: "casually badass" |

**Wave order:** H1 (CPU numbers and Godot shots), H3 (no GPU), H4 and H2 step 1 (frames only) start together. H2 step 2 and H5 (GPU) as slots free. After H1, H3 and H4 merge: build `demo-rc2`, the owner plays. Then H2's restyles against the bible, and the old order's rest (the NPC packages, Act 2) as game dev.

**Rough cost before the owner plays rc2:** H1 ~2.5M, H3 ~1M, H4 ~1M, H2 step 1 ~0.3M: about 5M. H2 step 2 and H5: 4-7M after.

### Owner decides (one line each; the default runs if there is no answer)
1. **Tag:** no `demo` tag now; `demo-rc2` after H1/H3/H4. Default: as written.
2. **Her surfaces in the one look:** her forms never change; do her skin, hair and cloth take the same painted light ramp and surface treatment as the world (recommended: yes, she is in every frame, and a realistic her against a painted world is the split the owner saw), or does "she stays realistic" (the 19 Oct rule) stand? Default: the rule stands.
3. **First nights:** tier-1 table nights at the story-night shape (10-14 min, the boss at about 10) and 30 min from tier 2 (recommended), or 30 min everywhere with the first softened? Default: tier 1 to 12 min.
4. **Click-to-move:** no (recommended: WASD plus hover priority target keeps her hands on the keys; click-to-move fights the auto-attack), or yes? Default: no.
5. **Sound route:** ElevenLabs sound generation on the owner's account plus CC0 beds (recommended: owned output, no credit), or CC0 libraries only? Default: CC0 only until the key is set.

## Why we loop

1. **Nobody gates the loop as a whole.** Every area judges its own sheet (a HUD crop, a hair style, one Flare), so each area polishes toward AAA in isolation while the demo, start to finish, has never been played and passed. The last end-to-end audit (`docs/EXPERIENCE_AUDIT.md`) is a month old.
2. **Fixed lists grow from judges' notes, not from the player's path.** A judge's "later list" becomes the next lead's fixed list. The fingers, the nape, the shelf of buffs: real marks, none of them between the player and the demo.
3. **Decision pages ask the owner to pick between details** (scale 0.85 or 1.0, inward curl or gap fill). That is where the loops feel like loops.

## The rule from now: one gate, the player's path

`docs/team/DEMO_GATE.md` is the only backlog until the demo ships. Each item is a step on the player's path, in one of three classes:
- **BROKEN:** the player can't continue (a crash, a stall, a dead control, a save that doesn't).
- **MISSING:** a step of the loop doesn't exist yet (no way to pick a tier at the table, no result that returns her).
- **CONFUSING:** a player who hasn't read our docs wouldn't know what to do next.

A polish mark (a thing that looks less than AAA but works) is not a gate item. It goes under "After the demo" with its area. A lead's fixed list is its items on the gate, and nothing else. Round cap 2 per gate item; what doesn't pass in two rounds gets the simplest version that works, or is cut from the demo.

## The loop, and what exists today

| Step | Exists | State |
|---|---|---|
| 1. Title, creation (4 callings, backgrounds, the Look) | yes | played many times |
| 2. The storybook lore intro SB00 (89 s, ink) | yes | judged; `live: false` in `godot/data/storybook/sb00.json`, waits on the owner |
| 3. The prologue: C01-C04, the Low Ford, the Verge, the teach callouts | yes | Cinematics 11 and Experience 10 merged; C01 ends with the drowning (storybook), C02/C03 the Ford-Warden (a placeholder model for the demo) |
| 4. The Waystation: NPCs, inn and save, smith, stash, shops | yes | NPC 18 town wiring merged; named NPC packages half done (Holloway, Brannoc; the other 11 later) |
| 5. The Lamps screen (the skill tree) in town | half | Lamps build 2 is building the real screen; the functional `--board` pages work |
| 6. The Wayfinder's table: queue into an arena | yes, mechanically | `Waystation.AtTable` returns her after an arena; the pick (which scar, which tier) has never been judged as a player's screen |
| 7. The night: ember scars at tiers 1-4, pacing, the four callings within x1.25 | yes | Hollow by Night and the Dig at grade ~3.5, Barrow and Ruts ~3; pacing and the charge director done |
| 8. The result, back to the table | yes | the story-night result's left column is empty (known) |

So the demo is not missing systems. It is missing a pass as a whole.

## The phases

**Phase 0 (now): finish what is open, once.** The three in-flight leads (UI 29, Classes 21, Lamps build 2) are each one judge and a merge from done. Finish them to DONE-ONCE: one judge round, merge, worktree removed. No "later lists" start. The Lamps screen ships functional and clean after one max judge; its beauty rounds come after the demo has been played (the owner's "whatever it takes" still stands, but after the loop passes).

**Phase 1 (now, in parallel): the demo gate.** One lead (Experience 11, "the demo gate") plays the whole loop as a first-time player: the autopilot where it can, frames at the player's pace, every screen the loop passes through, all four callings at creation, one calling (the Warden) through the night. It writes `DEMO_GATE.md`: the ranked BROKEN / MISSING / CONFUSING list, each item with its area, its evidence frame and the smallest fix that makes it pass. It also sorts every open "later list" in the handoffs into "on the gate" or "after the demo". About one session.

**Phase 2: the spine fixes.** Three or four leads at once, each on its gate items only: town flow (the table as a player's screen: pick a scar and a tier, see what the night is), arena art for the two scars the demo ships, the tutorial's words and beats (story: SB00 and C01-C04 only), UI for whatever the gate says is confusing. Each lead reports in "the app can now X" lines and leaves its tool in `tools/`.

**Phase 3: the owner plays.** One evening on a tagged demo build, start to finish, notes sorted onto the gate (not into area lists). One pass over them. Tag the demo.

**After the demo:** the AAA passes resume in this order, on what the player sees most: her face, body and motion at the game cameras; the HUD's soul; the Warden at boss tier; the Lamps screen's beauty rounds; the other three callings' identity; the named NPC packages; Act 2.

## Reusability rules (every lead, every brief)

- **New content is data on a shared system,** never a one-off: NPCs as Marionette packages; gear as smart armor parts; weapons by the grip spec; arenas from the kit and presets; cinematics as cue data; VFX as telegraph and shader presets; teach callouts from `Callout`.
- **Fix the system, not the instance.** A mark that would come back on the next asset of its kind gets a tool or a check, not a hand fix on this one.
- **Every report names the capability it leaves:** "the app can now X", with the tool's path. A fix with no reusable part says so.
- **One judge, on what varies.** Numbers and runners cover the rest.

## Scope decisions for the demo (the coordinator's; the owner overrides with a line)

- **Callings:** all four playable at creation. The Warden is the one with full identity (its four skills, their VFX, the Long Cut). The other three keep their current skills.
- **Arenas:** two scars at ship grade (Hollow by Night and the Dig); the rest exist but are not polished. The Wayfinder's atlas (the permanent maps) is not in the demo.
- **Story:** the tutorial's words only (SB00, C01-C04, the town's first lines). Act 2 and 3 untouched. "Shaky" story is fine beyond the tutorial: the demo never reaches it.
- **Animation, face, hair, outfits:** frozen at the merged state. Only BROKEN motion (clipping through a wall, a T-pose, a stuck state) goes on the gate. The braid is the default.
- **The male hero:** out (19 October stands).
- **The Ford-Warden:** the placeholder model ships in the demo's cinematics; the boss-tier remake resumes after.
- **Meshy, ChatGPT, GPU jobs:** only for a gate item.

## The order, in one line

Finish the three open MRs once; gate the loop; fix only the gate; the owner plays; tag; then beauty.

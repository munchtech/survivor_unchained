# The demo plan (3 November 2026)

**The goal:** a playable demo. Title, creation, the tutorial (the storybook intro and the prologue), the Waystation, queue into the arenas from the Wayfinder's table, fight, come back to town. Everything else waits.

**The owner, 2 November:** "I have been going through a lot of loops and circles and am struggling to feel like I'm making progress ... I keep getting lost in details that probably don't matter right now." And: things we build must be reusable, so the next use is cheaper.

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

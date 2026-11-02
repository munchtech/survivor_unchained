# Skill trees, Phase 2: the board for real (a decision page for the owner)

Classes 17, 2 November 2026. It follows CLASS_IDENTITY_AND_TALENTS.md §3.2-3.7 and §6.2, which you approved on 27 October ("Go with all 10 recommendations").

## Where we are
Phase 1 (the Warden, felt) is done, or will be when MR2 merges:
- calling access and the draft filter;
- the four Hands;
- skills in data;
- Wicks with the first 8 Turns;
- the Warden's four skills (Sunder, Groundbreaker, Rebuke, Watch Bell);
- the type pick at creation;
- six day slots;
- a plain board and Wick screen behind `--board`.

Today's board is still v1:
- 360 lamps, 72 of them skill lamps that v2 moves into the Wicks;
- 2 layouts;
- points from levels, story bosses and the atlas;
- no positions, so a screen can't draw it as a tree.

## What Phase 2 builds
1. **The v2 board as data: 574 lamps with positions.** The four hearths with Hand lamps, the eight roads with rites and links, bridges, six crossings, the Ford with *Unhoused*, the ten Old Roads, and 45 blue lamps. They are generated from `tools/classes/lamps_build.py` / `lamps_quarters.py`. The depth gates move to 4/8/16. The rules for rites, links and Hand lamps go in the sim.
2. **Points:** levels, story bosses, the atlas (30), and the relit lamp-posts. For the posts we build **Act 1's four now** (a small scene each); Acts 2-3 get theirs when those acts are built.
3. **Three saved layouts**, each a whole build (board, wicks, skills, Flare). Respec is free by day at any town lamp-post.
4. **Save v6:** a full refund of lamps, wicks laid on the suggested strands, and off-calling skills moved to the storeroom as tomes. Saves are expendable, so it's kept simple.
5. **The Lamps screen, the real one:** the board drawn over the live world, pad navigation along the roads, the wick panel, and the dimming and one-line rule (§3.6). This is a UI design brief at max, then UI art and the build by the UI lead. Classes keeps the functional pages working until it lands.
6. **Names:** about 290 new lamp names (574 less the 288 kept from v1), from the story writer.
7. **Acceptance (the harness):**
   - a full board at night within ×1.25 of an empty one, for every calling (the warden reads ×1.53 today on v1);
   - Act 1 within ±3% of "pre-Flare 11 Oct";
   - every type within ×1.35 of the median.

## Cost
Classes: 3 sessions (the data and the sim rules; points, layouts and save; the harness and balance).
UI: 1 max design brief, then 2-3 sessions.
Story: about half a session.
**About 6 sessions, about 1.8M tokens.** Little GPU: the screen's art only.

## My recommendation: yes, with two changes to the order
- **The screen starts on day 1, not after the data.** The first thing Classes lands is the positions and kinds for all 574 lamps (no balance yet), so UI's design brief can lay out the real tree straight away. The screen is what you'll feel as "the skill tree", so it shouldn't wait for the balance work.
- **The Warden's wave (Phase 3's first calling) starts as soon as Classes' three sessions are done**, while UI is still building the screen. That's her other 8 skills and their bespoke strands. "Get going on our skill trees" then means real new skills every week, not only a board.
- **Not now:** relit lamp-posts in Acts 2-3, new Flares (decided), and kindred and the Old Roads' new skills (Phases 4-5). Their lamps exist on the board from day 1 and dim with "carry a ... skill" until those skills land.

**One question for you:** yes to this order (the board data and the screen in parallel, then the Warden's wave)? Or would you rather have the Warden's wave first, and the board after?

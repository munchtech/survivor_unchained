# M5 zones and encounters, lead 1 (9 Nov, coordinator ad002ada): the Low Ford as the first ARPG zone

Area: M5 of `docs/design/ARPG.md` (PICKED by the owner 9 Nov; read its PICKED block, the one-page, the systems table §2, §5 the first hour, §7.3 world tiers, and the M5 row in §9). Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\zones-m5`, branch `zones-m5`. Handoff file `docs/handoff/experience.md` (your block on top; end **MR READY zones-m5@<sha>**). Role `su-lead-high`. Pipelines: P5 (world) and P6 (combat content) in `docs/team/PIPELINE.md`: data, one build, one check; nothing hand-fixed on an output.

**Standing:** `docs/handoff/lead_brief.md` whole (the junction rule before any git merge/reset; the delete rule; pictures at half size), OWNER_NOTES top four blocks, `docs/design/ARPG_DIRECTION.md`, `docs/design/SIEGES.md` §6 and §12 (the director as assault groups, three LODs: build nothing for it, leave the doors open).

**The job (the M5 row):** the Low Ford as the first ARPG zone, as data:
1. Packs with captains and champions with affixes drawn from the telegraph kit (`telegraphs.json`, `teeth.json`), placed from §5's beats; `DayStretch.cs`'s eight beats become every zone's encounter list (one data shape per zone, the Low Ford first).
2. Lamp-posts as checkpoints and waypoints; a lamp-post at every boss door; the act's dark posts off the road give a board point when relit, checkpoint posts give none.
3. `zone_resets.json` per zone; the day's 12-minute clock OFF in the Low Ford (time follows the story: call 9).
4. World tiers I-IV picked at a lamp-post with §7.3's multipliers.
5. Death: she rises at the last lamp-post with nothing lost, the boss heals (call 7).
6. The zone sim: a harness run that measures an hour (kills, drops, falls) with the H6 bots; the bots that PRESS are M3's, so run with today's bots and say so.
7. Count the Low Ford's packs against §5's first hour; if it does not fit its 260 m, write the ground it needs (meters, beats) as a line for L1/P5 with a cost, do not build ground yourself.

Coordinate through main: the skills lead (skills-p7) owns skills.json, Unions, the dash and the Warden's new skills; M3 (combat systems, after M1 merges) owns the press path, Resolve and the bots; you own zones, encounters, lamp-posts, resets, tiers, death and the zone sim. Touch `Enemies.cs`/the director only through data where you can; when you must change shared combat code, say which file to main first.

Check: the zone sim's numbers (an hour's kills, drops at ~40 gear an hour per §6, falls by bot, the first Legendary from the Ford-Warden), the suite green (`dotnet test` in godot/tests). Judge: one `su-lead-max` judge in the foreground on a 1:1 play-camera clip of the first 10 minutes ("would a Diablo player keep walking?"). Report shape: "P5/P6: the app can now X; the Low Ford cost Y; the next zone costs about Z." Est ~2M, 3 rounds. First report within a few turns: the list with states and an estimate. hand off at ~200k with HANDOFF READY.

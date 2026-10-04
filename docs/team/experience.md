# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `a33f58e68e89e3ccf`, branch
`worktree-agent-a33f58e68e89e3ccf`). The audit is `docs/EXPERIENCE_AUDIT.md` (draft one); its
evidence frames are in `docs/experience/`.

## Current state (2026-10-03, stopped at the owner's usage limit)

- **Merged:** the integration branch at `4ffa6ef` (with combat's newer long night) and the
  retired combat lead's branch. Tests green (484). Pushed.
- **Done:** `godot/logic/Play/Zones/ArenaPacing.cs`, wired into `ArenaRun`. The night now has
  a shape:
  - a sawtooth into 10, 20 and 28;
  - breathers after turns;
  - a herald's duel on a thinned field, then a flood;
  - the hush (28½–30);
  - no turn twice running;
  - a chest in every three turns from minute 8;
  - each people's own question at 6, 17 and 26 minutes, with a tell, led by a captain with a
    chest.

  Tests: `PacingTests`, and `ArenaTests.The_people_ask_their_own_question_with_a_tell_first`.
- **Measured** (64 runs, plain bot, before → after): win rate 94% → 94%, ember at 30:00 53 → 53,
  alive in the long push 202 → 225, in the hush 224 → 126.
- **Combat's side:** the danger doesn't rise with the numbers, so combat
  (`ac4ec5bbd2763a0df`) wired its charge director to `pacing.Building`, `Breather` and `Hush`
  (`e9e591d` on its branch).
- **Autopilot:** it opens the watch-post chest from the far side (it used to loop on the
  watchman's book).
- **Played and seen:** the title, creation, the prologue to the Waystation, every hub screen,
  the draft and the result, and an arena to minute 25 (tier 1, Risen). **Not yet seen:** the
  boss on screen, the endless phase, the Verge.

## Next steps, in order

1. **Finish playing:**
   - an arena through the boss into the long night (`play.py arena`, below);
   - boss bursts with `--minute 29.5 --give ...`;
   - the Verge by day and night.
2. **Frame times:** measure them clean, with nothing else on the GPU. Find out why the
   Waystation costs 23–26 ms with nothing fighting.
3. **Finish the audit:** add the boss and the long night, research links, and the briefs.
   Then send short briefs:
   - **UI** (`a5629aff0f215ea4a`):
     - one bark at a time;
     - the table showing what a map pays;
     - the result as the run's story;
     - pausing only in arena combat. This is the owner's decision; I can make the rule's
       change myself.
   - **Story** (`a7622ae77d19e31dc`): the town reacts to your nights. I record the facts:
     `arena.last.*`, killer, longest, people, won or lost.
   - **Combat:** choice that decides survival from tier 3. Today random and greedy drafting win
     equally at tiers 1–3.
4. **Build my own items, in order:**
   1. moments: chest sequence, evolution ceremony, boss death slow motion, ducking, XP ladder,
      multi-kill swell, dash buffer, rumble; the specs are in `docs/feel/SUGGESTIONS.md`;
   2. readability: camera close-then-far, whole-occluder fade, the dead darken and sink, real
      bone and skull gibs, no flat discs;
   3. onboarding: bank the prologue's character XP and pay it at dawn;
   4. the first minute of an arena: the first group visible at once.
5. **Escalate to the owner** (recommendations in the audit): a composed score; story nights at
   20 minutes; someone to own the arenas' art.

## Tools (scratchpad `experience/`)

- `play.py NAME -- [game args]`: runs the game from this worktree at 1920×1080 with a log in
  `logs/NAME.log`. For example: `--quick warden --sex female --zone arena --people dead --auto
  --log 30 --seconds 10 --every 30 --count 110`.
- `sheet.py OUT COLS WIDTH NAME FIRST LAST [STEP]`: a contact sheet of a frame run.
- `arc.py`, `compare.py`: the night's arc from balance sweeps (`godot/balance/out/exp/*.jsonl`).

## Decisions

- **Pacing reshapes the night and never re-prices it:** the average share is about 1. Danger is
  combat's: the charge director, new kinds, minibosses.
- **The people's own turns are set pieces built from existing kinds:** the timing and the tell
  are mine; what spawns in them is combat's, as kinds unlock.
- **A climax and then a hush, not one or the other:** the long push peaks at 28; the people
  draw back for 90 s while the sign burns.

## Notes for other areas

- **Combat:** `ArenaPacing` gives you `TargetShare`, `Breather`, `Flooding`, `Hush`, `Building`
  and `Next`; `heraldAt > 0` marks a duel. Keep minibosses out of the hush and the duel.
- **Everyone:** frame times measured while the GPU is shared mean nothing. Say so when you
  quote one.

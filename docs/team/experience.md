# Experience: the game as a player lives it

Status page for the gameplay experience director (agent `a33f58e68e89e3ccf`, branch
`worktree-agent-a33f58e68e89e3ccf`). The audit is `docs/EXPERIENCE_AUDIT.md` (in progress).

## Current state (2026-10-03)

- Merged the integration branch at `d2a2eab`; tests green (470).
- Playing: title, creation and the prologue on autopilot, frames and logs; a 63-run arena sweep
  (`godot/balance`, plain bot, greedy and random, all callings, tiers 1–2 at their level, table
  oaths, staying up to an hour past the win).
- Performance numbers are on hold: the shared GPU was at 100% (ComfyUI, the voice placeholders,
  other agents' game runs) while I played, so frame times then (30–110 ms) say nothing yet.

## Pacing by minute, for the combat lead's escalation schedule

Measured on the integration branch before combat's newest endless work. Plain bot (`godot/balance`
arena, 63 runs). "Dipped" is the share of runs whose lowest health in that stretch went under half.

| Minutes | What happens | Cards a minute | Horde alive | Dipped below ½ | Read |
|---|---|---|---|---|---|
| 0–2 | first great blessing, the draft flood | 6.2, 3.6 | 40–47 | 16% | a flood of choices, no threat |
| 2–10 | events every 60–85 s, in a fixed cycle of four | ~2.3 | 54–104 | 17% | **flat**: the same ring, champion, stampede, swarm |
| 10–15 | herald at 10 | ~1.7 | 104–130 | **28%** | the hardest stretch before the boss |
| 15–20 | great blessing at 15 | ~1.5 | 130–157 | **8%** | **dead**: the easiest stretch of the night |
| 20–25 | herald at 20 | ~1.4 | 157–186 | 19% | |
| 25–30 | the boss's sign at 28:00 | ~1.3 | 186–217 | **9%** | **falls away before the climax**: should be the night's crescendo |
| 30–35 | the boss | — | held at a share | 27% | |
| 35–45 | past the win | 1 | 250–330 | 62% | the danger arrives only after the win |

- The horde's size is a straight line (40 → 217), with no swells or lulls; kills a minute climb in
  step (190 → 1,600). Fodder die in 0.07–0.22 s all night: the melt is there.
- The first evolution comes at a median 13 minutes; four by the end; a finished build (every slot
  evolved) in only 10 of 63 runs.
- In the prologue the autopilot took no damage at all in the first two minutes (327 kills).

**What I want from the escalation schedule:** a sawtooth that rises into each landmark (8–10,
18–20, 27–30 the tensest pre-boss stretches) and releases after it; breathers after events; one
people's signature event per landmark; no event kind twice in a row; and the last three minutes
before the boss as the night's peak, not its second-easiest stretch.

## Next

1. Finish playing: a full arena with the autopilot, the boss, the endless phase, the hub, the
   Verge by day and by night; frame sequences of each.
2. Write `docs/EXPERIENCE_AUDIT.md` and the prioritised plan; send briefs to the leads.
3. Build my own items (feel and juice, pacing and set pieces, onboarding, the loop).

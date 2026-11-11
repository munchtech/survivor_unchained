# Local hit-stop mechanism

The single switch is `enabled` in `godot/data/content/hit_stop.json`. It ships **false**. Turning it on replaces WorldScene's legacy whole-fight hit-stop pulses with holds on the attacker and target. HitShake, camera updates, UI, audio, other actors, projectiles already in flight, and ground effects keep their clocks. Existing perfect-dodge, victory, and staged Flare clocks remain separate systems.

| Class | Shipped duration |
|---|---:|
| Trash hit | 0 ms |
| Heavy hit | 50 ms |
| Critical hit | 50 ms |
| Elite or boss kill | 90 ms |
| Finisher | 90 ms |

Kills take precedence over critical and heavy hits. Ordinary damage-over-time ticks and blocked hits do not hold actors; an elite kill still uses the kill class. Executions use the finisher class independently of whether the existing bark is shown. A summon holds itself and its victim, with no hold on the player. Enemy elite/boss blows use the heavy class.

Above 30 live hostile enemies on screen, durations are multiplied by 0.5. The view supplies the actual camera frustum. The headless zone sim uses the same policy with the data's player-centered screen footprint (18 m half-width, 14 m half-depth); this is an approximation for headless checks, not a replacement for camera judgment.

Each actor raises its remaining hold to the longer duration, never adds durations. The whole continuous hold, including later extensions, is limited to 150 ms. Parsing rejects a cap above that safety ceiling. Pending player contacts, chain deadlines, and enemy marked blows wait with their actor. Reused pool slots clear their hold; projectiles and marked blows check the caster's spawn identity.

## Verification

- Untouched baseline: 2211 passed, 0 failed, 11 skipped.
- Final full suite: 2240 passed, 0 failed, 11 skipped (29 new hit-stop cases), on the job's integration base `ede4bf910`.
- The OFF Low Ford report matches the untouched baseline, excluding the command's output filename: seed 1, tier II, human and deft; both through, 5.1 / 5.5 minutes, 0 falls. Kills, drops, levels, and all other report rows match too.
- Enabled Low Ford checks: both through; human 5.1 minutes, 152 kills, 0 falls; deft 6.2 minutes, 175 kills, 0 falls. These are completion checks, not balance or feel targets.
- The Godot C# project builds. No Godot run, art edit, capture, or feel tuning was performed.

Reproduce the full suite with `dotnet test -c Release` in `godot/tests`. `LocalHitStopTests` exercises the policy, cap, crowd boundary, max-only extensions, actor isolation, pending beats, recycled slots, and enabled Low Ford completion. ZoneSim accepts an optional policy instance so tests can enable the shipped data without changing the process-wide content or adding another feature flag.

Local run evidence is in the worktree's ignored `.shots/hitstop/` reports and `godot/tests/results/hitstop/` TRX files. The team still judges the enabled feel at the game camera after merge.

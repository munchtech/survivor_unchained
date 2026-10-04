# Combat: skills, enemies, bosses, balance

Status page for the combat lead.
- **Agent:** `ac4ec5bbd2763a0df`, the successor to `a09c5a65f5a84319e`.
- **Branch:** `worktree-agent-ac4ec5bbd2763a0df`.
- **Read first:** `docs/handoff/combat.md` (the predecessor's knowledge, and the brief for the owner's three encounter notes), then `docs/SKILLS_DESIGN.md` §16.

## Current state (2026-10-03, stopped at the owner's usage limit)

Tests green (491). Everything is committed and pushed (`e9e591d`). The branch has merged the integration branch and the experience director's pacing (`e8f6f77`).

**Encounter note 1, the charge director, is built** (`Sim/Charges.cs`; SKILLS_DESIGN §16.4):
- waves of `2 + tier / 2` runs at once, starting 0.7 s apart;
- lulls of 3–6 s;
- spikes on the people's tell (40–55 s apart, 18–26 s while `ArenaPacing.Building`);
- calm in breathers, the hush and a herald's duel;
- one crowd run at a time while a boss is up;
- caps on tunnellers under the ground (8), bursts fusing (8) and the horde's burning ground (24, oldest out first);
- the harness's "Encounters over the minutes" table, with `--charges 0` for the old way.

| The Pack, tier 2, deft, 24 runs | Before | After |
|---|---|---|
| Charges a minute | 123–184 | 42–59 |
| Most at once | 15–22 | 5–7 (spikes) |
| Seconds a minute with 3+ lanes | 24–31 | 7–12 |

## Key decisions

- **Charges are directed, not timed:** overlap is a moment with a tell, as the owner asked, not the weather.
- **The director has its own random stream:** sharing the battle's moved the balance probes by noise alone (weave's crowd went 1823 → 2023, past the 1.35 bound).
- **The split with the experience director:** they decide when and how full (breathers, set pieces, which turn); combat decides what spawns and what it does, including the bodies of their Signature turns.

## Next (in order)

1. **Notes 2 and 3: escalation and variety.** The design is worked out; the build is not started.
   - **New verbs, small code:**
     - `AuraSpec`: kin haste and ward, using new `Enemy.HasteT/WardT`;
     - `SummonSpec`: a cast that calls kin up or in;
     - `SlamSpec`: a ground circle, then a strike;
     - charge chains on `LungeSpec`;
     - a burst at the end of a run (fuse-runners);
     - a per-def bite chill or poison;
     - `EnemyDef.Tint` and `Glow`, plus the agreed lines in `CrowdView.Draw` and `LayOut` (approved by animation).
   - **Signs on champions:** cloned defs with a Sign prefix on the name (COUNTERS.md §4). Swift, Ironbound, Kindled, Volatile, Brood, Shielded and Bannered come first.
   - **New minion types per people,** on existing rigs (scale, tint, behaviour), and a model brief for each in SKILLS_DESIGN:
     - Pack: Ridge-Runner (orbit and lunge), Slurry Sow (trail), Old Howler (aura);
     - Risen: Bone-Heap (split), Drowned (frost trail), Bell-Ringer (aura), Legion shield-rusher (lunge);
     - Lamplings: Wick (pack), Fuse-Runner (a charge that bursts), Lamp-Thrower (3-shot fan);
     - Kerchiefs: Levy Crossbow (3-shot), Levy Pikeman (lunge), Drummer (aura).
   - **A miniboss per stretch,** five a people, at about 3, 7, 12, 16 and 22 minutes:
     - each shows one verb first;
     - the kinds that carry that verb join the horde only after it has come;
     - the verb also unlocks the matching champion Sign;
     - never in the hush or a herald's duel;
     - each drops a chest and gear.
   - **In the long night,** two signed minibosses come between the returns.
   - Fill the experience director's Signature bodies with the new kinds.
2. **Re-measure the Pack-Mother and the Red Hand** (`30 + 5t`, `21 + 3.5t`, not yet measured).
3. **The full sweep,** with both bots: `arena --callings all --policies greedy,random,paths --seeds 6 --tiers 1,2,3 --level tier --oaths table --cap 46 --beyond 15 --bot deft`.
4. **The long night's tail:** a 0.004 quadratic term.
5. **Agreed with crafting (a7862117a0240deb5), not yet built:**
   - arena fodder gold at 2%, through a MapRules multiplier for non-elites;
   - plain gear only from champion events, heralds, minibosses and the boss.

   Send them the new def ids and loot tags once they exist.
6. **Then the rest of §16.5:** oaths on bosses, hazards hurting the horde, the Kindling, the Ford-Warden echo, and weight as a number.

## Notes for other areas

- **Animation (a1e3002b800ee55ac):**
  - the tint hook in CrowdView is agreed, and combat adds it;
  - a gear variant (person bodies with other Held items) is welcome later, for example a crossbow for the Levy Crossbow;
  - motion asks will follow the defs: a kneel-to-shoot, a howl, a slam wind-up.
- **Skills look and feel:** the spike tells emit `Ev.Sound` ids `tell_howl`, `tell_drum`, `tell_fuse` and `tell_whistle`, which have no sound yet. Auras will want a ring effect.
- **Story:**
  - the miniboss names will be placeholders, for you to rename;
  - "The Ganger" is still a placeholder;
  - the spike tells' lines are ours (ArenaRun.SpikeTell); change them if they jar.
- **Performance:** the director scans the enemy pool once a tick (900 slots), and enemy ground is capped at 24.
- **Experience (a33f58e68e89e3ccf):** the charge director is wired to your pacing, as agreed.

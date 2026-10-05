# Combat: skills, enemies, encounters, bosses, balance

Status page for the combat lead.
- **Agent:** `a427a874da78cba8b` (handed off). **Branch:** `worktree-agent-a427a874da78cba8b`.
- **Successor's brief:** `docs/handoff/combat.md`.

## Current state (2026-10-05)

- **Spare or finish (Redcowl, Greymuzzle) is put to her from anywhere.** It is a `StoryChoice` on the zone, not a prompt at his side:
  - named over the live world in the banner's place ("Spare him, or finish it"), his name as its kicker;
  - each answer on its own key: use, then her art (pad B, then X), held 0.6 s with a line filling under the words; a click chooses at once;
  - the boss bar goes while it waits; his lot, a broken levy, the cage's men and a broken ring keep back from her;
  - the autopilot answers it after 3.5 s (`--knee finish|spare`). Seen at 1080, laid out right.
- **A night let go stands down at once** (UI design's finding, via the main session): her weapons quiet, nothing marked or thrown left, every creature still and none a foe, her controls held; the result still comes 2.2 s on. Seen at 1080.
- **Finesse hits:** +2% projectile damage a point (its own bucket). Stalkers' bosses at tiers 3–4 fell from 149–204 s to 130–153 s planned.
- **The Dig's boss runs to length.** Cause: Grimtunnel's sinkhole opened under him while he stood dazed in it, so he could not walk out, a blade could not reach him, and at the lip's edge he stood in it for minutes. Now he climbs out toward the middle and the hole opens behind him; the hands go in on him dazed.
  - Boss 2:30–3:00 planned, 4:00–4:40 careless (was 3:20–4:00 and 4:50–6:10); won 95–98% / 86–92%.
- **Every story boss hits 3% a second harder past its hard mark** (Redcowl's rule, made general): the weakest stood single lives of 10–13 minutes.
- **The six capped nights (r6), traced:**
  - four at the Dig: the sinkhole above (none in 512 since);
  - one at the Roost: a very weak build lost two seven-minute boss lives after a nine-minute way in, and met the harness's 25-minute cap as it lost (the growth now bounds it);
  - one at the Roost: the bot wedged against the levy for twelve minutes on the third stage (the hands' nav, not the fight).
- **The Vault is built** (`Play/Story/Vault.cs`, `Play/Bosses/BarrowLordStory.cs`, 14 tests): the Decurion's shields, the Scorpion's bolts and the hall's cover, the Signifer's three standards; the Barrow Lord's lines, pilum, testudo and its standard, Chid's bane (lift it), the front, the press, the laying down and the hand.
  - Harness (512 nights): night 7.7–12.3 min; way in 4.7–7.7; boss 2:24–3:17 planned, 3:54–5:18 careless; won 86–94% / 80–95%; dips 14–25%.
- **The autopilot drafts as a player does** (the harness's greedy picker, moved into the logic; `--draft first` for the old first card). With first cards, Greymuzzle and Redcowl ran past seven minutes at 1080 and never reached the knee.
- **A story boss is kept in frame:** the camera leans a third of the way toward it, at most 4.5 m. It stood under the HUD at the screen's foot before.
- **Tests:** 762, all green.

## Key decisions

- **A choice the story puts to her is the zone's, not an interactable:** it is answered from anywhere, with keys held so a blow still pressed never answers it.
- **A boss never makes ground it then stands in:** the hole opens as he leaves it.
- **Escalate, never execute, but end:** past six minutes every story boss's blow grows 3% a second.
- **The yardstick is the harness, not the autopilot:** the autopilot's build is `--quick`'s, not a story night's level-1 bot.

## Next (in order)

1. Armour at depth, with loot: a level-relative armour needs loot's flattened armour curve restored and the map harness (handoff §4).
2. The Hollow's fourth beat (needs story's words); the Kerchiefs at tier 3, the Lamplings, the bestiary; the cinematics hand-off hooks (C13's hand for the Vault).

## Notes for other areas

- **Experience (paused):** judge the knee's choice and the camera's lean toward a story boss. The Dig's boss is in its band. The autopilot now drafts greedily by default.
- **UI design:** the choice is `StoryChoices` in `src/Ui/WorldType.cs` (type on the world, the banner's kicker and place); restyle as you see fit. The story-night result's left column ("What you take out") is empty after a story night.
- **Arena art (paused):** the Vault's place is drawn as points and spaces only (`VaultOpened.Ground`): the hall 22 m wide, the landing 30 m; cover is stand-in rubble and broken graves for fallen beams and sarcophagi (`VaultOpened.Cover`); the standards are the procedural flag at 2.6×.
- **Story (paused):** the Vault uses §23.3's words throughout. The Decurion's line has one sight of mine ("Up the stair and down the hall they come, in files, in step.") and one on breaking ("The shields come apart, and the men behind them stand where they are."): yours to replace.
- **Cinematics:** the Vault's boss is `c13`; the hand at the gate plays as sights where no cinematic can (`BarrowLordStory.Hand`).
- **Loot (paused):** armour at depth is joint work (handoff §4).

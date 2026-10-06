"""WRITING_PASS.md: facts, the fortune, the routes, the audit, the risks."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
P = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/docs/WRITING_PASS.md'
s = open(P, encoding='utf-8').read()

def rep(old, new):
    global s
    if old not in s:
        raise SystemExit(f'not found: {old[:80]!r}')
    s = s.replace(old, new, 1)

rep('''| **`be.crates`** | `redcowl`, `harlan`; at the chapter's close `burned`, `watch` or `dig` (rule `crates.settle`); `sunk` (C5) | `redcowl.crates_keep`, `harlan.crates`, rule | Redcowl, Harlan, fortune, folk, concerns, Act 2 beats 1, 5, 7 |''',
    '''| **`be.crates`** | `redcowl`, `harlan`; `sunk` (C5); `burned` the moment the Roost's powder goes up (unless Harlan's men have them); `dig` when the Kerchiefs sell the cargo on (rule `caravan.box_moved`); at the chapter's close, if still unset, `burned`, `watch` or `dig` (rule `crates.settle`) | `redcowl.crates_keep`, `harlan.crates`, `Verge.cs`, rules | Redcowl, Harlan, fortune, folk, concerns, Standings, `Verge.cs`, Act 2 beats 1, 5, 7 |
| **`crates.charge_taken`** | true | C5 "Take a charge" | C5 |
| **`corran.home`** | true | rule `holloway.corran` (the dawn after Holloway hears) | Holloway's concern, the town's talk |''')

rep('''9. `f_door`: a variant with the name after the accusation; then "Close the
   book on this chapter." (action `fortune`).''',
    '''9. `f_door`: a variant with the name after the accusation; then "Close the
   book on this chapter." (action `fortune`).

The accusation is made once (`once: accuse`), and once the book is closed
("Your chapter is written") the fortune is not read again: her mark and the
tracker's "A Note in Violet Ink" go with it. `f_ember` has two more readings:
crates gone down the south road with the cargo (`be.crates` `dig` and
`caravan.cargo` `with_kerchiefs`), and crates that burned with the Roost
whether or not anyone was in its cages.''')

rep('''### Wrong order, all hidden rather than greyed''',
    '''### Every road, end to end (`RouteTests.cs`)

Played through the game's own pieces (conversations, the Waystation, the
Verge and its night fights, nights slept, a save and a load at the turns that
matter, asserting nothing is lost and the next step is the same):

- **The Beast Problem.** B1 in order (the scholar reads the water, Snib moves
  the pump); B2 the Dig first, a dead wolf as the reason to care, Pell's
  charge the same day, the pump blown; B6 Redcowl's charge; B7 the cure sold
  to Pell; B5 the hunter kneels and the Pack runs; B8 left alone; the wood
  emptied (slaughtered); the Dig boiling over by night; the Pack hunted in
  its Hollow by night.
- **The Missing Caravan.** K1 in order (wreck, ruts, the Roost bought, the
  cages, the box home); K2 the Roost first; K3 and K10 the cages first by a
  bluff and the box sold to Rav's friend, the arrest and the fine; K5 the
  ledger burgled on the first night, read, then proved; K12 where Pell
  sleeps; K16 too late, the box all that comes home; the box kept three days
  and the boy still paid for; the Roost raided by night, the camp empty, the
  crates sunk; the sealed door opened by night.
- **The Lamps.** Every piece, Nell told the truth, the accusation and the
  chapter's page.
- **The whole chapter** from the gate to the fortune, with a save at every
  turn, to the crates the chapter's close sends to the Dig.

### Wrong order, all hidden rather than greyed''')

rep('''## 14. Risks and open questions''',
    '''## 15. The implementation audit

Act 1 played as a QA lead would, every road and the wrong turns between
them. Each finding is fixed and proved by a play-through in `AuditTests.cs`
(or a route in `RouteTests.cs`); content fixes were made in the data, in the
writers' words where a line was needed (VOICES.md).

**Rewards taken twice, choices that outlive their sense**

- Redcowl read Pell's ledger ("Give me that.") and handed it back: shown
  again, Pell's fate could be told twice, both ways; shown to Holloway, it
  put "in irons before dark" a man already gone. He keeps it now.
- Redcowl's hundred ("I'll throw in the teamsters... Open them yourself; my
  lads won't stop you") did not free the cages: his men still refused. It
  does now (`redcowl.releases`). The teamsters' keep (fifty) could be paid
  twice; he sold the strongbox to someone already carrying it.
- Rav slid Jessop's key across the table every time he was asked.
- Snib could be asked to move, shut off, be bribed over, or be fought for a
  pump already moved or broken, paying the bribe again; and said "Pump is
  still pumping" of a broken one. He now says what became of it (two lines
  in his voice) and is asked nothing about it.
- Vonnra's accusation could be made, and paid for in feeling, every time the
  fortune was read; her toll ledger was paid for every time it was asked
  about.
- Tam warmed to being believed every time he told it (twenty trust a time).
- Quest things could be sold over Rav's and Vonnra's counters: the strongbox
  sold there set nothing (no fence, no "wanted", the story never knew), the
  ledger or the sigil's fragment for a copper. Now nothing the story still
  needs goes over a counter or is dropped; each quest item says, in
  `items.json` ("needed"), how long it is needed, after which it is a
  keepsake that can be left behind.

**Gates and breadcrumbs**

- Greymuzzle met before the Roost was known showed "You would need somewhere
  to lead them", and never offered it again. He does now, to anyone who has
  not broken their word to him.
- The arrest's way out ("You should be asking who paid the Kerchiefs")
  exposed Pell with a ledger that proved nothing yet; it needs `LEDGER_CTX`.
- Harlan's question mark stayed up for good once Jory was home, and was up
  for a box he no longer wanted; Holloway's was up for a ledger he had
  already read and could not use. Marks now mean something to bring them:
  Harlan for the box, Jory's news and the Roost; Holloway while the ledger
  can be read or proves something; Vonnra until the book is closed.
- Leads were written into stories already over ("Harlan blames the wolves"
  after Jory was home, the bounty after the cure), from Rook, Holloway,
  Maeca, Wenna, Tam and Harlan. Harlan asked after a nephew who was home and
  offered a reward for him; Maeca met after the cure lectured about the
  bounty before she thanked anyone.
- The town spoke of Corran brought home, and of Aldo buried, the day before
  either happened.
- Sold to Pell, the Dig's step said "Stop the slurry" while Pell was doing
  it: it says to give him two days, or beat him to it.
- Journal notices were split at the first colon in a line, so a line with
  one put half of itself in capitals as a title: the quest's name is the
  title now.

**What the world remembers**

- Cages opened were open only until the survivor left the Verge, or loaded a
  save: on the next visit they were shut again, and once all three were
  open Jory could be let out of his cage a second time. They are the zone's
  memory now, and stay open.
- A Roost whose Redcowl fell first and his crew after was never "cleared".
- The Roost's powder burned "the prisoners still in their cages" after they
  had starved, and left the crates "still waiting in a ravine"; the cargo
  sold down the south road left them there too, to be told to Harlan. Now
  only the living burn, and the crates go with the fire or with the cargo.
- The strongbox's chest and the crates stayed on screen after they were
  taken or sunk.

**Lint.** `StoryLint.Every_fact_written_is_read_or_is_a_seed_for_a_later_act`:
every fact Act 1 writes is read, or is one of the named seeds of section 9.

**Checked in the real game** (1920x1080, saves from `QaSaves.cs`, `--open
talk:ID>words>+` to reach a line deep in a conversation): the journal and
the tracker mid-caravan, Harlan's longest greeting, Brannoc and Nell, the
fortune's crates and last pages with the accusation, the chapter's page,
Pell's shelf with the charge, the Roost before and after the crates. Text
fits everywhere; the tracker wraps its longer steps to two lines.

## 14. Risks and open questions''')

rep('''- **C6 changes the save** (`ShopState.Offered`): migrate old saves with an
  empty list.''',
    '''- **C6 changed the save** (`ShopState.Offered`, save version 2): done, and
  a version 1 save is migrated (section 11, C6).
- **A strongbox kept three days** is Harlan's no more (`caravan.cargo`
  `kept`): it can still be fenced through Rav, but not given back. That is
  the writers' clock, kept as written; a late return would be a new choice.''')

open(P, 'w', encoding='utf-8').write(s)
print('ok')

"""WRITING_PASS.md: the code items marked done, each with the test that proves it."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
P = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/docs/WRITING_PASS.md'
s = open(P, encoding='utf-8').read()

def rep(old, new, count=1):
    global s
    if old not in s:
        raise SystemExit(f'not found: {old[:80]!r}')
    s = s.replace(old, new, count)

rep('''- **[CODE, to do]**: needs the implementer. Section 11 has each one: what,
  where, the exact data, and the test scenarios that prove it.''',
'''- **[CODE, done]**: built in code by the implementation pass, with the test
  that plays it. Section 11 has each one: what, where, the exact data, the
  choices made where the spec left room, and the test.
- **[CODE, to do]**: needs an implementer (none are left in Act 1).''')

rep('''Tests: `cd godot/tests && dotnet test` (238 pass). The pass's own scenarios
are `godot/tests/BreadcrumbTests.cs`; four older tests in `QuestTests.cs`
were given the context the new gates require (section 13).''',
'''Tests: `cd godot/tests && dotnet test` (288 pass). The pass's own scenarios
are `godot/tests/BreadcrumbTests.cs` (the code items' scenarios at its end);
four older tests in `QuestTests.cs` were given the context the new gates
require (section 13). The implementation pass added `RouteTests.cs` (every
road of Act 1 played end to end through the game's own conversations, the
Waystation, the Verge and its night fights, with a save and a load at the
turns that matter), `AuditTests.cs` (one play-through per bug the audit
found, section 15), the `Route` harness they share (`Route.cs`) and
`QaSaves.cs` (saves at the moments worth looking at in the real game).''')

rep('''[DATA, done] (dialogue gates and reactions); [CODE, to do] C1, C2 (the strongbox's journal line, ledger objectives) |''',
    '''[DATA, done] (dialogue gates and reactions); [CODE, done] C1, C2 (the strongbox's journal line, ledger objectives) |''')
rep('''Pell sells the charge only to someone who knows the Dig | [DATA, done]; [CODE, to do] C6 |''',
    '''Pell sells the charge only to someone who knows the Dig | [DATA, done]; [CODE, done] C6 |''')
rep('''Harlan pays for the boy even after you sold his box | [DATA, done]; [CODE, to do] C5 (the crates in an empty camp) |''',
    '''Harlan pays for the boy even after you sold his box | [DATA, done]; [CODE, done] C5 (the crates in an empty camp) |''')
rep('''the accusation at the fortune | [DATA, done]; [CODE, to do] C3 (the prologue writes the first line) |''',
    '''the accusation at the fortune | [DATA, done]; [CODE, done] C3 (the prologue writes the first line) |''')
rep('''| The chapter's end page | The lamps as an open thread; the new beats | [CODE, to do] C4 |''',
    '''| The chapter's end page | The lamps as an open thread; the new beats | [CODE, done] C4 |
| Implementation audit | Rewards taken once, choices that outlive their sense hidden, honest marks, no stale leads, what the world remembers across a save (section 15) | [CODE, done] |''')

rep('''| Pell's blasting ember on his shelf | Pell's shop, once `root_cause` or `clue.blasting_ember` | the item | [DATA, done]; restock timing is C6 |''',
    '''| Pell's blasting ember on his shelf | Pell's shop, once `root_cause` or `clue.blasting_ember` | the item, the same day | [DATA, done]; [CODE, done] C6 |''')
rep('''| Picking up the strongbox | the Roost | journal line and tracker step | [CODE, to do] C1 |
| The ledger's next step | tracker | by context | [CODE, to do] C2 |''',
    '''| Picking up the strongbox | the Roost | `strongbox_found`, quest active; tracker step | [CODE, done] C1 |
| The ledger's next step | tracker; the wreck gold on the map | by context | [CODE, done] C2 |
| Vonnra's note under the door | tracker, from `chapter.ready` until the book is closed | "A Note in Violet Ink" | [CODE, done] (section 15) |''')
rep('''| The crates in an empty camp | Redcowl gone | Harlan can still be told; take a charge or sink them | [CODE, to do] C5 |''',
    '''| The crates in an empty camp | Redcowl gone | Harlan can still be told; take a charge or sink them | [CODE, done] C5 |''')
rep('''Pending (with code): `strongbox_found` (C1), `crates_sunk` (C5).''',
    '''Added with code: **`strongbox_found`** (C1): "The Coyle strongbox, out of the
Kerchiefs' camp: heavy, locked, the Coyle Company seal on the lid. There is a
Coyle Trading Post in the Waystation."; **`crates_sunk`** (C5): "You rolled
the six crates marked "B.E." into the ravine's stream, one at a time, and
listened to each one not go off."''')
rep('''`lore.warden` | [DATA, done] for the three; [CODE, to do] C3 for the prologue itself |''',
    '''`lore.warden` | [DATA, done] for the three; [CODE, done] C3 for the prologue itself |''')

rep('''- **B9. Pell's charge waits for the knowledge** (to write, C6).''',
    '''- **B9. Pell's charge waits for the knowledge** (C6; `BreadcrumbTests.B9_Pells_charge_is_on_the_shelf_as_soon_as_the_survivor_knows_the_Dig`,
  `An_older_save_counts_what_its_shelf_already_holds_as_rolled`; played in `RouteTests.B2_...`).''')
rep('''- **K5b. The ledger's tracker** (to write, C2).''',
    '''- **K5b. The ledger's tracker** (C2; `BreadcrumbTests.K5b_the_ledgers_step_follows_what_the_survivor_knows`).''')
rep('''- **K14. The crates in an empty camp** (to write, C5).''',
    '''- **K14. The crates in an empty camp** (C5; `BreadcrumbTests.K14_the_crates_in_an_empty_camp_can_be_broken_into_or_sunk`,
  `AuditTests.What_the_story_carries_off_is_gone_from_the_Roost`).''')
rep('''- **L1. The book opens the mystery** (to write, C3).''',
    '''- **L1. The book opens the mystery** (C3; `BreadcrumbTests.L1_the_dead_watchmans_book_opens_the_lamps`).''')
rep('''- **E2. The chapter page** (to write, C4).''',
    '''- **E2. The chapter page** (C4; `BreadcrumbTests.E2_the_chapters_page_reads_back_the_crates_Jory_and_the_accusation`).''')
rep('''- **K4. The strongbox first.** Auto (greeting):
  `BreadcrumbTests.A_strongbox_carried_in_cold_is_met_with_the_seal_and_the_boy`.
  To write (C1):''',
    '''- **K4. The strongbox first.** Auto (greeting):
  `BreadcrumbTests.A_strongbox_carried_in_cold_is_met_with_the_seal_and_the_boy`;
  C1: `BreadcrumbTests.K4_a_strongbox_taken_before_anyone_asked_says_whose_it_is_and_where_it_goes`.''')
open(P, 'w', encoding='utf-8').write(s)
print('ok')

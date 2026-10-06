"""WRITING_PASS.md section 11: each code item's status, choices and test."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
P = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/docs/WRITING_PASS.md'
s = open(P, encoding='utf-8').read()

def rep(old, new):
    global s
    if old not in s:
        raise SystemExit(f'not found: {old[:80]!r}')
    s = s.replace(old, new, 1)

rep('''### C1. The strongbox, found, says whose it is and where to take it
''', '''### C1. The strongbox, found, says whose it is and where to take it [CODE, done]
''')
rep('''  once the survivors are settled).
- **Tests.** K4.
''', '''  once the survivors are settled).
- **Tests.** K4.
- **Done.** As specified. Also: a caravan settled at the cages while Harlan
  has not yet heard that Jory is alive keeps one step on the tracker, "Tell
  Harlan Coyle that Jory is alive", until he has (returning the box first and
  freeing the cages after resolves the quest at once, and the hundred for the
  boy was then nowhere on screen). `QuestTests.Say_how_long_the_cages_will_hold...`
  asserts it.
''')
rep('''### C2. The ledger's next step follows what the survivor knows
''', '''### C2. The ledger's next step follows what the survivor knows [CODE, done]
''')
rep('''- **Tests.** K5b.

### C3''', '''- **Tests.** K5b.
- **Done.** `H` has `Any(...)`; the two contexts are `KnowsKerchiefs` and
  `KnowsTheNight` in `Objectives.cs`, read exactly as `CTX_KERCHIEF` and
  `CTX_COYLE`. The tracker shows at most three steps, so with Harlan not yet
  met his "offering a reward" line (which points at the same man) may push
  "Ask Harlan about the crates" off the bottom: deliberate.

### C3''')
rep('''### C3. The dead watchman's book opens the lamps
''', '''### C3. The dead watchman's book opens the lamps [CODE, done]
''')
rep('''- **Tests.** L1.

### C4''', '''- **Tests.** L1.
- **Done.** As specified. Because the lamps now open on the Low Ford road,
  before anyone in town has asked the survivor for anything, the journal
  lists the troubles first and the mysteries after (`Book.cs`), so it opens
  on the Beast Problem, not on the lamps.

### C4''')
rep('''### C4. The chapter's page
''', '''### C4. The chapter's page [CODE, done]
''')
rep('''- **Tests.** E2.

### C5''', '''- **Tests.** E2.
- **Done.** As specified, and `crates_sunk` (C5) is a caravan beat too. A
  Pell taken from his bed by Redcowl no longer also reads "Pell Varrow fled
  the Waystation in the night." (his `pell_given` line says what happened).

### C5''')
rep('''### C5. The crates in an empty Roost
''', '''### C5. The crates in an empty Roost [CODE, done]
''')
rep('''- **Tests.** K14.

### C6''', '''- **Tests.** K14.
- **Done, with three choices.** (1) Both interactables need
  `clue.blasting_ember` as well: "Take a charge" and "Sink them" give away
  what B.E. is, and a survivor who never learned it sees six crates of
  somebody's salt (the manifest and Harlan's "be" are the breadcrumb). (2)
  While any of the Roost's crew stands within 16 m of the cargo, both are
  refused ("Too many eyes. Deal with them first"), as the cages are. (3) What
  is taken leaves the scene: the strongbox's chest when it is carried off,
  and the crates (and their colliders) once sunk, fetched by Harlan's men,
  sold on with the cargo, burned or taken by the Watch, now and on every
  visit after (`IZoneLook.HideProps`). A bluffed Roost empties at once
  (Redcowl and his crew leave the camp the moment the bluff lands), so
  nobody is left to call the survivor a thief or to watch the crates.

### C6''')
rep('''### C6. A shop line that becomes true is on the shelf when you next look
''', '''### C6. A shop line that becomes true is on the shelf when you next look [CODE, done]
''')
rep('''- **Tests.** B9.

### C7''', '''- **Tests.** B9.
- **Done.** `ShopState.Offered` holds "index:item" keys (an item may have
  two lines in one shop: Harlan's draughts). A conditional line counts as
  offered once it has been rolled this restock, whether or not its chance
  came up, so reopening a shop never re-rolls a chance. Saves are version 2;
  a version 1 save counts the conditional lines whose item is already on the
  shelf as rolled (`An_older_save_counts_what_its_shelf_already_holds_as_rolled`).

### C7''')
rep('''### C7. Where you stand with the Kerchiefs (optional)
''', '''### C7. Where you stand with the Kerchiefs (optional) [CODE, done]
''')
rep('''- **Tests.** One line in an existing standings test.
''', '''- **Tests.** One line in an existing standings test.
- **Done.** `BreadcrumbTests.C7_the_Kerchiefs_tolerate_whoever_kept_the_crates_from_the_Dig`.
  The reason replaces the bargain's only where the Kerchiefs already
  tolerate the survivor (telling Redcowl about the crates is not itself a
  pass).
''')
open(P, 'w', encoding='utf-8').write(s)
print('ok')

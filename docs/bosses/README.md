# Boss fights: research, audit and designs

How survivors-likes and ARPGs build their bosses, what ours do today, and
eight arena bosses, a midpoint, two endless shapes and three day bosses
designed for Survivor Unchained. Written for the main development session
to read and judge; nothing under `godot/` was changed. It builds on
`docs/feel/` (whose S-11, the boss as the run's peak and end, covers the
ceremony of the arrival and the kill) and does not repeat it.

## Reading order

1. **`README.md`** (this file): the top ten and the decisions.
2. **`AUDIT.md`**: what our bosses do today, read from the code and
   measured. Start here if you want the problem in one page: the arena
   boss is the herald again with more health, and lives about twenty
   seconds.
3. **`SURVIVORS_BOSSES.md`**: the main designs. §0 is the contract every
   arena boss keeps (phases as gates, the budget, telegraphs, enrages,
   banes, stagger, oaths); then the Pack-Mother, the Barrow Lord, Grimtunnel,
   the Red Hand, the Kiln Warden, the Silver Penitent, the Thing in the Barn
   and the Centurion; the Kindling at fifteen minutes; Echoes and the Dawn
   after the win.
4. **`ARPG_BOSSES.md`**: three day bosses (the Slurry Engine, Keegan at first
   light, the Keeper of the Silver Cages).
5. **`IMPLEMENTATION.md`**: what each design needs from the code, sized,
   and an order to build in.
6. **`MECHANICS.md`**: the catalogue: ten families of boss mechanics with
   how they work, why they are fun, how they fail, readability and
   scaling, and a one-page checklist for any new boss.
7. **`RESEARCH.md`**: the game-by-game teardown (Halls of Torment, Vampire
   Survivors, a dozen survivors-likes, Diablo, Path of Exile, Last Epoch and
   other ARPGs, Risk of Rain 2, Hades, Gungeon, Isaac and others), with its
   ten findings at the top.
8. **`notes/`**: the eleven research strands in full (about 80,000 words,
   every claim with its URL, each strand adversarially fact-checked at its
   end).
9. **`probe/`**: the measuring program behind `AUDIT.md` §4. From the repo
   root, with the .NET 8 SDK:

       dotnet run --project docs/bosses/probe -c Release -- 0.25,0.5,1,2,4,10 1,2,4

## What we found, in four lines

- **Our arena boss is not a boss.** It is the people's champion (the same
  creature as the heralds at 10 and 20 for three peoples of four) with more
  health, fourteen random escorts and one verb.
- **Measured, it lives a median of 16–20 seconds** for any build that
  reaches it, lands no blow in half the fights, and is outlived by the
  herald at twenty in two wins out of three; against a weak build,
  Grimtunnel can be kited for ever.
- **The prologue's Ford-Warden is the good model**: a ward fed by lamps, a
  charge you steer into them, a channel you break or pay for, a bar that
  shows it all.
- **The genre's lesson**: players hate HP sponges and attacks they cannot
  see, and love a boss that turns the game into a learnable dance on a
  cleared stage, then pays out big.

## The top ten recommendations

In order of return for the work.

1. **Fix the climax's basics in a day** (`IMPLEMENTATION.md` §4, step 1). The boss
   drops the run's best chest (today it drops none); heralds stop playing
   the boss music; the boss arrives on camera from a bearing the player has
   heard, with its own escort; `Cone` telegraphs draw as cones.
2. **Govern the fight's length before adding moves** (`SURVIVORS_BOSSES.md`
   §0.5–0.7). Phases end at a health mark or a time ceiling, never before a
   floor; overkill becomes a loud **Break** and a better chest rather than a
   skipped phase; thresholds crossed together queue. Boss health × (12 + 2 ×
   tier) on the boss's own body. Target: 90–120 s at par, 45–60 s for an
   absurd build, an enrage for a weak one.
3. **Give every boss a soft and a hard enrage** (§0.10): a known move turned
   up at 3:00, its signature on a loop at 5:00. Halls of Torment's lesson:
   escalate, never execute.
4. **Port the Ford-Warden into the new framework first** (`IMPLEMENTATION.md`
   §4, step 3) as the Warden's echo at the Wayfinder's table. It proves the
   framework on code that already works.
5. **Grimtunnel next** (`SURVIVORS_BOSSES.md` §3): burrowing exists, pits and
   lamp parts are small, and he ends "back down the hole" as the story
   needs. It also ends the probe's only stalemate.
6. **A telegraph language with four rules and a sound each** (`MECHANICS.md`
   §2): amber a blow, violet bad ground, pale blue stand here, grey this will
   be solid; each with its own edge pattern; boss telegraphs drawn above the
   survivor's effects; the survivor's effects dimmed while a boss lives.
7. **The Kindling at fifteen minutes** (§9): a heart and the boss's
   lieutenant, previewing one of its moves; break the heart in time and the
   great blessing is drawn from four. A fight where the run already wants a
   peak, and the boss's first verse before its exam.
8. **Stagger and banes** (§0.13, §0.15): crowd control fills a stagger bar
   instead of being refused; each boss has a bane learned by day (Maeca's
   fed fires, Chid's standard, Grimtunnel's own lamp). The day half arms the
   night.
9. **The Dawn as the end of every arena** (§11): the bible's own rule (the
   ember drains at dawn) as the endless hour's hard cap, a line of daylight
   crossing the arena from 55:00.
10. **The Barrow Lord, the Red Hand and the Pack-Mother** (§1, §2, §4), with
    formations (N5) serving the first two and the Legion later; then the
    Slurry Engine by day; then Act 2 and 3's bosses as their content lands,
    the Silver Penitent last.

## Decisions for the owner

1. **How long should the half hour's fight be?** Recommended 90–120 s at
   par, held by floors and ceilings, with the surplus shown as a Break.
   The alternative is to keep it short and make it a ceremony only (as
   Vampire Survivors' Reaper is a curtain); the research says players want
   a fight (`RESEARCH.md` §0, §6).
2. **Clear the horde for the boss, or thin it?** Recommended: clear a circle
   round its entrance and hold the rest at 40% while it lives, with the
   boss commanding what remains (§0.4). Clearing everything (HoloCure,
   Greater Rifts) reads best; keeping some keeps it a survivors fight.
3. **When a boss takes ember (the Silver Ink, the Dawn, the Centurion's
   toll), do the cards go too?** Recommended: no. The bar and the level step
   back; the build stays. Taking cards punishes the build players love,
   which is the Mithrix lesson (`MECHANICS.md` §8).
4. **How does the endless hour end?** Recommended: **the Dawn** at 60:00,
   the world's own rule. Alternatives: a Vigil hunter from 45:00 (a
   Reaper in the story's clothes), or no end (Halls of Torment's Vault,
   which "starts breaking" at about 95 minutes).
5. **Grimtunnel never dies in an arena.** The bible keeps him for Act 3; the
   designs end his fights with him driven back down. Confirm, or let table
   arenas kill a "Grimtunnel" that is not him.
6. **Keegan's duel at first light, or by night?** The bible says a night
   duel. Recommended: first light, by her own handbook's rule, which keeps it
   a day fight without ember (`ARPG_BOSSES.md` §2). Otherwise a small
   no-horde arena with the survivor's ember.
7. **New story outcomes from fights.** The designs add a few: Greymuzzle let
   go when the stream is clean (a new `beasts.outcome`), the crates blown in
   the Roost fight, Edric lost if the Keeper escapes, the pump broken or
   blown by how the Slurry Engine ends. Each is a branch for the writing to
   carry; accept, trim or refuse each.
8. **Banes shown or secret?** Recommended: learned by day and recorded in
   the bestiary once seen, never hidden for good. Halls of Torment keeps its
   hexes secret and players enjoy finding them, but our banes are story
   knowledge and should feel earned, not wiki'd.
9. **Build the Silver Penitent?** It is the best "your own tools" boss and
   the most expensive (an enemy that collects ember and fires the
   survivor's weapons). Recommended: yes, last, behind a flag.
10. **Oaths on bosses** (§0.12): each oath changes the boss as it changes
    the horde. Confirm the table, or keep bosses oath-blind and let the
    horde carry the oath.

## Confidence

- The code reading is direct, with file and line references; the probe's
  numbers come from a bot with no gear that drafts blindly, so absolute
  survival is noisy, but the boss's lifetime held for all four callings.
- The research cites a source for every claim in `notes/`. Some wikis and
  Reddit could not be fetched; those claims are marked "(secondary)". Each
  strand was fact-checked by a second agent; its corrections are at the
  end of each notes file and were applied here.
- Every number in the designs is a starting point for the balance lab, not
  a tuned value.

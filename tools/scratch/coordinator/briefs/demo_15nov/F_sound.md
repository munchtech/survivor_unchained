# Lane F: the den's sound, from the owner's own files (brief, 16 Nov 2026, coordinator #14 on Fable; #15 spawns it)

Read `tools/scratch/coordinator/briefs/wave1_15nov.md` "## Common" first (read "#13" as the coordinator who spawned you). Suggested type `su-lead-sonnet` (wiring with measurable acceptance; nobody but the owner can listen), `Context budget: 250k`, own worktree from integration, branch `demo-sound`. State file: a new TOP block in `docs/handoff/sound.md` (create the page if there is none), current from your first commit. It is not a judged lane: the gate is the owner's ear in a den run.

## The owner (word for word)
- 16 Nov 2026: "please give me a list of sounds needed for this demo (abilities, monsters and their abilities, whatever) so I can do something on my own while you work on things"
- 16 Nov 2026: "I put a bunch in that folder, all are elevenlabs no attribution needed"
Standing: sound sits at the visual bar; nothing that needs a credit.

## What the owner made
`C:\Users\munch\Desktop\survivorsunchained_inputs\sounds_demo\` (56 wav, 68 MB; `PROVENANCE.txt` there). By name:
- Den: `Ambience Loop`, `Green pits loop`, `pack at a distance`; music `Music den exploration track`, `Music den boss fight`, `Music boss falls`.
- Longtooth Wolf: `wolf notice1-2`, `wolf lunge1-2`, `wolf hurtyelp 1`, `wolf death1` (no bite).
- Blight-Sick Wolf: `blight wolf notice1-3`, `bite 1`, `bite2`, `lunge1-2`, `hurtyelp1`, `death1`.
- Thicket Tusker: `snort1`, `grunt1`, `charge`, `death`.
- The Pack-Mother's Yearling: `notice1`, `bite1-2`, `lunge1-2`, `hurtyelp1`, `death1`.
- The Pack-Mother: `arrival howl`, `the drive`, `hamstring`, `moon-howl`, `phase change`, `the call that brings wolves`, `death`.
- Her: `swing grunt1-4`, `leap1-4`, `landing1-3`, `dodge1-2`, `perfect`, `Stance1-2`, `low-health-heartbeat`.
NOT supplied (keep today's sound, or reuse a near take, and list them for the owner at the end): a common wolf's bite, the tusker's hooves and hurt, bones underfoot, her death, loot pickups, plate equip (helm, body, boots), "set complete", interface hover and click, the skill tree's cues, the moon-howl broken off by fire.

## How sound works here (found 15-16 Nov; verify before you lean on it)
- The bank: `godot/art/sound/<family>_<n>.wav` (144 families) and `godot/art/sound/sounds.json`; events in `godot/data/content/sounds.json` ("buses", "ducks", "materials", "events": each event has a bus and layers of take, gain, pitch range). 114 events are banked today; an event with no banked takes plays a made (synth) recipe.
- Every id the code can ask for, with the method that asks: `godot/data/content/sounds_ids.txt` (hand-written from `godot/src/Audio/Sfx*.cs`). Free-form ids go through `SoundHooks.Play` and `Sfx.Cue`.
- Beds exist as `bed.arena`, `bed.lowford`, `bed.title`, `bed.verge.day`, `bed.waystation`: the den has none. There is NO music anywhere (no folder, no event): find out whether a music bus and a player exist before you design one; keep it the simplest thing that loops, crossfades into the boss track when the Pack-Mother's fight starts, and plays the sting when she falls.
- No creature has a voice today: only hits and kills by material (`hit.hide`, `kill.hide`), the attack warnings (`telegraph.<tell>.windup|land`), and one generic howl take. The den's foes: `wolf`, `wolf_blighted`, `boar`, `lt_pack`, `boss_pack` (`godot/logic/Content/Enemies.cs` lines 222-236, 474, 536); the Pack-Mother's moves by name in `godot/logic/Play/Bosses/ArenaBosses.cs` (Drive, Hamstring, Howl, lunge, shake, the last ring of wolves, phases).

## The fixed list, in order
1. **Ingest, by a script** (`tools/sound/demo_ingest.py`, re-runnable; no hand edits on outputs): from the owner's folder to bank families with the bank's naming; trim leading silence, fade the tail, convert to the bank's format and rate, level each family to the loudness of its nearest banked neighbour (measure, write the table). Loops (`Ambience Loop`, `Green pits loop`, the two music tracks): find or make a seamless join and prove it by measurement at the seam. Provenance rows in `docs/team/provenance.md`, a row in `docs/team/PIPELINE.md`.
2. **The den's bed and the pits:** `bed.den` under the whole run; the pits' loop placed in the world at each lit pit, falling off with distance; `pack at a distance` now and then before the first fight and never during one.
3. **Music:** exploration track from the den's entrance, the boss track from the Pack-Mother's arrival, the sting on her death, then quiet. Ducks under the unlock cards and big hits as the existing "ducks" do for beds.
4. **Creature voices, as events with hooks:** per foe kind `voice.<kind>.notice`, `.bite`, `.lunge`, `.hurt`, `.death` (whichever exist), fired from the sim's own moments (first sight, a strike's start, a hit taken above a threshold, death). Limits so a pack does not become noise: at most N voices at once, a per-kind cooldown, nearest first (pick the numbers by a 5-wolf pack fight's log, write them down). The yearling and the Pack-Mother use their own files; the common wolf's missing bite borrows the blight wolf's, pitched.
5. **The Pack-Mother:** arrival howl on her entrance (with `stinger.boss`, not on top of it: decide by loudness which leads), the Drive's bark at its wind-up, Hamstring, the moon-howl, the phase change, the call for the last ring, her death (with `kill.boss`).
6. **Her:** effort grunts on Sunder and the heavy swings (not on every light hit: a chance and a cooldown), the leap shout and the landing exhale on Heroic Leap, dodge and perfect dodge, stance on and off, the heartbeat under low health (the id `heartbeat` exists and is made today).
7. **Proof without ears:** a den bot run with the sound log on, a table of every new event with how often it fired and its peak level; no clipping on the master bus in the boss fight; the suite green. Then a short list for the owner: what to listen for, in order, in one den run, and the not-supplied list above.

## The gate
The owner plays one den run and listens. Before that: the suite in `godot/tests` (`python ../../tools/quiet.py -- dotnet test`), the tables of step 7. Never `git add -A` (generated `.uid` and `.import` files stay untracked; new sound `.import` files follow whatever the bank's existing files do: check `git ls-files godot/art/sound | head`). Report: result first, branch@sha, suite, the event table's path, the owner's listen list.

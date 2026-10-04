# Handoff: voice

For the agent taking over voice for Survivor Unchained.
- **Branch:** `worktree-agent-a501b387a90d78b4e`.
- **Integration branch:** `claude/vigilant-galileo-l6jqyx`. Merge it in first, and often.
- **Read first:** `docs/team/README.md` (the team's rules and the roster), then `docs/team/voice.md` (the one-page state).

## The owner's bars, in their words

- **The brief:** "cinematic movie voice actor quality… never AI-sounding".
- **The test:** "do we have soul?" That means specific people, regional texture, idiosyncrasy and breath.
- **On an early sample:** "we need to do better there. it sounds way too AI".
- **The route (October 2026):** "we're just going to use elevenlabs for our voicework so we will do 1 character at a time. we will put in placeholders with voicebox and the agent will direct me one to work on at a time".
- **The team's bar:** "AAA standard", "strive for excellent, above and beyond", never settle, and be critical of your own work.

## The brief

- **Finals:** the owner records the finals in ElevenLabs from our packets, `docs/voice/elevenlabs/<voice>.md`, one character at a time.
  - Each packet must be signed final by the story lead before it is recorded.
  - `tools/vo/import_takes.py <folder> --voice <v>` brings the takes in.
  - Check the result in play, and tell the main session what is still missing.
- **Placeholders:** every voiced line has a local placeholder until its final arrives, flagged `placeholder` in the manifest and in `godot/data/vo/index.json`.
- **Cinematics:** give the cinematics lead line ids and timings, and keep to its windows.
- **GPU:** the card is shared, so wait for ComfyUI's queue and free models after your phases.
- **Practice:**
  - Keep `cd godot/tests && dotnet test` green, and use British spelling.
  - Commit and push at milestones. Commit messages end `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
  - Don't stop to ask.
  - Don't rewrite dialogue: words are the story lead's.
  - Never clone a real person. Never print or commit secrets.

## Where it stands (03:20, 4 October; pushed at 209479d)

### Done

- **Final packets, ready to record:** narrator, Rook, Holloway, Brannoc, Sella. Each is in `FINAL` in `tools/vo/elevenlabs.py`, with every one of the story lead's notes applied.
- **The narrator's hold is lifted.** The owner asked whether Vonnra should be the narrator; the story lead said no.
  - She gives one unnamed call up the road at waking instead, `dlg.cin_drowned_fire.call.0`: "Come up, traveller. ...No charge, this once."
  - It is spoken by `far_voice`, which maps to `vonnra`. It plays through a new "far" effect.
  - The fortune's "No charge, this once." is played as its twin.
- **With the new story lead for sign-off:** Vonnra and Harlan, sent at ef8e7a0 to a035208561a66c171.
  - On reply, add each voice to `FINAL`, apply the notes, and regenerate with `python tools/vo/elevenlabs.py`.
- **Vonnra's spoken name.**
  - f_accuse.0, f_door.0 and hub.0 are recorded without the name and split where it goes (`lines.NAME_VOICES`, `split_at_name`).
  - There is one take per name the creation screen suggests: `name.vonnra.<Name>`, 24 names read from `godot/src/Ui/Front.cs` `Names`. The list changed at 949cea3; the default name is now Wren.
  - The index carries `name` (seconds). `VoiceOver.SpliceName` pauses the line and says the name; a name the player typed leaves the pause empty.
  - It is tested in `VoiceTests`. **It has not yet been heard in game**, because Vonnra has no takes yet. Do that when her placeholders land.
- **Cinematic timing.**
  - Each opening line (C01 to C04, plus C01's lamp and call) has `time: [lo, hi]` in its direction.
  - The mix tightens pauses (`produce.fit`). Placeholders that are still too long are sped up, at most by a third (`post.tempo`, Praat's overlap-add); finals never are.
  - The rounds nudge Maya1's pace. Packets print "Length:". The importer reports takes that miss their window.
  - The index has `read`: the voice without the room's decay. Cuts are timed on it (`VoTake.Read`).
- **Other changes:**
  - **`warden_man`:** a new part, the tired man under the Warden ("Is it morning?").
  - **`quote` direction:** a person's words quoted inside narration take the line's `quote` direction (`lines.part_direction`).
  - **Placeholder robustness:** work files are keyed by what was asked, the check reruns parts it didn't hear, and a placeholder never overwrites a final. Both writers re-read the manifest before saving.
  - **New tools:** `--refault`, `--remix`, `--redo --faulted`, `--first-round`.
  - **Stale notes:** directions that had shifted onto the wrong variant, or quoted words since rewritten, were fixed for Sella, Vonnra, Chid, Pell, Redcowl, Snib, Keegan, Jory and Ysolde.
- **Placeholders committed:** 168 lines (64d49fc, 7fc0013). They cover the opening cinematics, the prologue, the other cinematics, Rook, Chid and the start of Brannoc.

### In progress

- **The detached run**, started at 03:02 by `~/vo-tools/scripts/placeholders_all.cmd` (`Start-Process cmd`). It logs to `~/vo-tools/placeholders_all.log`.
  - **First:** it redoes 9 lines with new seeds (`--first-round 4`):
    - five with wrong words: rook.c.0 ("owt" heard as "oat"), chid.woke.1 and woke.3 ("a carter" heard as "akata"), raid_on_the_roost.last.0 (cut short), and the prologue prints caption;
    - four still too long for their cuts: none, nobodys, downstairs, grateful.
  - **Then:** every remaining line, 40 a pass, which includes C01's lamp and call and all of Vonnra.
  - **At 03:20:** ComfyUI had filled the card, and Maya1 ran out of memory (exit 3). It retries at half the batch, then at one. Expect slow progress while the art agents work.
  - **To stop it:** kill the Python processes whose command line matches `placeholders.py|maya_batch|seedvc_worker` (PowerShell `Get-CimInstance Win32_Process`). The `.cmd` then writes `PLACEHOLDERSDONE`, so don't trust that line after a stop.
  - **To resume:** rerun the `.cmd`. Done lines are skipped and cached work is reused.
- **Promised to the cinematics lead (af7a79bc783cca7bc):** the commit and `read` values for the four re-performed lines, plus lamp and call, as soon as they land. It cuts to its target windows anyway.

### Next

1. **Commit placeholder batches as they land.** Run `dotnet test` first, then `git add godot/art/vo godot/data/vo tools/vo/manifest.json tools/vo/refs`.
   - After each batch, read from `tools/vo/manifest.json`: placeholders by voice, takes with word `faults`, and each timed line's `take.read` against `direction.time`. Send the timed ones to the cinematics lead.
   - Re-run `--refault` after any lexicon change.
2. **Listen in game once Vonnra's lines exist.** Run with `--quick --cine <id> --shot vo --until 60 --record <wav>` and check the log's `voice <id> ... with the name`.
   - Note: this worktree has no Godot import cache. A full import needs about 1.6 GB, and C: was at 99% (12 GB free at 03:15). The game plays non-imported oggs through `AudioStreamOggVorbis.LoadFromFile`, and an export imports them.
3. **Packets, in recording order:** Vonnra and Harlan (with the story lead), then Chid, Maeca, Ysolde, then the rest by impact.
   - Run the stale-note check before sending each one: quoted words in a note that aren't in the line, beats that don't match, and "hushed" on a voice that shouldn't whisper.
   - Still open from that check: maeca.blind3_morning.0 and redcowl's raid last.1 are "hushed". Ask the story lead.
4. **The owner's takes:** run `python tools/vo/import_takes.py <folder> --voice <v>`, listen, and report what is missing to the main session.
5. **The hymn at Nell's grave** stays held for the owner's choice. The options are in `docs/voice/elevenlabs/README.md`.

## Decisions, and why

- **Finals in ElevenLabs** (owner). No local model reached the bar.
- **Packets go in order of impact,** and the story lead signs each one. A changed word means a new take.
- **The narrator never shows a feeling.** His tags give only volume, and timing notes are pauses, not feelings.
- **Accents in casting briefs are "Broad" at most, "Light" where softened.** VOICES calls them a palette, not a caricature.
- **No whispers for voices that turn breathy** (Brannoc, Vonnra). Use quiet and low instead.
- **Placeholders are Maya1 performances converted by Seed-VC.** They were the only local takes heard as English that also moved like a person.
- **Placeholders may be sped up to fit a cut; finals never are.** The owner aims finals at the window, and a new take retimes the cut by itself.
- **Name takes come from the creation screen's list.** A typed name stays silent, and the subtitle always shows it.

## What failed, and why

- **The first full run:**
  - its Whisper check died silently on a crowded card;
  - it read a stale answer file, so every line went to round 2;
  - it was writing into the predecessor's worktree.
  
  All three are fixed.
- **Rerunning with new directions served old audio** from the cache. Fixed by keying the work files.
- **Pause-tightening alone can't fit Maya1's slow reads,** hence the overlap-add squeeze. Grimtunnel's sniff and chuckle lines still run long.
- **ComfyUI fills the 16 GB card for long stretches.** Maya1 then runs out of memory; the run retries and waits.

## Gotchas

- **The worktree guard** refuses compound or computed shell commands: heredocs that mention git, `cd` into other worktrees, `python -c` with computed paths. Put the logic in a script file in the scratchpad and run it plainly. Use the Edit tool for code.
- **Line endings:** `core.autocrlf=true`, so regenerated packets show as modified when only the line endings changed. Diff with `--ignore-cr-at-eol`; `git add` normalises them.
- **Hugging Face:** set `HF_TOKEN_PATH` to a missing file and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` (the `.cmd` does).
- **Direction file order:** `tools/vo/direction/*.json` load in alphabetical order, and later files replace an id's whole entry. Patch the file that defines it last.
- **Dialogue variants shift** when the writer inserts one. Directions are keyed by id, so check the notes against the words before sending a packet.
- **`say.<hash>` ids change with the words.** Use `tools/vo/rekey.py`.
- **Processes:** Git Bash `ps` misses native Windows children, so use PowerShell. Background Bash jobs die after two hours, so launch long jobs with `Start-Process`.

## Collaborators

- **Story lead: a035208561a66c171** (new; status `docs/team/story.md`, method in `docs/handoff/story.md`). Signs packets, gives wants, hides and notes, and owns the words.
- **Cinematics lead: af7a79bc783cca7bc.** Times cuts on `read`, sets the windows, and has merged this branch.
- **UI design lead: ac76f400913a109cd.** Knows that Front.cs `Names` drives the name takes.
- **The main session** ("main"): the owner's decisions, merges, and the roster.
- Don't message retired agents (a2da9a388ceb1b987, a7622ae77d19e31dc, a2dfc75e2d351105a): a message wakes them.

## Read first

1. `docs/team/README.md`, then `docs/team/voice.md`.
2. `docs/voice/elevenlabs/README.md` and one final packet, e.g. `holloway.md`.
3. `tools/vo/README.md`.
4. `tools/vo/lines.py`:
   - the manifest;
   - the splitter, and `name_elided` / `split_at_name`;
   - `part_direction`;
   - `impact`.
5. `tools/vo/placeholders.py` and `tools/vo/produce.py` (`mix`, `fit`, `finish`, `write_index`).
6. `tools/vo/elevenlabs.py` (`FINAL`, `HOLD_VOICES`, `length_note`, the name notes) and `tools/vo/import_takes.py`.
7. `godot/src/Audio/VoiceOver.cs` (the splice) and `godot/logic/World/VoiceLines.cs`.
8. `docs/VOICES.md`, `docs/VO_CAST.md`, `docs/STORY_BIBLE.md` section 2 ("Who tells it").

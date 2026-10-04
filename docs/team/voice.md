# Voice: status

Agent a501b387a90d78b4e (took over from a2da9a388ceb1b987 on 3 October). Branch: `worktree-agent-a501b387a90d78b4e`.
Read this with the predecessor's handoff, `docs/handoff/voice.md`. Where the two differ, this page is current.

## The route (the owner, October 2026)

"we're just going to use elevenlabs for our voicework so we will do 1 character at a time. we will put in placeholders with voicebox and the agent will direct me one to work on at a time"

- **Finals:** recorded by the owner in ElevenLabs from `docs/voice/elevenlabs/<voice>.md`. `tools/vo/import_takes.py <folder> --voice <v>` brings them in.
- **Placeholders:** Maya1 performs the line, Seed-VC converts it to the cast voice, and our chain mixes it (`tools/vo/placeholders.py`). Each one is flagged as a placeholder.

## State (03:30, 4 October)

- **Final packets, ready to record:** narrator, Rook, Holloway, Brannoc, Sella.
  - **Narrator:** off hold. Vonnra is not the narrator. The packet adds C01's lamp line.
  - **Story lead's sign-off:** the story lead is now a035208561a66c171. Their predecessor signed off the five finals.
- **With the story lead for sign-off:** Vonnra and Harlan (sent at ef8e7a0).
  - Vonnra's packet has the name splice, 24 name takes from the new list (949cea3), the C01 call, and realigned directions.
- **C01 voice up the road:** "Come up, traveller. ...No charge, this once." is Vonnra, unnamed (`far_voice`). A new "far" effect plays it at a distance. The fortune's "No charge, this once." is played as its twin.
- **Cinematic timing** (cinematics lead af7a79bc783cca7bc, who has merged 7fc0013):
  - Every C01 to C04 line carries its window (`time`). Cuts are timed on the index's `read`.
  - A placeholder still too long after its pauses are tightened is sped up by Praat's overlap-add, at most by a third. Finals are never sped up.
  - Lines still long: none 3.61 s, nobodys 3.15, downstairs 4.16, grateful 4.30. All four are being re-performed.
  - I promised the cinematics lead the commit with those four, lamp and call once they land.
- **Placeholders:** 168 lines are committed (64d49fc and 7fc0013).
  - Fifteen word faults were Whisper's spelling of a right word, now in the lexicon.
  - Five lines had wrong words; they are being redone with new seeds (`--first-round 4`).
- **Name list:** the UI design lead (ac76f400913a109cd) knows that Front.cs `Names` drives Vonnra's name takes.

## The detached run

- **Started:** 03:02, via `~/vo-tools/scripts/placeholders_all.cmd` (`Start-Process cmd`). It logs to `~/vo-tools/placeholders_all.log`.
- **What it does:** first it redoes 9 lines (the five wrong-word lines and the four long cinematic ones). Then it makes every remaining line, 40 a pass, most important first, which includes C01's lamp and call.
- **03:25:** ComfyUI had the card full. Maya1 ran out of memory and the run is retrying at smaller batches. The run waits up to 30 minutes for ComfyUI's queue to empty before each phase.
- **To stop it:** kill the Python processes whose command line matches `placeholders.py|maya_batch|seedvc_worker`. Killing them makes the `.cmd` write `PLACEHOLDERSDONE`, so that line can't be trusted after a stop.
- **To resume:** rerun the `.cmd`. It skips done lines and reuses cached work.

## Next

1. **Commit placeholder batches as they land:** `git add godot/art/vo godot/data/vo tools/vo/manifest.json tools/vo/refs`, after `dotnet test`. Then send the cinematics lead the commit and the `read` values.
2. **Apply sign-offs:** add each voice the story lead signs to `FINAL`, apply their notes, and regenerate the packets.
3. **Owner's takes:** import them when they arrive and report what is missing.
4. **Godot import:** not done here.
   - The game plays non-imported oggs (`VoiceOver.Stream` falls back to `AudioStreamOggVorbis.LoadFromFile`).
   - An export imports them itself.
   - A full import of this worktree needs about 1.6 GB of cache, and C: was at 99%.
5. **The hymn** stays held for the owner's choice.

## Decisions

- **Finals come from ElevenLabs** (owner). No local model reaches the bar.
- **Packets are signed one at a time.** They go in order of impact, and the story lead signs each.
- **The narrator never shows a feeling.** Timing notes are pauses, not feelings.
- **Accents are a palette, not a caricature.** Casting briefs ask for "Broad" at most, and "Light" where the accent is softened.
- **A person's words quoted inside narration take the line's `quote` direction,** not the narrator's.
- **Placeholder work files are keyed by what was asked,** so a changed direction is acted again. A placeholder never overwrites a final.

## Notes for others

- **GPU:** the run waits for ComfyUI's queue to empty before each phase, then frees its models. A busy card still costs it retries.
- **Disk:** C: was at 99% at 03:00 (3.9 GB free, later 12 GB). The placeholder work grows by about 2.3 MB per line.
- **Worktree guard:** compound shell commands are refused. Put the logic in a script file.

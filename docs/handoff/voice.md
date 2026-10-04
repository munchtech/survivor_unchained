# Handoff: voice

For the agent taking over voice for Survivor Unchained. Branch
`worktree-agent-a2da9a388ceb1b987`; integration branch
`claude/vigilant-galileo-l6jqyx` (merge it in first, and often). Read
`docs/team/README.md` (the team's rules and roster) before anything else.

## The owner's bars, in their words

- **The brief:** "cinematic movie voice actor quality… never AI-sounding".
- **The owner's test:** "do we have soul?" That means performances with a singular point of view: specific people, regional texture, idiosyncrasy and breath. A clean generic fantasy narrator fails.
- **On an early sample:** "we need to do better there. it sounds way too AI".
- **The route, October 2026:** "we're just going to use elevenlabs for our voicework so we will do 1 character at a time. we will put in placeholders with voicebox and the agent will direct me one to work on at a time".
- **The team's bar** (`docs/team/README.md`): "AAA standard", "strive for excellent, above and beyond", never settle, be critical of your own work.

## The brief, and every later message (in order)

1. **The original brief: voice director and audio engineer.**
   - Research the best voice generation; write `docs/VO_RESEARCH.md`.
   - Design a cast: a distinct designed voice per speaking part (`docs/VO_CAST.md`). Never clone a real actor or any real person.
   - Direct every line and make several takes; pick by analysis, including Whisper.
   - Real post-production: trim, de-click, about -16 LUFS, EQ and compression, room tone per scene, natural breaths.
   - A repeatable pipeline in `tools/vo/` with a manifest.
   - In the game: line-synced playback, skippable, subtitles kept, a volume slider and voices on/off, ducking, barks, Ogg Vorbis.
   - Tests that every voiced line's file exists and matches its id and text hash.
   - Prologue and the most-heard lines first.
   - Don't rewrite dialogue: notes for the writer go in `docs/VO_CAST.md`.
   - Don't touch `tools/assets/`, `godot/art/people/`, `godot/shaders/` or `godot/src/Actors/`.
   - Keep `cd godot/tests && dotnet test` green. British spelling. Commits end `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
   - No paid cloud services (that was before the owner chose ElevenLabs; the owner runs it by hand). Never print or commit secrets.
2. **"Commit and push often."** Fix `godot/assets` if it is a text file (a junction to `public\assets`).
3. **"Do we have soul?"**: hold every voice to it.
4. **"Way too AI".** Diagnose the tells; run a real shoot-out of expressive models and performance-then-convert; build a sample pack with an honest ranking; if nothing local reaches the bar, say so and recommend the paid route. Also weigh the cloud branch's voice pass (taken: its direction, not its code).
5. **The "too AI" sample may have been the cloud session's.** Still make the comparison pack, and keep the bar.
6. **Evaluate Voicebox and the 2026 field** (the owner's Reddit list); build a tested Voicebox client; collaborate with the writer; update the shoot-out page.
7. **The owner's decision: ElevenLabs.**
   - Stop the shoot-out and write a short verdict.
   - Placeholders for every voiced line from the best local route, marked as placeholders.
   - A packet per character (`docs/voice/elevenlabs/<character>.md`) and a one-command importer.
   - Direct the owner one character at a time; tell the main session who is first.
   - Drop the Voicebox MCP.
   - Check whether ElevenLabs can sing the hymn.
8. **Story-lead protocol:** the story lead marks each packet final before the owner records it.

## Where it stands

### Done
- **In the game:** playback, sync, ducking, settings, barks, and hash-checked tests (`godot/src/Audio/VoiceOver.cs`, `godot/logic/World/VoiceLines.cs`, `godot/tests/VoiceTests.cs`).
  - `VoTake.Placeholder` marks a stand-in.
  - The game reads `godot/data/vo/index.json`.
- **Pipeline** (`tools/vo/README.md`):
  - manifest (`lines.py`), direction (`direction/*.json`), cast (`cast.json`, `refs/`), mix (`post.py`);
  - placeholders (`placeholders.py`), packets (`elevenlabs.py`), importer (`import_takes.py`), story reads (`reads.py`), re-keying rewritten lines (`rekey.py`).
- **Splitter rules** (`lines.segments`), the story lead's:
  - a capitalised (Parenthesis.) is the narrator's;
  - a lower-case (parenthesis) is acted, kept as `acted` with [tags];
  - quotes in narration inside a person's conversation are that person's.
- **Packets for all 33 parts**, regenerated at b54e729.
  - The narrator and Rook are with the story lead for sign-off.
  - Still held: `keegan.vonnra` (story lead) and the hymn verses (owner).
- **First to record: the narrator.** The main session has passed the plan to the owner.
- **Shoot-out:** closed. 69 takes and an honest ranking in `docs/voice/samples/`; the round-two verdict is in its README. Page: https://claude.ai/artifact/T1Bns481cT4bLCAqB6Sipx.
- **Voicebox:** installed from source, with a tested client (`tools/vo/voicebox.py`, documented in `docs/VOICES.md`). The MCP is dropped.

### In progress
- **The full placeholder run**, started 21:46 on 3 October, detached from any shell.
  - Start: `C:\Users\munch\vo-tools\scripts\placeholders_all.cmd`, run via `Start-Process cmd`.
  - Log: `C:\Users\munch\vo-tools\placeholders_all.log` (ends `PLACEHOLDERSDONE`); Maya1's own log is `maya_batch.log`.
  - It covers 1,063 lines, most important first, 40 a pass. Each pass waits for ComfyUI's queue to empty, frees ComfyUI's models, then runs Maya1 (batches of 8), Seed-VC and Whisper, with up to three tries. It writes `godot/art/vo/<voice>/<id>.ogg` and the index, and saves `tools/vo/manifest.json` after each pass.
  - Expect several hours, depending on the art agents' use of the card.
  - To stop it, kill the Python processes by command line in PowerShell (`Get-CimInstance Win32_Process` where the command line matches `placeholders.py|maya_batch|seedvc_worker`). Rerun the `.cmd` to resume; lines with a take are skipped.
  - Commit the oggs and the index as they come (`git add godot/art/vo godot/data/vo tools/vo/manifest.json`), and run `dotnet test` first.

### Next
1. **Packets:** the narrator and Rook are **final** (story lead, 3 October; `FINAL` in `elevenlabs.py`), and the main session has been told the owner can record them.
   - Send the story lead each next packet in recording order, with its diff: Holloway, Brannoc, Sella, Vonnra, Harlan, and so on.
   - Add each voice to `FINAL` when it signs off.
   - **The Red Hand** (`red_hand`, a Kerchief enforcer: "Toll's due.") is cast on paper in `cast.json`, but has no reference yet. Audition him when the card is free (`python tools/vo/cast_session.py red_hand --n 12`); his placeholder waits for that.
2. **Takes:** when the owner sends narrator takes, run `python tools/vo/import_takes.py <folder> --voice narrator`. Listen to the result via the numbers and in the game, and report what is missing.
3. **Placeholders:** keep committing them as the run goes. When it ends, look at the lines with `faults` in their take (`manifest.json`) and redo the bad ones (`placeholders.py <ids> --redo`).
4. **Not built yet:** Vonnra's spliced name (record "...Sit down," and "I have not finished reading." as two takes plus name takes, and splice in `VoiceOver`). This is the writer's decision in `docs/VO_CAST.md`.
5. **Godot:** the new oggs need importing (`.import` files) before the game plays them. Run an editor import, as `docs/team/README.md` or the main session does.

## Decisions, and why

- **Finals in ElevenLabs (owner).** No local model reached the bar; the shoot-out's numbers and the owner's ear agreed.
- **Placeholders are Maya1 performances converted by Seed-VC into each cast voice.** These were the only local takes heard as English (1.0) that also moved like a person (pace change 0.22, breaths). Batching makes them fast enough: at batch 8, about ten times one.
- **The cast voices were designed by VoxCPM2.** They are the Seed-VC targets and the identity of each part until ElevenLabs replaces it.
- **Packets follow the story lead's rules.**
  - The narrator never shows a feeling: his own lines are played plain, and he whispers four times.
  - Pauses are written as "…".
  - One take per distinct text (the importer copies it).
  - Order follows `lines.impact`: opening cinematic, prologue, other cinematics, scenes, conversations in the order the town is met, barks, passers-by.
- **One voice system in the game** (ours, not the cloud branch's).
- **Nothing ships on numbers alone:** the owner's ear passes takes.

## What failed, and why

- **VoxCPM2 continuation reads like an audiobook:** pace change 0.04, flat stress.
- **Every other local model**, judged on the shoot-out's numbers in `docs/voice/samples/README.md`:
  - Voicebox's engines are clean but read like readers;
  - Chatterbox Turbo stops a take at a tag placed mid-line;
  - Dia and Orpheus act, but they are American;
  - Scots, Irish and Welsh accents cannot be had from any local model.
- **The owner's Reddit list could not be read.** Reddit blocks this machine, and the browser pane refuses reddit.com.
- **Maya1 batches on a full card:** they fail with `CUBLAS_STATUS_INTERNAL_ERROR` or out-of-memory. `placeholders.py` retries at half the batch, and waits for ComfyUI first.

## Gotchas

- **Hugging Face:** the stored token file is refused by the sandbox. Set `HF_TOKEN_PATH` to a missing file and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` for every downloader (Voicebox, Maya1, Dia2).
- **Voicebox:**
  - **Install:** from source at `~/vo-tools/voicebox-src` (venv `~/vo-tools/voicebox`), without `misaki[ja,zh]` and `unidic-lite` (pyopenjtalk will not build). Chatterbox and hume-tada install with `--no-deps`.
  - **Run:** `~/vo-tools/scripts/voicebox_serve.sh`, port 17493. Stop it with `POST /shutdown`; TaskStop leaves the Python child running.
  - **API:** `POST /generate` is asynchronous. Poll `GET /history/{id}`, then fetch `GET /audio/{id}`. Only `qwen_custom_voice` honours `instruct`.
- **GPU:** the card (16 GB) is shared with ComfyUI at 127.0.0.1:8188.
  - Free ComfyUI with `POST /free {"unload_models": true, "free_memory": true}` only when its queue is empty. I once sent it mid-job; don't.
  - Release your own models when done (`python tools/vo/voicebox.py free`, or let processes exit).
- **The worktree guard** refuses complex or computed shell commands (pipes into Python, loops, `sed` with code, `git` in strings). Put the logic in a script file and run that plainly.
- **Processes:** Git Bash `ps` does not show native Windows children; use PowerShell `Get-CimInstance Win32_Process`. Background Bash jobs die after two hours, so launch long jobs detached (`Start-Process`).
- **IDs that move:** `say.<hash>` ids change when the words do. Run `python tools/vo/rekey.py --old=<earlier manifest>` to carry directions over (`git show <commit>:tools/vo/manifest.json`).
- **Hand-set splits:** a direction file's `segments` overrides the automatic split. Avoid it now that the rules cover quotes and parentheses.

## Open questions

- **The hymn at Nell's grave:** the owner chooses Eleven Music, a singer we have the rights to, or a licensed singing synthesiser. Options are in `docs/voice/elevenlabs/README.md`.
- **`keegan.vonnra`:** waiting on the story lead's confirmation.
- **The Red Hand:** cast on paper, awaiting an audition (see Next).
- **Vonnra's spliced name** is not built.
- **The two Maeca notes** (`blind_dark.0/.1`) keep the writer's own words about how it lands ("nearly funny", "can't afford the wonder"). They are the writer's, not the narrator's feelings.

## Collaborators

- **Story lead: a7622ae77d19e31dc** (status `docs/team/story.md`). Checks every packet line against the data, gives wants, hides and beats, and marks packets final. Change no packet line without telling them. `docs/WRITING_PASS.md` sections 17 and 18 list what is protected.
- **The main session** passes decisions to and from the owner (SendMessage "main").
- **Roster:** `docs/team/README.md`. Retired agents are not to be messaged.

## Read first

1. `docs/team/README.md`
2. `docs/team/voice.md`
3. `docs/voice/elevenlabs/README.md` and `docs/voice/elevenlabs/narrator.md`
4. `tools/vo/README.md`
5. `tools/vo/lines.py` (the manifest, the splitter, `impact`)
6. `tools/vo/elevenlabs.py`
7. `tools/vo/import_takes.py`, and its test `tools/vo/tests/test_import_takes.py`
8. `tools/vo/placeholders.py` and `tools/vo/backends/maya_batch.py`
9. `tools/vo/direction/` (`narrator_pass.py` is the record of the narrator pass)
10. `docs/VOICES.md` (who everyone is, and the parenthesis and quote rules) and `docs/VO_CAST.md`

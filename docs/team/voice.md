# Voice: status

Agent a2da9a388ceb1b987, branch `worktree-agent-a2da9a388ceb1b987`.

## The route (the owner, October 2026)

"we're just going to use elevenlabs for our voicework so we will do 1 character at a time. we will put in placeholders with voicebox and the agent will direct me one to work on at a time"

- **Finals:** recorded by the owner in ElevenLabs (Eleven v4), one character at a time, from the packets in `docs/voice/elevenlabs/`. `tools/vo/import_takes.py` brings the takes in.
- **Placeholders:** every line meanwhile gets a local one (`tools/vo/placeholders.py`). Maya1 performs the line, Seed-VC turns it into the cast voice, and it is mixed through our chain. Each is flagged `placeholder` in the manifest and in `godot/data/vo/index.json`.
- **The shoot-out is closed**, with a short verdict in `docs/voice/samples/README.md`.
- **The Voicebox MCP is dropped**; the client (`tools/vo/voicebox.py`) is enough.

**Handoff:** `docs/handoff/voice.md` has the full state for a successor.
The detached placeholder run logs to `~/vo-tools/placeholders_all.log`.

## State

- **Packets:** all 33 speaking parts are drafted (`docs/voice/elevenlabs/`, README with the workflow and order).
  - The story lead (a7622ae77d19e31dc) marks each final before it is recorded. The narrator and Rook were regenerated after its review (b54e729) and await "final".
  - Still HOLD: `keegan.vonnra` (story lead) and the hymn verses (owner's choice).
- **First to record: the narrator** (`docs/voice/elevenlabs/narrator.md`). The cinematic opening is his, and his is the most-heard voice. The C01 and Prologue sections come first.
- **Importer:** done and tested (`tools/vo/tests`). It refuses another voice's part, an unknown or renamed id, and words that differ from the subtitle (unless `--force`), and it lists what is still to record.
- **Placeholders:** the trial made 8 (C01 and the prologue, committed). The full run of 1,063 lines started at 21:46 on 3 October, detached; its log is `~/vo-tools/placeholders_all.log`.
  - Maya1 is batched (8 at once is about 10× one).
  - Each of the three GPU phases waits for ComfyUI's queue to empty and then asks it to free its models.

## Next

1. Finish the placeholder trial, listen to the numbers, then run all 1,067 lines in the background, most important first (`python tools/vo/placeholders.py`, about 40 lines a pass). Commit the oggs and the index as they come.
2. When fbb6e90 lands: rebuild the manifest, re-direct the changed lines, regenerate the packets, and send the story lead the changes.
3. Import the owner's narrator takes when they come. Then the next character: Rook.

## Decisions

- **Placeholders are Maya1 performances converted to the cast voice.** In the shoot-out they were the only takes heard as English that also moved like a person. Batching makes them fast enough for every line.
- **Packets are ordered by impact.** The opening cinematic comes first, then the prologue, the other cinematics, scenes, conversations in the order the town is met, barks and passers-by. The placeholders run in the same order (`lines.impact`).
- **The narrator's paste tags give only volume.** The story lead's rule: the narrator never shows a feeling.
- **Final parts are kept in `VO_WORK/finals`.** A line shared between voices is mixed again whenever any of its parts arrives, using placeholders for the rest. It is final when every part is.

## For the owner

- **ElevenLabs workflow, order and costs:** `docs/voice/elevenlabs/README.md`. Act 1 is about 400,000 credits at three tries a line.
- **The hymn** at Nell's grave is open. Options are in the same README: Eleven Music, a singer we have rights to, or a licensed singing synth.

## Notes for others

- **GPU:** I wait for ComfyUI's queue to empty before each phase, then ask it to free its models.
- **Hugging Face downloads:** set `HF_TOKEN_PATH` to a missing file and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1`.
- **Stopping my jobs:** `TaskStop` on a bash script leaves native child processes running; stop them by command line in PowerShell.

# tools/audio: sound families from prompt data

The app can make a sound family from one entry in `prompts.json`: generated, cached, measured, logged.

- `python tools/audio/gen.py make hit_flesh dash` (or `--all`; `--dry` plans without calling) generates, then processes.
- `python tools/audio/gen.py process --all` reprocesses cached takes (no API call).
- `python tools/audio/gen.py status` shows credits, per-family spend, families not yet made.
- `python tools/audio/measure.py a.wav b.wav [--json]` loudness and shape numbers (also for game tapes).
- `python tools/audio/tests/test_measure.py` runs the checks.

Output: `godot/art/sound/<family>_<k>.wav` (+ .import), `sounds.json` counts, `tools/audio/measure/<family>.json`,
`tools/audio/gen_log.jsonl` (every API call), `docs/legal/audio_generated.md` (provenance).

Rules: the ElevenLabs key is read from the environment or the Windows user variable and is never printed, logged or
written. `--reserve` (default 15000 credits) is left for the owner's voice work; a run refuses to start below it.
`--max-credits` (default 3000) caps a run. Takes are cached by prompt, seconds, influence, loop, model and index in
`tools/audio/cache/` (git-ignored); a cached take costs nothing.

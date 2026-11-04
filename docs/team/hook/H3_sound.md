# H3: sound (a new area: the audio lead)

Lead: `su-lead-high` in worktree `audio-h3` (branch `audio-h3`). Est 1M. Read first: `docs/handoff/lead_brief.md`, `docs/team/DEMO_PLAN.md` "Phase 3 verdict" (your row and the owner's answer 5), `docs/team/DEMO_GATE.md` N7, `docs/team/voice.md` (the ElevenLabs voice route, for the account's conventions), `docs/team/provenance.md` (how sources are logged), `docs/team/legal.md` (no asset that needs crediting: CC0 only, besides generated output the owner owns).

## The owner's words
"all the sounds kinda stink". "some stuff is satisfying like corpses exploding". Route: "you may use my elevenlabs, or give me a detailed list of sounds to make".

## What exists
Every effect is a synthesized tone: `godot/src/Audio/Synth.cs` plays `Tone`s from `Sfx.cs`, `Sfx.Skills.cs`, `Sfx.Flare.cs`, `Sfx.Lamps.cs`; `Music.cs`, `Ambience.cs`, `SoundBridge.cs`, `VoiceOver.cs`, `Recordings.cs`. `godot/art/sound/` holds 205 wavs (footstep, impact*, tell, select, error, chainLink, switch, scroll...) with a json: find what they are and whether they are wired and CC0 (provenance) before you use any.

## The fixed list
1. **A sound bank as data:** `godot/data/content/sounds.json`: event -> variants, gain, pitch spread, cooldown, bus, falloff; `Sfx` plays samples by event, the synth only where no sample is better. Buses: master, sfx, music, ambience, vo; ducking under VO; a loudness target per bus (measure peaks and LUFS with a script, numbers in your report). The capability: "the app can now give any event a sound from a line of data".
2. **Generation as a tool:** `tools/audio/gen.py`: the ElevenLabs sound-generation endpoint, prompts as data (`tools/audio/prompts.json`), cached by prompt hash, each output logged in `docs/team/provenance.md` (generated, owner's account, owned). The key is the environment variable `ELEVENLABS_API_KEY` (the owner sets it; never print it, never commit it; if it is missing, say so to main and build everything else). CC0 beds where generation does worse (log the source and license).
3. **The palette, in this order:** her auto-attack hits and kills (by foe material), the corpse pop (keep what the owner liked: give it weight), the dash, the Warden's four skills and the Long Cut Flare, then the other callings' skills; ember pickup, level up, the draft; the lamps (lit, out), the Ford-Warden's channel and lamp; foe tells (H1 builds `Ev.Telegraph` with a kind: give each kind a sound; the combat lead's agent id comes from main); boss arrival and down; the way out opening (H4 wants a sound on its banner); UI (open, close, pick, back); footsteps by ground and her armor; ambience beds (the Verge by day, the Low Ford by night, the Waystation, the Deep Shaw at night); the result (won, fell); the title.
4. **The owner's list:** `docs/team/audio.md` "For the owner": every sound you could not get right by generation, with a one-line brief each (what it is, length, character, a reference in words), so the owner can make them.

## Judge and exit
No model judges sound: the owner's ears are the judge. Deliver a listening sheet: ten moments recorded from the game (before and after, short clips, `Recordings.cs` or an OBS-free capture through Godot's audio bus recording) in `survivorsunchained_inputs\audio_h3\`, with the numbers (peaks, LUFS per bus). Main builds `demo-rc2`; the exit is the owner playing a night with headphones: "it sounds like a game".

Rules: no GPU; commit as you go; tests green; a status page `docs/team/audio.md` and a handoff `docs/handoff/audio.md` (you are the first). Report to main.

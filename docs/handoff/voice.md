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
   - Keep `cd godot/tests && dotnet test` green. Commits end `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
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


Older blocks: history/voice.md (grep by keyword, never read whole).

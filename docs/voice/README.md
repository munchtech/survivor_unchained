# The voice pass

Everything needed to voice Survivor Unchained's people with a local TTS
(Qwen3-TTS on the owner's machine) or with actors, and the game's side of
playing what gets recorded. Nothing here changes a word of the writing:
the tools read the content and regenerate from it, so the writing can go
on changing underneath.

## What is here

| Where | What |
|---|---|
| `tools/voice/extract.py` | Finds every spoken line and writes the manifest, the scripts and the casting sheet. Standard-library Python. |
| `godot/data/voice/lines.json` | The manifest: per line, its ID, speaker and voice, the words as written (`text`), the words to record (`say`, where they differ), the hash of the words, the take's path (`res://audio/vo/<voice>/<id>.ogg`), its context and its direction. |
| `docs/voice/script/<voice>.md` | The recording script, one per voice: each line with who it is said to, what was said before, the choice that led there, when it is shown, and how to say it (emotion, intensity, pace, what the speaker wants, notes), with pronunciation for the invented names. |
| `docs/voice/CASTING.md` | A profile per voice (age, accent, timbre, pace, range, habits), a voice-design paragraph for a model that builds a voice from words, audition lines, and which voices can share. Rendered from `tools/voice/voices.json`. |
| `tools/voice/directions.json` | The hand-written direction for every line, keyed by line ID, each with the hash of the words it was written for. |
| `tools/voice/voices.json` | The casting, and the pronunciation lexicon. |
| `tools/voice/tts_batch.py` | Voices what is missing or stale, normalises it to about -16 LUFS and writes Ogg Vorbis where the game looks. |
| `godot/data/voice/takes.json` | Written by the batch: what has been recorded, and for which words. The game reads only this. |
| `godot/logic/World/VoiceLines.cs` | The game's side of IDs, hashes, which variant is on screen, and which take (if any) still matches it. Tested in `godot/tests/VoiceTests.cs`. |
| `godot/src/Audio/VoiceOver.cs` | Plays the takes: see *In the game* below. |

## Lines and IDs

A line's ID comes from where it lives, never from its words, so a rewrite
keeps the ID and changes the hash:

- conversations: `<conversation>.<node>`, with `.<n>` for the n-th variant
  (from 1) when the node has several (`rook.hub.3`). A notice board's
  notices are variants read in turn.
- barks: `bark.<person>.<n>`, `bark.<person>.night.<n>`; the gate guards
  `bark.guard.<n>.<m|f>`; stall-keepers `bark.stall.<kind>.<n>.<m|f>`.
- the town's passing lines: `folk.<n>.<m|f>` (a take per sex, since anyone
  might say them, except lines only one sex could say, such as "my
  husband"), `folk.<n>` for children's.
- the zone scripts: `<zone>.say.<n>[.<k>]` for captions (the n-th `G.Say`
  in the file, the k-th of a ternary), `<zone>.bark.<n>` for named barks
  (the Ford-Warden, Grimtunnel, Snib), `verge.cagelines.<n>`.
- the chapter's last page: `chapter.*`, marked optional (nothing reads it
  aloud yet).

The hash is the first twelve hex digits of the SHA-1 of the words exactly as
written, tokens and stage directions included (`VoiceLines.Hash`). The
player's own choices are not voiced: the survivor is silent, as the writing
assumes (their lines are short and dry, and a voiced survivor would need a
take per sex for every choice). Combat callouts ("Executed", "Thud") and
the arena's event shouts are not voices.

### What the tool does to the words

- **Tokens** (`{name}`, `{gold}`, `{day}`, `{fact:...}`) cannot be recorded.
  The take drops them with the punctuation that hangs on them ("Late,
  {name}. Stew's cold." is recorded as "Late. Stew's cold."); the subtitle
  still shows the name. A `say` in `directions.json` overrides the proposal
  (two of Redcowl's lines have one). Every such line is flagged `token:*`.
- **Stage directions** in brackets inside someone's speech ("(The hammer
  comes down.)") are the narrator's, not the speaker's: they leave the take,
  leave a pause ("...") where they fell mid-line, and become part of the
  line's direction. Flagged `stage-direction`.
- **Writer's slots** (`[explicit scene: ...]`) are not recorded (`skip`).
- **Lines split by sex.** Where a node has variants by who the survivor is
  taken for (Redcowl's lad and lass), each variant is its own take and the
  script marks it **survivor: female/male**. A line that calls the survivor
  "lad", "lass", "sir" and so on with no variant for the other sex is
  flagged `gendered-address` (none at present).

## How to regenerate

After any change to the writing (content JSON, a zone's captions, a bark):

    python3 tools/voice/extract.py --check   # what changed: new, rewritten, gone
    python3 tools/voice/extract.py           # rewrite the manifest, the scripts and CASTING.md

It also reports direction written for words that have since changed, and
direction for lines that are gone. `cd godot/tests && dotnet test --logger
"console;verbosity=detailed"` reports the same drift from the game's side
(`VoiceTests.Report_lines_the_manifest_has_not_caught_up_with`) and never
fails because of it.

To change how a line is said, edit `tools/voice/directions.json` (keep the
`hash`: it is how a rewrite is noticed) and regenerate. To change a voice,
edit `tools/voice/voices.json`.

## How to voice

On the machine with the TTS (Python 3.9+, ffmpeg with libvorbis):

1. **Connect the TTS.** Fill in `synthesize()` at the top of
   `tools/voice/tts_batch.py`: it gets the words, the voice's key, its
   design paragraph, an instruction built from the line's direction, and the
   voice's reference clip if one has been chosen, and writes a WAV. It is the
   only function that knows about the TTS.
2. **Cast.** `python3 tools/voice/tts_batch.py --auditions` voices each
   voice's audition lines three times from its design paragraph into
   `tools/voice/auditions/<voice>/`. Pick the take that is the person, copy it
   to `tools/voice/refs/<voice>.wav`, and its words to `<voice>.txt`. From
   then on every take of that voice is cloned from the same reference, so
   Vonnra sounds like Vonnra on line 1 and line 73. Vonnra is the casting
   that matters most (`CASTING.md`); start there.
3. **Check the pipeline** without spending GPU time:
   `python3 tools/voice/tts_batch.py --dry-run` lists what is to do;
   `--placeholder --voice brannoc --limit 5` writes soft tones in place of
   voices so the game's playback can be heard working (delete them, and
   `godot/data/voice/takes.json`, before committing).
4. **Voice.** `python3 tools/voice/tts_batch.py` does every missing or stale
   line, `--voice vonnra` one voice, `--id rook.hub.3` one line, `--limit N`
   a few, `--force` again regardless, `--optional` the chapter page too,
   `--prune` forgets takes whose lines are gone. Each take is loudness-
   normalised (two-pass loudnorm, -16 LUFS integrated, -1.5 dBTP), trimmed of
   leading and trailing silence, and written as mono Ogg Vorbis at 48 kHz.
   `takes.json` is saved after every take, so a stopped batch resumes. A line
   with the same words in the same voice as a take already made is copied,
   not voiced again.
5. **Import.** Open the Godot editor once (or run Godot with `--headless
   --import --path godot`) so the new `.ogg` files are imported; the game
   plays unimported files too while working, but an export needs them
   imported.
6. **Listen and commit** `godot/audio/vo/`, `godot/data/voice/takes.json`
   (and the `.import` files Godot writes beside the takes).

## In the game

- When a conversation shows a line, `VoiceOver` works out which variant is
  on screen, looks up its take, and plays it if the take was recorded for
  exactly these words; a notice board's notices play in turn. The next line,
  a choice, or leaving the conversation stops it. The same node shown again
  (back from a shop) is not said twice.
- Barks are said from where the speaker stands (an `AudioStreamPlayer3D`),
  two at most at once, and none over a conversation. A passer-by's line
  plays the take of the walker's sex; a line recorded only for the other sex
  stays unvoiced rather than come from the wrong mouth.
- Captions under the picture (`G.Say`) are read by the narrator, or by
  whoever the take belongs to.
- Music and ambience duck under any voice (more under a conversation than
  under a bark).
- Voices play on their own `Voice` bus; the settings have **Voices: on,
  quiet, off**, beside Sound.
- Subtitles are untouched. With no `takes.json`, or no take matching the
  words on screen, nothing plays: it is safe to merge before a single line
  is recorded.

## What to merge

All of it is additive. The game-side changes, each small:

- `godot/logic/World/VoiceLines.cs` (new) and `godot/tests/VoiceTests.cs` (new).
- `godot/src/Audio/VoiceOver.cs` (new); `godot/src/Audio/Synth.cs`: one
  more duck, under voices, on the music and the ambience.
- Hooks, a line or two each: `Game.cs` (makes the player; captions; fight
  barks; the volume), `GameMenus.cs` (a line shown; the conversation ended),
  `WorldScene.cs` (barks), `Settings.cs` and `Ui/Menus.cs` (the Voices row;
  the pause menu's settings box 40 px taller to fit it).
- `IZoneLook.Bark` takes an optional `voice` (who is speaking, for the
  take), passed by `Zone.cs` (people's barks) and `Folk.cs` (walkers now
  remember their sex); `tests/FakeHost.cs` follows the signature.
- Tools and documents: `tools/voice/`, `docs/voice/`, `godot/data/voice/lines.json`,
  a Voices section in `godot/README.md`.

Do not merge placeholder takes (`--placeholder`) or a `takes.json` made from
them.

## For the writers

Found while directing every line; none of it was changed here.

- **Vonnra's name.** VOICES.md makes her saying the survivor's name, after
  the fortune, the only answer she gives. `vonnra.f_accuse`,
  `vonnra.hub.1` and `vonnra.f_door.1` lose it in the take ("Sit down. I
  have not finished reading."). Options: keep the subtitle carrying it; or
  record a short take of the name alone for the names the game suggests at
  creation and splice it in at runtime. Worth deciding before Vonnra is
  voiced.
- **Mixed voices in one caption.** `prologue.say.2` (the dead Watchman) and
  `verge.say.19` (the bones) begin with the narrator's words ("...and for
  you alone, the dead man's jaw moves:"), then the dead speak; and
  `verge.cagelines.3` puts Jory's words in the narrator's mouth. Each would
  be better as two captions (narrator, then speaker), which the tools would
  pick up as two lines.
- **Rules VOICES.md sets that a line breaks:** `vonnra.cb_vault3` ("It is.
  For now.") is close to a yes; `vonnra.f_pell.4` ends "He will not forget
  you", close to the retired "I will not forget"; Jory says "cage" in
  `jory.first`, `bark.jory.1` and `bark.jory.3`, though his rule is that he
  never does; `redcowl.first.5` (to a woman) has no lad-side counterpart.
- **Passing lines.** `folk.73` ("Gates are shut till dawn.") and `folk.75`
  ("Piss off home. It's past curfew.") have no after-dark condition, so can
  be heard by day.
- **Duplicates.** Several `say_calling.4`/`.5` pairs have the same words
  (the stalker's and the fallback); the batch records them once and copies.
- **Heard rather than read**, `verge.say.3` ("Maeca said none since you
  last slept") is hard to follow; `tam.again.2`'s capitals ("I SAID") are
  for stress, and some TTS models spell capitals out: respell in a `say` if
  a take does.

<!-- generated:start (tools/voice/extract.py writes this section) -->

## Line counts

Takes to record, per voice (a passer-by's line counts once per sex; optional lines are the chapter page).

| Voice | Who | dialogue | notice | bark | folk | zone | chapter | Takes |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `narrator` | The narrator | 12 | 18 |  |  | 55 | 31 | **116** |
| `townswoman` | A townswoman |  |  | 13 | 90 |  |  | **103** |
| `townsman` | A townsman |  |  | 13 | 87 |  |  | **100** |
| `vonnra` | Vonnra Ash-of-Morrow | 68 |  | 7 |  |  |  | **75** |
| `holloway` | Captain Holloway | 51 |  | 8 |  |  |  | **59** |
| `harlan` | Harlan Coyle | 44 |  | 7 |  |  |  | **51** |
| `rook` | Mother Rook | 34 |  | 8 |  |  |  | **42** |
| `sella` | Sella | 33 |  | 7 |  |  |  | **40** |
| `brannoc` | Brannoc | 29 |  | 9 |  |  |  | **38** |
| `maeca` | Maeca Barefoot | 29 |  | 7 |  |  |  | **36** |
| `rav` | Rav Cutwell | 25 |  | 10 |  |  |  | **35** |
| `chid` | Chid | 28 |  | 7 |  |  |  | **35** |
| `redcowl` | Redcowl | 28 |  | 4 |  |  |  | **32** |
| `wenna` | Old Wenna | 23 |  | 7 |  |  |  | **30** |
| `pell` | Pell Varrow | 23 |  | 7 |  |  |  | **30** |
| `keegan` | Dame Keegan Orme | 21 |  | 7 |  |  |  | **28** |
| `wayfinder` | Ysolde Marrow, the Wayfinder | 19 |  | 6 |  |  |  | **25** |
| `tam` | Tam | 13 |  | 3 |  |  |  | **16** |
| `snib` | Snib | 13 |  | 1 |  |  |  | **14** |
| `watchman` | A watchman |  |  | 3 | 9 |  |  | **12** |
| `watchwoman` | A watchwoman |  |  | 3 | 9 |  |  | **12** |
| `jory` | Jory Coyle | 8 |  | 3 |  |  |  | **11** |
| `child` | A child |  |  |  | 7 |  |  | **7** |
| `lampling` | The babbling lampling | 2 |  |  |  |  |  | **2** |
| `ford_warden` | The Ford-Warden |  |  | 2 |  |  |  | **2** |
| `grimtunnel` | Grimtunnel |  |  | 2 |  |  |  | **2** |
| `dead_watchman` | The dead Watchman |  |  |  |  | 1 |  | **1** |
| `bones` | The bones |  |  |  |  | 1 |  | **1** |
| | **All** | **503** | **18** | **144** | **202** | **57** | **31** | **955** |

3 lines are writer's slots and are not recorded; 31 are optional.

## Flagged lines

Lines whose take cannot say exactly what the subtitle says. The proposed take is in the script; a `say` in `tools/voice/directions.json` replaces it. Lines with stage directions taken out (`stage-direction`, 76 of them) are listed in each script.

| Line | Flags | Recorded as |
|---|---|---|
| `rook.hub.1` | token:name | Late. Stew's cold. Beds aren't. |
| `rook.hub.3` | token:name | Back again. What'll it be? |
| `holloway.expose.2` | token:name | Payments to "R.": Redcowl. And to Jessop, at Vonnra's toll. On the night. Pell Varrow, you careful, greedy little man.… |
| `maeca.thanks` | token:name | The Hollow's quiet. The Pack's eating again: deer, not travellers. I've been a hunter all my life, and I've never once… |
| `maeca.blind.1` | placeholder | (not recorded) |
| `wenna.analyse.2` | token:name | Green. Warm. Smells like a chapel lamp. Ember slurry, child: the dust of the stones, cooked and watered. Rots the belly… |
| `chid.woke.1` | token:name | You're awake! Good. Good! A carter found you on the Old Road and brought you here, and the flame... the flame kept you.… |
| `vonnra.hub.1` | token:name | Your chapter is written. The next one is not. ...Payment, always. |
| `vonnra.f_door.1` | token:name | The door in the hillside is listening, as I am. That is all I see for free. The rest you will walk into yourself, and y… |
| `vonnra.f_accuse` | stage-direction, token:name | Sit down. I have not finished reading. |
| `sella.hub.1` | token:name | Evening. The lamp's lit upstairs, if you're asking. You look like you're asking. You look like you've been asking all d… |
| `sella.again.2` | token:name | Still walking straight, I see. I'll take that as a compliment. |
| `sella.night.1` | placeholder | (not recorded) |
| `sella.morning.1` | token:name | You're getting to be a habit. I don't mind. Rook does; she says you're wearing out the stairs. Go on, the day's wasting… |
| `sella.free` | token:name | Put your purse away. Tonight I'm not working. ...Don't look at me like that. Don't make it strange. |
| `sella.free_night.1` | placeholder | (not recorded) |
| `redcowl.deal` | token:name | Pleasure. Box is by the tents; the teamsters are in the cages. Open them yourself; my lads won't stop you. And if Hollo… |
| `redcowl.crates_charge` | stage-direction, token:name | Take it. Put it where it'll do the most harm to the right people. And then... run. |
| `redcowl.pell_given` | stage-direction, token:name | Ha! Somebody who knows where the rats sleep. ... Go home. Stay off the square tonight. |
| `wayfinder.hub.1` | token:name | Back from the edges, and in one piece. The places you took are quieter for it. I've new ones. |
| `wayfinder.hub.2` | token:name | Maps. Places the road forgets. Pick one. |
| `wayfinder.margin_name` | stage-direction, token:name | There. Now you're in the margins for good. |
| `chapter.11` | token:name | Who runs with wolves |
| `chapter.12` | token:name | Who said it to Vonnra's face |
| `chapter.13` | token:name | In Pell Varrow's ledger |
| `chapter.14` | token:name | Who sold the cure |
| `chapter.15` | token:name | Who sold the Coyle strongbox |
| `chapter.16` | token:name | Who kept the Coyle strongbox |
| `chapter.17` | token:name | Who cleared the water and opened the cages |
| `chapter.18` | token:name | Who cleared the water |
| `chapter.19` | token:name | Who opened the cages |
| `chapter.20` | token:name | The wolf-killer |
| `chapter.21` | token:name | Who would not stay dead |
| `chapter.22` | token:name | Late of the Low Ford road |

<!-- generated:end -->

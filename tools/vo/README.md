# tools/vo: the voice-over pipeline

Every spoken line in the game, from the writing to an Ogg file the game
plays, repeatably: when a line is rewritten, its take goes stale and is made
again. Why VoxCPM2 and how it was chosen: `docs/VO_RESEARCH.md`. Who sounds
like what, and what could not be cast: `docs/VO_CAST.md`.

## The steps

| Step | Script | Makes |
|---|---|---|
| 1. The lines | `lines.py` | `manifest.json`: every line with its id, voice, parts (the narrator's asides split out), direction, the hash of its words, its take and status |
| 2. Direction | (written by hand) | `direction/*.json`: per line, emotion, intent, pace, volume, what the speaker wants, a note for the read; voices for passers-by; a respelling (`say`) where a line is read otherwise than written |
| 3. Casting | `cast_session.py` | `refs/<voice>.flac`: each part's voice, auditioned from VoxCPM2 voice designs (`cast.json`) and chosen by ear-numbers; `refs/casting.json` |
| 4. Moods | `registers.py` | `refs/<voice>.<mood>.flac`: the part in warm, quiet, hard, quick and hushed moods, kept only if still the same person; `refs/registers.json` |
| 5. Recording | `produce.py` | takes continued from the mood each line's direction calls for, judged, the best mixed (`post.py`) into `godot/art/vo/<voice>/<id>.ogg`, and `godot/data/vo/index.json` |

`analyse.py` is the ear (words, accent, naturalness, pitch, pace,
speaker match, artefacts); `post.py` the edit and mix; `script.py` prints a
part's lines as a recording script with their direction.

```sh
python tools/vo/lines.py --report                # what there is to record
python tools/vo/cast_session.py rook --n 12      # audition a part
python tools/vo/registers.py rook                # its moods
python tools/vo/produce.py dlg.rook              # record its lines
python tools/vo/produce.py --index               # rebuild the game's index only
cd godot/tests && dotnet test --filter VoiceTests
```

A line is recorded only when every part has a clean take: right words
(Whisper; names Whisper spells its own way are in `lexicon.json`), heard in
the part's accent, at a plausible pitch, at the direction's pace, the same
person as the reference, and no clipping, cut or noise. A line that never
gets one is left silent with status `failed` and the reasons in the
manifest; the game shows its words as always.

## Setting up (Windows, an NVIDIA GPU with 8 GB free)

Everything big lives outside the repo, in `VO_TOOLS` (default `~/vo-tools`):

```sh
uv venv ~/vo-tools/voxcpm --python 3.12
uv pip install --python ~/vo-tools/voxcpm/Scripts/python.exe torch torchaudio --index-url https://download.pytorch.org/whl/cu128
uv pip install --python ~/vo-tools/voxcpm/Scripts/python.exe voxcpm "triton-windows<3.8"
uv venv ~/vo-tools/analysis --python 3.12
uv pip install --python ~/vo-tools/analysis/Scripts/python.exe torch torchaudio --index-url https://download.pytorch.org/whl/cu128
uv pip install --python ~/vo-tools/analysis/Scripts/python.exe transformers accelerate speechbrain funasr librosa pyloudnorm soundfile praat-parselmouth scipy numpy modelscope
```

Run the scripts with the `analysis` venv's Python; they start the VoxCPM2
worker (`backends/voxcpm_worker.py`) in its own venv. The first start
compiles the model (several minutes; cached after). Models download on
first use: VoxCPM2 (about 5 GB), Whisper large-v3-turbo, UTMOS22,
CommonAccent ECAPA, ECAPA speaker, emotion2vec+ large. ffmpeg with libvorbis
is needed (`FFMPEG` if it is not on the path). Takes and casting candidates
are kept in `VO_WORK` (`~/vo-tools/work`).

`backends/chatterbox_worker.py` is the Chatterbox worker used in the
research (MIT; same protocol), kept for comparison.

## Licences

VoxCPM2 (the voices): Apache 2.0. The ear models are used only to judge:
Whisper (MIT), UTMOS22 (MIT), CommonAccent and ECAPA (SpeechBrain, Apache
2.0), emotion2vec+ (FunASR model licence). Every voice is designed from a
text description; none is cloned from a real person.

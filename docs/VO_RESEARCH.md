# Voice-over: which voice generation, and why

Research for Survivor Unchained's voice-over, October 2026. The bar is
cinematic: acted, not read; breath and timing; a designed voice that stays
the same person over hundreds of lines; accents from this world (northern
and West Country English, RP, Scots, Welsh, Irish); and a licence that lets
a commercial game ship the audio. Everything here was run on this PC (RTX
5080 16 GB, shared with other work) unless it says otherwise.

## The field, as of October 2026

Artificial Analysis's TTS arena (blind preference, read speech) has
ElevenLabs v4, Qwen-Audio 3.1 Plus, Cartesia, Gemini 3.8 and Inworld at the
top: all closed, all paid. Of models with open weights, the best ranked are
non-commercial.

| Model (open weights) | Arena | Licence | Usable to ship? |
|---|---|---|---|
| Breeze TTS 2 (BreezeBlue, Aug 2026, 3B) | #10, 1216 | weights research / non-commercial | No (commercial licence on request) |
| Fish Audio S2 Pro (Mar 2026, ~4.4B) | #32, 1117 | Fish Audio Research Licence | No (paid licence) |
| Step Audio EditX (StepFun, 3B) | #39, 1095 | Apache 2.0 | Yes |
| Voxtral TTS (Mistral, 4B) | #42, 1083 | CC BY-NC 4.0 | No |
| Kokoro 82M | #53 | Apache 2.0 | Yes, but fixed voices, no acting |
| Maya1 (3B) | #61 | Apache 2.0 | Yes |
| OpenAudio S1 Mini | #63 | CC BY-NC-SA | No |
| Higgs Audio v3 (Boson, Jun 2026, 4B) | #64 | research / non-commercial | No |
| Higgs Audio v2 | not ranked | community licence, < 100k annual users | Yes, under the cap |
| Chatterbox / Turbo (Resemble) | #72 | MIT | Yes |
| VibeVoice 1.5B (Microsoft) | #78 | MIT, research-only use guidance | Doubtful |
| Qwen3-TTS 1.7B (Alibaba, Jan 2026) | #83 (API) | Apache 2.0 | Yes |
| VoxCPM2 (OpenBMB, Apr/Aug 2026, 2B, 48 kHz) | not ranked | Apache 2.0 | Yes |
| IndexTTS-2.5 (bilibili, Aug 2026) | not ranked | bilibili licence: free under 100M MAU / RMB 1bn revenue | Yes |
| AuK (Tencent, Sep 2026, 1.5B) | not ranked | MIT | Yes, but see below |
| OmniVoice (k2-fsa) | not ranked | weights CC BY-NC | No |
| F5-TTS / E2 | – | weights CC BY-NC | No |
| CosyVoice 3 | – | Apache 2.0 | Yes; Chinese-first |
| Dia / Dia2 (Nari) | – | Apache 2.0 | Yes; dialogue, weak voice identity |
| Sesame CSM-1B | – | Apache 2.0 | Yes; conversational, needs context |
| Orpheus | – | Apache 2.0 (Llama) | Yes; fixed American voices |
| Zonos v0.1 | #76 | Apache 2.0 | Yes; uneven quality |
| StyleTTS 2 | #87 | MIT | Yes; dated |

Arena scores measure pleasant read speech in stock voices. They say nothing
about acting, accents or a designed voice holding across a script, which is
what this game needs, so the shortlist was tested directly.

Sources: [Artificial Analysis TTS leaderboard](https://artificialanalysis.ai/text-to-speech/leaderboard),
[Breeze TTS 2 licence](https://www.mindstudio.ai/blog/breeze-tts-2-open-weight-release),
[Fish S2 licence](https://fish.audio/blog/what-we-mean-by-open-source-for-s2/),
[Voxtral](https://siliconangle.com/2026/03/26/mistral-releases-open-weights-speaking-AI-model-voxtral-tts/),
[Higgs v3](https://www.llmreference.com/model/higgs-audio-v3-tts),
[VoxCPM2](https://huggingface.co/openbmb/VoxCPM2), [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS),
[IndexTTS-2.5](https://huggingface.co/IndexTeam/IndexTTS-2.5),
[bilibili licence terms](https://scancode-licensedb.aboutcode.org/bilibili-model-ula-2025-09-09.html),
[AuK](https://huggingface.co/tencent/AuK), [Chatterbox Turbo](https://the-decoder.com/resemble-ai-drops-chatterbox-turbo-an-open-source-text-to-speech-model-that-clones-voices-in-five-seconds/),
[Higgs v2 community licence](https://huggingface.co/bosonai/higgs-audio-v2-tokenizer/discussions/8),
[Step-Audio-EditX](https://github.com/stepfun-ai/Step-Audio-EditX),
[OmniVoice](https://huggingface.co/k2-fsa/OmniVoice).

## How takes were judged

I have no ears, so every take is measured the way a dialogue editor
listens, by `tools/vo/analyse.py`:

- **Words**: Whisper large-v3-turbo transcribes the take; word error rate
  against the script, and which words went wrong.
- **Accent**: CommonAccent (ECAPA, trained on Common Voice) scores 16
  accents: England, Scotland, Ireland, Wales, US, Canada, Australia and
  others. A take for Rook must be heard as England.
- **Naturalness**: UTMOS22 (a MOS predictor). It is biased against old,
  child and very expressive voices, so it is a floor, not a ranking.
- **Acting**: pitch median, spread and movement (Praat), pauses, words per
  second, and the emotion emotion2vec+ large hears.
- **Identity**: ECAPA speaker similarity to the part's reference.
- **Faults**: clipping, a cut at the head or tail, a hissy or buzzy voice,
  dead air.

The accent classifier was checked first: the same designed man asked for
in five accents (General American, RP, Yorkshire, Glaswegian, Dublin) by
each model.

## Results

### Accent control (the deciding test)

| Asked for | Qwen3-TTS VoiceDesign | VoxCPM2 voice design |
|---|---|---|
| General American | US 1.00 / US 1.00 | US 1.00 / US 0.84 |
| RP | US 1.00 / US 1.00 | Australia 0.89 / England 1.00 |
| Yorkshire | US 1.00 / US 1.00 | England 1.00 / England 1.00 |
| Glaswegian | US 1.00 / US 0.96 | Scotland 0.89 / England 1.00 |
| Dublin Irish | US 0.99 / US 1.00 | England 0.99 / England 1.00 |

(two seeds each; the accent CommonAccent hears and its probability)

Qwen3-TTS ignores accent in its voice description: every voice it designs
is American. It is the cleanest model on paper (UTMOS 4.3 to 4.5) and the
fastest to set up (its weights were already here, in ComfyUI's models), but
an American Mother Rook is not Mother Rook. VoxCPM2 does what it is asked
most of the time; Irish comes out as English, so Chid's Irish tinge has to
be found by casting more candidates.

### Voice design, the same seven parts in both

VoxCPM2 is less consistent than Qwen3 from seed to seed (some candidates
are broken: a 400 Hz squeak where Rook should be, UTMOS 1.3), but its good
candidates are in the right accent, at a storyteller's pace (2.3 to 2.8
words a second for the narrator; Qwen3 reads him at 3.4), and at 48 kHz.
Casting therefore auditions many candidates per part and keeps the best by
the numbers above (`tools/vo/cast_session.py`).

### Cloning a designed voice with direction

IndexTTS-2.5 (emotion by vector or by text, timbre from a reference) was
given VoxCPM2's designed voices as references. It loses the accent (every
take is heard as American, including the heroine whose reference is heard
as England 1.00), drifts in pitch (Rook's 209 Hz reference comes back at
285 to 292 Hz), and clips on shouted lines. Its emotion control is real but
it does not keep the person.

### Directing a cloned voice: style against continuation

Rook's cast voice, four of her lines with direction, three seeds each
(`rook`, 208 Hz reference, heard as England):

| How | Speaker match | UTMOS | England | Pitch | Words/s | Clean |
|---|---|---|---|---|---|---|
| VoxCPM2, styled clone, 10 steps | 0.70 | 2.81 | 0.81 | 236 Hz | 3.8 | 4/6 |
| VoxCPM2, styled clone, 25 steps | 0.73 | 3.05 | 0.75 | 231 Hz | 3.8 | 5/6 |
| VoxCPM2, styled clone, 25 steps, guidance 1.5 | 0.67 | 2.74 | 0.47 | 218 Hz | 3.5 | 3/6 |
| VoxCPM2, continuation + style | 0.87 | 3.35 | 0.94 | 213 Hz | 3.0 | 0/6 (says the style aloud) |
| VoxCPM2, continuation | 0.86 | 3.51 | 0.72 | 201 Hz | 4.3 | 6/6 |
| Chatterbox (MIT), exaggeration from direction | 0.80 | 3.88 | 0.47 | 175 Hz | 3.6 | 12/12 |

- **Styled cloning** acts (the style moves pace and weight) but the person
  drifts: pitch climbs 20 to 40 Hz, the accent slips on short lines, and
  the speaker match drops to around 0.7.
- **Continuation** (VoxCPM2 carries on from a take of the voice and its
  transcript) keeps the person (0.86 to 0.91) and the accent, with the best
  naturalness of the VoxCPM2 modes; but it speaks in the manner of the take
  it continues, and a style in brackets is read out as words.
- **Chatterbox** is the cleanest by UTMOS and harmonics-to-noise, but it
  pulls every voice toward its own prior (Rook drops 30 Hz) and loses the
  accent on half the lines (heard as American). Its only acting control is
  one intensity number.
- emotion2vec hears nearly every Rook take as "angry", whatever was asked:
  her designed timbre reads that way to it. It is reported, not used to
  choose.

So the pipeline does both, in that order: each voice gets a small bank of
itself in five moods (warm, quiet, hard, quick, hushed), made by styled
cloning and kept only where it is still plainly the same person in the same
accent at the mood's pace (`tools/vo/registers.py`); every line is then
spoken by continuation from the mood its direction calls for. Rook's
"Nothing. She paid me double." continued from her quiet take runs at 2.9
words a second; from her resting take, at 3.9.

### Accents beyond England

The deciding failure. Asked in every wording tried (three phrasings each,
two seeds), VoxCPM2's voice design produced no take heard as Irish (0 of 6)
or Welsh (0 of 4), and Scots in 1 of 8 (Glaswegian, in the first accent
test; 0 of 6 in the second). Qwen3-TTS produced American for all of them.
CommonAccent does recognise Scots from VoxCPM2 when it is there (0.89), so
this is the model, not the ear. Rav, Redcowl and Ysolde (Scots), Chid
(Irish) and Maeca (Welsh) cannot be cast locally as written; see
`VO_CAST.md` for what was done and what is recommended.

### Not run locally

- **AuK** (MIT, instruction-driven generation and emotion editing) needs
  about 25 GB of VRAM (17 GB with offload): not on a shared 16 GB card.
- **Breeze 2, Fish S2, Higgs v3, Voxtral**: excluded by licence, whatever
  they sound like.
- **Kokoro, Orpheus, Dia, CSM, Zonos, StyleTTS 2, F5**: fixed voices,
  non-commercial weights, or quality well below the shortlist.

## Speed on this machine

The card and the CPU are shared with other agents' work (ComfyUI image jobs,
Blender, test runs), so times varied by ten times over a day.

| Model | Real-time factor, quiet machine | Busy machine | VRAM |
|---|---|---|---|
| VoxCPM2, eager | ~1.5 | 3 to 15 | 5.5 GB |
| Qwen3-TTS 1.7B (no flash-attn) | ~3 | 5 to 30 | 4.7 GB |
| IndexTTS-2.5 bf16 | ~0.8 | 3+ | 7.6 GB |

## Choice

**VoxCPM2** (Apache 2.0) for every part: voice design to cast each part,
then cloning from that designed reference, line by line, with the
direction as a style instruction. It is the only commercially usable local
model that holds the world's accents, and its 48 kHz output is the best
source for a mix. The acting tests follow below.

"""Listen to takes the way a dialogue editor would, with numbers.

For each wav: the words actually said (Whisper large-v3-turbo) and how far
they are from the script, the pitch contour (Praat: median, spread and range
in semitones, how much it moves), the pauses, the speaking rate, a naturalness
score (UTMOS22), the accent heard (CommonAccent ECAPA), the emotion heard
(emotion2vec+ large), and the artefacts a mixer would hear: clipping, a hard
cut at the head or tail, a buzzy or noisy tail, long dead air.

    python tools/vo/analyse.py <wav or dir> [--text "script"] [--json out.json]

Used as a library by produce.py, which loads each model once.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass, asdict, field

import numpy as np
import soundfile as sf

_whisper = None
_utmos = None
_accent = None
_emotion = None
_spk = None
DEVICE = "cuda"


# ------------------------------------------------------------------ text --

_NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
        "8": "eight", "9": "nine", "10": "ten", "11": "eleven", "12": "twelve", "20": "twenty", "30": "thirty",
        "40": "forty", "41": "forty one", "50": "fifty", "100": "a hundred"}


_CONTRACT = [(r"n't\b", " not"), (r"'ll\b", " will"), (r"'ve\b", " have"), (r"'re\b", " are"), (r"'m\b", " am"),
             (r"'d\b", " would"), (r"\bcan not\b", "cannot"), (r"\bwo not\b", "will not"), (r"\bca not\b", "can not")]
_lex = None


def lexicon() -> dict:
    global _lex
    if _lex is None:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lexicon.json")
        _lex = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"say": {}, "hear": {}}
    return _lex


def norm_words(s: str) -> list[str]:
    """Words as a listener hears them: no punctuation, case, stage directions
    or contractions; names Whisper spells its own way taken as said right."""
    s = re.sub(r"\([^)]*\)", " ", s)          # stage directions are not said by the speaker
    s = s.replace("’", "'").replace("‘", "'").lower()
    for a, b in _CONTRACT:
        s = re.sub(a, b, s)
    s = re.sub(r"'s\b", "s", s)
    s = re.sub(r"[—–-]", " ", s)
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    s = " " + " ".join(s.split()) + " "
    for canon, heard in lexicon().get("hear", {}).items():
        for h in sorted(heard, key=len, reverse=True):
            s = s.replace(f" {h} ", f" {canon} ").replace(f" {h}s ", f" {canon}s ")
    words = []
    for w in s.split():
        w = w.strip("'")
        if not w:
            continue
        if w in _NUM:
            words.extend(_NUM[w].split())
        else:
            words.append(w)
    return words


def _near(a: str, b: str) -> bool:
    """Two spellings of one word (Whisper's guess at a name, a dialect word)."""
    if a == b:
        return True
    if min(len(a), len(b)) < 4:
        return False
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.75


def substantive(wrong: list[str]) -> list[str]:
    """The errors a listener would hear: a dropped or added word, or a
    different word; not a near-spelling of the same one, nor 'oh' and 'ha'."""
    out = []
    fill = {"oh", "ah", "ha", "hah", "um", "uh", "eh", "hm", "hmm", "mm", "huh", "oho", "oi"}
    # A compound written whole on one side and as two words on the other
    # ("saw-bones" heard as "sawbones"): '-saw' then 'bones->sawbones'.
    wrong = list(wrong)
    i = 0
    while i < len(wrong) - 1:
        a, b = wrong[i], wrong[i + 1]
        if a.startswith("-") and "->" in b and b.split("->")[1] == a[1:] + b.split("->")[0]:
            del wrong[i:i + 2]; continue
        if "->" in a and b.startswith("-") and a.split("->")[1] == a.split("->")[0] + b[1:]:
            del wrong[i:i + 2]; continue
        if a.startswith("+") and "->" in b and b.split("->")[0] == a[1:] + b.split("->")[1]:
            del wrong[i:i + 2]; continue
        if "->" in a and b.startswith("+") and a.split("->")[0] == a.split("->")[1] + b[1:]:
            del wrong[i:i + 2]; continue
        i += 1
    for w in wrong:
        if "->" in w:
            a, b = w.split("->")
            if _near(a, b):
                continue
        elif w[1:] in fill:
            continue
        out.append(w)
    return out


def wer(ref: str, hyp: str) -> tuple[float, list[str]]:
    """Word error rate and the words that went wrong (substituted or dropped)."""
    r, h = norm_words(ref), norm_words(hyp)
    if not r:
        return 0.0, []
    # Levenshtein with backtrace.
    d = np.zeros((len(r) + 1, len(h) + 1), dtype=np.int32)
    d[:, 0] = np.arange(len(r) + 1)
    d[0, :] = np.arange(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    i, j, bad = len(r), len(h), []
    while i > 0 and j > 0:
        if r[i - 1] == h[j - 1] and d[i, j] == d[i - 1, j - 1]:
            i, j = i - 1, j - 1
        elif d[i, j] == d[i - 1, j - 1] + 1:
            bad.append(f"{r[i-1]}->{h[j-1]}"); i, j = i - 1, j - 1
        elif d[i, j] == d[i - 1, j] + 1:
            bad.append(f"-{r[i-1]}"); i -= 1
        else:
            bad.append(f"+{h[j-1]}"); j -= 1
    bad += [f"-{w}" for w in r[:i]] + [f"+{w}" for w in h[:j]]
    return d[len(r), len(h)] / len(r), list(reversed(bad))


# --------------------------------------------------------------- models --

def whisper():
    global _whisper
    if _whisper is None:
        import torch
        from transformers import pipeline
        _whisper = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo",
                            torch_dtype=torch.float16, device=DEVICE)
    return _whisper


def transcribe(wav: np.ndarray, sr: int) -> str:
    import librosa
    a = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else wav.astype(np.float32)
    long = len(a) > 29 * 16000  # a long speech is heard in pieces
    out = whisper()({"raw": a, "sampling_rate": 16000}, generate_kwargs={"language": "english", "task": "transcribe"},
                    **({"return_timestamps": True, "chunk_length_s": 28} if long else {}))
    return out["text"].strip()


def utmos(wav: np.ndarray, sr: int) -> float:
    global _utmos
    import torch
    if _utmos is None:
        _utmos = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True).to(DEVICE).eval()
    import librosa
    a = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else wav.astype(np.float32)
    with torch.no_grad():
        return float(_utmos(torch.from_numpy(a)[None].to(DEVICE), 16000)[0])


def accent(wav: np.ndarray, sr: int) -> tuple[str, float, dict]:
    """The accent CommonAccent hears, its confidence, and the top three."""
    global _accent
    import torch
    import librosa
    if _accent is None:
        from speechbrain.inference.classifiers import EncoderClassifier
        from speechbrain.utils.fetching import LocalStrategy
        _accent = EncoderClassifier.from_hparams(source="Jzuluaga/accent-id-commonaccent_ecapa", local_strategy=LocalStrategy.COPY,
                                                 savedir=os.path.expanduser("~/.cache/vo/accent"), run_opts={"device": DEVICE})
    a = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else wav.astype(np.float32)
    with torch.no_grad():
        out_prob, score, index, label = _accent.classify_batch(torch.from_numpy(a)[None])
    # The ECAPA head scores each accent by cosine similarity; trained with
    # an additive-margin softmax at scale 30, so that is the scale to read it at.
    probs = torch.softmax(out_prob[0].float() * 30, -1).cpu().numpy()
    labels = _accent.hparams.label_encoder.decode_ndim(list(range(len(probs))))
    top = sorted(zip(labels, probs.tolist()), key=lambda x: -x[1])[:3]
    return label[0], float(top[0][1]), {k: round(v, 3) for k, v in top}


def emotion(wav: np.ndarray, sr: int) -> dict:
    """emotion2vec+ large: the probability of each emotion it knows."""
    global _emotion
    import librosa
    if _emotion is None:
        from funasr import AutoModel
        _emotion = AutoModel(model="iic/emotion2vec_plus_large", hub="ms", disable_update=True, device=DEVICE)
    a = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else wav.astype(np.float32)
    res = _emotion.generate(a, granularity="utterance", extract_embedding=False, disable_pbar=True)[0]
    out = {}
    for lab, sc in zip(res["labels"], res["scores"]):
        name = lab.split("/")[-1]
        out[name] = round(float(sc), 3)
    return out


def speaker_embedding(wav: np.ndarray, sr: int) -> np.ndarray:
    """ECAPA speaker embedding, for checking a voice holds across takes."""
    global _spk
    import torch
    import librosa
    if _spk is None:
        from speechbrain.inference.speaker import EncoderClassifier
        from speechbrain.utils.fetching import LocalStrategy
        _spk = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", local_strategy=LocalStrategy.COPY,
                                              savedir=os.path.expanduser("~/.cache/vo/ecapa"), run_opts={"device": DEVICE})
    a = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else wav.astype(np.float32)
    with torch.no_grad():
        e = _spk.encode_batch(torch.from_numpy(a)[None])[0, 0].cpu().numpy()
    return e / (np.linalg.norm(e) + 1e-9)


# --------------------------------------------------------------- signal --

def pitch(wav: np.ndarray, sr: int, floor=60, ceil=500) -> dict:
    import parselmouth
    snd = parselmouth.Sound(wav.astype(np.float64), sampling_frequency=sr)
    p = snd.to_pitch_ac(time_step=0.01, pitch_floor=floor, pitch_ceiling=ceil)
    f = p.selected_array["frequency"]
    f = f[f > 0]
    if len(f) < 10:
        return dict(f0_median=0, f0_sd_st=0, f0_range_st=0, voiced=0, f0_move_st=0)
    st = 12 * np.log2(f / np.median(f))
    lo, hi = np.percentile(st, [5, 95])
    # How much the contour moves: mean absolute slope in semitones per 100 ms
    # over voiced frames. Flat, robotic reads sit low; sing-song reads high.
    move = float(np.mean(np.abs(np.diff(st)))) * 10
    return dict(f0_median=round(float(np.median(f)), 1), f0_sd_st=round(float(np.std(st)), 2),
                f0_range_st=round(float(hi - lo), 2), voiced=round(len(f) / max(1, len(p.selected_array)), 2),
                f0_move_st=round(move, 2))


def frames_db(wav: np.ndarray, sr: int, hop=0.01, win=0.03) -> np.ndarray:
    h, w = int(sr * hop), int(sr * win)
    n = max(1, (len(wav) - w) // h + 1)
    idx = np.arange(w)[None, :] + h * np.arange(n)[:, None]
    seg = wav[np.clip(idx, 0, len(wav) - 1)]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2, axis=1)) + 1e-9)


def pauses(wav: np.ndarray, sr: int, thresh_rel=-38.0, min_len=0.18) -> dict:
    """Silences inside the line (not the head or tail), in seconds."""
    db = frames_db(wav, sr)
    peak = np.percentile(db, 99)
    voiced = db > peak + thresh_rel
    if not voiced.any():
        return dict(head=0, tail=0, pauses=[], longest=0, speech=0)
    first, last = np.argmax(voiced), len(voiced) - 1 - np.argmax(voiced[::-1])
    runs, cur = [], 0
    for v in voiced[first:last + 1]:
        if not v:
            cur += 1
        else:
            if cur * 0.01 >= min_len:
                runs.append(round(cur * 0.01, 2))
            cur = 0
    return dict(head=round(first * 0.01, 2), tail=round((len(voiced) - 1 - last) * 0.01, 2), pauses=runs,
                longest=max(runs) if runs else 0, speech=round((last - first) * 0.01, 2))


def artefacts(wav: np.ndarray, sr: int) -> list[str]:
    """Things a mixer would reject the take for."""
    bad = []
    peak = float(np.max(np.abs(wav))) if len(wav) else 0
    if peak >= 0.999:
        clipped = np.mean(np.abs(wav) >= 0.999)
        if clipped > 1e-4:
            bad.append(f"clipping {clipped:.4%}")
    db = frames_db(wav, sr)
    if len(db) > 20:
        if db[-1] > np.percentile(db, 99) - 20:
            bad.append("cut off at the tail")
        if db[0] > np.percentile(db, 99) - 20:
            bad.append("cut off at the head")
    # Buzz or hiss: spectral flatness of the quietest voiced-looking frames.
    try:
        import librosa
        flat = librosa.feature.spectral_flatness(y=wav.astype(np.float32), n_fft=2048, hop_length=512)[0]
        rms = librosa.feature.rms(y=wav.astype(np.float32), frame_length=2048, hop_length=512)[0]
        loud = rms > np.percentile(rms, 60)
        if loud.any() and np.median(flat[loud]) > 0.08:
            bad.append(f"noisy/whispery voice (flatness {np.median(flat[loud]):.2f})")
    except Exception:
        pass
    return bad


# ---------------------------------------------------------------- whole --

@dataclass
class Report:
    path: str
    seconds: float
    said: str = ""
    wer: float = 0.0
    wrong: list = field(default_factory=list)
    faults: list = field(default_factory=list)
    words_per_sec: float = 0.0
    utmos: float = 0.0
    accent: str = ""
    accent_p: float = 0.0
    accent_top: dict = field(default_factory=dict)
    emotion: dict = field(default_factory=dict)
    pitch: dict = field(default_factory=dict)
    pauses: dict = field(default_factory=dict)
    artefacts: list = field(default_factory=list)


def _retry(fn, *args, tries: int = 4):
    """The card is shared: a CUDA error under someone else's load is waited
    out and tried again, not taken as the take's fault."""
    import time
    import torch
    for i in range(tries):
        try:
            return fn(*args)
        except RuntimeError as e:
            if "CUDA" not in str(e) and "cuDNN" not in str(e) and "CUDNN" not in str(e) or i == tries - 1:
                raise
            torch.cuda.empty_cache()
            time.sleep(5 * (i + 1))


def analyse(path: str, text: str | None = None, want=("asr", "utmos", "accent", "emotion")) -> Report:
    wav, sr = sf.read(path, dtype="float32", always_2d=False)
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    r = Report(path=path, seconds=round(len(wav) / sr, 2))
    if "asr" in want:
        r.said = _retry(transcribe, wav, sr)
        if text:
            r.wer, r.wrong = wer(text, r.said)
            r.wer = round(r.wer, 3)
            r.faults = substantive(r.wrong)
    r.pauses = pauses(wav, sr)
    nwords = len(norm_words(text or r.said))
    if r.pauses.get("speech"):
        r.words_per_sec = round(float(nwords / max(0.5, r.pauses["speech"] - sum(r.pauses["pauses"]))), 2)
    r.pitch = pitch(wav, sr)
    if "utmos" in want:
        r.utmos = round(_retry(utmos, wav, sr), 2)
    if "accent" in want:
        r.accent, r.accent_p, r.accent_top = _retry(accent, wav, sr)
    if "emotion" in want:
        r.emotion = _retry(emotion, wav, sr)
    r.artefacts = artefacts(wav, sr)
    return r


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--text")
    ap.add_argument("--texts", help="json {stem: text} for a directory")
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    texts = json.load(open(a.texts, encoding="utf-8")) if a.texts else {}
    paths = [a.path] if os.path.isfile(a.path) else sorted(
        os.path.join(a.path, f) for f in os.listdir(a.path) if f.endswith(".wav"))
    out = []
    for p in paths:
        stem = os.path.splitext(os.path.basename(p))[0]
        t = a.text or next((v for k, v in texts.items() if stem.startswith(k)), None)
        r = analyse(p, t)
        out.append(asdict(r))
        print(json.dumps(asdict(r), ensure_ascii=False), flush=True)
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1:])

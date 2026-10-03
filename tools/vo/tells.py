"""The tells of generated speech, measured: what makes a take sound made.

A listener hears these before they can name them. Each is a number here,
from the take and Whisper's word timings:

  flat prosody      pitch spread across the take (semitones) and how far
                    each word's pitch moves from its neighbours'
  even pacing       how much the speed changes from phrase to phrase
                    (coefficient of variation): people rush and hold back
  even stress       how much louder the strong words are than the weak
                    (spread of word loudness, dB): a reader stresses all
  no breath         breaths and mouth sounds between phrases
  sheen             harmonics-to-noise (dB) and how tonal the 4-8 kHz band
                    is in voiced speech (spectral flatness: real breathy
                    air is noisy; a vocoder's is too clean)
  dead air          the longest silence inside the line

    python tools/vo/tells.py take.wav [--text "the words"]
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyse  # noqa: E402

_asr_words = None


def word_times(wav: np.ndarray, sr: int) -> list[tuple[str, float, float]]:
    global _asr_words
    import librosa
    if _asr_words is None:
        _asr_words = analyse.whisper()
    a = librosa.resample(wav.astype(np.float32), orig_sr=sr, target_sr=16000) if sr != 16000 else wav.astype(np.float32)
    out = _asr_words({"raw": a, "sampling_rate": 16000}, return_timestamps="word",
                     generate_kwargs={"language": "english", "task": "transcribe"})
    words = []
    for c in out.get("chunks", []):
        s, e = c["timestamp"]
        if s is None:
            continue
        words.append((c["text"].strip(), float(s), float(e if e is not None else s + 0.3)))
    return words


def tells(path: str) -> dict:
    import librosa
    import parselmouth
    x, sr = sf.read(path, dtype="float32", always_2d=False)
    if x.ndim > 1:
        x = x.mean(1)
    words = word_times(x, sr)
    snd = parselmouth.Sound(x.astype(np.float64), sampling_frequency=sr)
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=60, pitch_ceiling=500)
    f = pitch.selected_array["frequency"]
    t = pitch.xs()
    voiced = f > 0
    st = np.full_like(f, np.nan)
    if voiced.sum() > 5:
        st[voiced] = 12 * np.log2(f[voiced] / np.median(f[voiced]))
    # Per word: its pitch, its loudness.
    wp, wl = [], []
    for w, s, e in words:
        m = (t >= s) & (t <= e)
        if np.any(m & voiced):
            wp.append(np.nanmedian(st[m & voiced]))
        seg = x[int(s * sr): max(int(s * sr) + 1, int(e * sr))]
        if len(seg):
            wl.append(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9))
    # Phrases: words split where the gap is a pause.
    phrases, cur = [], []
    for i, wd in enumerate(words):
        if cur and wd[1] - cur[-1][2] > 0.18:
            phrases.append(cur); cur = []
        cur.append(wd)
    if cur:
        phrases.append(cur)
    rates = [len(p) / max(0.2, p[-1][2] - p[0][1]) for p in phrases if len(p) >= 2]
    gaps = [b[1] - a[2] for a, b in zip(words, words[1:])]
    # Breaths: noisy, unvoiced energy in a gap, well under the speech.
    breaths = 0
    env = 20 * np.log10(np.sqrt(np.convolve(x * x, np.ones(int(0.02 * sr)) / int(0.02 * sr), mode="same")) + 1e-9)
    peak = np.percentile(env, 99)
    edges = [(0.0, words[0][1])] if words else []
    edges += [(a[2], b[1]) for a, b in zip(words, words[1:]) if b[1] - a[2] > 0.15]
    for s, e in edges:
        seg = env[int(s * sr): int(e * sr)]
        if len(seg) > int(0.1 * sr) and np.percentile(seg, 90) > peak - 38:
            breaths += 1
    # Sheen: harmonicity and the 4-8 kHz band's flatness in voiced frames.
    h = snd.to_harmonicity_cc(0.01, 75, 0.1, 1.0)
    hv = h.values[h.values > -100]
    S = np.abs(librosa.stft(x, n_fft=2048, hop_length=512)) ** 2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    band = S[(freqs >= 4000) & (freqs <= min(8000, sr / 2 - 1))]
    rms = librosa.feature.rms(y=x, frame_length=2048, hop_length=512)[0]
    loud = rms > np.percentile(rms, 50)
    flat = np.exp(np.mean(np.log(band + 1e-12), axis=0)) / (np.mean(band, axis=0) + 1e-12)
    return {
        "words": len(words),
        "pitch_spread_st": round(float(np.nanstd(st)), 2) if voiced.sum() > 5 else 0.0,
        "word_pitch_moves_st": round(float(np.mean(np.abs(np.diff(wp)))), 2) if len(wp) > 2 else 0.0,
        "pace_variation": round(float(np.std(rates) / np.mean(rates)), 2) if len(rates) >= 2 else 0.0,
        "stress_spread_db": round(float(np.std(wl)), 2) if len(wl) > 2 else 0.0,
        "breaths": breaths,
        "hnr_db": round(float(np.mean(hv)), 1) if len(hv) else 0.0,
        "hf_flatness": round(float(np.median(flat[loud])), 3) if loud.any() else 0.0,
        "longest_gap_s": round(float(max(gaps)) if gaps else 0.0, 2),
        "said": " ".join(w for w, _, _ in words),
    }


if __name__ == "__main__":
    print(json.dumps(tells(sys.argv[1]), indent=1))

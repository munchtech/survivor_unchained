"""Shoot-out takes from VibeVoice 1.5B (Microsoft's weights, MIT; run through
the community fork's code since Microsoft withdrew its own): long-form,
conversational speech trained on podcasts, cloning a voice prompt.
`vibe` clones the part's cast reference; `vibe-acted` clones an acted take of
the line already in the cast voice (as run_voicebox.py does).

    ~/vo-tools/vibevoice/Scripts/python tools/vo/shootout/run_vibevoice.py
"""
import json
import os
import sys

import soundfile as sf
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools"))
RAW = os.path.join(TOOLS, "shootout", "raw")
REFS = os.path.join(os.path.dirname(HERE), "refs")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
ACTED = ("dia-vc", "orpheus-vcf0", "orpheus-vc", "vox_design-vc")

from vibevoice.modular.modeling_vibevoice_inference import VibeVoiceForConditionalGenerationInference  # noqa: E402
from vibevoice.processor.vibevoice_processor import VibeVoiceProcessor  # noqa: E402


def wav24(src: str, name: str) -> str:
    import librosa
    out = os.path.join(TOOLS, "shootout", "vibe_refs", name + ".wav")
    if not os.path.exists(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        x, sr = sf.read(src, dtype="float32")
        if x.ndim > 1:
            x = x.mean(1)
        sf.write(out, librosa.resample(x, orig_sr=sr, target_sr=24000), 24000)
    return out


def acted_ref(key: str):
    heard_path = os.path.join(TOOLS, "shootout", "heard.json")
    heard = json.load(open(heard_path, encoding="utf-8")) if os.path.exists(heard_path) else {}
    for method in ACTED:
        takes = [(k, r) for k, r in heard.items()
                 if k.replace("\\", "/").startswith(f"{key}/{method}_s") and not r.get("faults")]
        if takes:
            k, _ = max(takes, key=lambda kr: kr[1]["tells"]["pace_variation"] + kr[1]["similarity"])
            return os.path.join(RAW, k)
    return None


def main():
    name = "microsoft/VibeVoice-1.5B"
    proc = VibeVoiceProcessor.from_pretrained(name)
    model = VibeVoiceForConditionalGenerationInference.from_pretrained(
        name, torch_dtype=torch.bfloat16, device_map="cuda", attn_implementation="sdpa").eval()
    model.set_ddpm_inference_steps(num_steps=10)
    for key, L in LINES.items():
        refs = {"vibe": wav24(os.path.join(REFS, f"{L['voice']}.flac"), L["voice"])}
        acted = acted_ref(key)
        if acted:
            refs["vibe-acted"] = wav24(acted, f"{key}_acted")
        for method, ref in refs.items():
            for s in (1, 2, 3):
                out = os.path.join(RAW, key, f"{method}_s{s}.wav")
                if os.path.exists(out):
                    continue
                torch.manual_seed(s)
                inputs = proc(text=[f"Speaker 1: {L['text']}"], voice_samples=[[ref]], padding=True,
                              return_tensors="pt", return_attention_mask=True)
                inputs = {k: (v.to("cuda") if torch.is_tensor(v) else v) for k, v in inputs.items()}
                with torch.inference_mode():
                    o = model.generate(**inputs, max_new_tokens=None, cfg_scale=1.3, tokenizer=proc.tokenizer,
                                       generation_config={"do_sample": False}, verbose=False, is_prefill=True)
                proc.save_audio(o.speech_outputs[0], output_path=out)
                print(key, method, s, flush=True)


if __name__ == "__main__":
    sys.exit(main())

"""Shoot-out takes from Maya1 (Maya Research, Apache 2.0, 3B): a voice
designed from a sentence (age, accent, timbre, pace, tone) acting the line
with inline emotion tags (<sigh>, <angry>, <giggle>, <chuckle>, <cry>).
Its voices are designed, not ours, so it is also converted to the cast voice
(run_vc.py maya).

Runs in the Orpheus venv (transformers + SNAC):
    ~/vo-tools/orpheus/Scripts/python tools/vo/shootout/run_maya.py [seeds]
"""
import json
import os
import sys

import soundfile as sf
import torch
from snac import SNAC
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools")), "shootout", "raw")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
NAME = "maya-research/maya1"
# The model card's token ids: start/end of human turn, start of audio, start
# and end of speech; SNAC codes from CODE_OFFSET, seven a frame.
SOH, EOH, SOA, SOS, EOS, EOT = 128259, 128260, 128261, 128257, 128258, 128009
CODE_OFFSET, CODE_MAX = 128266, 156937

tok = AutoTokenizer.from_pretrained(NAME)
model = AutoModelForCausalLM.from_pretrained(NAME, torch_dtype=torch.bfloat16).cuda().eval()
snac = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").cuda().eval()


def prompt(description: str, text: str) -> str:
    d = tok.decode
    return d([SOH]) + tok.bos_token + f'<description="{description}"> {text}' + d([EOT]) + d([EOH]) + d([SOA]) + d([SOS])


def decode(ids: list[int]):
    if EOS in ids:
        ids = ids[: ids.index(EOS)]
    codes = [t for t in ids if CODE_OFFSET <= t <= CODE_MAX]
    codes = codes[: len(codes) // 7 * 7]
    l1, l2, l3 = [], [], []
    for i in range(len(codes) // 7):
        s = [(c - CODE_OFFSET) % 4096 for c in codes[7 * i: 7 * i + 7]]
        l1.append(s[0]); l2 += [s[1], s[4]]; l3 += [s[2], s[3], s[5], s[6]]
    z = [torch.tensor(l, dtype=torch.long, device="cuda").unsqueeze(0) for l in (l1, l2, l3)]
    with torch.inference_mode():
        audio = snac.decoder(snac.quantizer.from_codes(z))[0, 0].float().cpu().numpy()
    return audio[2048:]  # the decoder's warm-up


def main(seeds):
    for key, L in LINES.items():
        description, text = L["maya"]
        d = os.path.join(RAW, key)
        os.makedirs(d, exist_ok=True)
        for s in seeds:
            out = os.path.join(d, f"maya_s{s}.wav")
            if os.path.exists(out):
                continue
            torch.manual_seed(s)
            ids = tok(prompt(description, text), return_tensors="pt", add_special_tokens=False).input_ids.cuda()
            with torch.inference_mode():
                g = model.generate(ids, max_new_tokens=2400, min_new_tokens=28, do_sample=True, temperature=0.4, top_p=0.9,
                                   repetition_penalty=1.1, eos_token_id=EOS, pad_token_id=tok.pad_token_id or EOS)
            audio = decode(g[0, ids.shape[1]:].tolist())
            sf.write(out, audio, 24000)
            print(key, s, f"{len(audio) / 24000:.1f} s", flush=True)


if __name__ == "__main__":
    main([int(s) for s in sys.argv[1:]] or [1, 2, 3, 4])

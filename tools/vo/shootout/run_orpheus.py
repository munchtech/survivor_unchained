"""Shoot-out takes from Orpheus 3B (Canopy Labs, Apache 2.0; an ungated
mirror): its stock American voices with emotive tags (<sigh>, <chuckle>,
<sniffle>). Used as a performance to convert to the cast voice (run_vc.py),
not as the cast voice itself."""
import json
import os

import soundfile as sf
import torch
from snac import SNAC
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.environ.get("VO_TOOLS", os.path.expanduser("~/vo-tools")), "shootout", "raw")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
NAME = "unsloth/orpheus-3b-0.1-ft"
tok = AutoTokenizer.from_pretrained(NAME)
model = AutoModelForCausalLM.from_pretrained(NAME, torch_dtype=torch.bfloat16).cuda().eval()
snac = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").cuda().eval()


def decode(codes):
    # Orpheus: 7 tokens a frame, spread over SNAC's three codebooks.
    l1, l2, l3 = [], [], []
    for i in range(len(codes) // 7):
        c = codes[7 * i: 7 * i + 7]
        l1.append(c[0]); l2.append(c[1] - 4096); l3.append(c[2] - 2 * 4096); l3.append(c[3] - 3 * 4096)
        l2.append(c[4] - 4 * 4096); l3.append(c[5] - 5 * 4096); l3.append(c[6] - 6 * 4096)
    z = [torch.tensor(l, device="cuda").unsqueeze(0) for l in (l1, l2, l3)]
    with torch.no_grad():
        return snac.decode(z).squeeze().cpu().numpy()


for key, L in LINES.items():
    voice, text = L["orpheus"]
    d = os.path.join(RAW, key)
    os.makedirs(d, exist_ok=True)
    for s in (1, 2, 3):
        out = os.path.join(d, f"orpheus_s{s}.wav")
        if os.path.exists(out):
            continue
        torch.manual_seed(s)
        ids = tok(f"{voice}: {text}", return_tensors="pt").input_ids
        ids = torch.cat([torch.tensor([[128259]]), ids, torch.tensor([[128009, 128260]])], dim=1).cuda()
        with torch.no_grad():
            g = model.generate(ids, max_new_tokens=2400, do_sample=True, temperature=0.6, top_p=0.95, repetition_penalty=1.1,
                               eos_token_id=128258)
        row = g[0, ids.shape[1]:].tolist()
        if 128257 in row:
            row = row[len(row) - row[::-1].index(128257):]
        codes = [t - 128266 for t in row if t not in (128258,) and t >= 128266]
        codes = codes[: len(codes) // 7 * 7]
        sf.write(out, decode(codes), 24000)
        print(key, s, flush=True)

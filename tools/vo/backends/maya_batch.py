"""Maya1 performances in batches (runs in the Orpheus venv: transformers + SNAC).

Maya1 (Maya Research, Apache 2.0, 3B) acts a line in a voice designed from
one sentence, with inline emotion tags. Decoding is memory-bound, so lines of
similar length are generated together: about eight at the cost of one.

    python maya_batch.py jobs.json [--batch 8]

jobs.json: [{"out": wav path, "description": ..., "text": ..., "seed": int}, ...]
Jobs whose `out` exists are skipped. Prints one JSON line per finished job.
"""
import argparse
import json
import os
import sys
import time

import soundfile as sf
import torch
from snac import SNAC
from transformers import AutoModelForCausalLM, AutoTokenizer

NAME = "maya-research/maya1"
SOH, EOH, SOA, SOS, EOS, EOT = 128259, 128260, 128261, 128257, 128258, 128009
CODE_OFFSET, CODE_MAX = 128266, 156937
SR = 24000
TOKENS_PER_SEC = 86  # SNAC 24 kHz: seven codes a frame, about twelve frames a second


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--batch", type=int, default=8)
    a = ap.parse_args()
    jobs = [j for j in json.load(open(a.jobs, encoding="utf-8")) if not os.path.exists(j["out"])]
    if not jobs:
        return
    tok = AutoTokenizer.from_pretrained(NAME)
    tok.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(NAME, dtype=torch.bfloat16).cuda().eval()
    snac = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").cuda().eval()
    d = tok.decode
    head = d([SOH]) + tok.bos_token
    tail = d([EOT]) + d([EOH]) + d([SOA]) + d([SOS])

    def decode(ids):
        if EOS in ids:
            ids = ids[: ids.index(EOS)]
        codes = [t for t in ids if CODE_OFFSET <= t <= CODE_MAX]
        codes = codes[: len(codes) // 7 * 7]
        if len(codes) < 28:
            return None
        l1, l2, l3 = [], [], []
        for i in range(len(codes) // 7):
            s = [(c - CODE_OFFSET) % 4096 for c in codes[7 * i: 7 * i + 7]]
            l1.append(s[0]); l2 += [s[1], s[4]]; l3 += [s[2], s[3], s[5], s[6]]
        z = [torch.tensor(l, dtype=torch.long, device="cuda").unsqueeze(0) for l in (l1, l2, l3)]
        with torch.inference_mode():
            return snac.decoder(snac.quantizer.from_codes(z))[0, 0].float().cpu().numpy()[2048:]

    # Similar lengths together, so a batch finishes about when its longest line does.
    jobs.sort(key=lambda j: len(j["text"]))
    for b in range(0, len(jobs), a.batch):
        group = jobs[b: b + a.batch]
        t0 = time.time()
        prompts = [head + f'<description="{j["description"]}"> {j["text"]}' + tail for j in group]
        enc = tok(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to("cuda")
        # Room for a slow read: about 14 characters a second spoken, and then some.
        most = min(2600, int(max(len(j["text"]) for j in group) / 14 * 1.9 * TOKENS_PER_SEC) + 300)
        torch.manual_seed(group[0].get("seed", 1))
        try:
            with torch.inference_mode():
                g = model.generate(**enc, max_new_tokens=most, min_new_tokens=28, do_sample=True, temperature=0.4, top_p=0.9,
                                   repetition_penalty=1.1, eos_token_id=EOS, pad_token_id=EOS)
        except (torch.OutOfMemoryError, RuntimeError) as e:
            # A shared card: out of memory, or cuBLAS failing for want of it. The
            # caller runs the rest again with a smaller batch.
            print(json.dumps({"error": f"{type(e).__name__}: {e}"[:300], "batch": len(group)}), flush=True)
            sys.exit(3)
        n_in = enc["input_ids"].shape[1]
        for j, row in zip(group, g[:, n_in:].tolist()):
            audio = decode(row)
            if audio is None:
                print(json.dumps({"out": j["out"], "error": "no speech"}), flush=True)
                continue
            os.makedirs(os.path.dirname(j["out"]), exist_ok=True)
            sf.write(j["out"], audio, SR)
            print(json.dumps({"out": j["out"], "sec": round(len(audio) / SR, 2)}), flush=True)
        print(json.dumps({"batch": len(group), "took": round(time.time() - t0, 1)}), flush=True)


if __name__ == "__main__":
    main()

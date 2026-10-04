"""The sample pack as one page to listen from (published as an artifact):
every line, every method, ranked by how much each take moves like a person,
with the numbers beside each player. Writes <out>/index.html; the .ogg files
sit beside it under the same names as in docs/voice/samples.

    python tools/vo/shootout/page.py <out dir>
"""
import html
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import ROOT  # noqa: E402

SAMPLES = os.path.join(ROOT, "docs", "voice", "samples")
LINES = json.load(open(os.path.join(HERE, "lines.json"), encoding="utf-8"))["lines"]
WHAT = {
    "kokoro": "Stock British reader (Kokoro). Clean, unacted, not our voices: the yardstick.",
    "vox_cont": "VoxCPM2 continuing from the cast voice. The first pipeline.",
    "vox_style": "VoxCPM2 cloning the cast voice, direction as a style note.",
    "vox_design": "VoxCPM2 acting the line from a written performance; a slightly different person each take.",
    "vox_design-vc": "That performance, converted to the cast voice (Seed-VC, 22 kHz).",
    "vox_design-vcf0": "That performance, converted following its pitch (Seed-VC, 44 kHz).",
    "chatterbox": "Chatterbox cloning the cast voice, intensity from the direction.",
    "indextts": "IndexTTS-2.5 cloning the cast voice, emotion by numbers.",
    "dia": "Dia with sighs and laughs, cast voice as prompt.",
    "dia-vc": "Dia's performance converted to the cast voice.",
    "dia-vcf0": "Dia's performance converted following its pitch.",
    "orpheus": "Orpheus stock American voice with emotive tags: a performance, not our voice.",
    "orpheus-vc": "Orpheus's performance converted to the cast voice (accent stays American).",
    "orpheus-vcf0": "Orpheus's performance converted following its pitch.",
    "f5": "F5-TTS cloning the cast voice. Non-commercial weights: comparison only.",
    "maya": "Maya1 acting the line in a voice designed from a sentence (British, the part's age and temper), with emotion tags. Not our cast voice.",
    "maya-vc": "Maya1's performance converted to the cast voice (Seed-VC, 22 kHz).",
    "maya-vcf0": "Maya1's performance converted following its pitch (Seed-VC, 44 kHz).",
    "dia2": "Dia2 (the newer Dia) with the cast voice as its speaker prompt.",
    "dia2-free": "Dia2 in its own voice: a performance, not our voice.",
    "dia2-free-vc": "Dia2's own performance converted to the cast voice.",
    "dia2-free-vcf0": "Dia2's own performance converted following its pitch.",
    "vb_turbo": "Voicebox: Chatterbox Turbo cloning the cast voice, with tags ([sigh], [chuckle]).",
    "vb_turbo-acted": "Voicebox: Chatterbox Turbo cloning an acted take of the line in the cast voice.",
    "vb_qwen": "Voicebox: Qwen3-TTS 1.7B cloning the cast voice.",
    "vb_qwen-acted": "Voicebox: Qwen3-TTS cloning an acted take of the line in the cast voice.",
    "vb_cb": "Voicebox: Chatterbox (multilingual) cloning the cast voice.",
    "vb_cb-acted": "Voicebox: Chatterbox cloning an acted take of the line in the cast voice.",
    "vb_lux": "Voicebox: LuxTTS cloning the cast voice (48 kHz).",
    "vb_lux-acted": "Voicebox: LuxTTS cloning an acted take of the line in the cast voice.",
    "vb_tada": "Voicebox: HumeAI TADA 1B cloning the cast voice.",
    "vb_tada-acted": "Voicebox: TADA cloning an acted take of the line in the cast voice.",
    "vibe": "VibeVoice 1.5B (conversational, trained on podcasts) cloning the cast voice.",
    "vibe-acted": "VibeVoice cloning an acted take of the line in the cast voice.",
}
SHIP = {"f5": False}
TITLES = {"1_angry": ("Anger held down", "Holloway"), "2_intimate": ("Intimate, unsure", "Sella"),
          "3_wry": ("A wry aside", "Rook"), "4_grief": ("Grief", "Brannoc"), "5_shout": ("A shout", "Redcowl")}


def main(out):
    m = json.load(open(os.path.join(SAMPLES, "metrics.json"), encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    sections = []
    for key, L in LINES.items():
        name, who = TITLES[key]
        rows = sorted(((k, r) for k, r in m.items() if k.startswith(key + "__")), key=lambda kr: -kr[1]["human"])
        items = []
        for k, r in rows:
            method = k.split("__")[1]
            shutil.copy(os.path.join(SAMPLES, k + ".ogg"), os.path.join(out, k + ".ogg"))
            flags = []
            if not r["words_right"]:
                flags.append("<span class=flag>words wrong</span>")
            if method.startswith("f5"):
                flags.append("<span class=flag>can't ship</span>")
            if r["accent_target_p"] < 0.5:
                flags.append(f"<span class=flag>heard as {html.escape(r['accent'])}</span>")
            items.append(
                f"<li><div class=meta><code>{method}</code>{''.join(flags)}<p>{html.escape(WHAT.get(method, ''))}</p></div>"
                f"<audio controls preload=none src='{k}.ogg'></audio>"
                f"<dl><div><dt>moves like a person</dt><dd>{r['human']:.1f}</dd></div>"
                f"<div><dt>same voice as cast</dt><dd>{r['similarity_to_cast_voice']:.2f}</dd></div>"
                f"<div><dt>naturalness</dt><dd>{r['utmos']:.1f}</dd></div></dl></li>")
        sections.append(f"<section id='{key}'><header><h2>{name}</h2><span class=who>{who}</span></header>"
                        f"<blockquote>{html.escape(L['text'])}</blockquote><ol>{''.join(items)}</ol></section>")
    page = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read().replace("<!--SECTIONS-->", "".join(sections))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])

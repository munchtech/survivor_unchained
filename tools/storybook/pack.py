"""Build the SB00 painter pack from tools/storybook/out/comps outputs.

python tools/storybook/pack.py [--picks p0=PATH,p3=PATH] [--keep-comps] [--comps DIR] [--pack DIR] [--no-pdf]

--keep-comps keeps a plate's comp already in the pack when it has no pick (the picks' sources are git-ignored).
"""
import argparse, re, shutil, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
IDS = ["p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p7u"]
DEFAULT_PACK = Path(r"C:\Users\munch\Desktop\survivorsunchained_inputs\storybook_painter_pack")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FORBIDDEN = ("art/storybook/sb00/style", "sb00_style.json")
copied = []  # (source, dest)


def cp(src, dst):
    src, dst = Path(src), Path(dst)
    if not src.is_file():
        sys.exit(f"missing source: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    copied.append((src, dst))


def jpg(src, dst, width):
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=85)


def soften(src, out_png):
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([sys.executable, str(ROOT / "tools/storybook/comps.py"), "--soften", str(src), "--out", td], check=True)
        res = Path(td) / (Path(src).stem + "_soft.png")
        if not res.is_file():
            sys.exit(f"soften produced no {res.name}")
        shutil.copyfile(res, out_png)


def build_brief(comps, pack):
    brief = (ROOT / "docs/storybook/sb00_painter_brief.md").read_text(encoding="utf-8")
    plates = (comps / "plates.md").read_text(encoding="utf-8").splitlines()
    heads = [(i, len(m.group(1)), m.group(2)) for i, l in enumerate(plates) if (m := re.match(r"^(#{1,6})\s+(.*)", l))]
    counts = Counter(h[1] for h in heads)
    lvl = next((k for k, v in sorted(counts.items()) if v == len(IDS)), None)
    if lvl is None:
        lvl = counts.most_common(1)[0][0]
    plate_heads = [h for h in heads if h[1] == lvl]
    by_id = {}
    for n, (i, _, text) in enumerate(plate_heads):
        m = re.search(r"\b(p7u|p[0-7])\b", text, re.I)
        pid = m.group(1).lower() if m else (IDS[n] if len(plate_heads) == len(IDS) and n < len(IDS) else None)
        if pid:
            by_id[i] = pid
    shift = 3 - lvl
    out = []
    for i, l in enumerate(plates):
        m = re.match(r"^(#{1,6})(\s+.*)", l)
        if m:
            l = "#" * min(6, max(1, len(m.group(1)) + shift)) + m.group(2)
        out.append(l)
        if i in by_id:
            pid = by_id[i]
            out += ["", f"![](plates/{pid}/sb00_{pid}_comp_preview.jpg)", "",
                    f"![](plates/{pid}/sb00_{pid}_layers_preview.jpg)", ""]
    marker = "<!-- APPENDIX: filled from tools/storybook/out/comps/plates.md -->"
    if marker not in brief:
        sys.exit("appendix marker not found in brief")
    brief = brief.replace(marker, "\n".join(out))
    brief = re.sub(r"<!--.*?-->[ \t]*\n?", "", brief, flags=re.S)
    (pack / "SB00_painter_brief.md").write_text(brief, encoding="utf-8")
    return brief


CSS = """
@page { size: Letter; margin: 0.7in }
body { font-family: Georgia, serif; font-size: 10.5pt; line-height: 1.4; color: #1a1a1a }
h1 { font-size: 26pt }
h2 { font-size: 15pt; border-top: 1px solid #999; margin-top: 1.6em; padding-top: 0.5em }
h3 { font-size: 13pt; page-break-before: always }
table { width: 100%; border-collapse: collapse; font-size: 9pt }
td, th { padding: 4px; border: 1px solid #ccc; vertical-align: top; text-align: left }
tr { page-break-inside: avoid }
td img { width: 1.7in }
img { max-width: 100%; margin-bottom: 8px }
blockquote { font-style: italic; border-left: 3px solid #999; margin-left: 0; padding-left: 12px }
"""


def build_pdf(brief, pack):
    try:
        import markdown
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "markdown"], check=True)
        import markdown
    body = markdown.markdown(brief, extensions=["tables"])
    html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>SB00 painter brief</title><style>{CSS}</style></head><body>{body}</body></html>'
    hp = pack / "SB00_painter_brief.html"
    pdf = pack / "SB00_painter_brief.pdf"
    hp.write_text(html, encoding="utf-8")
    if pdf.exists():
        pdf.unlink()
    p = subprocess.Popen([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                          "--virtual-time-budget=10000", f"--print-to-pdf={pdf}", "file:///" + hp.as_posix()])
    p.wait()
    if not pdf.is_file() or pdf.stat().st_size < 100_000:
        sys.exit(f"PDF missing or under 100 KB (html kept at {hp})")
    hp.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", default="")
    ap.add_argument("--comps", default=str(ROOT / "tools/storybook/out/comps"))
    ap.add_argument("--pack", default=str(DEFAULT_PACK))
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--keep-comps", action="store_true")
    a = ap.parse_args()
    comps, pack = Path(a.comps), Path(a.pack)
    picks = dict(kv.split("=", 1) for kv in a.picks.split(",") if kv)
    bad = set(picks) - set(IDS)
    if bad:
        sys.exit(f"unknown plate ids in --picks: {bad}")
    pack.mkdir(parents=True, exist_ok=True)
    notes = []
    for pid in IDS:
        d = pack / "plates" / pid
        d.mkdir(parents=True, exist_ok=True)
        comp = d / f"sb00_{pid}_comp.png"
        if pid in picks:
            soften(picks[pid], comp)
        elif a.keep_comps and comp.is_file():
            notes.append(f"{pid}: comp kept from the pack")
        else:
            cp(comps / f"{pid}_block.png", comp)
            notes.append(f"{pid}: no pick, block-in used as comp")
        jpg(comp, d / f"sb00_{pid}_comp_thumb.jpg", 400)
        jpg(comp, d / f"sb00_{pid}_comp_preview.jpg", 1500)
        cp(comps / f"{pid}_block.png", d / f"sb00_{pid}_layout.png")
        cp(comps / f"{pid}_underlay.jpg", d / f"sb00_{pid}_underlay.jpg")
        cp(comps / f"{pid}_layers.png", d / f"sb00_{pid}_layers.png")
        jpg(d / f"sb00_{pid}_layers.png", d / f"sb00_{pid}_layers_preview.jpg", 1500)
        cp(comps / f"{pid}_notes.png", d / f"sb00_{pid}_camera.png")
    cp(comps / "palette.png", pack / "palette.png")
    cp(ROOT / "godot/art/storybook/sb00/audio/sb00_bed.ogg", pack / "temp_music/sb00_temp_score.ogg")
    brief = build_brief(comps, pack)
    if not a.no_pdf:
        build_pdf(brief, pack)
    for s, _ in copied:
        sp = s.as_posix()
        assert not any(f in sp for f in FORBIDDEN), f"forbidden source {s}"
    files = sorted(f for f in pack.rglob("*") if f.is_file())
    total = 0
    for f in files:
        total += f.stat().st_size
        print(f"{f.stat().st_size/1e6:8.2f} MB  {f.relative_to(pack).as_posix()}")
    print(f"{len(files)} files, {total/1e6:.1f} MB total")
    for n in notes:
        print("NOTE", n)
    print("Assertion ok: no copied file came from sb00/style/ or sb00_style.json")


if __name__ == "__main__":
    main()

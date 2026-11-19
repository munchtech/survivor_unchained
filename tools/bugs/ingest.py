#!/usr/bin/env python3
"""Index in-game bug reports: python tools/bugs/ingest.py <folder or zip>... [--out DIR]

A report folder is any folder holding report.json (beside shot.png, clip.avi,
the log and the save). Writes <out>/INDEX.md and <out>/sheets/<folder>.jpg.
Stdlib + Pillow only.
"""
import argparse
import io
import json
import os
import re
import struct
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# ---- AVI reading (same layout as godot/logic/Core/MjpegAvi.cs) ----

def avi_read(path):
    """Returns (width, height, fps, frames) where frames is a list of JPEG bytes."""
    d = Path(path).read_bytes()
    info = {"w": 0, "h": 0, "fps": 0.0, "n": 0}
    frames = []

    def walk(pos, end):
        end = min(end, len(d))
        while pos + 8 <= end:
            cid = d[pos:pos + 4]
            size = struct.unpack_from("<I", d, pos + 4)[0]
            body = pos + 8
            if cid in (b"LIST", b"RIFF"):
                if body + size > len(d):
                    walk(body + 4, len(d))
                    return False
                if not walk(body + 4, body + size):
                    return False
            elif cid == b"avih" and body + 40 <= len(d):
                us, = struct.unpack_from("<I", d, body)
                info["n"] = struct.unpack_from("<I", d, body + 16)[0]
                info["w"], info["h"] = struct.unpack_from("<II", d, body + 32)
                if us:
                    info["fps"] = 1e6 / us
            elif cid == b"strh" and body + 28 <= len(d):
                sc, rt = struct.unpack_from("<II", d, body + 20)
                if sc and rt:
                    info["fps"] = rt / sc
            elif len(cid) == 4 and cid[:2].isdigit() and cid[2:] in (b"dc", b"db"):
                if body + size > len(d):
                    return False
                frames.append(d[body:body + size])
            nxt = body + size + (size & 1)
            if nxt > len(d):
                return False
            if nxt > end:
                return True
            pos = nxt
        return True

    if d[:4] == b"RIFF":
        walk(12, len(d))
    return info["w"], info["h"], info["fps"], frames


# ---- reading reports ----

def find_reports(root):
    return sorted(p.parent for p in Path(root).rglob("report.json"))


def safe_extract(zpath, dest):
    dest = Path(dest).resolve()
    with zipfile.ZipFile(zpath) as z:
        for m in z.infolist():
            name = m.filename
            if name.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", name) or ".." in Path(name.replace("\\", "/")).parts:
                raise ValueError(f"unsafe path in zip: {name}")
            target = (dest / name).resolve()
            if dest not in target.parents and target != dest:
                raise ValueError(f"unsafe path in zip: {name}")
        z.extractall(dest)


def norm_title(t):
    t = re.sub(r"\s+", " ", (t or "").strip().lower())
    return re.sub(r"[\s.!?,;:]+$", "", t)


def num(v, fmt="{:.1f}"):
    return fmt.format(v) if isinstance(v, (int, float)) else "-"


# ---- contact sheet ----

def font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def make_sheet(folder, rep, out_path):
    W = 1280
    parts = []
    shot = folder / "shot.png"
    if shot.exists():
        try:
            im = Image.open(shot).convert("RGB")
            parts.append(im.resize((W, max(1, round(im.height * W / im.width)))))
        except Exception:
            pass
    clip = folder / "clip.avi"
    if clip.exists():
        try:
            _, _, fps, frames = avi_read(clip)
            if frames:
                k = min(8, len(frames))
                idxs = sorted({round(i * (len(frames) - 1) / max(1, k - 1)) for i in range(k)})
                cols = 4
                cw = W // cols
                cells = []
                for i in idxs:
                    try:
                        fr = Image.open(io.BytesIO(frames[i])).convert("RGB")
                    except Exception:
                        continue
                    fr = fr.resize((cw, max(1, round(fr.height * cw / fr.width))))
                    t = (i - len(frames)) / fps if fps else 0.0
                    ImageDraw.Draw(fr).text((6, 4), f"{t:+.1f} s", fill=(255, 255, 0), font=font(18), stroke_width=2, stroke_fill=(0, 0, 0))
                    cells.append(fr)
                if cells:
                    ch = max(c.height for c in cells)
                    rows = (len(cells) + cols - 1) // cols
                    grid = Image.new("RGB", (W, ch * rows), (20, 20, 20))
                    for n, c in enumerate(cells):
                        grid.paste(c, ((n % cols) * cw, (n // cols) * ch))
                    parts.append(grid)
        except Exception:
            pass
    cap_h = 44
    total_h = cap_h + sum(p.height for p in parts)
    sheet = Image.new("RGB", (W, max(total_h, cap_h)), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 4), folder.name, fill=(255, 255, 255), font=font(18))
    dr.text((8, 24), str(rep.get("title") or ""), fill=(200, 200, 200), font=font(16))
    y = cap_h
    for p in parts:
        sheet.paste(p, (0, y))
        y += p.height
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=85)


# ---- main ----

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", default="bug_index")
    a = ap.parse_args(argv)
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="unzipped_", dir=out))

    roots = []
    for i, arg in enumerate(a.inputs):
        p = Path(arg)
        if p.is_file() and p.suffix.lower() == ".zip":
            dest = tmp / f"{i}_{p.stem}"
            dest.mkdir()
            try:
                safe_extract(p, dest)
            except Exception as e:
                print(f"skip {p}: {e}", file=sys.stderr)
                continue
            roots.append(dest)
        elif p.is_dir():
            roots.append(p)
        else:
            print(f"skip {arg}: not a folder or zip", file=sys.stderr)

    reports, unreadable, seen = [], [], set()
    for r in roots:
        for f in find_reports(r):
            key = f.resolve()
            if key in seen:
                continue
            seen.add(key)
            try:
                rep = json.loads((f / "report.json").read_text(encoding="utf-8-sig"))
                if not isinstance(rep, dict):
                    raise ValueError("not an object")
                reports.append((f, rep))
            except Exception as e:
                unreadable.append((f / "report.json", str(e)))

    def sk(fr):
        rep = fr[1]
        return (str(rep.get("build") or ""), str(rep.get("sha") or ""), str(rep.get("zone") or ""), str(rep.get("time_local") or ""))
    reports.sort(key=sk)

    groups = {}
    for f, rep in reports:
        g = (str(rep.get("build") or ""), str(rep.get("sha") or ""), str(rep.get("zone") or ""), norm_title(rep.get("title")))
        groups.setdefault(g, []).append((f, rep))

    sheets = out / "sheets"
    for f, rep in reports:
        try:
            make_sheet(f, rep, sheets / f"{f.name}.jpg")
        except Exception as e:
            print(f"sheet failed for {f.name}: {e}", file=sys.stderr)

    def rel(p):
        try:
            return Path(os.path.relpath(Path(p).resolve(), out)).as_posix().replace(" ", "%20")
        except ValueError:
            return Path(p).resolve().as_uri()

    testers = {str(r.get("tester")) for _, r in reports if r.get("tester")}
    builds = {g[0] for g in groups}
    zones = {g[2] for g in groups}
    L = ["# Bug report index", "",
         f"- Reports: {len(reports)}", f"- Testers: {len(testers)}", f"- Builds: {len(builds)}",
         f"- Zones: {len(zones)}", f"- Groups: {len(groups)}", f"- Unreadable: {len(unreadable)}", ""]
    cur_b = cur_z = None
    for g, items in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2], kv[1][0][1].get("time_local") or "")):
        b, sha, z, _ = g
        if b != cur_b:
            L += [f"## Build {b or '(none)'}", ""]
            cur_b, cur_z = b, None
        if (b, z) != (cur_b, cur_z):
            L += [f"### Zone {z or '(none)'}", ""]
            cur_z = z
        first = items[0][1]
        L += [f"#### {first.get('title') or '(untitled)'}  (x{len(items)}, sha {sha or '-'})", ""]
        for f, rep in items:
            pos = ", ".join(num(rep.get(k), "{:.1f}") for k in ("x", "y", "z"))
            L.append(f"- **{f.name}** | tester {rep.get('tester') or '-'} | {rep.get('time_local') or '-'} | level {rep.get('level') if rep.get('level') is not None else '-'}"
                     f" | pos ({pos}) | den clears {rep.get('den_clears') if rep.get('den_clears') is not None else '-'}"
                     f" | frame ms avg/p99/max {num(rep.get('frame_ms_avg'))}/{num(rep.get('frame_ms_p99'))}/{num(rep.get('frame_ms_max'))}")
            desc = (rep.get("description") or "").strip()
            if desc:
                L += ["  " + ln for ln in ("> " + desc.replace("\n", "\n> ")).split("\n")]
            links = []
            for label, pat in (("shot", "shot.png"), ("clip", "clip.avi"), ("log", "*.log"), ("save", "*.save"), ("save", "save*.json")):
                for hit in sorted(f.glob(pat))[:1]:
                    links.append(f"[{label}]({rel(hit)})")
            sh = sheets / f"{f.name}.jpg"
            if sh.exists():
                links.append(f"[sheet]({rel(sh)})")
            if links:
                L.append("  " + " | ".join(links))
            L.append("")
    if unreadable:
        L += ["## Unreadable", ""]
        L += [f"- {p}: {e}" for p, e in unreadable]
        L.append("")
    (out / "INDEX.md").write_text("\n".join(L), encoding="utf-8")
    print(f"{len(reports)} reports, {len(groups)} groups, {len(unreadable)} unreadable -> {out / 'INDEX.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""frame-pacing-4: read samp.py's samples. No symbols: the game exe's functions are named by the strings they reference
(Godot's error macros carry the function name and the source file), their bounds come from the exe's .pdata.

  python sym.py <prefix> [t0 ms] [t1 ms] [--top N] [--thread TID] [--paths N]

Prints, for the window: CPU ms per thread, CPU ms by module (leaf frame), the game exe's top functions by self and by
inclusive time with their string labels, and the heaviest named call paths.
"""
import bisect
import collections
import os
import re
import struct
import sys
import winreg


def tsc_hz():
    k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
    return winreg.QueryValueEx(k, "~MHz")[0] * 1e6


class Pe:
    def __init__(self, path):
        self.b = open(path, "rb").read()
        b = self.b
        pe = struct.unpack_from("<I", b, 0x3C)[0]
        nsec = struct.unpack_from("<H", b, pe + 6)[0]
        opt = pe + 24
        optsz = struct.unpack_from("<H", b, pe + 20)[0]
        self.secs = []
        for i in range(nsec):
            o = opt + optsz + 40 * i
            name = b[o:o + 8].rstrip(b"\0").decode("latin1")
            vsize, va, rsize, raw = struct.unpack_from("<IIII", b, o + 8)
            self.secs.append((name, va, max(vsize, rsize), raw, rsize))
        ddir = opt + 112  # PE32+: data directories
        exc_rva, exc_size = struct.unpack_from("<II", b, ddir + 8 * 3)
        o = self.off(exc_rva)
        n = exc_size // 12
        fs = struct.unpack_from("<%dI" % (n * 3), b, o)
        self.begins = list(fs[0::3]); self.ends = list(fs[1::3])
        self.labels = {}

    def off(self, rva):
        for name, va, size, raw, rsize in self.secs:
            if va <= rva < va + size:
                d = rva - va
                return raw + d if d < rsize else None
        return None

    def sec(self, rva):
        for name, va, size, raw, rsize in self.secs:
            if va <= rva < va + size:
                return name
        return ""

    def func(self, rva):
        i = bisect.bisect_right(self.begins, rva) - 1
        if i >= 0 and rva < self.ends[i]:
            return i
        return -1

    def cstr(self, rva):
        o = self.off(rva)
        if o is None:
            return None
        e = self.b.find(b"\0", o, o + 200)
        if e < 0 or e - o < 4:
            return None
        s = self.b[o:e]
        if all(32 <= c < 127 for c in s):
            return s.decode()
        return None

    def label(self, i):
        if i in self.labels:
            return self.labels[i]
        b0, b1 = self.begins[i], self.ends[i]
        o = self.off(b0)
        code = self.b[o:o + (b1 - b0)]
        ids, files, other = [], [], []
        for m in re.finditer(rb"[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]", code):
            p = m.start()
            if p + 7 > len(code):
                continue
            tgt = b0 + p + 7 + struct.unpack_from("<i", code, p + 3)[0]
            if self.sec(tgt) in (".text", ""):
                continue
            s = self.cstr(tgt)
            if not s:
                continue
            if re.fullmatch(r"[\w./\\-]+\.(cpp|h|hpp|inc|c|cc)", s):
                if s not in files: files.append(s)
            elif re.fullmatch(r"[A-Za-z_~][\w:~<>]{3,60}", s):
                if s not in ids: ids.append(s)
            elif s not in other:
                other.append(s)
        lab = "fn_%x" % b0
        bits = ids[:3] + [os.path.basename(f) for f in files[:2]]
        if not bits and other:
            bits = ['"%s"' % other[0][:50]]
        if bits:
            lab += "[" + " ".join(bits) + "]"
        self.labels[i] = (lab, bool(ids or files))
        return self.labels[i]


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    opt = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith("--")}
    a = [x for x in a if x not in opt.values()]
    pre = a[0]
    t0 = float(a[1]) if len(a) > 1 else 0
    t1 = float(a[2]) if len(a) > 2 else 1e12
    top = int(opt.get("--top", 25)); only = int(opt.get("--thread", 0)); npaths = int(opt.get("--paths", 12))
    hz = tsc_hz()
    mods = []
    for line in open(pre + ".modules", encoding="utf-8"):
        if line.startswith("#"):
            print(line.strip()); continue
        b, s, p = line.rstrip("\n").split(" ", 2)
        mods.append((int(b, 16), int(s, 16), p))
    mods.sort()
    bases = [m[0] for m in mods]
    exe = next((m for m in mods if m[2].lower().endswith(".exe")), None)
    pe = Pe(exe[2]) if exe else None

    def mod(addr):
        i = bisect.bisect_right(bases, addr) - 1
        if i >= 0 and addr < mods[i][0] + mods[i][1]:
            return mods[i]
        return None

    thr = collections.Counter(); leafmod = collections.Counter(); selff = collections.Counter(); incl = collections.Counter()
    paths = collections.Counter(); anymod = collections.Counter(); total = 0.0
    thrmod = collections.defaultdict(collections.Counter)
    for line in open(pre + ".samples"):
        t, tid, cyc, st = line.split(" ")
        t = float(t); tid = int(tid)
        if t < t0 or t > t1 or (only and tid != only):
            continue
        ms = int(cyc) / hz * 1000.0
        addrs = [int(x, 16) for x in st.strip().split(",") if x] or [0]
        total += ms; thr[tid] += ms
        m = mod(addrs[0])
        name = os.path.basename(m[2]) if m else "?(jit or unknown)"
        leafmod[name] += ms; thrmod[tid][name] += ms
        seen = set(); seenm = set(); named = []
        for k, ad in enumerate(addrs):
            mm = mod(ad)
            mn = os.path.basename(mm[2]) if mm else "?(jit)"
            if mn not in seenm:
                seenm.add(mn); anymod[mn] += ms
            if pe and mm is exe:
                i = pe.func(ad - exe[0])
                if i < 0:
                    continue
                if k == 0:
                    selff[i] += ms
                if i not in seen:
                    seen.add(i); incl[i] += ms
                    lab, good = pe.label(i)
                    if good and len(named) < 7:
                        named.append(lab)
        if named:
            leaf = name if (not m or m is not exe) else "exe"
            paths[leaf + " <- " + " <- ".join(named)] += ms
    span = (min(t1, 1e9) - t0) if t1 < 1e12 else 0
    print("window %.0f-%s ms: %.0f CPU ms sampled over %d threads" % (t0, "%.0f" % t1 if t1 < 1e12 else "end", total, len(thr)))
    print("== threads (CPU ms; leaf modules)")
    for tid, ms in thr.most_common(14):
        print("  tid %6d %8.0f  %s" % (tid, ms, ", ".join("%s %.0f" % kv for kv in thrmod[tid].most_common(4))))
    print("== leaf module (CPU ms)")
    for n, ms in leafmod.most_common(12):
        print("  %8.0f %5.1f%%  %s" % (ms, 100 * ms / max(total, 1), n))
    print("== module anywhere on the stack (CPU ms)")
    for n, ms in anymod.most_common(12):
        print("  %8.0f %5.1f%%  %s" % (ms, 100 * ms / max(total, 1), n))
    if pe:
        print("== exe functions by SELF time")
        for i, ms in selff.most_common(top):
            print("  %8.0f %5.1f%%  %s" % (ms, 100 * ms / max(total, 1), pe.label(i)[0]))
        print("== exe functions by INCLUSIVE time (named ones)")
        k = 0
        for i, ms in incl.most_common(400):
            lab, good = pe.label(i)
            if good:
                print("  %8.0f %5.1f%%  %s" % (ms, 100 * ms / max(total, 1), lab)); k += 1
                if k >= top * 2:
                    break
        print("== heaviest named call paths (leaf module <- nearest named callers)")
        for p, ms in paths.most_common(npaths):
            print("  %8.0f %5.1f%%  %s" % (ms, 100 * ms / max(total, 1), p[:700]))


if __name__ == "__main__":
    main()

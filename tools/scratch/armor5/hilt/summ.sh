f="$1"; head -1 "$f" | cut -c1-60
python - "$f" <<'PY'
import sys,re
L=[l for l in open(sys.argv[1]) if l.startswith(('run_','sprint'))]
def num(l,k):
    return float(re.search(k+r'\s*([0-9.]+)',l).group(1))
el=[num(l,'el') for l in L]; wr=[num(l,' wr') for l in L]
wp=[float(x) for l in L for x in re.search(r'w:a\s*([0-9.]+) p\s*([0-9.]+)-\s*([0-9.]+)',l).groups()[1:]]
wa=[float(re.search(r'w:a\s*([0-9.]+)',l).group(1)) for l in L]
ra=[float(re.search(r'r:a\s*([0-9.]+)',l).group(1)) for l in L]
X=[l.split(" X ")[1].split() for l in L]; xs=[max(float(x[i]) for x in X) for i in range(2)]
print(f"shield {xs[0]} xbow {xs[1]} ", end="")
print(f"el {min(el):.1f}-{max(el):.1f} wr {min(wr):.1f}-{max(wr):.1f} palm {min(wp):.1f}-{max(wp):.1f} wdep {max(wa):.1f} rdep {max(ra):.1f}")
PY

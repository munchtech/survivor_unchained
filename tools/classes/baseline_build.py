# Build the Balance harness of an old commit, for a named Act 1 baseline (CLASSES §7, "Act 1 baseline").
# Exports godot/{logic,data,balance} at <commit> with git archive (no worktree), optionally adds a never-press switch
# (SU_NOPRESS=1 makes UseFlare refuse, for builds that have a Flare), sets the Act 1 story bosses' health, and builds.
#   python tools/classes/baseline_build.py <out_dir> [commit=9cbc654c] [roost,vault,hollow,dig health=103,130,100,109]
# Then, from <out_dir>/godot:  [SU_NOPRESS=1] dotnet <out_dir>/out/Balance.dll story --seeds 32 --policies greedy,random
#   --bot plain,deft --par 16 --out <file>.jsonl
import io, os, re, subprocess, sys, tarfile
REPO = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(__file__)), "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
dst = os.path.abspath(sys.argv[1])
commit = sys.argv[2] if len(sys.argv) > 2 else "9cbc654c"
hps = [int(x) for x in (sys.argv[3] if len(sys.argv) > 3 else "103,130,100,109").split(",")]
os.makedirs(dst, exist_ok=True)
tar = subprocess.run(["git", "-C", REPO, "archive", "--format=tar", commit, "godot/logic", "godot/data", "godot/balance"],
                     capture_output=True, check=True).stdout
tarfile.open(fileobj=io.BytesIO(tar)).extractall(dst)
g = os.path.join(dst, "godot")
fl = os.path.join(g, "logic/Sim/Flare.cs")
if os.path.exists(fl):
    s = open(fl, encoding="utf-8").read()
    m = re.search(r"public bool UseFlare\([^)]*\)\s*\{", s)
    if m:
        s = s[:m.end()] + '\n        if (System.Environment.GetEnvironmentVariable("SU_NOPRESS") == "1") return false;' + s[m.end():]
        open(fl, "w", encoding="utf-8", newline="").write(s)
        print("UseFlare patched (SU_NOPRESS=1 never presses)")
for f, hp in zip(["Redcowl", "BarrowLordStory", "Greymuzzle", "GrimtunnelStory"], hps):
    p = os.path.join(g, f"logic/Play/Bosses/{f}.cs")
    s = open(p, encoding="utf-8").read()
    s2, n = re.subn(r"(public override double HealthMul\(int tier\) =>)\s*[^;]+;", rf"\1 {hp};", s)
    open(p, "w", encoding="utf-8", newline="").write(s2)
    print(f, "health", hp, "subs", n)
r = subprocess.run(["dotnet", "build", "-c", "Release", "-o", os.path.join(dst, "out"), os.path.join(g, "balance/Balance.csproj")],
                   capture_output=True, text=True)
print("build", "ok" if r.returncode == 0 else "FAILED\n" + r.stdout[-2000:])

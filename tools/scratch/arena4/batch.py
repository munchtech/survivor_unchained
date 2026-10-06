"""Run several game shots in turn: python batch.py SPEC.txt [PREFIX] [--only a,b] [--build]
Each line of SPEC: NAME | game args (after --). Lines starting with # are skipped.
{p} in a name becomes PREFIX. --build runs dotnet build first. Frames land in
godot/.shots of the arena worktree; a summary prints at the end."""
import subprocess, sys, os, time

HERE = os.path.dirname(os.path.abspath(__file__))
GD = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0b61c278bdd5c994\godot"
args = sys.argv[1:]
only = None
if "--only" in args:
    i = args.index("--only"); only = args[i + 1].split(","); args = args[:i] + args[i + 2:]
build = "--build" in args
args = [a for a in args if a != "--build"]
spec = open(args[0], encoding="utf-8-sig").read().splitlines()
prefix = args[1] if len(args) > 1 else ""
t0 = time.time()
if build:
    r = subprocess.run(["dotnet", "build", "-v", "q", "-nologo", os.path.join(GD, "SurvivorUnchained.csproj")], capture_output=True, text=True)
    errs = [l for l in r.stdout.splitlines() if "error" in l.lower() and "0 Error" not in l]
    if errs:
        print("\n".join(errs[:10])); sys.exit(1)
names = []
# Heavy work takes turns (tools/turn.py): a Godot run for pictures holds a godot turn, given
# back however the batch ends.
TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
WHO = "arena art: shots " + os.path.basename(args[0])
r = subprocess.run([sys.executable, TURN, "take", "godot", WHO, "--wait", "45"], capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    sys.exit(1)
import atexit
atexit.register(lambda: subprocess.run([sys.executable, TURN, "give", "godot", WHO], capture_output=True))
for line in spec:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, a = [p.strip() for p in line.split("|", 1)]
    name = name.replace("{p}", prefix)
    if only and not any(o in name for o in only):
        continue
    r = subprocess.run([sys.executable, os.path.join(HERE, "play.py"), name, "--timeout", "900", "--"] + a.split(),
                       capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[0] if r.stdout.strip() else name + ": no output", flush=True)
    for l in r.stdout.strip().splitlines()[1:4]:
        print("  ", l[:200])
    names.append(name)
print(f"batch done in {time.time() - t0:.0f}s")

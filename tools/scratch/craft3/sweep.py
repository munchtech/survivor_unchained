"""Run the crafting economy simulation for several material and iron chances (a non-gear carrier roll)."""
import os, subprocess, sys
T = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af01b0d61ef656dd4\godot\tests"
pairs = [p.split(":") for p in sys.argv[1:]] or [["0.3", "0.3", "2"]]
for m, i, b in pairs:
    env = dict(os.environ, ECON_MAT=m, ECON_IRON=i, ECON_BOSS=b)
    out = subprocess.run(["dotnet", "test", "--no-build", "--filter", "FullyQualifiedName~Act_one_crafting_meets_its_targets",
                          "--logger", "console;verbosity=detailed"], cwd=T, env=env, capture_output=True, text=True).stdout
    line = next((l for l in out.splitlines() if "today (" in l), "?")
    ok = "Passed!" in out
    print(f"mat {m} iron {i} boss {b} {'PASS' if ok else 'FAIL'}: {line.split('):', 1)[-1].strip()}")

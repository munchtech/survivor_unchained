# Tests for read_guard.py and noisy_guard.py: fake files and transcripts in a temp dir, stdin piped to the hook.
# Run: python tools/hooks/test_read_guard.py
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
READ, NOISY = os.path.join(HERE, "read_guard.py"), os.path.join(HERE, "noisy_guard.py")
tmp = tempfile.mkdtemp()
main_t = os.path.join(tmp, "sess.jsonl")
os.makedirs(os.path.join(tmp, "docs", "team"))
os.makedirs(os.path.join(tmp, "src"))
BIG = os.path.join(tmp, "docs", "team", "README.md")
open(BIG, "w").write("a line of plain text here\n" * 500)            # 501 lines, 13 KB
WIDE = os.path.join(tmp, "docs", "team", "WIDE.md")
open(WIDE, "w").write(("y" * 400 + "\n") * 100)                       # 100 lines, 40 KB
SMALL = os.path.join(tmp, "docs", "team", "SMALL.md")
open(SMALL, "w").write("short\n" * 20)
CODE = os.path.join(tmp, "src", "Big.cs")
open(CODE, "w").write("code\n" * 900)                                 # not a guarded path
DATA = os.path.join(tmp, "src", "data.json")
open(DATA, "w").write('{"a": 1, "name": "some entry"}\n' * 600)
PNG = os.path.join(tmp, "docs", "shot.png")
open(PNG, "wb").write(b"\x89PNG" + b"0" * 60000)


def brief(text):
    with open(main_t, "w") as f:
        f.write(json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": text}]}}) + "\n")


def run(hook, tool, inp, raw=None):
    data = raw if raw is not None else json.dumps(
        {"tool_name": tool, "tool_input": inp, "transcript_path": main_t, "cwd": tmp})
    r = subprocess.run([sys.executable, hook], input=data, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


fails = 0


def check(name, out, denied, word=None):
    global fails
    ok = (("deny" in out) == denied) and (denied or out == "") and (word is None or word in out)
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {out!r}"))
    fails += not ok


brief("do the job")
# read_guard
check("Read big doc whole denied", run(READ, "Read", {"file_path": BIG}), True, "offset/limit")
check("Read big doc with limit allowed", run(READ, "Read", {"file_path": BIG, "limit": 80}), False)
check("Read big doc with offset allowed", run(READ, "Read", {"file_path": BIG, "offset": 200}), False)
check("Read 40 KB doc whole denied", run(READ, "Read", {"file_path": WIDE}), True, "39 KB")
check("Read small doc allowed", run(READ, "Read", {"file_path": SMALL}), False)
check("Read big code file allowed", run(READ, "Read", {"file_path": CODE}), False)
check("Read big json denied", run(READ, "Read", {"file_path": DATA}), True)
check("Read image allowed", run(READ, "Read", {"file_path": PNG}), False)
check("Read missing file allowed", run(READ, "Read", {"file_path": os.path.join(tmp, "docs", "nope.md")}), False)
check("garbage stdin", run(READ, "Read", None, raw="not json{"), False)
brief("do the job\nReadWhole: docs/team/README.md")
check("ReadWhole line allows that file", run(READ, "Read", {"file_path": BIG}), False)
check("ReadWhole line, other file still denied", run(READ, "Read", {"file_path": WIDE}), True)
brief("do the job")

# noisy_guard: raw runs
G = r'"C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"'
bash = lambda c: run(NOISY, "Bash", {"command": c})
check("raw godot denied", bash(f"{G} --headless --path godot --quit"), True, "turn.py run godot")
check("raw godot after cd denied", bash(f"cd /c/x && {G} --headless --path godot -s t.gd"), True)
check("godot --version allowed", bash(f"{G} --version"), False)
check("godot to a file allowed", bash(f"{G} --headless --path godot --quit > out/g.txt 2>&1"), False)
check("godot | tail still denied", bash(f"{G} --headless --path godot --quit 2>&1 | tail -20"), True)
check("godot via turn.py run allowed", bash(f'python tools/turn.py run godot "x: y" -- {G} --headless --path godot --quit'), False)
check("dotnet test denied", bash("cd godot/tests && dotnet test"), True, "quiet.py")
check("dotnet test via quiet allowed", bash("python tools/quiet.py dotnet test godot/tests"), False)
check("dotnet build allowed", bash("dotnet build godot"), False)
check("build script denied", bash("python tools/armor/gear_fit.py build --body godot/art/people/body_p1"), True)
check("gear_fit check allowed", bash("python tools/armor/gear_fit.py check --synthetic"), False)
check("anim build denied (PowerShell)", run(NOISY, "PowerShell", {"command": "python tools\\anim\\build.py --all"}), True)
check("grep for 'dotnet test' allowed", bash("grep -rn 'dotnet test' docs/team"), False)
check("dotnet test inside single quotes allowed", bash("echo '{\"command\":\"cd x && dotnet test\"}' | python h.py"), False)
check("heredoc body naming dotnet test allowed", bash("python - <<'EOF'\nrun('x && dotnet test')\nprint(1)\nEOF\necho done"), False)
check("dotnet test after a heredoc denied", bash("cat > f.txt <<'EOF'\nhello\nEOF\ndotnet test godot/tests"), True)
check("git commit message naming godot allowed", bash('git commit -m "fix godot.exe crash"'), False)
# noisy_guard: whole reads through the shell
check("cat big doc denied", bash(f"cat {BIG}"), True, "grep -n")
check("cat big doc | head allowed", bash(f"cat {BIG} | head -50"), False)
check("Get-Content big doc denied", run(NOISY, "PowerShell", {"command": f"Get-Content {BIG}"}), True)
check("Get-Content -TotalCount allowed", run(NOISY, "PowerShell", {"command": f"Get-Content {BIG} -TotalCount 40"}), False)
check("sed 1,450p big doc denied", bash(f"sed -n 1,450p {BIG}"), True)
check("sed 1,120p big doc allowed", bash(f"sed -n 1,120p {BIG}"), False)
check("cat relative path in cwd denied", bash("cat docs/team/README.md"), True)
check("cat small doc allowed", bash(f"cat {SMALL}"), False)
check("cat big code allowed", bash(f"cat {CODE}"), False)
check("noisy garbage stdin", run(NOISY, "Bash", None, raw="{"), False)
print("FAILED" if fails else "ALL PASSED")
sys.exit(1 if fails else 0)

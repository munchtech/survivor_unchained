# PreToolUse hook on Bash and PowerShell: noisy commands go through the quiet wrapper, big docs aren't read whole.
# Measured 10-13 Nov (where_tokens_go, re-split by first command): shell output carried about $430 a week. Real
# Godot runs, dotnet test and build scripts were already small (agents tail them), but nothing made that the
# default; two thirds of it ($289) was files read through the shell (sed, grep, cat), which the Read guard can't see.
#
# Refused (one line, with the command to run instead):
#   1. A raw Godot run, `dotnet test`, or a named build script, unless it runs through `tools/quiet.py` or
#      `tools/turn.py run`, or its stdout goes to a file (`> f`, `>> f`, `| Out-File`, `| Tee-Object`).
#      `--version` / `--help` runs are allowed.
#   2. A whole read through the shell of a file read_guard.py protects (`cat f`, `type f`, `Get-Content f` with no
#      pipe into head/tail/grep/sed/Select-*, or `sed -n A,Bp f` over 400 lines). `ReadWhole: <path>` in the
#      brief allows it, as for Read.
# Never fails a tool call: any error exits 0 silently.
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_guard import big_guarded, deny, whole_ok, MAX_LINES  # noqa: E402

MARK = "[noisy_guard]"
POS = r"(?:^|&&|\|\||[;&|(\n]|\bthen\b|\bdo\b)\s*(?:timeout\s+\d+\s+|time\s+|&\s*|start\s+|exec\s+)?"
GODOT = re.compile(POS + r"[\"']?[^\s\"';&|]*godot[^\s\"';&|]*\.exe\b[\"']?|" + POS + r"[\"']?[^\"'\n;&|]*Godot_v4[^\"'\n;&|]*\.exe[\"']?", re.I)
DOTNET_TEST = re.compile(POS + r"dotnet(?:\.exe)?\s+test\b", re.I)
BUILD = re.compile(POS + r"(?:\S*python[0-9.]*(?:\.exe)?|py)\s+(?:-\S+\s+)*[\"']?\S*?tools[/\\]+(?:"
                   r"(?:anim|armor|body)[/\\]+build\.py|armor[/\\]+native_build\.py|assets[/\\]+build_heroine\.py|"
                   r"armor[/\\]+gear_fit\.py[\"']?\s+build|combat[/\\]+play_clip\.py|fx[/\\]+skill_clip\.py)", re.I)
WRAPPED = re.compile(r"tools[/\\]+quiet\.py|tools[/\\]+turn\.py[\"']?\s+run\b", re.I)
TO_FILE = re.compile(r"(?<![0-9&])>>?\s*(?!&)[\"']?[^\s&|;\"']+|\|\s*(Out-File|Tee-Object|Set-Content)\b", re.I)
TRIVIAL = re.compile(r"--version\b|--help\b|\s-h\b", re.I)
READ_CMD = re.compile(r"(?:^|&&|[;|\n])\s*(cat|type|Get-Content|gc)\s+((?:-\S+\s+)*)([\"']?)([^\s\"'|;&>]+)\3([^\n;&]*)", re.I)
SED_RANGE = re.compile(r"(?:^|&&|[;|\n])\s*sed\s+-n\s+[\"']?(\d+),(\d+)p[\"']?\s+([\"']?)([^\s\"'|;&>]+)\3", re.I)
LIMITERS = re.compile(r"\|\s*(head|tail|grep|sed|awk|cut|wc|Select-Object|Select-String|findstr|rg)\b|-TotalCount\b|-Head\b|-Tail\b|-First\b", re.I)


def cwd_of(cmd, base):
    m = re.match(r"\s*(?:cd|Set-Location)\s+([\"']?)([^\"';&\n]+?)\1\s*(?:&&|;)", cmd)
    d = m.group(2) if m else base
    if re.match(r"^/[a-zA-Z]/", d or ""):
        d = d[1] + ":" + d[2:]  # Git Bash /c/... -> c:/...
    return d or "."


def resolve(p, cwd):
    if re.match(r"^/[a-zA-Z]/", p):
        p = p[1] + ":" + p[2:]
    return p if os.path.isabs(p) else os.path.join(cwd, p)


def code_only(cmd):
    """The command without heredoc bodies and single-quoted strings (text, not commands: a JSON test input, a script)."""
    cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\s*(?=\n|$)", "\n", cmd, flags=re.S)
    return re.sub(r"'[^'\n]*'", "''", cmd)


def noisy(cmd):
    for seg in re.split(r"\n|&&|\|\||;", code_only(cmd)):  # each command with its own pipes and redirects
        if WRAPPED.search(seg) or TO_FILE.search(seg):
            continue
        for kind, rx in (("Godot run", GODOT), ("dotnet test", DOTNET_TEST), ("build script", BUILD)):
            if rx.search(seg) and not (kind == "Godot run" and TRIVIAL.search(seg)):
                return kind
    return None


def whole_read(d, cmd):
    cwd = cwd_of(cmd, d.get("cwd") or ".")
    for m in READ_CMD.finditer(cmd):
        if LIMITERS.search(m.group(2) + m.group(5)):
            continue
        path = resolve(m.group(4), cwd)
        hit = big_guarded(path)
        if hit and not whole_ok(d, path):
            return path, hit
    for m in SED_RANGE.finditer(cmd):
        a, b = int(m.group(1)), int(m.group(2))
        if b - a + 1 <= MAX_LINES:
            continue
        path = resolve(m.group(4), cwd)
        hit = big_guarded(path)
        if hit and not whole_ok(d, path):
            return path, hit
    return None


def main():
    d = json.load(sys.stdin)
    if d.get("tool_name") not in ("Bash", "PowerShell"):
        return
    cmd = str((d.get("tool_input") or {}).get("command") or "")
    kind = noisy(cmd)
    if kind:
        tools = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace(os.sep, "/")
        m = re.match(r"\s*((?:cd|Set-Location)\s+[^;&\n]+?\s*(?:&&|;)\s*)(.*)", cmd, re.S)
        pre, inner = (m.group(1), m.group(2).strip()) if m else ("", cmd.strip())
        if len(inner) > 160:
            inner = inner[:160] + " ..."
        how = (f'python {tools}/turn.py run godot "<who>: <job>" -- <the godot command>' if kind == "Godot run"
               else f"python {tools}/quiet.py -- <the command>")
        deny(f"{MARK} Raw {kind} output rides in your context for every later turn. Run it through the quiet wrapper "
             f"(full log to a file, summary and errors to you): `{how}`, e.g. `{pre}python {tools}/quiet.py -- {inner}`. "
             f"Add `--tail N` to keep more lines; grep the log it names for the rest.")
        return
    hit = whole_read(d, cmd)
    if hit:
        path, (n, size) = hit
        deny(f"{MARK} {os.path.basename(path)} is {n} lines / {size // 1024} KB: don't read it whole through the shell. "
             f"grep -n for the section, then read that range (sed -n A,Bp or Read with offset/limit). A brief that "
             f"truly needs it whole names it on a line `ReadWhole: <path>`.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

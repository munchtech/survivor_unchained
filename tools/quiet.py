"""Run a noisy command quietly: the full log goes to a file, stdout gets a summary plus the errors.

Shell output was the largest single carried cost in the week of 10-13 November (about $430 at list price):
every line a command prints rides in the agent's context for the rest of its life. So routine runs print
only what a decision needs. The full log is always on disk; grep it or read it by line range.

  python tools/quiet.py dotnet test godot/tests                      # the suite before every commit
  python tools/quiet.py -- "<Godot>_console.exe" --headless --path godot --import
  python tools/quiet.py --tail 30 -- python tools/anim/p4.py build   # a build script, last 30 lines kept
  python tools/turn.py run godot "<area>: <job>" -- <godot command>  # take the turn, run quietly, give it back

Prints: the exit code, the time, the log's path and size, then by kind of command:
  dotnet test  the result line, each failed test with its first error lines, build errors (CS/MSB);
  godot        ERROR / SCRIPT ERROR / exceptions, deduplicated with counts, and the warning count;
  anything     tracebacks and error lines (deduplicated), then the last --tail lines (default 12).
A failure (non-zero exit) always adds the last 20 lines. The summary is capped at about 60 lines.
Exit code: the command's own.
"""
import collections
import datetime as dt
import os
import re
import shlex
import subprocess
import sys
import time

MAX_LINES = 60


def log_dir():
    d = os.environ.get("QUIET_LOG_DIR")
    if not d:
        try:
            root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                                  timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            root = ""
        # *.log is git-ignored repo-wide, so the logs stay out of commits (CLAUDE.md: big output lives in the repo, not Temp).
        d = os.path.join(root, ".quiet") if root else os.path.join(os.environ.get("TEMP", "."), "quiet")
    os.makedirs(d, exist_ok=True)
    return d


def kind_of(cmd):
    s = " ".join(cmd).lower()
    if re.search(r"\bdotnet(\.exe)?\s+test\b", s):
        return "dotnet test"
    if re.search(r"\bdotnet(\.exe)?\s+build\b", s):
        return "dotnet build"
    if re.search(r"godot[^\s/\\]*\.exe|godot_console|godot_v4", s):
        return "godot"
    return "other"


def dedup(lines, cap):
    c = collections.Counter(lines)
    out = []
    for l in dict.fromkeys(lines):
        out.append(l if c[l] == 1 else f"{l}  (x{c[l]})")
        if len(out) >= cap:
            out.append(f"... {len(c) - cap} more distinct, see the log")
            break
    return out


def summarize(kind, lines, code, tail):
    out = []
    if kind in ("dotnet test", "dotnet build"):
        builderr = [l.strip() for l in lines if re.search(r"\berror (CS|MSB|NU)\d+|: error ", l)]
        out += dedup(builderr, 12)
        i = 0
        nfail = 0
        while i < len(lines):
            m = re.match(r"\s*Failed\s+(\S+)\s*\[", lines[i])
            if m:
                nfail += 1
                if nfail <= 10:
                    out.append("FAILED " + m.group(1))
                    j, got = i + 1, 0
                    while j < len(lines) and got < 6 and not re.match(r"\s*(Failed|Passed)\s+\S+\s*\[", lines[j]):
                        t = lines[j].strip()
                        if t and not t.startswith(("Stack Trace:", "at ")) and "Error Message:" not in t:
                            out.append("   " + t[:300]); got += 1
                        j += 1
            i += 1
        if nfail > 10:
            out.append(f"... {nfail - 10} more failed tests, see the log")
        res = [l.strip() for l in lines if re.search(r"(Passed|Failed)!\s+-|Total tests:|Build succeeded|Build FAILED|"
                                                     r"\d+ Warning\(s\)|\d+ Error\(s\)|Time Elapsed", l)]
        out += res[-4:]
        if not res and not builderr:
            out += [l.rstrip() for l in lines[-max(tail, 5):]]
    elif kind == "godot":
        errs = [l.strip() for l in lines if re.search(r"^\s*(ERROR|SCRIPT ERROR|USER ERROR|USER SCRIPT ERROR|Parse Error)\b|"
                                                      r"Unhandled exception|Exception:|CrashHandler|signal 11", l)]
        warns = sum(1 for l in lines if re.match(r"\s*(WARNING|USER WARNING)\b", l))
        out += dedup(errs, 15)
        out.append(f"{len(errs)} error lines, {warns} warnings")
        out += [l.rstrip() for l in lines[-tail:] if l.strip() not in errs and not l.startswith(" ")] if tail else []
    else:
        tb, inside = [], None
        for l in lines:
            if l.startswith("Traceback (most recent call last)"):
                inside = [l.rstrip()]
            elif inside is not None:
                inside.append(l.rstrip())
                if l and not l[0].isspace():
                    tb.append("\n".join(inside[:2] + ["  ..."] + inside[-3:]) if len(inside) > 6 else "\n".join(inside))
                    inside = None
        out += tb[-2:]
        seen = "\n".join(tb)
        errs = [l.strip() for l in lines if re.search(r"\b(error|failed|failure|fatal|exception)\b", l, re.I)
                and not l.startswith(" ") and l.strip() not in seen]
        out += dedup(errs, 10)
        if tb:  # the traceback is the answer; the tail would repeat it
            return out
        out += [l.rstrip() for l in lines[-tail:]] if tail else []
    if code != 0:
        last = [l.rstrip() for l in lines[-20:]]
        out += ["--- last 20 lines ---"] + [l for l in last if l not in out]
    return out


def main(argv):
    tail = 12
    name = None
    args = list(argv)
    while args and args[0].startswith("--") and args[0] != "--":
        flag = args.pop(0)
        if flag == "--tail":
            tail = int(args.pop(0))
        elif flag == "--name":
            name = args.pop(0)
        else:
            print(f"quiet.py: unknown flag {flag}", file=sys.stderr)
            return 2
    if args and args[0] == "--":
        args.pop(0)
    if not args:
        print(__doc__)
        return 2
    if len(args) == 1 and " " in args[0]:
        args = shlex.split(args[0], posix=os.name != "nt")
    kind = kind_of(args)
    slug = name or re.sub(r"[^A-Za-z0-9]+", "_", " ".join(os.path.basename(a) for a in args[:3]))[:40].strip("_")
    path = os.path.join(log_dir(), f"{dt.datetime.now():%Y%m%d_%H%M%S}_{os.getpid()}_{slug}.log")
    t0 = time.time()
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"$ {subprocess.list2cmdline(args)}\n# cwd {os.getcwd()}\n")
        f.flush()
        try:
            p = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                               shell=(os.name == "nt" and not os.path.splitext(args[0])[1]))
            code = p.returncode
        except OSError as e:
            f.write(f"quiet.py: could not start: {e}\n")
            code = 127
    secs = time.time() - t0
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()[2:]
    body = summarize(kind, lines, code, 0 if kind == "dotnet test" and code == 0 else tail)
    head = (f"[quiet] exit {code} in {secs:.0f}s, {kind}; {len(lines)} lines logged to {path}")
    text = [head] + body
    if len(text) > MAX_LINES:
        text = text[:MAX_LINES] + [f"... summary cut at {MAX_LINES} lines; grep the log"]
    print("\n".join(t[:400] for t in text))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

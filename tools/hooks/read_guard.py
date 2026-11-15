# PreToolUse hook on Read: refuse a whole-file read of a big doc, brief or data file.
# Measured 10-13 Nov (where_tokens_go): handoffs and big docs read whole at 22-27k tokens each, then carried in
# every later request, although the rule said "read by section". So the rule is held here, not remembered.
#
# Refused: a Read with no offset and no limit of a file over MAX_LINES lines or MAX_BYTES bytes that is
#   under a docs/ folder (either repo), under tools/scratch/coordinator/briefs/, a handoff or RESUME file,
#   or a .json data file. Images, PDFs and notebooks are never touched.
# Allowed: any read with offset or limit; any file under the limits; a path named on a line
#   `ReadWhole: <path>` in the agent's first message (its brief; the main session's first user message).
# The message is one line: grep for the section, then Read with offset/limit.
# tools/hooks/noisy_guard.py uses big_guarded() for whole reads through the shell (cat, Get-Content, sed ranges).
# Never fails a tool call: any error exits 0 silently.
import json
import os
import re
import sys

MARK = "[read_guard]"
MAX_LINES = 400
MAX_BYTES = 32 * 1024  # "about 40 KB" in the task; 32 KB so README (35 KB, the most-read big doc) is covered
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".exr", ".pdf", ".ipynb"}
GUARDED = re.compile(r"(^|/)docs/|(^|/)tools/scratch/coordinator/briefs/|(^|/)[^/]*handoff[^/]*\.md$|(^|/)resume\.md$|\.json$",
                     re.I)


def norm(p):
    return (p or "").replace("\\", "/")


def big_guarded(path):
    """(lines, bytes) if path is a guarded file over the limits, else None."""
    p = norm(path)
    if os.path.splitext(p)[1].lower() in SKIP_EXT or not GUARDED.search(p) or not os.path.isfile(path):
        return None
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        with open(path, "rb") as f:
            return f.read().count(b"\n") + 1, size
    if size > MAX_LINES * 20:  # under ~8 KB a file can't pass 400 lines of real text; skip the read
        with open(path, "rb") as f:
            n = f.read().count(b"\n") + 1
        if n > MAX_LINES:
            return n, size
    return None


def text_of(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type") == "text")
    return ""


def transcript(d):
    aid, main_path = d.get("agent_id"), d.get("transcript_path") or ""
    if aid:
        return os.path.join(main_path[:-len(".jsonl")], "subagents", f"agent-{aid}.jsonl")
    return main_path


def whole_ok(d, path):
    """True if the brief (first user message) has `ReadWhole: <path>` naming this file (suffix match)."""
    t = transcript(d)
    if not t or not os.path.exists(t):
        return False
    with open(t, "rb") as f:
        for line in f:
            if b'"user"' not in line:
                continue
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            if m.get("role") != "user":
                continue
            target = norm(path).lower()
            for w in re.findall(r"^[ \t>*-]*ReadWhole:[ \t]*(.+?)[ \t]*$", text_of(m.get("content")), re.I | re.M):
                w = norm(w).strip("`'\" ").lower()
                if w and (target.endswith(w.lstrip("./")) or w.endswith(target)):
                    return True
            return False
    return False


def message(path, n, size):
    return (f"{MARK} {os.path.basename(path)} is {n} lines / {size // 1024} KB: don't read it whole. Grep for the section "
            f"(Grep with -n, or the headings), then Read with offset/limit. A brief that truly needs it whole names it "
            f"on a line `ReadWhole: <path>`.")


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def main():
    d = json.load(sys.stdin)
    if d.get("tool_name") != "Read":
        return
    inp = d.get("tool_input") or {}
    if inp.get("offset") is not None or inp.get("limit") is not None or inp.get("pages"):
        return
    path = inp.get("file_path") or ""
    hit = big_guarded(path)
    if hit and not whole_ok(d, path):
        deny(message(path, *hit))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

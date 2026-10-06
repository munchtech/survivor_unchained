# Audit the survivorsunchained worktrees: merged? dirty? size? longest path? -> JSON
import json, os, subprocess, sys
REPO = r"C:\Users\munch\Desktop\survivorsunchained"
INTEG = "origin/claude/vigilant-galileo-l6jqyx"
def git(*a, cwd=REPO):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
subprocess.run(["git", "fetch", "-q", "origin"], cwd=REPO)
out, cur = [], {}
for line in git("worktree", "list", "--porcelain").stdout.splitlines() + [""]:
    if not line:
        if cur: out.append(cur)
        cur = {}
    elif line.startswith("worktree "): cur["path"] = line[9:]
    elif line.startswith("branch "): cur["branch"] = line[7:].replace("refs/heads/", "")
res = []
for w in out:
    p = os.path.normpath(w["path"])
    if os.path.normcase(p) == os.path.normcase(REPO) or not os.path.isdir(p):
        continue
    b = w.get("branch", "")
    merged = bool(b) and git("merge-base", "--is-ancestor", b, INTEG).returncode == 0
    st = git("status", "--porcelain", cwd=p).stdout.splitlines()
    tracked_dirty = [l for l in st if not l.startswith("??")]
    untracked = [l[3:] for l in st if l.startswith("??")]
    size, longest, nfiles = 0, 0, 0
    for root, dirs, files in os.walk(p):
        for f in files:
            fp = os.path.join(root, f)
            longest = max(longest, len(fp)); nfiles += 1
            try: size += os.lstat(fp).st_size
            except OSError: pass
        for d in dirs:
            longest = max(longest, len(os.path.join(root, d)))
    res.append(dict(path=p, branch=b, merged=merged, tracked_dirty=len(tracked_dirty),
                    dirty_sample=[l[3:] for l in tracked_dirty[:4]], untracked=len(untracked), untracked_sample=untracked[:6],
                    gb=round(size / 2**30, 2), files=nfiles, longest=longest,
                    mtime=os.path.getmtime(p)))
    print(p[-30:], b[-22:], merged, len(tracked_dirty), len(untracked), round(size/2**30,2), longest, flush=True)
json.dump(res, open(os.path.join(os.environ["TEMP"], "hs", "wt_audit.json"), "w"), indent=1)

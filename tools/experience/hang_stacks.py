"""Catch a hung Godot's stacks before the wrapper kills it: dump(pid, out_dir, name) -> path or None.
Writes the PID tree, `dotnet-stack report` per PID (managed stacks) and the thread states (native view). Never raises."""
import os, shutil, subprocess, time

def _ps(cmd, timeout):
    r = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")

def _tree(pid):
    rows = _ps("Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId)|$($_.ParentProcessId)|$($_.Name)\" }", 30).splitlines()
    procs = {}
    for ln in rows:
        a = ln.strip().split("|")
        if len(a) == 3 and a[0].isdigit() and a[1].isdigit(): procs[int(a[0])] = (int(a[1]), a[2])
    tree, todo = [pid], [pid]
    while todo:
        cur = todo.pop()
        for k, (par, _) in procs.items():
            if par == cur and k not in tree: tree.append(k); todo.append(k)
    return [(k, procs.get(k, (0, "?"))[1]) for k in tree]

def dump(pid, out_dir, name):
    try:
        t0 = time.time(); tool = shutil.which("dotnet-stack") or os.path.join(os.path.expanduser("~"), ".dotnet", "tools", "dotnet-stack.exe")
        try: tree = _tree(pid)
        except Exception as e: tree = [(pid, f"? (tree failed: {e})")]
        out = [f"hang stacks {time.strftime('%Y-%m-%d %H:%M:%S')}  name {name}  root PID {pid}", "PID tree:"] + [f"  {k}  {n}" for k, n in tree]
        for k, n in reversed(tree):  # children first: the real Godot hosts .NET, the console wrapper may not
            out += ["", "=" * 70, f"PID {k} {n}: dotnet-stack report", "=" * 70]
            if time.time() - t0 > 90: out.append("(skipped: time bound)"); continue
            try:
                r = subprocess.run([tool, "report", "-p", str(k)], capture_output=True, text=True, timeout=40)
                out += [f"exit {r.returncode}", "-- stdout --", r.stdout or "", "-- stderr --", r.stderr or ""]
            except Exception as e: out.append(f"FAILED: {type(e).__name__}: {e}")
            out += ["", f"PID {k} {n}: threads"]
            try: out.append(_ps(f"(Get-Process -Id {k}).Threads | Select-Object Id, ThreadState, WaitReason | Format-Table -AutoSize | Out-String", 20))
            except Exception as e: out.append(f"FAILED: {type(e).__name__}: {e}")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"hang_stacks_{name}_{time.strftime('%Y%m%d_%H%M%S')}.txt")
        with open(path, "w", encoding="utf-8") as f: f.write("\n".join(out))
        return path
    except Exception as e:
        print(f"hang_stacks: failed: {e}", flush=True); return None

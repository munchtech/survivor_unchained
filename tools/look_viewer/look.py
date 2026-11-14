"""The live look viewer's command line (docs/tools/LOOK_VIEWER.md).

  python tools/look_viewer/look.py start [--game ROOT] [--size 1920x1080] [--no-build]
  python tools/look_viewer/look.py capture PKG --out DIR [--id ID] [--cams play,chest] [--zone Z] [--time day|night]
                                   [--clock S] [--walk] [--turn DEG] [--spot sun|shade|dx,dz] [--off a,b] [--light P]
                                   [--light-only P] [--global "N=a,b;M=c"] [--solo] [--mods all|A,B] [--name NAME]
                                   [--size WxH] [--timeout 600] [--stale-ok]
  python tools/look_viewer/look.py status
  python tools/look_viewer/look.py stop

The viewer is the game itself (--look-viewer DROP) on the MAIN checkout by default; it watches DROP/live (the live
package) and DROP/live.json (its settings) and answers DROP/requests/*.json. capture writes a request, waits for the
answer and prints the frames; it exits 1 on a failed request, 2 on bad use, 3 when the viewer is not running or stale.
PKG is a package folder (manifest.json + body.glb + pieces), "live", or a game package name (godot/art/npc/NAME).
"""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

MAIN = Path("C:/Users/munch/Desktop/survivorsunchained")
DROP = Path(os.environ.get("LOOK_DROP", "C:/Users/munch/Desktop/survivorsunchained_inputs/look_viewer"))
GODOT = Path(os.environ.get("GODOT_EXE", "C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe"))
TURN = MAIN / "tools" / "turn.py"
ALIVE_S = 10          # a heartbeat older than this: the viewer is not running (a timer thread writes it)
HUNG_S = 150          # the main thread silent this long (main_at): hung (a replay fails itself at 120 s)
BASE = ["--quick", "warden", "--sex", "female", "--nohud", "--zone", "waystation", "--facing", "0", "--seed", "1", "--time", "day"]


def status():
    try:
        s = json.loads((DROP / "status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    s["age_s"] = round(time.time() - float(s.get("heartbeat", 0)), 1)
    s["main_age_s"] = round(time.time() - float(s.get("main_at", s.get("heartbeat", 0))), 1)
    s["alive"] = s["age_s"] <= ALIVE_S and s["main_age_s"] <= HUNG_S and s.get("state") != "stopped"
    return s


def pid_alive(pid):
    r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
    return str(pid) in r.stdout


def start(a):
    s = status()
    if s and s["alive"]:
        print(f"look: already running (pid {s['pid']}, {s['state']})")
        return 0
    game = Path(a.game)
    if not a.no_build:
        r = subprocess.run(["dotnet", "build", "-v", "q", "-nologo", "SurvivorUnchained.csproj"], cwd=game / "godot", capture_output=True, text=True)
        if r.returncode:
            print("look: dotnet build failed:\n" + r.stdout[-2000:], file=sys.stderr)
            return 1
    DROP.mkdir(parents=True, exist_ok=True)
    who = "look-viewer: boot"
    took = subprocess.run([sys.executable, str(TURN), "take", "godot", who, "--wait", "30", "--root", str(game)]).returncode == 0
    if not took:
        print("look: no godot turn for the boot", file=sys.stderr)
        return 1
    try:
        cmd = [str(GODOT), "--path", ".", "--fixed-fps", "60", "--resolution", a.size, "--", "--look-viewer", DROP.as_posix()] + BASE
        if a.turn == "off":
            cmd += ["--look-turn", "off"]
        log = open(DROP / "viewer_log.txt", "w", encoding="utf-8")
        flags = 0x00000008 | 0x00000200   # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP: it outlives this command
        t0 = time.time()
        p = subprocess.Popen(cmd, cwd=game / "godot", stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=flags)
        print(f"look: started pid {p.pid} on {game} ({a.size}); log {DROP / 'viewer_log.txt'}")
        end = time.time() + 240
        while time.time() < end:
            time.sleep(2)
            s = status()
            # (the console exe is a wrapper: the game's own pid is the one status.json names)
            if s and s["alive"] and float(s.get("main_at", 0)) >= t0 and s["state"] in ("idle", "failed", "replaying", "waiting-turn"):
                (DROP / "viewer.pid").write_text(str(s["pid"]))
                print(f"look: up ({s['state']}; game {s['game_commit'][:10]}, shaders {s['shader_fingerprint']})")
                return 0
            if p.poll() is not None:
                print(f"look: the viewer exited ({p.returncode}); see the log", file=sys.stderr)
                return 1
        print("look: no heartbeat within 240 s; see the log", file=sys.stderr)
        return 1
    finally:
        subprocess.run([sys.executable, str(TURN), "give", "godot", who])


def request_of(a):
    pkg = a.package
    if pkg != "live" and Path(pkg).exists():
        pkg = Path(pkg).resolve().as_posix()
    r = {"package": pkg, "out": Path(a.out).resolve().as_posix()}
    if a.id:
        r["id"] = a.id
    for k in ("zone", "time", "spot", "size", "name", "mods"):
        if getattr(a, k) is not None:
            r[k] = getattr(a, k)
    for k in ("cams", "off", "light", "light_only"):
        if getattr(a, k) is not None:
            r[k] = [x.strip() for x in getattr(a, k).split(",") if x.strip()]
    if a.clock is not None:
        r["clock"] = a.clock
    if a.turn is not None:
        r["turn"] = a.turn
    if a.walk:
        r["walk"] = True
    if a.solo:
        r["solo"] = True
    if a.glob:
        g = {}
        for item in a.glob.split(";"):
            if item.strip():
                k, v = item.split("=", 1)
                g[k.strip()] = [float(x) for x in v.split(",") if x.strip()]
        r["global"] = g
    return r


def capture(a):
    s = status()
    if not s or not s["alive"]:
        print("look: the viewer is not running (look.py start)" + (f"; last heartbeat {s['age_s']} s ago, state {s.get('state')}" if s else ""), file=sys.stderr)
        return 3
    if s.get("stale") and not a.stale_ok:
        print("look: the viewer is STALE: " + "; ".join(s.get("stale_why", [])) + " (--stale-ok to shoot anyway)", file=sys.stderr)
        return 3
    req = request_of(a)
    stem = (a.id or "base") + "-" + uuid.uuid4().hex[:8]
    rq = DROP / "requests"
    rq.mkdir(parents=True, exist_ok=True)
    tmp = rq / f"{stem}.json.tmp"
    tmp.write_text(json.dumps(req, indent=1), encoding="utf-8")
    os.replace(tmp, rq / f"{stem}.json")
    t0 = time.time()
    print(f"look: request {rq / (stem + '.json')}")
    end = t0 + a.timeout
    while time.time() < end:
        for kind in ("done", "failed"):
            f = rq / f"{stem}.{kind}.json"
            if f.exists():
                time.sleep(0.05)
                ans = json.loads(f.read_text(encoding="utf-8"))
                if kind == "failed":
                    print(f"look: FAILED: {ans.get('error')}", file=sys.stderr)
                    return 1
                for fr in ans.get("frames", []):
                    print(fr)
                print(f"look: done in {time.time() - t0:.1f} s ({ans.get('out')})")
                return 0
        s = status()
        if not s or not s["alive"]:
            print("look: the viewer stopped while the request waited", file=sys.stderr)
            return 3
        time.sleep(0.25)
    print(f"look: no answer within {a.timeout} s", file=sys.stderr)
    return 1


def stop(a):
    s = status()
    pid = s.get("pid") if s else None
    if pid is None and (DROP / "viewer.pid").exists():
        pid = int((DROP / "viewer.pid").read_text())
    if pid is None or not pid_alive(pid):
        print("look: not running")
        return 0
    (DROP / "stop").write_text("stop")
    end = time.time() + HUNG_S
    while time.time() < end and pid_alive(pid):
        time.sleep(1)
    if pid_alive(pid):
        # (its own pid only, from status.json / viewer.pid; never by name)
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
        subprocess.run([sys.executable, str(TURN), "give", "godot", s.get("turn_name", "") if s else ""], capture_output=True)
        print(f"look: pid {pid} did not quit in {HUNG_S} s; ended it")
    else:
        print(f"look: stopped (pid {pid})")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("start")
    st.add_argument("--game", default=str(MAIN), help="the game checkout (default: the main checkout)")
    st.add_argument("--size", default="1920x1080")
    st.add_argument("--no-build", action="store_true")
    st.add_argument("--turn", choices=["on", "off"], default="on", help="off: the viewer takes no godot turns (tests only)")
    c = sub.add_parser("capture")
    c.add_argument("package")
    c.add_argument("--out", required=True)
    c.add_argument("--id")
    c.add_argument("--cams")
    c.add_argument("--zone")
    c.add_argument("--time", choices=["day", "night"])
    c.add_argument("--clock", type=float)
    c.add_argument("--walk", action="store_true")
    c.add_argument("--turn", type=float)
    c.add_argument("--spot")
    c.add_argument("--off")
    c.add_argument("--light")
    c.add_argument("--light-only", dest="light_only")
    c.add_argument("--global", dest="glob")
    c.add_argument("--solo", action="store_true")
    c.add_argument("--mods")
    c.add_argument("--name")
    c.add_argument("--size")
    c.add_argument("--timeout", type=float, default=600)
    c.add_argument("--stale-ok", action="store_true")
    sub.add_parser("status")
    sub.add_parser("stop")
    a = ap.parse_args(argv)
    if a.cmd == "start":
        return start(a)
    if a.cmd == "capture":
        return capture(a)
    if a.cmd == "status":
        s = status()
        print(json.dumps(s, indent=1) if s else "look: no status.json (never started)")
        return 0 if s and s["alive"] else 3
    return stop(a)


if __name__ == "__main__":
    sys.exit(main())

"""Run the close-up lifetime check with user storage isolated before renderer startup.

Build the game first, then run:
  python tools/experience/closeup_lifetime.py --timeout 600 --log godot/.shots/closeup-lifetime.log
Add --headless for the dummy renderer. GODOT_CONSOLE selects the engine executable.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
PROFILE = "Survivor Unchained Codex closeup-blackscreen"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--godot", default=os.environ.get("GODOT_CONSOLE"))
    args = parser.parse_args()
    if not args.godot:
        parser.error("Set GODOT_CONSOLE or pass --godot with the Godot 4.5.1 Mono executable")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    engine = Path(args.godot)
    if os.name == "nt" and engine.name.lower().endswith("_console.exe"):
        # The console wrapper spawns a child; timeouts must stop the actual engine PID.
        engine = engine.with_name(engine.name[:-len("_console.exe")] + ".exe")
        if not engine.is_file():
            parser.error("The console wrapper's sibling Godot executable was not found")

    project = ROOT / "godot"
    override = project / "override.cfg"
    lock = project / ".godot" / "closeup-lifetime.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_file = lock.open("x", encoding="utf-8")
    except FileExistsError:
        parser.error(f"Another lifetime check owns {lock}; do not run two in one worktree")
    turn = [sys.executable, str(ROOT / "tools" / "turn.py")]
    who = "codex: closeup-lifetime"
    held = False
    installed = False
    try:
        original = override.read_bytes() if override.exists() else None
        configured = (original or b"") + (
            '\n[application]\nconfig/use_custom_user_dir=true\n'
            f'config/custom_user_dir_name="{PROFILE}"\n'
        ).encode("utf-8")
        lock_file.write(str(os.getpid()))
        lock_file.close()
        # This lifecycle check makes no judgment about the current art.
        taken = subprocess.run(turn + ["take", "godot", who, "--stale-ok"], cwd=ROOT)
        if taken.returncode:
            return taken.returncode
        held = True
        # user:// must remain stable after the renderer initializes its cache directories.
        override.write_bytes(configured)
        installed = True
        log = args.log.resolve()
        log.parent.mkdir(parents=True, exist_ok=True)
        command = [str(engine), "--path", str(project), "--fixed-fps", "60",
                   "--resolution", "1920x1080", "--windowed", "--audio-driver", "Dummy",
                   "-s", "res://tools_scenes/closeup_lifetime.gd",
                   "--", "--quick", "warden", "--zone", "waystation"]
        if args.headless:
            command.insert(1, "--headless")
        with log.open("w", encoding="utf-8") as output:
            run = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                 timeout=args.timeout,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        text = log.read_text(encoding="utf-8", errors="replace")
        passed = sum(line.startswith("closeup lifetime: PASS") for line in text.splitlines())
        cache_errors = text.count("at: _save_to_cache")
        print(f"{log}: exit {run.returncode}, {passed}/3 checks, {cache_errors} cache write errors")
        return 0 if run.returncode == 0 and passed == 3 and cache_errors == 0 else 1
    finally:
        try:
            if installed:
                if not override.exists() or override.read_bytes() != configured:
                    raise RuntimeError(f"{override} changed during the check; leaving that edit intact")
                if original is None:
                    override.unlink()
                else:
                    override.write_bytes(original)
        finally:
            try:
                if held:
                    subprocess.run(turn + ["give", "godot", who], cwd=ROOT, check=True)
            finally:
                if not lock_file.closed:
                    lock_file.close()
                lock.unlink()


if __name__ == "__main__":
    sys.exit(main())

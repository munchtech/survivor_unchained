"""Wait for a turn and take it: python wait_turn.py KIND "NAME" [max minutes]. Exits 0 once held."""
import subprocess, sys, time
kind, name = sys.argv[1], sys.argv[2]
limit = float(sys.argv[3]) if len(sys.argv) > 3 else 60
t0 = time.time()
while time.time() - t0 < limit * 60:
    r = subprocess.run([sys.executable, "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py", "take", kind, name],
                       capture_output=True, text=True)
    if r.returncode == 0:
        print("TAKEN", r.stdout.strip())
        sys.exit(0)
    time.sleep(30)
print("GAVE UP waiting")
sys.exit(1)

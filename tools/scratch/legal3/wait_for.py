"""Blocks until a file contains a word, or a turn holder disappears, or the time runs out.
    python wait_for.py file <path> <word> [minutes]
    python wait_for.py turnfree <word> [minutes]      (no holder whose name contains <word>)"""
import subprocess
import sys
import time

mode = sys.argv[1]
mins = float(sys.argv[4] if mode == 'file' and len(sys.argv) > 4 else sys.argv[3] if mode == 'turnfree' and len(sys.argv) > 3 else 9)
end = time.time() + mins * 60
while time.time() < end:
    if mode == 'file':
        try:
            if sys.argv[3] in open(sys.argv[2], encoding='utf-8', errors='ignore').read():
                print('found', sys.argv[3])
                sys.exit(0)
        except OSError:
            pass
    else:
        out = subprocess.run([sys.executable, 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py', 'show'],
                             capture_output=True, text=True).stdout
        if sys.argv[2] not in out:
            print('free of', sys.argv[2])
            sys.exit(0)
    time.sleep(15)
print('timed out')
sys.exit(1)

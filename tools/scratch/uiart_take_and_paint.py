"""Take the gpu turn the moment it frees (tries every 3 s; tools/turn.py has no queue, and a
holder that gives back and takes again within a minute beat a slower poll), run the repaint,
give the turn back whatever happens."""
import importlib.util
import runpy
import sys
import time

TURN = r"C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
SCR = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
WHO = "ui art: four item icons repainted"
spec = importlib.util.spec_from_file_location("turn", TURN)
turn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(turn)

end = time.time() + 3 * 3600
why = turn.try_take("gpu", WHO)
while why and time.time() < end:
    time.sleep(3)
    why = turn.try_take("gpu", WHO)
if why:
    print("no turn within 3 hours:", why, flush=True)
    sys.exit(1)
print("took the gpu turn at", time.strftime("%H:%M:%S"), flush=True)
try:
    runpy.run_path(SCR + r"\uiart_paint3.py", run_name="__main__")
finally:
    turn.give("gpu", WHO)
    print("gave it back at", time.strftime("%H:%M:%S"), flush=True)

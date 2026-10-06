import sys, os, shutil
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\uiforge")
import smallforge as SF, forge as F
UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\godot\art\ui"
F.save(SF.keycap(), UI + r"\frames\keycap.png")
F.save(SF.track(), UI + r"\bars\track.png")
F.save(SF.segment_on(), UI + r"\frames\segment_on.png")
F.save(SF.row_on(), UI + r"\frames\row_on.png")
F.save(SF.you_arrow(), UI + r"\minimap\you.png")

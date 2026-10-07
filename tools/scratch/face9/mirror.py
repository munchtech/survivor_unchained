"""Mirror this session's own face scripts (new in face9, and the two shot wrappers the batches call) into the repo's
tools/scratch/face9, for the successor."""
import os
import shutil
SRC = os.path.dirname(os.path.abspath(__file__))
DST = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\tools\scratch\face9'
NAMES = ['fair.py', 'regions.py', 'headpose.py', 'irisw.py', 'speck.py', 'speck_sheet.py', 'uv_measure.py', 'uvcrop.py',
         'lip_overlay.py', 'mouth_probe.py', 'plot_profile.py', 'clay_now.py', 'preview_front.py', 'previews.ps1',
         'lay_probe.ps1', 'batch_v12.ps1', 'batch_res.ps1', 'batch_tone.ps1', 'batch_sss.ps1', 'batch_try.ps1',
         'batch_speck.ps1', 'batch_speck2.ps1', 'batch_unlit.ps1', 'lin_down.py', 'which_paint.py', 'repoint9.py',
         'set_mips.py', 'mirror.py', 'shot.ps1', 'shotr.ps1']
os.makedirs(DST, exist_ok=True)
for n in NAMES:
    shutil.copy2(os.path.join(SRC, n), os.path.join(DST, n))
print(len(NAMES), 'mirrored to', DST)

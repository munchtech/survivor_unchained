import os
import sys

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import lamp  # noqa: E402

lamp.build()
print('lamp done', flush=True)

import os
import sys

WT = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0bff3ffe4d3ad748'
sys.path.insert(0, os.path.join(WT, 'tools', 'uiforge'))
import coals  # noqa: E402

coals.build()
print('coals done', flush=True)

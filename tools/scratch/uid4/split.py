"""Split the UI art lead's before/after shots (3840x1080) into halves for viewing at full size."""
import sys
from PIL import Image

src = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-aa9c11f1e40170a4d/godot/.shots/'
out = r'C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/uid4/'
for n in sys.argv[1:]:
    im = Image.open(src + 'beforeafter_' + n + '.png').convert('RGB')
    im.crop((1920, 0, 3840, 1080)).save(out + 'after_' + n + '.jpg', quality=92)
    im.crop((0, 0, 1920, 1080)).save(out + 'before_' + n + '.jpg', quality=92)
print('ok')

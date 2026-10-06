from fontTools.ttLib import TTFont
import glob, os
d = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\art\fonts'
chars = "★▲▼◀▶◆◇•◦✓✕×·—–←→↑↓…"
for f in sorted(glob.glob(os.path.join(d, '*.woff2'))):
    cmap = TTFont(f).getBestCmap()
    print(os.path.basename(f), ''.join(c if ord(c) in cmap else '_' for c in chars))
print('ref', chars)

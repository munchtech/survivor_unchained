import os, re, glob
R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
old = os.path.join(R, 'Ui', 'Skin.cs')
new = os.path.join(R, 'Ui', 'UiArt.cs')
if os.path.exists(old):
    os.replace(old, new)
for f in glob.glob(os.path.join(R, '**', '*.cs'), recursive=True):
    s = open(f, encoding='utf-8').read()
    t = s.replace('public static class Skin\n', 'public static class UiArt\n')
    t = re.sub(r'\bSkin\.(Frame|Has|Icon|Art|Cursors|Tex|Frames)\b', r'UiArt.\1', t)
    if t != s:
        open(f, 'w', encoding='utf-8', newline='').write(t)
        print('edited', os.path.basename(f))

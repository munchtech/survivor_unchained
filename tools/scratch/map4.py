p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\MapScreen.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

# Ignore the texture's size before setting the rect's: a control is never smaller than its
# minimum, and the drawing (1600) would keep its own.
rep("""        world.AddChild(new TextureRect { Texture = Drawing(scene.Data), Size = new Vector2(F, F), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore, TextureFilter = TextureFilterEnum.LinearWithMipmaps });""",
    """        // The expand mode first: a control is never smaller than its minimum, and the drawing's own is 1600.
        world.AddChild(new TextureRect { ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Texture = Drawing(scene.Data), Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore, TextureFilter = TextureFilterEnum.LinearWithMipmaps });""")
rep("""        world.AddChild(new TextureRect { Texture = Fog(seen, Journey.FogN), Size = new Vector2(F, F), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore });""",
    """        world.AddChild(new TextureRect { ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Texture = Fog(seen, Journey.FogN), Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore });""")
rep("""        if (G.Zone?.MapFocus == null) Fit(seen);""", """        minZoom = Math.Min(View.Size.X, View.Size.Y) / F * 0.9f;
        if (G.Zone?.MapFocus == null) Fit(seen);""")
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')

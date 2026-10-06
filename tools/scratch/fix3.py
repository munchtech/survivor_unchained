R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Ui\MapTable.cs', [
("""            $"Maps to places the road forgets: each an ember arena, half an hour and what rules it at the end. {(won > 0 ? $"You have won tier {won}." : "You have won none yet.")} Spoils lean toward what answers the map.");""",
"""            $"Maps to places the road forgets: each an ember arena, half an hour and what rules it at the end. {(won > 0 ? $"You have won tier {won}." : "You have won none yet.")} Spoils lean toward what answers the map.", fit: true);"""),
])
edit(r'Ui\Book.cs', [
("""        if (met.Count == 0) return P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft);""",
"""        if (met.Count == 0) return Style.V(0, P("You have not met anyone yet. Those you speak with are written here, and how they feel about you.", Style.Body, Style.TextItalic, InkSoft));"""),
])
edit(r'Game\Game.cs', [
("""        // Something over the game has the buttons: pad buttons mean their menu meaning first.
        controls.MenuMode = screens.Current != null || hudMode != null;""",
"""        // Something over the game has the buttons: pad buttons mean their menu meaning first.
        controls.MenuMode = screens.Current != null || hudMode != null;
        // --pad (pictures of pad play): the pad stays in hand whatever the window's mouse does.
        if (Args.Has("pad") && keyI > 0) controls.UsingPad = true;"""),
])
print('done')

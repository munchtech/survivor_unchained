p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\ItemViews.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""    static (string Text, bool Good) Delta(string key, double before, double after)""",
"""    /// <summary>A change in words: "+5% Area", and whether it is for the better.</summary>
    public static (string Text, bool Good) Delta(string key, double before, double after)"""),
("""        string? nav = null, Action<ItemInstance>? onAlt = null, Action<int, ItemInstance?, SlotView>? setup = null)
    {""",
"""        string? nav = null, Action<ItemInstance>? onAlt = null, Action<int, ItemInstance?, SlotView>? setup = null, Func<ItemInstance, bool>? dear = null)
    {"""),
("""                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null);""",
"""                onHover != null ? c => onHover(it, c) : null, null, null, nav != null ? $"{nav}:{i}" : null, it != null && onAlt != null ? () => onAlt(it) : null,
                dear: it != null && dear?.Invoke(it) == true);"""),
]
for old, new in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')

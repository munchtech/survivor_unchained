R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui'
p = R + r'\Book.cs'
s = open(p, encoding='utf-8').read()

def rep(old, new):
    global s
    assert old in s, old[:90]
    s = s.replace(old, new, 1)

# Ribbons stand up out of the book's top edge, clear of the words; the open one stands taller.
rep("""        var ribbons = Style.H(14);
        ribbons.Position = new Vector2(70 + 120, 52 - 30);""", """        var ribbons = Style.H(14);
        ribbons.Position = new Vector2(70 + 120, 52 + 22 - 86);""")
rep("""        lt.SizeFlagsVertical = SizeFlags.ShrinkBegin;""", """        lt.SizeFlagsVertical = SizeFlags.ShrinkCenter;""")
rep("""        rt.SizeFlagsVertical = SizeFlags.ShrinkBegin;""", """        rt.SizeFlagsVertical = SizeFlags.ShrinkCenter;""")
rep("""            b.CustomMinimumSize = new Vector2(124, on ? 96 : 70);
            b.SizeFlagsVertical = SizeFlags.ShrinkBegin;""", """            b.CustomMinimumSize = new Vector2(132, on ? 86 : 66);
            b.SizeFlagsVertical = SizeFlags.ShrinkEnd;""")
# An empty leaf carries the house's mark faintly, so it reads as a page waiting, not a hole.
rep("""        Fill(book.Left, left);
        Fill(book.Right, right);""", """        Fill(book.Left, left);
        Fill(book.Right, right);
        if (right is Container rc && rc.GetChildCount() == 0 || right.GetChildCount() == 0)
        {
            var mark = Glyphs.Icon(tab switch { "people" => "talk", "deeds" => "sigil", "codex" => "book", _ => "quest" }, 220, new Color(0.35f, 0.24f, 0.1f, 0.12f));
            mark.Position = (book.Right.Size - new Vector2(220, 220)) / 2;
            book.Right.AddChild(mark);
        }""")
open(p, 'w', encoding='utf-8', newline='').write(s)

o = open(R + r'\Ornate.cs', encoding='utf-8').read()
old = """    public RibbonBox() { ContentMarginLeft = ContentMarginRight = 10; ContentMarginTop = 8; ContentMarginBottom = 22; }"""
assert old in o
o = o.replace(old, """    public RibbonBox() { ContentMarginLeft = ContentMarginRight = 10; ContentMarginTop = 6; ContentMarginBottom = 26; }""", 1)
open(R + r'\Ornate.cs', 'w', encoding='utf-8', newline='').write(o)
print('done')

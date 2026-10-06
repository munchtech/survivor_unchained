p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
old = '''            axes.AddChild(P(label, Style.Small, Style.UiBold, Ink));
            axes.AddChild(Feel(val, 260));
            axes.AddChild(P(Math.Abs(val) < 12 ? "neither way" : $"{(Math.Abs(val) > 55 ? "much " : "")}{(val < 0 ? lo : hi)}".Replace("much unafraid", "quite unafraid"), Style.Caption, Style.TextItalic, InkSoft));'''
new = '''            var name = Style.Label(label, Style.UiBold, Style.Small, Ink, false, HorizontalAlignment.Left, false);
            name.CustomMinimumSize = new Vector2(90, 0);
            axes.AddChild(name);
            axes.AddChild(Feel(val, 260));
            axes.AddChild(Style.Label(Math.Abs(val) < 12 ? "neither way" : $"{(Math.Abs(val) > 55 ? "much " : "")}{(val < 0 ? lo : hi)}".Replace("much unafraid", "quite unafraid"), Style.TextItalic, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false));'''
assert old in s
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')

import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"
p = os.path.join(G, "src", "Ui", "CinemaBars.cs")
s = open(p, encoding="utf-8").read()
old = '''    /// <summary>A line under the picture for this long: the narrator's in italics, unnamed.</summary>
    public void Say(string text, string? speaker, double seconds)
    {
        // The script's '/' marks where a long line breaks.
        words.Text = text.Replace(" / ", "\\n").Replace("/", "\\n");
        words.AddThemeFontOverride("font", speaker == null ? Style.TextItalic : Style.Text);'''
new = '''    /// <summary>A line under the picture for this long: the narrator's in italics,
    /// unnamed; a sung line in italics under its singer's name.</summary>
    public void Say(string text, string? speaker, double seconds, bool sung = false)
    {
        // The script's '/' marks where a long line breaks.
        words.Text = text.Replace(" / ", "\\n").Replace("/", "\\n");
        words.AddThemeFontOverride("font", speaker == null || sung ? Style.TextItalic : Style.Text);'''
assert old in s, "bars"
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(s)
p = os.path.join(G, "src", "Game", "GameCinema.cs")
s = open(p, encoding="utf-8").read()
old = '''bars.Say(l.Text, file.Narrators.Contains(l.SpeakerId ?? "") ? null : l.Speaker, (take?.Sec ?? CineLines.Reading(l.Text)) + c.Num("linger", 0.7));'''
new = '''bars.Say(l.Text, file.Narrators.Contains(l.SpeakerId ?? "") ? null : l.Speaker, (take?.Sec ?? CineLines.Reading(l.Text)) + c.Num("linger", 0.7), l.Sung);'''
assert old in s, "gc"
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")

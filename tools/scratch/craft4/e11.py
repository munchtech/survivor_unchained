from ed import sub

sub("src/Ui/Forge.cs", [
# The hold press says "Hold:" itself.
('"Hold: break down", "break"', '"Break down", "break"'),
('"Hold: bind", $"bind:{n++}"', '"Bind", $"bind:{n++}"'),
('var b = Hold("Hold: steep", q,', 'var b = Hold("Steep", q,'),
# The seam the crafts are for rides the head, before the tabs.
("""        v.AddChild(Kit.Head(title, groups.Count > 1 ? null : note, end));
        if (groups.Count > 1 && note != null) v.AddChild(Style.Label(note, Style.TextItalic, 15, Kit.Dim, false));""",
"""        v.AddChild(Kit.Head(title, note, end));"""),
# The prompts on a quiet plate of their own: over the bright cobbles they could not be read.
("""        var prompts = Prompts();
        prompts.Position = new Vector2(0, 1004);
        prompts.Size = new Vector2(1920, 36);
        AddChild(prompts);""",
"""        var plate = Style.Panel(Kit.PanelBox(18, 6, Kit.Ground with { A = 0.9f }), Prompts());
        plate.MouseFilter = MouseFilterEnum.Ignore;
        var foot = new CenterContainer { Position = new Vector2(0, 996), Size = new Vector2(1920, 48), MouseFilter = MouseFilterEnum.Ignore };
        foot.AddChild(plate);
        AddChild(foot);"""),
])

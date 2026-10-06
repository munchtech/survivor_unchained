from ed import sub

sub("src/Ui/Forge.cs", [
("""        string? where = seam >= 0 && SeamCrafts ? open ? "at the open seam" : $"at {Items.Affix(it.Affixes[seam].Id)?.Name ?? "the seam"}" : null;""",
"""        // ("at of the Wolf" read as a slip: the seam is named by its place)
        string? where = seam >= 0 && SeamCrafts ? open ? "at the open seam" : $"at the {Ordinal(seam)} seam" : null;"""),
("""    Control Closed() => Style.Label(closed!, Style.TextItalic, 17, Style.Bad, true);""",
"""    Control Closed() => Style.Label(closed!, Style.TextItalic, 17, Style.Bad, true);

    static string Ordinal(int k) => k switch { 0 => "first", 1 => "second", 2 => "third", 3 => "fourth", _ => $"{k + 1}th" };"""),
("""            : Kit.Prompts(Kit.Prompt("Click", "Put a piece on the anvil"), Kit.Prompt("Click", "Choose a seam"), Kit.Prompt("Hold", "What cannot be undone"), Kit.Prompt("Esc", "Close"));""",
"""            : SeamCrafts ? Kit.Prompts(Kit.Prompt("Click", "Put a piece on the anvil"), Kit.Prompt("Click", "Choose a seam"), Kit.Prompt("Hold", "What cannot be undone"), Kit.Prompt("Esc", "Close"))
            : Kit.Prompts(Kit.Prompt("Click", "Put a piece on the anvil"), Kit.Prompt("Hold", "What cannot be undone"), Kit.Prompt("Esc", "Close"));"""),
])

from ed import sub
sub("src/Ui/Forge.cs", [
    ("if (came is { } c && c.Uid == it.Uid) body.AddChild(Came(c.Text, c.Good));", "if (came is { } c && c.Uid == it.Uid) body.AddChild(Came(c.Text, c.Mood));"),
    ("            var (text, good) = Crafting.Outcome(steeped, q);\n            came = (uid, text, good);", "            var (text, mood) = Crafting.Outcome(steeped, q);\n            came = (uid, text, mood);"),
    ("    (string Uid, string Text, bool Good)? came;", "    (string Uid, string Text, int Mood)? came;"),
])
sub("src/Ui/Pack.cs", [
    ("        var (text, good) = Crafting.Outcome(it, q);\n        came = (it.Uid, text, good, G.Journey.CraftSaid?.After);",
     "        var (text, mood) = Crafting.Outcome(it, q);\n        came = (it.Uid, text, mood, G.Journey.CraftSaid?.After);"),
    ("    (string Uid, string Text, bool Good, string? Seen)? came;", "    (string Uid, string Text, int Mood, string? Seen)? came;"),
    ("            var col = cm.Good ? ItemViews.SlurryGreen : Style.Bad;\n            var words = Style.V(2, Style.Label(\"STEEPED\", Style.UiHeavy, Style.Badge, col), Style.Label(cm.Text, Style.UiBold, Style.Body, cm.Good ? Style.Ink : Style.Bad, true));",
     "            var col = cm.Mood > 0 ? ItemViews.SlurryGreen : cm.Mood < 0 ? Style.Bad : new Color(\"#9aa890\");\n            var words = Style.V(2, Style.Label(\"STEEPED\", Style.UiHeavy, Style.Badge, col), Style.Label(cm.Text, Style.UiBold, Style.Body, cm.Mood < 0 ? Style.Bad : Style.Ink, true));"),
])

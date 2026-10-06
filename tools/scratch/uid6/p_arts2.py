PAIRS = [
("""            d.AddChild(Style.H(12, icon, Style.V(0, Style.Label(title.ToUpperInvariant(), Style.DisplayLight, 17, Kit.HeadInk), Style.Label(text, Style.Ui, 15, Kit.Ink2, true))));""",
"""            var tv = Style.V(0, Style.Label(title.ToUpperInvariant(), Style.DisplayLight, 17, Kit.HeadInk), Style.Label(text, Style.Ui, 15, Kit.Ink2, true));
            // (the words take the column's width, not the narrowest a word allows)
            tv.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            d.AddChild(Style.H(12, icon, tv));"""),
]

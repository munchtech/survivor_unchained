from ed import sub
sub('src/Ui/Pack.cs', [
("""            var row = Style.H(Style.Gap3, ItemPhotos.Icon(Items.Get(b.Icon).Icon, 48, Style.InkDim),
                Style.V(1, Style.Label($"Broken down: {b.Name}", Style.UiBold, Style.Body, Style.Ink, true),
                    Style.Label($"{Style.Cap1(b.Gives)}, into the pouch for the forge.", Style.TextItalic, Style.Small, Style.InkDim, true)));""",
"""            var words = Style.V(1, Style.Label($"Broken down: {b.Name}", Style.UiBold, Style.Body, Style.Ink, true),
                Style.Label($"{Style.Cap1(b.Gives)}, into the pouch for the forge.", Style.TextItalic, Style.Small, Style.InkDim, true));
            words.CustomMinimumSize = new Vector2(380, 0);
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var row = Style.H(Style.Gap3, ItemPhotos.Icon(Items.Get(b.Icon).Icon, 48, Style.InkDim), words);"""),
])

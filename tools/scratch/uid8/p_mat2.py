PAIRS = [
("""        Label Words(string t, bool quiet = false) => Style.Label(t, quiet ? Style.TextItalic : Style.Text, quiet ? 16 : 18, quiet ? Kit.Dim : Kit.Ink2, true, HorizontalAlignment.Center, false);""", """        // (broken into even lines across the panel's measure, never a word or two alone on the last)
        Label Words(string t, bool quiet = false)
        {
            var f = quiet ? Style.TextItalic : Style.Text;
            int size = quiet ? 16 : 18;
            return Style.Label(Kit.Balance(t, f, size, 620 - 2 * (Margin + 8)), f, size, quiet ? Kit.Dim : Kit.Ink2, false, HorizontalAlignment.Center, false);
        }"""),
]

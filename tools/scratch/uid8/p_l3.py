PAIRS = [
("""        var row = Style.H(6, name, low, g, high);
        row.Alignment = BoxContainer.AlignmentMode.Begin;""", """        // (the groove takes the room between its words, so every row runs the column's width)
        g.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var row = Style.H(6, name, low, g, high);
        row.Alignment = BoxContainer.AlignmentMode.Begin;"""),
]

from ed import sub
sub('src/Ui/Forge.cs', [
("""        words.AddThemeColorOverride("font_color", Style.EmberHi);
        if (!preview) { words.Text = $"Heat {heat} of {full}"; return; }""",
"""        words.AddThemeColorOverride("font_color", Style.EmberHi);
        // Just worked: what it took, said while the cells burn out.
        if (burnFrom >= 0 && !preview)
        {
            words.Text = burnFrom > heat ? $"{burnFrom - heat} heat spent: {heat} of {full}" : $"+{heat - burnFrom} heat: {heat} of {full}";
            if (heat == 0) words.Text = "Set: the last of its heat spent";
            return;
        }
        if (!preview) { words.Text = $"Heat {heat} of {full}"; return; }"""),
("""        if (preview) { pending = (lo, hi, grows); preview = false; Say(); }
        burnFrom = before;
        burnT = 0;
        cells.QueueRedraw();""",
"""        if (preview) { pending = (lo, hi, grows); preview = false; }
        burnFrom = before;
        burnT = 0;
        Say();
        cells.QueueRedraw();"""),
("""            if (burnT > 1.1)
            {
                burnFrom = -1;
                if (pending is { } p) { pending = null; Preview(p.Lo, p.Hi, p.Grows); }
            }""",
"""            if (burnT > 1.6)
            {
                burnFrom = -1;
                Say();
                if (pending is { } p) { pending = null; Preview(p.Lo, p.Hi, p.Grows); }
            }"""),
])

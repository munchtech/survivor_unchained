PAIRS = [
("""    public void ZoneInfo(string name, string? region, int day, TimeOfDay time)
    {
        zoneName.Text = name.ToUpperInvariant();
        foreach (var c in zoneSub.GetChildren()) c.QueueFree();
        zoneSub.AddChild(Glyphs.Icon(time == TimeOfDay.Night ? "moon" : "sun", 15, time == TimeOfDay.Night ? Hex("#b8ccff") : Hex("#ffd890")));
        zoneSub.AddChild(Style.Label($"{time}  ·  Day {day}" + (region != null ? $"  ·  {region}" : ""), Style.Ui, 17, Style.Ink with { A = 0.85f }));
    }""",
"""    public void ZoneInfo(string name, string? region, int day, TimeOfDay time)
    {
        zoneName.Text = name.ToUpperInvariant();
        foreach (var c in zoneSub.GetChildren()) if (c != dial) c.QueueFree();
        // Where the clock runs, its dial says the time of day; elsewhere a sun or a moon.
        if (!dial.Visible) zoneSub.AddChild(Glyphs.Icon(time == TimeOfDay.Night ? "moon" : "sun", 15, time == TimeOfDay.Night ? Hex("#b8ccff") : Hex("#ffd890")));
        zoneSub.AddChild(Style.Label($"{time}  ·  Day {day}" + (region != null ? $"  ·  {region}" : ""), Style.Ui, 17, Style.Ink with { A = 0.85f }));
    }

    /// <summary>The day's clock on its dial by the place's name (null: where the clock does not run).</summary>
    public void Clock(double? clock, bool running)
    {
        bool on = clock != null;
        if (on != dial.Visible)
        {
            dial.Visible = on;
            // (the sun or moon glyph it stands in for comes or goes with it)
            if (zoneSub.GetChildCount() > 1 && zoneSub.GetChild(1) is TextureRect g) g.Visible = !on;
        }
        if (clock is double c) dial.Set(c, running);
    }"""),
("""        zoneSub = Style.H(6);
        zoneSub.Alignment = BoxContainer.AlignmentMode.End;
        c.AddChild(zoneSub);""",
"""        zoneSub = Style.H(6);
        zoneSub.Alignment = BoxContainer.AlignmentMode.End;
        c.AddChild(zoneSub);
        dial = new DayDial { Visible = false, SizeFlagsVertical = Control.SizeFlags.ShrinkEnd };
        zoneSub.AddChild(dial);"""),
("""    Label zoneName = null!;""", """    Label zoneName = null!;
    DayDial dial = null!;"""),
]

from ed import sub
sub('src/Ui/Forge.cs', [
("""    void Strike()
    {
        if (struck is not { } s || Chosen is not { } it || it.Uid != s.Uid) { struck = null; return; }
        struck = null;
        gauge?.Burn(s.Heat);
        if (!rows.TryGetValue(s.Seam, out var r)) return;
        var (row, badge) = r;
        GetTree().CreateTimer(0.03).Timeout += () =>
        {
            if (!IsInstanceValid(row) || !IsInstanceValid(badge)) return;
            badge.PivotOffset = badge.Size / 2;""",
"""    void Strike()
    {
        if (struck is not { } s || Chosen is not { } it || it.Uid != s.Uid) { struck = null; return; }
        if (striking || !IsInsideTree()) return;
        striking = true;
        // A craft can build the page more than once (the gear folded back into the fight, then the
        // pack touched): the moment plays once, a moment later, on the page as it stands then.
        GetTree().CreateTimer(0.05).Timeout += () =>
        {
            striking = false;
            if (!IsInsideTree() || struck is not { } now) return;
            struck = null;
            if (IsInstanceValid(gauge) && gauge!.IsInsideTree()) gauge.Burn(now.Heat);
            if (!rows.TryGetValue(now.Seam, out var r) || !IsInstanceValid(r.Row) || !r.Row.IsInsideTree()) return;
            var (row, badge) = r;
            badge.PivotOffset = badge.Size / 2;"""),
("""            Sparks(row, badge.Position + badge.Size / 2, s.Verb == Verb.Cage);
        };
    }""",
"""            Sparks(row, badge.Position + badge.Size / 2, now.Verb == Verb.Cage);
        };
    }

    bool striking;"""),
])

"""Marks at Vonnra's table: the seam row, the inscribe cards, the badge."""
from ed import sub
F = "src/Ui/Forge.cs"
sub(F, [
    ("""        bool coal = ad?.Kindled != null, skill = ad?.Grants != null, slurry = ad?.Slurry == true, on = k == seam && SeamCrafts;""",
     """        bool coal = ad?.Kindled != null, skill = ad?.Grants != null, slurry = ad?.Slurry == true, mark = ad?.Mark == true, on = k == seam && SeamCrafts;"""),
    ("""        var badge = new GradeBadge(open ? GradeBadge.Mark.Open : coal ? GradeBadge.Mark.Coal : skill ? GradeBadge.Mark.Skill : slurry ? GradeBadge.Mark.Slurry : GradeBadge.Mark.Grade, a?.Tier ?? 0, cap);""",
     """        var badge = new GradeBadge(open ? GradeBadge.Mark.Open : coal ? GradeBadge.Mark.Coal : skill ? GradeBadge.Mark.Skill : slurry ? GradeBadge.Mark.Slurry
            : mark ? GradeBadge.Mark.Inscribed : GradeBadge.Mark.Grade, a?.Tier ?? 0, cap);"""),
    ("""        bool bright = !open && a!.Tier >= Crafting.Bright;""", """        bool bright = !open && !mark && a!.Tier >= Crafting.Bright;"""),
    ("""            : slurry ? $"{ad!.Name}: the slurry's, past its seams; it has no grades\"""",
     """            : slurry ? $"{ad!.Name}: the slurry's, past its seams; it has no grades"
            : mark ? $"{ad!.Name}  ·  a mark at grade {Crafting.Grade(a!.Tier)}: it works in the Wayfinder's maps\""""),
    ("""        words.AddChild(Style.Label(title, Style.UiBold, Style.Body, open ? Style.GoldHi : coal ? Style.EmberHi : slurry ? ItemViews.SlurryGreen : bright ? ItemViews.BrightGrade : Style.Ink, true));""",
     """        words.AddChild(Style.Label(title, Style.UiBold, Style.Body, open ? Style.GoldHi : coal ? Style.EmberHi : slurry ? ItemViews.SlurryGreen : mark ? ItemViews.MarkInk : bright ? ItemViews.BrightGrade : Style.Ink, true));"""),
    ("""        if (Crafting.Does(crafter, Verb.Bind)) v.AddChild(Binding(it, k, open, ad));
        return v;""",
     """        if (Crafting.Does(crafter, Verb.Bind)) v.AddChild(Binding(it, k, open, ad));
        if (Crafting.Does(crafter, Verb.Mark)) v.AddChild(Marking(it, k, open, ad));
        return v;"""),
    ("""    /* ---------------------------------------------------- the slurry's -- */""",
     """    /// <summary>What a map's rulers left, read and written in (design 20.3): each thing carried that holds a
    /// Mark, at the grade it fell at. One Mark to a piece: a second goes where the first was.</summary>
    Control Marking(ItemInstance it, int k, bool open, AffixDef? here)
    {
        var v = Style.V(Style.Gap2);
        int held = it.Affixes.FindIndex(x => Items.Affix(x.Id)?.Mark == true);
        v.AddChild(new Section("Mark", held >= 0 ? "a mark in place of the one it has: one to a piece" : here != null ? $"in place of “{here.Name}”, which is lost; it works in the maps only"
            : "how a map's ruler fought, written into the piece: it works in the Wayfinder's maps"));
        var carried = Crafting.MarksCarried(Ch);
        if (carried.Count == 0)
        {
            v.AddChild(Quiet($"Bring {Him} what a map's ruler leaves: {He} reads how it fought, and writes it into a piece. It works in the Wayfinder's maps, three worn at once."));
            return v;
        }
        if (held >= 0 && held != k)
        {
            v.AddChild(Quiet("Its mark sits in another seam. Choose that seam to write another in its place."));
            return v;
        }
        var grid = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", Style.Gap2);
        grid.AddThemeConstantOverride("v_separation", Style.Gap2);
        int n = 0;
        foreach (var from in carried)
        {
            var m = Crafting.MarkIn(from)!;
            var q = Crafting.Inscribe(X, it, from, open ? -1 : k, crafter);
            q.Before = null;
            var fd = Items.Get(from.Def);
            var card = Craft("Inscribe", q, () => Work(q, () => { Sound.Sfx.Cage(); Sound.Sfx.Discovery(); }),
                $"{Items.Affix(m.Id)?.Name}, at grade {Crafting.Grade(m.Tier)}", ItemPhotos.Icon(fd.Icon, 44, Style.RarityOf(from.Rarity)), $"mark:{n++}",
                $"From your {fd.Name}, which is used up");
            card.CustomMinimumSize = new Vector2(452, 0);
            grid.AddChild(card);
        }
        v.AddChild(grid);
        return v;
    }

    /* ---------------------------------------------------- the slurry's -- */"""),
    ("""    public enum Mark { Grade, Coal, Skill, Open, Slurry }""", """    public enum Mark { Grade, Coal, Skill, Open, Slurry, Inscribed }"""),
    ("""        var col = mark switch { Mark.Coal => Style.Ember, Mark.Open => Style.GoldDim, Mark.Skill => Style.Day, Mark.Slurry => ItemViews.SlurryGreen, _ => bright ? ItemViews.BrightGrade : Style.RarityOf(tier) };""",
     """        var col = mark switch { Mark.Coal => Style.Ember, Mark.Open => Style.GoldDim, Mark.Skill => Style.Day, Mark.Slurry => ItemViews.SlurryGreen, Mark.Inscribed => ItemViews.MarkInk, _ => bright ? ItemViews.BrightGrade : Style.RarityOf(tier) };"""),
])
# Work: a mark rings its seam, as a binding does.
sub(F, [("""            Verb.Temper or Verb.WorkIn or Verb.Cage or Verb.Bind => q.Index >= 0 ? q.Index : at,""",
         """            Verb.Temper or Verb.WorkIn or Verb.Cage or Verb.Bind or Verb.Mark => q.Index >= 0 ? q.Index : at,""")])
sub(F, [("""                case Verb.Bind: Motes(row, at, new Color("#fff4d8"), new Color("#ffd27a"), -30, 1.8); break;""",
         """                case Verb.Bind: Motes(row, at, new Color("#fff4d8"), new Color("#ffd27a"), -30, 1.8); break;
                case Verb.Mark: Motes(row, at, new Color("#efe2ff"), new Color("#9a7ae0"), -30, 1.8); break;""")])
sub(F, [("""                Verb.Bind => (new Color(1f, 0.86f, 0.55f, 0.32f), new Color(1f, 0.95f, 0.78f, 0.9f), 1.6),""",
         """                Verb.Bind => (new Color(1f, 0.86f, 0.55f, 0.32f), new Color(1f, 0.95f, 0.78f, 0.9f), 1.6),
                Verb.Mark => (new Color(0.62f, 0.5f, 0.95f, 0.3f), new Color(0.9f, 0.82f, 1f, 0.9f), 1.6),""")])
sub("src/Ui/ItemViews.cs", [("""    public static readonly Color BrightGrade = new("#eaffd6");""",
    """    public static readonly Color BrightGrade = new("#eaffd6");
    /// <summary>A Mark's: the binders' ink, a violet that is no rarity's.</summary>
    public static readonly Color MarkInk = new("#c4a8ff");""")])

from ed import sub
sub('src/Ui/StillRoom.cs', [
("""        this.crafter = crafter;
        Nav.Prefer = "brew:0";""",
"""        this.crafter = crafter;
        // --focus ID (with --pad): that press has the focus first (pictures).
        Nav.Prefer = Args.Get("focus") ?? "brew:0";"""),
("""            v.AddChild(new Section("Her flask", Crafting.HasFlask(Ch) ? "yours" : "the end of brewing"));""",
"""            v.AddChild(new Section("Her flask", Crafting.HasFlask(Ch) ? "yours: Rook fills it while you sleep" : "Rook fills it while you sleep"));"""),
("""        h.AddChild(presses);
        slab.AddChild(h);
        return slab;
    }

    Control Flask(FlaskRules f)""",
"""        h.AddChild(presses);
        slab.AddChild(h);
        // Just brewed: the row warms and cools, as the still does.
        if (poured == r.Draught) Glow(slab);
        return slab;
    }

    /// <summary>The draught just brewed, for its row's moment when the panel is built again.</summary>
    string? poured;

    static void Glow(Control row)
    {
        var flare = new Panel { MouseFilter = MouseFilterEnum.Ignore, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
        flare.AddThemeStyleboxOverride("panel", Style.Box(new Color(0.55f, 0.75f, 0.45f, 0.35f), new Color(0.85f, 1f, 0.7f, 0.8f), 2, 5, 0));
        row.AddChild(flare);
        flare.CreateTween().TweenProperty(flare, "modulate:a", 0f, 1.0).SetDelay(0.1).SetTrans(Tween.TransitionType.Quad).SetEase(Tween.EaseType.Out);
    }

    Control Flask(FlaskRules f)"""),
("""            (q.Verb == Verb.Buy ? (Action)(() => Sound.Sfx.Loot(true)) : Sound.Sfx.Discovery)();
            if (G.Journey.Make(q)) Refresh();""",
"""            (q.Verb == Verb.Buy ? (Action)(() => Sound.Sfx.Loot(true)) : Sound.Sfx.Pour)();
            poured = q.Verb == Verb.Brew ? q.Def : null;
            if (G.Journey.Make(q)) Refresh();
            poured = null;"""),
])

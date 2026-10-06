import sys
root = sys.argv[1]

def patch(path, pairs):
    q = root + '/' + path
    s = open(q, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (path, old[:100])
        s = s.replace(old, new, 1)
    open(q, 'w', encoding='utf-8').write(s)

patch('src/Ui/GameHud.cs', [
("""    EdgeMarks edges = null!;""",
"""    EdgeMarks edges = null!;
    GroundLabels ground = null!;"""),
("""        edges = new EdgeMarks();
        Style.Fill(edges);
        combat.AddChild(edges);""",
"""        // Loot's names on the ground, under everything else the fight shows (docs/design/LOOT_DESIGN.md §8.1).
        ground = new GroundLabels();
        Style.Fill(ground);
        combat.AddChild(ground);
        edges = new EdgeMarks();
        Style.Fill(edges);
        combat.AddChild(edges);"""),
("""    /// <summary>What matters off the screen, each frame.</summary>
    public void Beyond(List<Beyond> list) => edges.Show(list);""",
"""    /// <summary>What matters off the screen, each frame.</summary>
    public void Beyond(List<Beyond> list) => edges.Show(list);

    /// <summary>Loot's names on the ground, each frame.</summary>
    public void Ground(List<GroundLabel> list) => ground.Show(list);"""),
])

patch('src/Game/Game.cs', [
("""            hud.Beyond(Overlay == null ? Offscreen(fb2) : new());
        }""",
"""            hud.Beyond(Overlay == null ? Offscreen(fb2) : new());
            hud.Ground(Overlay == null ? Labels(fb2) : new());
        }"""),
("""    /// <summary>What the corner map shows now: by day and on the story's roads, not in an arena.</summary>""",
"""    /// <summary>Loot's names on the ground (docs/design/LOOT_DESIGN.md §8.1): what the filter shows, Rare
    /// and up wherever it lies on screen, the rest only near her, so a horde's floor is not a page of text.</summary>
    List<Ui.GroundLabel> Labels(Battle b)
    {
        var o = new List<Ui.GroundLabel>();
        if (scene == null) return o;
        var view = new Rect2(Vector2.Zero, GetViewport().GetVisibleRect().Size);
        double px = b.Player.X, pz = b.Player.Z;
        foreach (var p in b.Pickups.Items)
        {
            if (!p.Alive || p.Loot < 0 || p.Look == Verdict.Hidden || p.Kind is PickupKind.Ember or PickupKind.Gold or PickupKind.Chest) continue;
            var tier = (LootTier)p.Loot;
            double d2 = (p.X - px) * (p.X - px) + (p.Z - pz) * (p.Z - pz);
            if (tier < LootTier.Rare && d2 > 10 * 10 || tier >= LootTier.Material && d2 > 8 * 8) continue;
            var w = new Vector3((float)p.X, (float)scene.HeightAt(p.X, p.Z) + 0.4f, (float)p.Z);
            if (camera.IsPositionBehind(w)) continue;
            var sp = camera.UnprojectPosition(w);
            if (!view.HasPoint(sp)) continue;
            string text = p.Payload is ItemInstance it ? Inventory.Name(it) : p.Ref != null && Items.Find(p.Ref) is { } def ? (p.Value > 1 ? Items.Several(def.Id, (int)p.Value) : def.Name) : "";
            if (text.Length == 0) continue;
            var col = tier switch
            {
                LootTier.Set => new Color("#3fd6c0"),
                LootTier.Material or LootTier.Draught => Style.InkDim,
                LootTier.Chart or LootTier.Book => new Color("#e8d8b0"),
                LootTier.Quest => Style.GoldHi,
                LootTier.Legendary => Style.RarityOf(4),
                LootTier.Storied => Style.RarityOf(5),
                _ => Style.RarityOf((int)tier),
            };
            int loud = tier >= LootTier.Legendary && tier <= LootTier.Storied ? 3 : p.Look == Verdict.Emphasised || tier is LootTier.Epic or LootTier.Set ? 2 : tier >= LootTier.Material || tier == LootTier.Common ? 0 : 1;
            o.Add(new Ui.GroundLabel(sp, text, col, loud, tier == LootTier.Set));
        }
        return o;
    }

    /// <summary>What the corner map shows now: by day and on the story's roads, not in an arena.</summary>"""),
])
print("ok")

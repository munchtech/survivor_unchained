W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "tests/MapTests.cs": [
        ("""    [Fact]
    public void A_charts_suffixes_weaken_the_survivor()""",
         """    /// <summary>The experience lead's shape: three clearings before the ruler's at tiers 1-2, four at
    /// 3-5, five from 6, the other turns of the way only bends; an altar in each clearing but the
    /// first, to three; and the last way to the ruler empty, a breath before it.</summary>
    [Theory]
    [InlineData(1, 3, 1)]
    [InlineData(3, 4, 2)]
    [InlineData(6, 5, 3)]
    public void A_map_has_its_tiers_clearings_and_a_breath_before_its_ruler(int tier, int clearings, int altars)
    {
        var r = Open(Chart("dead", tier));
        var areas = r.Map.Areas;
        Assert.Equal(clearings, areas.Count(a => a.Kind is AreaKind.Clearing or AreaKind.Altar));
        Assert.Equal(altars, areas.Count(a => a.Kind == AreaKind.Altar));
        Assert.NotEqual(AreaKind.Altar, areas.First(a => a.Kind is AreaKind.Clearing or AreaKind.Altar).Kind);
        // Walk the way to the ruler's clearing's edge: nothing set down on its last stretch.
        var last = areas[^2];
        var bc = r.Map.Boss;
        r.B.Player.Iframes = 1e9;
        for (double k = 0; k <= 1; k += 0.05)
        {
            r.B.Player.X = last.X + (bc.X - last.X) * k * 0.8; r.B.Player.Z = last.Z + (bc.Z - last.Z) * k * 0.8;
            Step(r, 0.05);
        }
        Assert.DoesNotContain(r.B.Enemies.Living(), e => (e.X - bc.X) * (e.X - bc.X) + (e.Z - bc.Z) * (e.Z - bc.Z) < 30 * 30
            && (e.X - last.X) * (e.X - last.X) + (e.Z - last.Z) * (e.Z - last.Z) > last.R * last.R && !e.Boss && e.Wake > 0);
    }

    /// <summary>The map's event: lit by the first altar's keeper falling, the people's question asked
    /// three times over about fifty seconds; then a strongbox at the altar, three to five things at
    /// the map's level, its opening shown.</summary>
    [Fact]
    public void The_first_altar_lit_asks_the_peoples_question_and_ends_in_a_strongbox()
    {
        var r = Open(Chart("pack"));
        var altar = r.Map.Altars.First();
        var p = r.B.Player;
        p.X = altar.X; p.Z = altar.Z;
        Step(r, 0.2);
        // The keepers down (an absurd build), the altar is lit and the question asked.
        int waves = 0;
        ChestOpened? chest = null;
        r.Host.Opened = c => chest = c;
        for (double t = 0; t < 75 && chest == null; t += 1 / 60.0)
        {
            p.Hp = r.B.MaxHp; p.Iframes = 1;
            foreach (var e in r.B.Enemies.Living().ToList())
                if (e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z) < 30 * 30)
                    r.B.HitEnemy(e, e.MaxHp * 2, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
            r.Zone.Step(1 / 60.0);
            r.B.Tick(1 / 60.0, 0, 0);
            foreach (var ev in r.B.Events.Drain()) if (ev is Ev.Telegraph { Kind: TelegraphKind.Ground }) waves++;
            r.Host.Pass(1 / 60.0);
            // The strongbox is walked to.
            foreach (var k in r.B.Pickups.Living()) if (k.Kind == PickupKind.Chest && k.Ref == "strongbox") { p.X = k.X; p.Z = k.Z; }
        }
        Assert.True(waves > 10);
        Assert.NotNull(chest);
        Assert.InRange(chest!.Items.Count, 3, 7);
        Assert.Contains(chest.Items, i => i.Kind == ChestItemKind.Gear);
    }

    [Fact]
    public void A_charts_suffixes_weaken_the_survivor()"""),
    ],
    W + "balance/Harness/Headless.cs": [
        ("""    public void ArenaOver(Arena.ArenaResult r) => Result = r;""",
         """    public void ArenaOver(Arena.ArenaResult r) => Result = r;
    /// <summary>A chest opened (its contents, for a test to read).</summary>
    public Action<ChestOpened>? Opened;
    public void Chest(ChestOpened c) => Opened?.Invoke(c);"""),
    ],
}

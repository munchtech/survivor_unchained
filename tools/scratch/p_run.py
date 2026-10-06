PAIRS = [
# fields
("""    bool herald10, herald20, great15, bossUp, won, over;
    double nextHerald, pulseT;
    (double X, double Z)? way;
    Enemy? boss, herald;""",
"""    bool herald10, herald20, great15, bossUp, won, over;
    double nextHerald, pulseT;
    (double X, double Z)? way;
    Enemy? boss, herald;
    /// <summary>What the people put in the field as the night goes on: its stretches, each opened
    /// by a miniboss wearing its verb (Escalation; the combat lead's).</summary>
    readonly Escalation escalation;
    /// <summary>The miniboss on the field (by pool slot and spawn: a slot let go is soon another
    /// creature), whether the long push has had its two, and the long night's turns.</summary>
    Enemy? miniboss;
    double minibossSeed;
    bool reprised;
    int nightTurn, auraAlive;"""),
("""    public override IReadOnlyList<string> Creatures => people.Arena.Select(h => h.Def).Append(people.Champion).Append(BossDef).Distinct().ToList();""",
"""    public override IReadOnlyList<string> Creatures => people.Arena.Select(h => h.Def).Concat(people.Stretches.Select(s => s.Miniboss))
        .Append(people.Champion).Append(BossDef).Distinct().ToList();"""),
("""    double Seconds => B?.Time ?? 0;
    double Minute => Seconds / 60;
    double End => Spec.Minutes * 60;""",
"""    double Seconds => B?.Time ?? 0;
    /// <summary>The night's clock, in minutes of a thirty-minute night: a story's twenty-minute night
    /// runs it half again as fast, so it is the same night (its kinds, levels, heralds, stretches
    /// and great blessing) told quicker. Past the boss, real minutes.</summary>
    double Minute => Seconds <= End ? Seconds / 60 * Pace : 30 + (Seconds - End) / 60;
    /// <summary>How much faster than a table's thirty minutes this night runs.</summary>
    double Pace => 30 / Spec.Minutes;
    double End => Spec.Minutes * 60;
    /// <summary>What the night calls the boss's coming, and its middle, in words.</summary>
    string HourName => Spec.Minutes switch { 30 => "the half hour", 20 => "the twentieth minute", 15 => "the quarter hour", _ => "the boss's hour" };
    string MiddleName => Spec.Minutes switch { 30 => "The fifteenth minute", 20 => "The tenth minute", _ => "Midnight" };
    static string Cap(string s) => s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];"""),
("""        pacing = new ArenaPacing(spec.Minutes * 60);
        Recount();
        lean = MapOffers.Lean(spec.Map, spec.People);
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot, OnPickup = OnPickup };""",
"""        pacing = new ArenaPacing(spec.Minutes * 60);
        escalation = new Escalation(people);
        Recount();
        lean = MapOffers.Lean(spec.Map, spec.People);
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot, OnPickup = OnPickup, OnCalled = (c, _) => Harden(c, false) };"""),
("""        b.Rules.FodderGold = 0.02;
""",
"""        b.Rules.FodderGold = 0.02;
        // A shorter night pays its ember quicker, so its boss meets the build a table's would.
        b.Rules.EmberGain *= Pace;
"""),
("""        pacing.SkipTo(seconds);
        hushed = pacing.Hush(seconds);""",
"""        pacing.SkipTo(seconds);
        escalation.SkipTo(Minute);
        hushed = pacing.Hush(seconds);"""),
# kinds from the escalation
("""        var open = people.Arena.Where(h => h.From <= Minute).ToList();
        double W((string Def, double Weight, double From) h) => h.Weight * (1 + (Minute - h.From) / 8);""",
"""        var open = escalation.Kinds(Minute).ToList();
        double W((string Def, double Weight, double From) h) => h.Weight * (1 + (Minute - h.From) / 8);"""),
("""    string Strongest() => people.Arena.Where(h => h.From <= Minute).OrderByDescending(h => Enemies.Get(h.Def).Health).First().Def;""",
"""    string Strongest() => escalation.Kinds(Minute).OrderByDescending(h => Enemies.Get(h.Def).Health).First().Def;"""),
("""                var melee = people.Arena.Where(h => h.From <= Minute && Enemies.Get(h.Def).Ranged == null).Select(h => h.Def).FirstOrDefault();
                if (melee == null) return null;
                def = melee;
            }
            else rangedAlive++;
        }""",
"""                var melee = escalation.Kinds(Minute).Where(h => Enemies.Get(h.Def).Ranged == null).Select(h => h.Def).FirstOrDefault();
                if (melee == null) return null;
                def = melee;
            }
            else rangedAlive++;
        }
        // One rallying voice at a time (a howler, a drummer, a bell): two would leave no plain first kill.
        if (Enemies.Get(def).Aura != null && !elite)
        {
            if (auraAlive > 0) def = people.Arena[0].Def;
            else auraAlive++;
        }"""),
("""        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level() + (elite ? 1 : 0), Elite = elite, Style = st });
        // The crowd softens as the night goes on, so the survivor's growth shows
        // as a horde that melts (docs/SKILLS_DESIGN.md, "The power curve");
        // champions, heralds and the boss keep the steep curve and are the test.
        if (e != null && !elite && def != BossDef) e.MaxHp = e.Hp = e.MaxHp / FodderEase(Math.Min(Minute, End / 60));
        // Past the half hour they harden by the minute and never stop (LongNight).
        if (e != null && Beyond > 0)
        {
            var (hp, dmg, pace) = Hardening(Beyond);
            e.MaxHp = e.Hp = e.MaxHp * hp;
            e.Damage *= dmg;
            e.Speed *= pace;
        }
        return e;
    }""",
"""        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level() + (elite ? 1 : 0), Elite = elite, Style = st });
        if (e != null) Harden(e, elite || def == BossDef);
        return e;
    }

    /// <summary>The night's hand on what comes: the crowd softens as the night goes on, so the
    /// survivor's growth shows as a horde that melts (docs/SKILLS_DESIGN.md, "The power curve"),
    /// while champions, heralds, minibosses and the boss keep the steep curve and are the test; past
    /// the boss everything hardens by the minute and never stops (LongNight). The called (a
    /// miniboss's whistle, the ground opening) are the crowd too.</summary>
    void Harden(Enemy e, bool champion)
    {
        if (!champion && !e.Elite) e.MaxHp = e.Hp = e.MaxHp / FodderEase(Math.Min(Minute, 30));
        if (Beyond > 0)
        {
            var (hp, dmg, pace) = Hardening(Beyond);
            e.MaxHp = e.Hp = e.MaxHp * hp;
            e.Damage *= dmg;
            e.Speed *= pace;
        }
    }

    /* ------------------------------------------- champions, Signs, minibosses -- */

    /// <summary>Signs on a champion (Content/Signs.cs): drawn from those its people have opened so
    /// far, as many as asked, never two that may not go together, and no second rallying voice.</summary>
    void Sign(Enemy e, int n)
    {
        if (n <= 0) return;
        var open = escalation.Signs(Minute);
        var worn = new List<string>();
        for (int k = 0; k < n; k++)
        {
            var fit = open.Where(s => Signs.Fits(e.Def, s, worn) && !(s == "bannered" && auraAlive > 0)).ToList();
            if (fit.Count == 0) break;
            var s = fit[(int)(R() * fit.Count)];
            worn.Add(s);
            if (s == "bannered") auraAlive++;
        }
        if (worn.Count == 0) return;
        double was = e.Def.Speed;
        e.Def = Signs.Wear(e.Def, worn);
        e.Speed *= e.Def.Speed / was;
    }

    /// <summary>A champion's Signs for this tier and minute.</summary>
    int SignsFor(bool herald) => Escalation.SignCount(Spec.Tier, Minute, herald, returns);

    bool MinibossUp => miniboss is { Alive: true } m && m.Seed == minibossSeed && m.State != EnemyState.Dying;

    /// <summary>A stretch's miniboss (or one come again in the long night): its verb on one big body
    /// first, named, its lesson said, the crowd's lanes held off a moment so it is read; it carries
    /// a chest. The kinds its stretch brings join the horde from now.</summary>
    Enemy? Miniboss(string def, int signs, string? kicker, double a)
    {
        if (Around(a, 19) is not var (x, z)) return null;
        var e = Spawn(def, x, z, true, SpawnStyle.Walk);
        if (e == null) return null;
        // Between a champion's turn (twice) and a herald (five to six times), as it should be.
        e.MaxHp = e.Hp = e.MaxHp * (1.6 + 0.6 * Spec.Tier) * (1 + Beyond / 10);
        Sign(e, signs);
        e.Named = new Named { Title = e.Def.Name };
        chests.Add(e.Id);
        miniboss = e;
        minibossSeed = e.Seed;
        B!.Charges.Calm(B, 6);
        if (kicker != null) G.Announce(new Announcement(e.Def.Name, e.Def.Lesson, "danger", 3.2, kicker));
        return e;
    }

    /// <summary>The night's minibosses: each stretch's as it is due (never in a herald's duel or the
    /// hush, and one at a time), and in the long push the two worst it has met, together.</summary>
    void Minibosses()
    {
        if (won || bossUp || MinibossUp || heraldAt > 0 || pacing.Hush(Seconds) || Seconds >= End - 90) return;
        if (escalation.Due(Minute) is int i)
        {
            escalation.Came(i);
            var st = people.Stretches[i];
            double a = R() * Math.PI * 2;
            if (Miniboss(st.Miniboss, 0, Cap(people.Name), a) is { } mb)
                // A few of what it brings beside it, so the verb is seen on the crowd's own bodies at once.
                foreach (var k in st.Joins.Take(1)) Group(k, 3 + Spec.Tier, mb.X, mb.Z, 2.5);
        }
        else if (!reprised && Minute >= 25 && escalation.Met(Minute) is { Count: >= 2 } met)
        {
            reprised = true;
            double a = R() * Math.PI * 2;
            var two = met.OrderBy(_ => R()).Take(2).ToList();
            Miniboss(two[0], 1, null, a);
            var second = miniboss;
            Miniboss(two[1], 1, null, a + Math.PI);
            // The bar follows the first; both carry chests.
            if (second != null) { miniboss = second; minibossSeed = second.Seed; }
            G.Announce(new Announcement("The long push", $"{Enemies.Get(two[0]).Name} and {Enemies.Get(two[1]).Name}, from both sides", "danger", 3.2, Cap(people.Name)));
        }
    }"""),
# crowd champions wear a Sign from the tenth minute at the second tier and above
("""            if (Spawn(def, sx, sz, R() < 0.012 * elites * (1 + Minute / 12)) is { } e) o.Add(e);""",
"""            if (Spawn(def, sx, sz, R() < 0.012 * elites * (1 + Minute / 12)) is { } e)
            {
                // A champion in the crowd wears a Sign from the tenth minute above the first tier.
                if (e.Elite && Spec.Tier >= 2 && Minute >= 10) Sign(e, 1);
                o.Add(e);
            }"""),
# step: aura count, minibosses, event spacing
("""            alive++;
            if (e.Def.Ranged != null) rangedAlive++;
        }""",
"""            alive++;
            if (e.Def.Ranged != null) rangedAlive++;
            if (e.Def.Aura != null) auraAlive++;
        }"""),
("""        int alive = 0;
        rangedAlive = 0;""",
"""        int alive = 0;
        rangedAlive = auraAlive = 0;"""),
("""            if (pacing.Next(Seconds, R) is Turn t)
            {
                eventT = (60 + R() * 25) / (1 + waves);""",
"""            if (pacing.Next(Seconds, R) is Turn t)
            {
                // (A shorter night has its turns closer, so it has as many.)
                eventT = (60 + R() * 25) / (1 + waves) / Pace;"""),
("""        if (!runUp && !won && Seconds >= End - 120) RunUp();
        if (makingWay.Count > 0) MakingWay();""",
"""        Minibosses();
        if (!runUp && !won && Seconds >= End - 120) RunUp();
        if (makingWay.Count > 0) MakingWay();"""),
("""            G.Announce(new Announcement("The fifteenth minute", "A great blessing", "reward", 2.6));""",
"""            G.Announce(new Announcement(MiddleName, "A great blessing", "reward", 2.6));"""),
# champion turns and captains wear Signs
("""                    var champ = Spawn(Strongest(), x, z, true);
                    if (champ == null) continue;
                    champ.MaxHp = champ.Hp = champ.MaxHp * 2;
                    chests.Add(champ.Id);""",
"""                    var champ = Spawn(Strongest(), x, z, true);
                    if (champ == null) continue;
                    champ.MaxHp = champ.Hp = champ.MaxHp * 2;
                    Sign(champ, SignsFor(false));
                    chests.Add(champ.Id);"""),
("""                string def = people.Arena.Where(h => h.From <= m).OrderByDescending(h => Enemies.Get(h.Def).Speed).First().Def;""",
"""                string def = Fastest();"""),
("""        var c = Spawn(Strongest(), x, z, true);
        if (c == null) return;
        c.MaxHp = c.Hp = c.MaxHp * 2;
        chests.Add(c.Id);""",
"""        var c = Spawn(Strongest(), x, z, true);
        if (c == null) return;
        c.MaxHp = c.Hp = c.MaxHp * 2;
        Sign(c, SignsFor(false));
        chests.Add(c.Id);"""),
("""    bool Has(string def) => people.Arena.Any(h => h.Def == def && h.From <= Minute);""",
"""    bool Has(string def) => escalation.Fields(def, Minute);"""),
("""    string Fastest() => people.Arena.Where(h => h.From <= Minute).OrderByDescending(h => Enemies.Get(h.Def).Speed).First().Def;""",
"""    string Fastest() => escalation.Kinds(Minute).OrderByDescending(h => Enemies.Get(h.Def).Speed).First().Def;"""),
# herald signs
("""        herald.Damage *= 1.2;
        chests.Add(herald.Id);
        herald.Named = new Named { Title = $"Herald of {people.Name}" };""",
"""        herald.Damage *= 1.2;
        Sign(herald, SignsFor(true));
        chests.Add(herald.Id);
        herald.Named = new Named { Title = $"Herald of {people.Name}" };"""),
# words by the night
("""            : new Announcement("The half hour nears", "It comes from where the sign was", "danger", 2.6));""",
"""            : new Announcement($"{Cap(HourName)} nears", "It comes from where the sign was", "danger", 2.6));"""),
("""            again ? (returns == 1 ? "Again" : $"Again, the {Ordinal(returns + 1)} time") : "The half hour"));""",
"""            again ? (returns == 1 ? "Again" : $"Again, the {Ordinal(returns + 1)} time") : Cap(HourName)));"""),
("""            Hint = () => $"Won. Or stay: {Clock(Seconds - End)} past the half hour",""",
"""            Hint = () => $"Won. Or stay: {Clock(Seconds - End)} past {HourName}","""),
("""            steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} past the half hour", Optional: true));""",
"""            steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} past {HourName}", Optional: true));"""),
# long night: heralds and minibosses in turn
("""        // A herald between the returns, not on one's heels.
        if (Seconds >= nextHerald)
        {
            nextHerald += 300;
            if (!bossUp && Math.Abs(Seconds - nextReturn) > 90) Herald();
        }""",
"""        // Between the returns, not on one's heels: a herald, then two of the night's minibosses come
        // back together, signed, then a herald again.
        if (Seconds >= nextHerald)
        {
            nextHerald += 300;
            if (!bossUp && Math.Abs(Seconds - nextReturn) > 90)
            {
                var met = escalation.Met(Minute);
                if (nightTurn++ % 2 == 0 || met.Count == 0) Herald();
                else
                {
                    double a = R() * Math.PI * 2;
                    var two = met.OrderBy(_ => R()).Take(2).ToList();
                    foreach (var (def, k) in two.Select((d, k) => (d, k))) Miniboss(def, SignsFor(false), null, a + k * Math.PI);
                    G.Announce(new Announcement("The dark sends them back", string.Join(" and ", two.Select(d => Enemies.Get(d).Name)), "danger", 3, "The long night"));
                }
            }
        }"""),
# victory: the ember's pace back to the table's
("""        won = true;
        bossUp = false;
        boss = null;
        nextHerald = Seconds + 300;""",
"""        won = true;
        bossUp = false;
        boss = null;
        // The long night runs in real minutes, whatever the night before it.
        B!.Rules.EmberGain /= Pace;
        nextHerald = Seconds + 300;"""),
# the bar
("""        else if (herald is { Alive: true } h && h.State != EnemyState.Dying) G.SetBoss(new BossBar(h.Named?.Title ?? $"Herald of {people.Name}", people.Name, h.Hp, h.MaxHp, IsBoss: false));""",
"""        else if (herald is { Alive: true } h && h.State != EnemyState.Dying)
            G.SetBoss(new BossBar(h.Named?.Title ?? $"Herald of {people.Name}", h.Def.Signs.Length > 0 ? string.Join(", ", h.Def.Signs.Select(s => Signs.Get(s).Name)) : people.Name, h.Hp, h.MaxHp, IsBoss: false));
        else if (MinibossUp && miniboss is { } mb)
            G.SetBoss(new BossBar(mb.Def.Name, mb.Def.Lesson.Length > 0 ? mb.Def.Lesson : people.Name, mb.Hp, mb.MaxHp, IsBoss: false));"""),
]

W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Zones\ArenaRun.cs', [
# header comment
(''' *   beyond       it goes on, and harder by the minute (a herald every five),
 *                until the survivor takes the way out that opened where the
 *                boss fell, or falls''',
''' *   the long     it goes on and never ends (the owner: "endless is truly
 *   night        endless"): harder by the minute, the dark swearing one of
 *                the table's oaths every five minutes, what rules the people
 *                coming again every quarter hour, heralds between, until the
 *                survivor takes the way out that opened where the boss fell,
 *                or falls'''),
# fields
('''    readonly List<OathDef> oaths;
    readonly double packSize, elites, ember, gear;
    readonly int levels, waves;''',
'''    readonly List<OathDef> oaths;
    /// <summary>The dark's own oaths, sworn one by one in the long night (and how many
    /// times it has deepened since it ran out of them).</summary>
    readonly List<OathDef> dark = new();
    int deeper;
    double packSize, elites, gear;
    int levels, waves;'''),
('''        oaths = spec.Oaths.Select(MapOffers.Oath).ToList();
        packSize = oaths.Aggregate(1.0, (a, o) => a * o.PackSize);
        elites = oaths.Aggregate(1.0, (a, o) => a * o.Elites);
        ember = oaths.Aggregate(1.0, (a, o) => a * o.Ember);
        gear = oaths.Aggregate(1.0, (a, o) => a * o.Gear);
        levels = oaths.Sum(o => o.Levels);
        waves = oaths.Sum(o => o.Waves);
        lean = MapOffers.Lean(spec.Map, spec.People);''',
'''        oaths = spec.Oaths.Select(MapOffers.Oath).ToList();
        Recount();
        lean = MapOffers.Lean(spec.Map, spec.People);'''),
('''    /// <summary>Always night: the ember burns only in the dark.</summary>
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Night;''',
'''    /// <summary>What every oath sworn, the table's and the dark's, comes to.</summary>
    void Recount()
    {
        var all = oaths.Concat(dark).ToList();
        packSize = all.Aggregate(1.0, (a, o) => a * o.PackSize);
        elites = all.Aggregate(1.0, (a, o) => a * o.Elites);
        gear = all.Aggregate(1.0, (a, o) => a * o.Gear);
        levels = all.Sum(o => o.Levels) + 2 * deeper;
        waves = all.Sum(o => o.Waves);
    }

    /// <summary>Always night: the ember burns only in the dark.</summary>
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Night;'''),
# spawn ramp
('''        // Past the half hour they harden by the minute, until something gives.
        if (e != null && Beyond > 0)
        {
            double m = Beyond;
            e.MaxHp = e.Hp = e.MaxHp * (1 + 0.1 * m + 0.006 * m * m);
            e.Damage *= 1 + 0.035 * m;
        }
        return e;''',
'''        // Past the half hour they harden by the minute and never stop (LongNight).
        if (e != null && Beyond > 0)
        {
            var (hp, dmg, pace) = Hardening(Beyond);
            e.MaxHp = e.Hp = e.MaxHp * hp;
            e.Damage *= dmg;
            e.Speed *= pace;
        }
        return e;'''),
# herald + long night in Step
('''        if (won && Seconds >= nextHerald) { nextHerald += 300; Herald(); }''',
'''        if (won) LongNight();'''),
# RunUp again
('''    void RunUp(bool quiet = false)
    {''',
'''    void RunUp(bool quiet = false, bool again = false)
    {'''),
('''        if (!quiet) G.Announce(new Announcement("The half hour nears", "It comes from where the sign was", "danger", 2.6));''',
'''        if (!quiet) G.Announce(again ? new Announcement($"{BossName} stirs again", "It comes from where the sign was, stronger", "danger", 2.6)
            : new Announcement("The half hour nears", "It comes from where the sign was", "danger", 2.6));'''),
# Boss again
('''    void Boss()
    {
        bossUp = true;
        var p = B!.Player;''',
'''    void Boss(bool again = false)
    {
        bossUp = true;
        bossShare = 0.4;
        var p = B!.Player;'''),
('''            boss.MaxHp = boss.Hp = boss.MaxHp * (script?.HealthMul(Spec.Tier) ?? 12 + 2 * Spec.Tier);
            boss.Damage *= script?.DamageMul ?? 1.3;''',
'''            boss.MaxHp = boss.Hp = boss.MaxHp * (script?.HealthMul(Spec.Tier) ?? 12 + 2 * Spec.Tier);
            // Come again, it is the first fight's length and a part more each time (its blows
            // harden with the night, as everything does); not the night's hardening on its
            // health too, which would make a quarter hour's return a ten-minute wall.
            if (!again) firstBossHp = boss.MaxHp;
            else boss.MaxHp = boss.Hp = firstBossHp * (1 + ReturnGrowth * returns);
            boss.Damage *= script?.DamageMul ?? 1.3;'''),
('''        G.Announce(new Announcement(BossName, script != null ? $"{BossTitle} · Weakness: {script.WeaknessText}" : BossTitle, "danger", 3.4, "The half hour"));
        Objectives();
    }''',
'''        G.Announce(new Announcement(BossName, script != null ? $"{BossTitle} · Weakness: {script.WeaknessText}" : BossTitle, "danger", 3.4,
            again ? (returns == 1 ? "Again" : $"Again, the {Ordinal(returns + 1)} time") : "The half hour"));
        Objectives();
    }

    static string Ordinal(int n) => n switch { 2 => "second", 3 => "third", 4 => "fourth", 5 => "fifth", 6 => "sixth", 7 => "seventh", 8 => "eighth", 9 => "ninth", 10 => "tenth", _ => $"{n}th" };

    /* ---------------------------------------------------- the long night -- */

    /* Past the win the night does not end; only a fall ends it, or the way out
     * (the owner: "endless is truly endless - just keep ramping up till its
     * impossible (or not if the users get better and better and finding ways to
     * win haha)"). It climbs on three lines at once, so that it is new pressure
     * and not only bigger numbers:
     *
     *   the horde    hardens by the minute (Hardening): smoothly, with no cliff,
     *                for the first three quarters of an hour past the half hour,
     *                where a great build has its hour; then compounding, so no
     *                build, however broken, holds for ever. A little quicker too,
     *                to a ceiling (pace a player can still read).
     *   the dark     swears one more of the table's oaths every five minutes
     *                (DarkDeck: each a new question with its answers, named as it
     *                comes, listed with the run's own, and paying what it pays at
     *                the table); never the moonless, since the night must stay
     *                readable. Out of oaths, it deepens: two levels a time.
     *   returns      what rules the people comes again every quarter hour, its
     *                sign a minute before, its own fight, a part stronger each
     *                time, its chest a card richer; heralds in between.
     *
     * Fair throughout: the crowd's number, its throwers and every telegraph keep
     * their caps, nothing kills without a mark, every new pressure is announced
     * with what it asks. */

    /// <summary>The order the dark swears the table's oaths: a verb, then a number, then a
    /// verb, so each five minutes asks something new (the table's own are passed over).</summary>
    static readonly string[] DarkDeck = ["hunt", "embers", "champions", "winter", "vigil", "ruin", "iron", "blight", "swarm", "deep"];
    /// <summary>A returning boss's health over the first's, per return.</summary>
    public const double ReturnGrowth = 0.35;
    double nextDark, nextReturn, firstBossHp;
    bool returnSigned;
    int returns;
    /// <summary>How many times what rules the people has come again (and been beaten, if it is down).</summary>
    public int Returns => returns;
    /// <summary>The dark's oaths sworn so far, and how often it has deepened since.</summary>
    public int DarkSworn => dark.Count + deeper;

    /// <summary>What the night does to a creature `m` minutes past the half hour: its health,
    /// its blows and its pace, over what it would have been at the half hour.</summary>
    public static (double Health, double Damage, double Pace) Hardening(double m)
    {
        // Compounding from three quarters of an hour past: a fortieth a minute.
        double press = m > 45 ? Math.Pow(1.025, m - 45) : 1;
        return ((1 + 0.1 * m + 0.006 * m * m) * press, (1 + 0.035 * m) * press, 1 + Math.Min(0.3, 0.005 * m));
    }

    void LongNight()
    {
        if (Seconds >= nextDark) { nextDark += 300; DarkSwears(); }
        if (!bossUp && !returnSigned && Seconds >= nextReturn - 60) { returnSigned = true; RunUp(again: true); }
        if (!bossUp && Seconds >= nextReturn) { returns++; returnSigned = false; nextReturn += 900; Boss(again: true); }
        // A herald between the returns, not on one's heels.
        if (Seconds >= nextHerald)
        {
            nextHerald += 300;
            if (!bossUp && Math.Abs(Seconds - nextReturn) > 90) Herald();
        }
    }

    /// <summary>The dark swears one more oath: its rule from now on, what it pays, and its name on screen.</summary>
    void DarkSwears()
    {
        var next = DarkDeck.Select(MapOffers.Oath).FirstOrDefault(o => !oaths.Contains(o) && !dark.Contains(o));
        if (next != null)
        {
            dark.Add(next);
            next.Rule?.Invoke(B!.Rules);
            B!.Rules.EmberGain *= next.Ember;
            Recount();
            G.Announce(new Announcement($"The dark swears the {next.Name}", $"{next.Asks}. {next.Gives}. Answer: {next.Answer}", "danger", 3.6, "The long night"));
        }
        else
        {
            deeper++;
            Recount();
            G.Announce(new Announcement("The dark deepens", "Everything that comes is two levels stronger", "danger", 3, "The long night"));
        }
        Objectives();
    }

    /// <summary>What rules the people, beaten again: its chest, and the night goes on.</summary>
    void Felled()
    {
        bossUp = false;
        boss = null;
        eventT = 20;
        G.Announce(new Announcement($"{BossName} is beaten again", $"It will come again in a quarter hour, stronger", "reward", 3.4));
        Objectives();
    }'''),
# IBossArena.Won
('''    void IBossArena.Won(double x, double z)
    {
        if (over || won) return;
        var b = boss;
        if (b != null) foreach (var l in OnLoot(b)) B!.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);
        Victory(x, z);
    }''',
'''    void IBossArena.Won(double x, double z)
    {
        if (over || !bossUp) return;
        var b = boss;
        if (b != null) foreach (var l in OnLoot(b)) B!.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);
        if (won) Felled();
        else Victory(x, z);
    }'''),
# boss chest richer on returns
('''            int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= e.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == 0 ? 1 : 0);''',
'''            int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= e.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == bossBlowsBefore ? 1 : 0) + returns;'''),
('''        if (e == boss && !over) { script?.Fell(e); Victory(e.X, e.Z); }''',
'''        if (e == boss && !over)
        {
            script?.Fell(e);
            if (won) Felled();
            else Victory(e.X, e.Z);
        }'''),
# victory sets the long night's clocks
('''        won = true;
        bossUp = false;
        boss = null;
        nextHerald = Seconds + 300;
        eventT = 20;''',
'''        won = true;
        bossUp = false;
        boss = null;
        nextHerald = Seconds + 300;
        nextDark = Seconds + 300;
        nextReturn = Seconds + 900;
        eventT = 20;'''),
('''        G.Announce(new Announcement($"{Spec.Name} is won", "The way out is open. Or stay, and see how far the ember goes.", "reward", 4, "Victory"));''',
'''        G.Announce(new Announcement($"{Spec.Name} is won", "The way out is open. Or stay: the night does not end, and it only gets harder.", "reward", 4, "Victory"));'''),
# objectives
('''        var steps = new List<Step>
        {
            won ? new Step($"{BossName} is dead: the arena is won", Done: true)
            : bossUp ? new Step($"{BossName} has come: kill it")
            : new Step($"Survive: {left / 60}:{left % 60:00} until {BossName} comes"),
        };
        if (won) steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} past the half hour", Optional: true));
        foreach (var o in oaths) steps.Add(new Step($"{o.Name}: {o.Asks.ToLowerInvariant()}", Optional: true));''',
'''        bool goesDown = script is Grimtunnel { Ganger: false };
        var steps = new List<Step>
        {
            won ? new Step(goesDown ? $"{BossName} is driven back down: the arena is won" : $"{BossName} is beaten: the arena is won", Done: true)
            : bossUp ? new Step($"{BossName} has come: {(goesDown ? "drive him back down" : "beat it")}")
            : new Step($"Survive: {left / 60}:{left % 60:00} until {BossName} comes"),
        };
        if (won)
        {
            steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} past the half hour", Optional: true));
            if (bossUp) steps.Add(new Step($"{BossName} has come again", Optional: true));
            else
            {
                int back = (int)Math.Max(0, nextReturn - Seconds);
                steps.Add(new Step($"{BossName} comes again in {back / 60}:{back % 60:00}", Optional: true));
            }
            if (dark.Count > 0 || deeper > 0)
                steps.Add(new Step($"The dark has sworn {string.Join(", ", dark.Select(o => o.Name.Replace("Oath of ", "")))}{(deeper > 0 ? $", and deepened {deeper} times" : "")}", Optional: true));
        }
        foreach (var o in oaths) steps.Add(new Step($"{o.Name}: {o.Asks.ToLowerInvariant()}", Optional: true));'''),
])

# the unscathed bonus counts this fight's blows, not the run's
edit(r'logic\Play\Zones\ArenaRun.cs', [
('''    void Boss(bool again = false)
    {
        bossUp = true;
        bossShare = 0.4;''',
'''    /// <summary>The run's boss blows taken before this fight (its chest pays for a clean one).</summary>
    int bossBlowsBefore;

    void Boss(bool again = false)
    {
        bossUp = true;
        bossShare = 0.4;
        bossBlowsBefore = B!.BossBlowsTaken;'''),
])

# the oaths' ember is paid: it never was
edit(r'logic\Sim\Battle.cs', [
('''    /// <summary>How fast a boss's stagger bar fills (the Oath of Iron fills it slower).</summary>
    public double StaggerTaken = 1;''',
'''    /// <summary>How fast a boss's stagger bar fills (the Oath of Iron fills it slower).</summary>
    public double StaggerTaken = 1;
    /// <summary>The ember the dead leave, over the usual (an oath's pay: "half again the ember").</summary>
    public double EmberGain = 1;'''),
('''            double xp = e.Def.Xp * Content.Enemies.ScaleFor(e.Level).Xp;''',
'''            double xp = e.Def.Xp * Content.Enemies.ScaleFor(e.Level).Xp * Rules.EmberGain;'''),
])
edit(r'logic\Maps\MapOffers.cs', [
('''        var r = new MapRules();
        foreach (var o in spec.Oaths) Oath(o).Rule?.Invoke(r);
        return r;''',
'''        var r = new MapRules();
        foreach (var o in spec.Oaths) { Oath(o).Rule?.Invoke(r); r.EmberGain *= Oath(o).Ember; }
        return r;'''),
])
print("ok")

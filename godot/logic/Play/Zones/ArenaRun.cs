using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Play.Zones;

/* An ember arena, run (Arena/Arena.cs): a horde that thickens by the minute.
 *
 *   the horde    kept at a number that climbs from a score to a few hundred;
 *                a people's kinds join as the minutes pass, and grow stronger
 *   events       every minute or so, in turn: a closing ring, a champion and
 *                its escort (a chest when it falls), a stampede, a swarm
 *   heralds      at ten and twenty minutes, a champion of champions
 *   the boss     at the half hour, what rules the people comes; kill it and
 *                the arena is won
 *   the long     it goes on and never ends (the owner: "endless is truly
 *   night        endless"): harder by the minute, the dark swearing one of
 *                the table's oaths every five minutes, what rules the people
 *                coming again every quarter hour, heralds between, until the
 *                survivor takes the way out that opened where the boss fell,
 *                or falls
 *
 * The ember starts at nothing here and goes nowhere afterward; the cards
 * come often. A great blessing is chosen as it begins and another at the
 * fifteenth minute, from all of them, whoever the survivor is. Win or die,
 * the arena is over and the story goes on. */
public sealed class ArenaRun : ZoneRuntime, IBossArena
{
    public readonly ArenaSpec Spec;
    readonly MapBuild map;
    readonly Denizens people;
    readonly List<OathDef> oaths;
    /// <summary>The dark's own oaths, sworn one by one in the long night (and how many
    /// times it has deepened since it ran out of them).</summary>
    readonly List<OathDef> dark = new();
    int deeper;
    double packSize, elites, gear;
    int levels, waves;
    readonly string[] lean;
    double spawnT = 1.2, eventT = 55;
    int eventIx;
    /// <summary>The night's shape before the boss: how full the field is kept, its breathers,
    /// and which turn comes next (ArenaPacing; the experience lead's).</summary>
    readonly ArenaPacing pacing;
    bool hushed, opened;
    double heraldAt;
    bool herald10, herald20, great15, bossUp, won, over, wayShown;
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
    int nightTurn, auraAlive;
    readonly HashSet<int> chests = new();
    /// <summary>Those carrying a small chest (one card): the minibosses. A full chest each made the
    /// night's builds a tenth stronger at the boss (measured: the boss fell 12-25 s sooner).</summary>
    readonly HashSet<int> smallChests = new();
    /// <summary>The boss's script (its phases, moves and weakness), the bearing its sign
    /// came from, and the share of its number the horde is kept at while it lives.</summary>
    ArenaBoss? script;
    double signAngle, bossShare = 0.4;
    bool runUp;
    public ArenaBoss? BossScript => script;

    public override string Id => "arena";
    public override string Name => Spec.Name;
    public override string? Region => Spec.Sub != "" ? Spec.Sub : $"Tier {Spec.Tier} · {people.Name}";
    public override bool Combat => true;
    public override IReadOnlyList<string> Creatures => people.Arena.Select(h => h.Def).Concat(people.Stretches.Select(s => s.Miniboss))
        .Append(people.Champion).Append(BossDef).Append(KeeperOf(people.Id)).Distinct().ToList();
    /// <summary>Higher and further out: the whole of the fight in view.</summary>
    public override (double Pitch, double Distance)? Camera => (64, CameraNear);

    /// <summary>How far out the camera stands now. A night begins close on the survivor, so
    /// she is seen, and pulls back as the horde grows, so the fight is (docs/EXPERIENCE_AUDIT.md,
    /// finding 3); it comes in a little in the hush and stands back for what rules the night.
    /// Eased slowly, so it breathes with the night rather than with every swarm.</summary>
    public double CameraDistance { get; private set; } = CameraNear;
    const double CameraNear = 22, CameraFar = 31;
    double crowdSeen;
    int aliveNow;
    public override bool Ember => true;
    public bool Over => over;
    /// <summary>What comes at the half hour: the story's named foe, or what rules the people.</summary>
    string BossDef => Spec.Boss ?? people.Boss;
    string BossName => Spec.BossName ?? people.BossName;
    string BossTitle => Spec.BossTitle ?? people.BossTitle;
    /// <summary>What rules the horde is dead: the fight is won, and the way out open.</summary>
    public bool Won => won;
    double Seconds => B?.Time ?? 0;
    /// <summary>The night's clock, in minutes of a thirty-minute night: a story's twenty-minute night
    /// runs it half again as fast, so it is the same night (its kinds, levels, heralds, stretches
    /// and great blessing) told quicker. Past the boss, real minutes.</summary>
    double Minute => Seconds <= End ? Seconds / 60 * Pace : 30 + (Seconds - End) / 60;
    /// <summary>How much faster than a table's thirty minutes this night runs.</summary>
    double Pace => 30 / Spec.Minutes;
    double End => Spec.Minutes * 60;
    /// <summary>What every night calls the boss's coming and its middle, in the story lead's one
    /// voice (the valley's idioms are plain truth; this one is).</summary>
    const string Nears = "The dead of night nears", Comes = "The dead of night", Past = "past the dead of night", Middle = "Halfway through the dark";
    static string Cap(string s) => s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];

    public ArenaRun(IZoneHost host, MapBuild map, ArenaSpec spec) : base(host, map.Meta)
    {
        Spec = spec;
        this.map = map;
        people = MapOffers.People(spec.People);
        oaths = spec.Oaths.Select(MapOffers.Oath).ToList();
        pacing = new ArenaPacing(spec.Minutes * 60);
        escalation = new Escalation(people);
        Recount();
        lean = MapOffers.Lean(spec.Map, spec.People);
        Hooks = new BattleHooks { OnKill = OnKill, OnLoot = OnLoot, OnPickup = OnPickup, OnCalled = (c, _) => Harden(c, false) };
    }

    /// <summary>What every oath sworn, the table's and the dark's, comes to.</summary>
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
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Night;

    /// <summary>An arena's night is its place's own (Maps/ArenaPlaces.cs).</summary>
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) =>
        t == TimeOfDay.Night && map.Place is { } place ? place.Night : base.AtmosphereFor(t);
    public override Arrival ArrivalFrom(string? from) => new(0, 0, 0);

    public override void Begin(Battle b)
    {
        base.Begin(b);
        // The people's own cover: graves, walls, rubble, lanterns.
        foreach (var pc in map.Pieces) G.Look.AddProp(pc.Id, pc.X, pc.Z, pc.Rot, pc.Scale);
        b.Rules = MapOffers.Rules(Spec.Map);
        sworn = MapOffers.Rules(Spec.Map);
        Dusk();
        // A fiftieth still paid a Kerchief night 1.6k-2.1k gold from its forty thousand dead, and a
        // three-hundredth 530-690 (crafting's probes, against an economy that holds at 350-450).
        b.Rules.FodderGold = 0.0015;
        b.Rules.ChampionGold = 0.07;
        // A shorter night pays its ember quicker, so its boss meets the build a table's would.
        b.Rules.EmberGain *= Pace;
        // The survivor's light reaches further here (the camera is further out); a moonless oath still halves it.
        b.Rules.Light *= 1.6;
        b.InBounds = map.CanStand;
        // The horde's charges come in waves with lulls, and now and then a spike on the people's tell.
        b.Charges.Spikes = true;
        (b.Charges.Tell, b.Charges.TellSound) = SpikeTell();
        b.Charges.Cap = ChargeCap();
        // The first great blessing, before anything moves.
        b.GreatOwed = 1;
        G.Announce(new Announcement(Spec.Name, Region, "zone", 3.4, "Ember arena"));
        Objectives();
    }

    /// <summary>The clock moved on to `seconds` (pictures and probes of the boss): what that
    /// stretch would have brought (its heralds, the fifteenth minute's great blessing, the
    /// opening one) is passed over rather than all arriving at once.</summary>
    public void SkipTo(double seconds)
    {
        if (B == null) return;
        B.Time = seconds;
        herald10 = Minute >= 10; herald20 = Minute >= 20; great15 = Minute >= 15; kindled = Minute >= 14.5;
        pacing.SkipTo(seconds);
        escalation.SkipTo(Minute);
        hushed = pacing.Hush(seconds);
        B.GreatOwed = 0;
        // Its sign was given two minutes ago: the light stands on the edge, the words long gone.
        if (!runUp && seconds >= End - 120) RunUp(quiet: true);
    }

    /* ---------------------------------------------------------- the horde -- */

    double R() => G.Rng.NextDouble();

    /// <summary>Minutes past the half hour (0 before it).</summary>
    double Beyond => Math.Max(0, Seconds - End) / 60;
    // A tier is three creature levels: the survivor's own pace (levels 1, 4, 7 for tiers 1 to 3),
    // so a tier at the survivor's level is a fair night and one above it a hard one.
    // Dusk: the tier's strength (and an oath's levels) comes in over the first three minutes (five
    // from the third tier), so a night is not lost before the ember has given anything to choose.
    int Level() => Math.Max(1, Spec.Tier * 3 - 2 + levels + (int)(Minute / 2.5) + (int)(Beyond / 2) - Math.Max(0, (int)Math.Ceiling(DuskMinutes - Minute)));
    double DuskMinutes => Asks ? 5 : 3;
    /// <summary>What an ordinary creature's health is divided by at a minute.</summary>
    public static double FodderEase(double minute) => 1 + 0.08 * minute;

    /// <summary>From the third tier the night asks the draft. The experience lead's brief: there a
    /// careless draft should lose noticeably more often than a planned one, while below it choice is
    /// expression (a random drafter won as often as a greedy one at tiers 1-3, 85% to 83%). So from
    /// the third tier the crowd softens less with the minutes (it tests the build's reach), its blows
    /// grow from the eighth minute to twice by the half hour (a build that cannot clear is touched
    /// more), and champions, heralds and minibosses come a quarter stronger from the sixth (they test
    /// what it does to one). Dusk is longer there too, so the night is lost to the draft, not to the
    /// first minutes. Measured (docs/team/combat.md): planned 87%, careless 70%, from 93% and 87%.</summary>
    bool Asks => Spec.Tier >= 3;
    double EaseFor(double m) => Asks ? 1 + 0.08 * m * 0.4 : FodderEase(m);

    /// <summary>The table's oaths as sworn, and whether dusk is over.</summary>
    MapRules sworn = new();
    bool dusked;

    /// <summary>Dusk for the oaths' bites too: what their blows carry (poison, the winter's crawl) and
    /// the blight's cut to mending come in over the first three minutes, as their levels do. At
    /// tier 3 the blight's poison and cut from the first blow felled a fifth of the runs in minutes
    /// 1-5, before a draft had made anything to answer it with.</summary>
    void Dusk()
    {
        if (B == null || dusked) return;
        double k = Math.Clamp(Minute / 3, 0, 1);
        if (k >= 1) dusked = true;
        B.Rules.HealCut = sworn.HealCut * k;
        B.Rules.HitPoison = sworn.HitPoison && k >= 0.5;
        B.Rules.HitChill = sworn.HitChill && k >= 0.5;
    }

    /// <summary>How many the horde is kept at (a dark bargain struck asks for more of them).</summary>
    // Before the boss, the night's shape (ArenaPacing) swells and thins the line.
    int Target() => (int)Math.Min(won ? 380 : 320, (22 + 7.5 * Minute) * packSize * (1 + 0.15 * (Spec.Tier - 1)) * Bargain * (won || bossUp ? 1 : pacing.TargetShare(Seconds)));
    double Bargain => 1 + 0.15 * (B?.Boons.GetValueOrDefault("dark_bargain") ?? 0);

    /// <summary>Throwers and shooters at once: a few behind the crowd, never a
    /// battery (hundreds of them, each lobbing fire, is not a fight but weather).</summary>
    int RangedCap() => (int)Math.Min(won ? 24 : 16, 5 + Minute / 3);
    int rangedAlive;

    /// <summary>The crowd's charges at once in a wave (Sim/Charges.cs): 2 + tier / 2, at most 4,
    /// one more each ten minutes of the long night (to three more); one while a boss is up, so
    /// its own marks are the ones read.</summary>
    int ChargeCap() => bossUp ? 1 : Math.Min(4, 2 + Spec.Tier / 2) + Math.Min(3, (int)(Beyond / 10));

    /// <summary>What a people does before many of them run at once: heard, then said.</summary>
    (string Tell, string Sound) SpikeTell() => people.Id switch
    {
        "pack" => ("The wolves give tongue, and the tuskers lower their heads.", "tell_howl"),
        "dead" => ("A horn, twice. The dead set their feet.", "tell_horn"),
        "lamplings" => ("Fuses spit, all round you.", "tell_fuse"),
        "kerchiefs" => ("A whistle, and a shout: \"Now!\"", "tell_whistle"),
        _ => ("Something gathers itself in the dark.", "tell"),
    };

    /// <summary>A kind from the people, weighted: those that joined long ago more often.</summary>
    string Pick()
    {
        var open = escalation.Kinds(Minute).ToList();
        double W((string Def, double Weight, double From) h) => h.Weight * (1 + (Minute - h.From) / 8);
        double r = R() * open.Sum(W);
        foreach (var h in open) { r -= W(h); if (r <= 0) return h.Def; }
        return open[0].Def;
    }

    /// <summary>The strongest kind the people have put in the field so far.</summary>
    string Strongest() => escalation.Kinds(Minute).OrderByDescending(h => Enemies.Get(h.Def).Health).First().Def;

    /// <summary>Somewhere standable a way off from the survivor, on this bearing if it can.</summary>
    (double X, double Z)? Around(double angle, double dist)
    {
        var p = B!.Player;
        for (int t = 0; t < 10; t++)
        {
            double a = angle + (t == 0 ? 0 : (R() - 0.5) * 2.4), d = dist * (t < 5 ? 1 : 0.7);
            double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
            if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.7)) return (x, z);
        }
        return null;
    }

    Enemy? Spawn(string def, double x, double z, bool elite = false, SpawnStyle? style = null)
    {
        if (B == null) return null;
        // One thrower too many is one of the crowd instead.
        if (Enemies.Get(def).Ranged != null && !elite && def != BossDef)
        {
            if (rangedAlive >= RangedCap())
            {
                var melee = escalation.Kinds(Minute).Where(h => Enemies.Get(h.Def).Ranged == null).Select(h => h.Def).FirstOrDefault();
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
        }
        var st = style ?? (Enemies.Get(def).Family == Family.Undead ? SpawnStyle.Rise : Enemies.Get(def).Behavior == Behavior.Tunneler ? SpawnStyle.Burrow : SpawnStyle.Walk);
        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level() + (elite ? 1 : 0), Elite = elite, Style = st });
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
        if (!champion && !e.Elite) e.MaxHp = e.Hp = e.MaxHp / EaseFor(Math.Min(Minute, 30));
        if (Asks && !champion && !e.Elite) e.Damage *= 1 + Math.Clamp((Math.Min(Minute, 30) - 8) / 22, 0, 1);
        // (Not the boss: its contract sets its own health.)
        if (Asks && (champion || e.Elite) && e.Def.Id != BossDef && Minute >= 6) { e.MaxHp = e.Hp = e.MaxHp * 1.25; e.Damage *= 1.25; }
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
        smallChests.Add(e.Id);
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
    }

    List<Enemy> Group(string def, int n, double x, double z, double spread)
    {
        var o = new List<Enemy>();
        for (int i = 0; i < n; i++)
        {
            double a = R() * Math.PI * 2, d = R() * spread;
            double sx = x + Math.Cos(a) * d, sz = z + Math.Sin(a) * d;
            if (!map.CanStand(sx, sz) || B!.Collision.Blocked(sx, sz, 0.6)) continue;
            // Now and then one of them a champion (more under the oath of champions, and as the minutes go).
            if (Spawn(def, sx, sz, R() < 0.012 * elites * (1 + Minute / 12)) is { } e)
            {
                // A champion in the crowd wears a Sign from the tenth minute above the first tier.
                if (e.Elite && Spec.Tier >= 2 && Minute >= 10) Sign(e, 1);
                o.Add(e);
            }
        }
        return o;
    }

    public override void Step(double dt)
    {
        if (B == null || over) return;
        var p = B.Player;
        int alive = 0;
        rangedAlive = auraAlive = 0;
        foreach (var e in B.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            alive++;
            if (e.Def.Ranged != null) rangedAlive++;
            if (e.Def.Aura != null) auraAlive++;
        }
        aliveNow = alive;
        Dusk();
        B.Charges.Cap = ChargeCap();
        B.Charges.Spikes = !bossUp;
        if (!won && !bossUp)
        {
            // The night's shape (ArenaPacing): no lanes from the crowd in a breather, the hush or a
            // herald's duel; spikes oftener while it builds into a landmark.
            if (pacing.Breather(Seconds) || pacing.Hush(Seconds) || heraldAt > 0) B.Charges.Calm(B, 0.5);
            B.Charges.SpikeEvery = pacing.Building(Seconds) ? (18, 26) : (40, 55);
        }
        else B.Charges.SpikeEvery = (40, 55);
        // The first of them in sight at once: the night used to open on an empty field for its
        // first half minute while the horde walked in from out of sight.
        if (!opened && Seconds > 1.5)
        {
            opened = true;
            double a0 = R() * Math.PI * 2;
            for (int k = 0; k < 3; k++)
                if (Around(a0 + k * 2.1, 12 + R() * 3) is var (ox, oz)) Group(Pick(), 4 + (int)(R() * 3), ox, oz, 2.5);
        }
        // The horde kept up: groups from out of sight, all round (a story's night, won, is over).
        spawnT -= dt;
        if (won && Spec.Story) { }
        else if (spawnT <= 0 && alive < Target() && !bossUp)
        {
            // A field mown thin fills twice as fast, so a strong build mows rather than waits.
            bool thin = alive < Target() * 0.6;
            spawnT = thin ? 0.225 : 0.45;
            if (Around(R() * Math.PI * 2, 24 + R() * 5) is var (x, z)) Group(Pick(), (3 + (int)(R() * 4) + (int)(Minute / 5)) * (thin ? 2 : 1), x, z, thin ? 4.5 : 3.5);
        }
        else if (bossUp && spawnT <= 0 && alive < Target() * bossShare)
        {
            spawnT = 0.9;
            if (Around(R() * Math.PI * 2, 24) is var (x, z)) Group(Pick(), 4, x, z, 3);
        }
        eventT -= dt;
        if (eventT <= 0 && !bossUp && won && !Spec.Story)
        {
            eventT = (60 + R() * 25) / (1 + waves);
            Event(eventIx++ % 4);
        }
        else if (eventT <= 0 && !bossUp)
        {
            // Before the boss the night's shape picks the turn (none in a herald's duel or the hush).
            if (pacing.Next(Seconds, R) is Turn t)
            {
                // (A shorter night has its turns closer, so it has as many.)
                eventT = (60 + R() * 25) / (1 + waves) / Pace;
                Event(t);
                pacing.Played(Seconds);
            }
            else eventT = 4;
        }
        // A herald's duel lasts while it lives, or a minute at most; its fall lets the people flood in.
        if (heraldAt > 0 && (herald is not { Alive: true } || herald.State == EnemyState.Dying || Seconds - heraldAt > 60))
        {
            heraldAt = 0;
            pacing.HeraldFell(Seconds);
        }
        // The hush: the people draw back from the survivor and wait for what rules them.
        if (!hushed && !won && pacing.Hush(Seconds))
        {
            hushed = true;
            // (The hush's own share is already in the target.)
            MakeWay(1);
        }
        // (Not on the boss's heels: a herald missed that late is let go.)
        if (!herald10 && Minute >= 10) { herald10 = true; if (Seconds < End - 60) Herald(); }
        if (!herald20 && Minute >= 20) { herald20 = true; if (Seconds < End - 60) Herald(); }
        // A story's night ends on its beat: no long night after it (the experience lead's loop; the
        // bible's pacing). The long night is the table's, where staying is the point.
        if (won && !Spec.Story) LongNight();
        // The Kindling: at the fourteen and a half minute's breath, the ember-core and its keeper.
        if (!kindled && !great15 && Minute >= 14.5 && !bossUp && !won) Kindle();
        if (kindled && !great15) Kindling();
        // (No core where one could not stand: the great blessing comes all the same.)
        if (!great15 && !kindled && Minute >= 15 && !bossUp) Midnight(false);
        Minibosses();
        if (!runUp && !won && Seconds >= End - 120) RunUp();
        if (makingWay.Count > 0) MakingWay();
        if (!bossUp && !won && Seconds >= End) Boss();
    }

    /* ---------------------------------------------------- the Kindling -- */

    /* The fifteenth minute's great blessing was an announcement; it is a moment now, and the
     * boss's first verse (docs/bosses/SURVIVORS_BOSSES.md 9). In the breath before it an
     * ember-core comes up out of the scar the arena was opened from, and beside it what rules
     * the people's own creature, wearing one of its ruler's verbs: the night teaches its boss's
     * language before the boss. Broken within the minute, the core makes the great blessing a
     * card richer; the keeper carries a full chest. The blessing is owed whatever happens. */

    Enemy? core, keeper;
    double coreSeed, kindledAt;
    bool kindled;
    IOrb? coreOrb;
    int coreLight = -1;
    /// <summary>Broken in time (null: not yet, or never came).</summary>
    public bool? CoreBroken { get; private set; }

    /// <summary>A fifth of what its ruler will have at the half hour, at this minute's level: the
    /// keeper's health, and the core's.</summary>
    double KeeperHealth() =>
        Enemies.Get(BossDef).Health * Enemies.ScaleFor(Level()).Health * (ArenaBosses.For(BossDef, this)?.HealthMul(Spec.Tier) ?? 12 + 2 * Spec.Tier) / 5;

    static string KeeperOf(string people) => people switch { "dead" => "lt_dead", "lamplings" => "lt_lamplings", "kerchiefs" => "lt_kerchiefs", _ => "lt_pack" };

    void Kindle()
    {
        kindled = true;
        kindledAt = Seconds;
        var p = B!.Player;
        // Toward the middle of the arena from where she stands, near enough to be in the picture.
        if (Around(Math.Atan2(-p.Z, -p.X), 8) is not var (x, z)) { kindled = false; Midnight(false); return; }
        core = B.SpawnEnemy("ember_core", x, z, new Battle.SpawnOpts { Level = Level(), Style = SpawnStyle.Rise, Faction = Enemies.Get(people.Champion).Faction });
        if (core == null) { kindled = false; Midnight(false); return; }
        double hp = KeeperHealth();
        // (Its keeper's health measured broken in time by one planned draft in six: half of it.)
        core.MaxHp = core.Hp = hp / 2;
        core.AttackT = 1e9;
        core.Named = new Named { Title = "The ember-core" };
        coreSeed = core.Seed;
        if (Around(Math.Atan2(z - p.Z, x - p.X) + 0.6, 12) is var (kx, kz) && Spawn(KeeperOf(people.Id), kx, kz, true) is { } k)
        {
            k.MaxHp = k.Hp = hp;
            k.Named = new Named { Title = k.Def.Name };
            chests.Add(k.Id);
            keeper = k;
        }
        coreOrb = G.Look.EmberCore(0.95);
        B.Charges.Calm(B, 8);
        B.Events.Emit(new Ev.Focus { X = x, Z = z, Duration = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.3 });
        G.Announce(new Announcement("The ember-core", "Break it within the minute, and the great blessing comes richer", "reward", 3.2, keeper?.Def.Name));
    }

    bool CoreUp => core is { Alive: true } c && c.Seed == coreSeed && c.State != EnemyState.Dying;

    void Kindling()
    {
        if (!CoreUp) { CoreBroken = true; B!.GreatExtra = 1; Midnight(true); return; }
        if (Seconds - kindledAt >= 60)
        {
            // It cools, and goes back into the ground: the blessing is the night's as it was.
            B!.Events.Emit(new Ev.Explosion { X = core!.X, Z = core.Z, Radius = 2.5, School = School.Fire, Power = 0.6 });
            B.Enemies.Release(core);
            CoreBroken = false;
            Midnight(false);
        }
    }

    /// <summary>The night's great blessing, and a banish with it (by now the build knows what it does not want).</summary>
    void Midnight(bool rich)
    {
        great15 = true;
        B!.GreatOwed++;
        B.Banishes++;
        coreOrb?.Dispose();
        coreOrb = null;
        if (coreLight >= 0) G.Look.SetLit(coreLight, false);
        if (rich && core != null) B.Events.Emit(new Ev.Explosion { X = core.X, Z = core.Z, Radius = 4, School = School.Fire, Power = 1.4 });
        G.Announce(new Announcement(Middle, rich ? "The core broken: a great blessing, and a choice more" : "A great blessing", "reward", 2.6));
    }

    /// <summary>The minute's turn: a ring, a champion, a stampede, a swarm.</summary>
    void Event(int kind)
    {
        var p = B!.Player;
        double m = Minute;
        switch (kind)
        {
            case 0:
            {
                // A closing ring: every way out has something in it.
                int n = 18 + (int)(m * 1.2);
                string def = Pick();
                for (int i = 0; i < n; i++)
                {
                    double a = (double)i / n * Math.PI * 2, rr = 13 + R() * 2;
                    double x = p.X + Math.Cos(a) * rr, z = p.Z + Math.Sin(a) * rr;
                    if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.6)) Spawn(def, x, z);
                }
                Shout("They close in from every side.");
                break;
            }
            case 1:
            {
                // A champion and its escort (two, or more, under the oath of champions); each carries a chest.
                int n = (int)elites + (R() < elites % 1 ? 1 : 0);
                double a0 = R() * Math.PI * 2;
                for (int k = 0; k < n; k++)
                {
                    if (Around(a0 + k * 1.1, 22) is not var (x, z)) continue;
                    var champ = Spawn(Strongest(), x, z, true);
                    if (champ == null) continue;
                    champ.MaxHp = champ.Hp = champ.MaxHp * 2;
                    Sign(champ, SignsFor(false));
                    chests.Add(champ.Id);
                    Group(Pick(), 5 + (int)(m / 3), x, z, 3);
                }
                Shout(n > 1 ? $"Champions of {people.Name}: they carry something." : $"A champion of {people.Name}: it carries something.");
                break;
            }
            case 2:
            {
                // A stampede: a column of the fastest, straight across.
                string def = Fastest();
                double a = R() * Math.PI * 2;
                double sx = -Math.Sin(a), sz = Math.Cos(a);
                int n = 12 + (int)(m / 2);
                for (int i = 0; i < n; i++)
                {
                    double off = (i - n / 2.0) * 1.3;
                    double x = p.X + Math.Cos(a) * 26 + sx * off, z = p.Z + Math.Sin(a) * 26 + sz * off;
                    if (!map.CanStand(x, z)) continue;
                    if (Spawn(def, x, z) is { } e) e.Speed *= 1.35;
                }
                Shout("A stampede!");
                break;
            }
            default:
            {
                // A swarm from one quarter.
                if (Around(R() * Math.PI * 2, 22) is var (x, z)) Group(Pick(), 25 + (int)m, x, z, 5);
                Shout("A swarm, from the dark.");
                break;
            }
        }
    }

    /// <summary>A turn the night's shape chose.</summary>
    void Event(Turn t)
    {
        switch (t)
        {
            case Turn.Ring: Event(0); break;
            case Turn.Champion: Event(1); break;
            case Turn.Stampede: Event(2); break;
            case Turn.Swarm: Event(3); break;
            default: Signature(t == Turn.SecondSignature); break;
        }
    }

    /* ------------------------------------------- the people's own turns -- */

    /// <summary>The people's own question as a moment with a tell (docs/bestiary/HORDES.md 4.3):
    /// a sound and a word first, then the thing itself, so a reader can answer it. The first
    /// comes at about six minutes and again, at full strength, in the long push; the second at
    /// about seventeen.</summary>
    void Signature(bool second)
    {
        double m = Minute;
        double scale = packSize * (1 + 0.15 * (Spec.Tier - 1));
        int N(double n) => Math.Max(4, (int)(n * scale));
        double a = R() * Math.PI * 2;
        switch (people.Id, second)
        {
            case ("pack", false):
                // The Hunt: the fastest of the pack from three sides at once.
                Shout("A howl, then another answering it, and another: they are all round you.");
                G.After(1.6, () => { for (int k = 0; k < 3; k++) Column(Fastest(), a + k * Math.Tau / 3, 24, N(5 + m / 4), 1.25); });
                break;
            case ("pack", true):
                // The Blight Runs: the sick ones in a rush from one side; they burst as they die.
                Shout("Coughing in the trees, and something green on the wind.");
                G.After(1.6, () => Column(Has("wolf_blighted") ? "wolf_blighted" : Fastest(), a, 24, N(10 + m / 2), 1.2));
                break;
            case ("dead", false):
                // The Ford Rises: the ground cracks in a ring round the survivor, and the dead come up out of it at once.
                RingRise(Has("risen_warrior") && m > 15 ? "risen_warrior" : "risen", N(12 + m / 2), 8.5, SpawnStyle.Rise, "The ground cracks in a ring round you.");
                break;
            case ("dead", true):
                // The Shield Line: shieldmen in a line out of the dark, bowmen behind; the answer is round its end.
                Shout("Shields, in a line, out of the dark.");
                G.After(1.2, () => Line(Has("risen_warrior") ? "risen_warrior" : "risen", Has("risen_archer") ? "risen_archer" : null, a, 20, N(8 + m / 3)));
                break;
            case ("lamplings", false):
                // The Dig Opens: picks under the survivor's feet, and the tunnellers come up in a ring.
                RingRise("lampling", N(12 + m / 2), 8, SpawnStyle.Burrow, "Picks, under your feet, all round.");
                break;
            case ("lamplings", true):
                // The Sappers' Rank: the throwers on one side with their fuses lit, the tunnellers ahead of them.
                Shout("Fuses hissing, out at the edge of the light.");
                G.After(1.4, () => Line("lampling", Has("lampling_sapper") ? "lampling_sapper" : null, a, 19, N(8 + m / 3)));
                break;
            case ("kerchiefs", false):
                // The Ambush: footpads from two sides at once, on a whistle.
                Shout("A whistle, and an answer from behind you.");
                G.After(1.4, () => { Column("footpad", a, 18, N(6 + m / 3), 1.1); Column("footpad", a + Math.PI, 18, N(6 + m / 3), 1.1); });
                break;
            default:
                // The Wall: bruisers walk in a line with the throwers behind it.
                Shout("A drum, and a wall of barn doors in the open.");
                G.After(1.4, () => Line(Has("bruiser") ? "bruiser" : "footpad", Has("pillager") ? "pillager" : null, a, 20, N(6 + m / 4)));
                break;
        }
        // Each is led by a captain who carries a chest: answering the question pays.
        G.After(1.5, () => Captain(a));
        // And the people's runners go with it, together (its own tell has been given).
        G.After(1.6, () => { if (B != null && !over) B.Charges.Spike(B, quiet: true); });
    }

    /// <summary>The captain of a people's own turn: a champion of the strongest kind in the field, with a chest.</summary>
    void Captain(double a)
    {
        if (B == null || over || Around(a, 19) is not var (x, z)) return;
        var c = Spawn(Strongest(), x, z, true);
        if (c == null) return;
        c.MaxHp = c.Hp = c.MaxHp * 2;
        Sign(c, SignsFor(false));
        chests.Add(c.Id);
    }

    /// <summary>A kind of this people already in the field.</summary>
    bool Has(string def) => escalation.Fields(def, Minute);

    /// <summary>The fastest kind this people has in the field so far.</summary>
    string Fastest() => escalation.Kinds(Minute).OrderByDescending(h => Enemies.Get(h.Def).Speed).First().Def;

    /// <summary>A column coming straight in: abreast across the bearing, a way out, a little faster than they walk.</summary>
    void Column(string def, double a, double dist, int n, double speed)
    {
        if (B == null || over) return;
        var p = B.Player;
        double sx = -Math.Sin(a), sz = Math.Cos(a);
        for (int i = 0; i < n; i++)
        {
            double off = (i - n / 2.0) * 1.3;
            double x = p.X + Math.Cos(a) * dist + sx * off, z = p.Z + Math.Sin(a) * dist + sz * off;
            if (!map.CanStand(x, z) || B.Collision.Blocked(x, z, 0.6)) continue;
            if (Spawn(def, x, z) is { } e) e.Speed *= speed;
        }
    }

    /// <summary>A rank walking in from one side, and a second rank behind it.</summary>
    void Line(string front, string? back, double a, double dist, int n)
    {
        if (B == null || over) return;
        var p = B.Player;
        double sx = -Math.Sin(a), sz = Math.Cos(a);
        for (int i = 0; i < n; i++)
        {
            double off = (i - (n - 1) / 2.0) * 1.7;
            double x = p.X + Math.Cos(a) * dist + sx * off, z = p.Z + Math.Sin(a) * dist + sz * off;
            if (map.CanStand(x, z) && !B.Collision.Blocked(x, z, 0.7)) Spawn(front, x, z);
            if (back == null || i % 2 == 1) continue;
            double bx = x + Math.Cos(a) * 3, bz = z + Math.Sin(a) * 3;
            if (map.CanStand(bx, bz) && !B.Collision.Blocked(bx, bz, 0.6)) Spawn(back, bx, bz);
        }
    }

    /// <summary>A ring round the survivor marked on the ground, and a moment later what was
    /// under it comes up at every mark at once (helpless for its first moment: the answer is
    /// to be ready in the middle, or out before it closes).</summary>
    void RingRise(string def, int n, double radius, SpawnStyle style, string tell)
    {
        var p = B!.Player;
        var at = new List<(double X, double Z)>();
        for (int i = 0; i < n; i++)
        {
            double a = (double)i / n * Math.Tau + R() * 0.2, rr = radius + (R() - 0.5) * 2;
            double x = p.X + Math.Cos(a) * rr, z = p.Z + Math.Sin(a) * rr;
            if (!map.CanStand(x, z) || B.Collision.Blocked(x, z, 0.6)) continue;
            at.Add((x, z));
            B.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.9, Duration = 1.3, Hostile = true, Kind = TelegraphKind.Ground });
        }
        Shout(tell);
        G.After(1.3, () =>
        {
            if (B == null || over) return;
            foreach (var (x, z) in at) Spawn(def, x, z, style: style);
        });
    }

    void Shout(string text)
    {
        var p = B!.Player;
        B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = text });
        B.Events.Emit(new Ev.Shake { Amount = 0.2 });
    }

    /// <summary>A champion of champions, at ten and twenty minutes.</summary>
    void Herald()
    {
        if (Around(R() * Math.PI * 2, 20) is not var (x, z)) return;
        herald = Spawn(people.Champion, x, z, true);
        if (herald == null) return;
        herald.MaxHp = herald.Hp = herald.MaxHp * (4 + Spec.Tier) * (Minute >= 20 ? 1.6 : 1) * (1 + Beyond / 10);
        herald.Damage *= 1.2;
        Sign(herald, SignsFor(true));
        chests.Add(herald.Id);
        herald.Named = new Named { Title = $"Herald of {people.Name}" };
        // Its arrival is read on its own: the crowd's lanes hold off a moment.
        B!.Charges.Calm(B, 10);
        G.Announce(new Announcement($"Herald of {people.Name}", "It carries a chest", "danger", 2.4));
        // Before the boss, its duel is the thing on the field: the crowd let thin round it.
        if (!won) { pacing.HeraldCame(); heraldAt = Seconds; }
    }

    /// <summary>Two minutes out: its sign, from the bearing it will come from (a sound,
    /// then a light on the arena's edge), so the survivor turns to face it.</summary>
    void RunUp(bool quiet = false, bool again = false)
    {
        runUp = true;
        var p = B!.Player;
        signAngle = R() * Math.PI * 2;
        string sign = BossDef switch
        {
            "boss_pack" => "A howl from the edge of the wood; the wolves lift their heads.",
            "boss_dead" => "A drum, slow, under everything; the dead turn to face it.",
            "grimtunnel_roused" or "boss_lamplings" => "A blasting thump, and the ground shivers; picks rattle somewhere.",
            "boss_kerchiefs" => "A whistle, three notes, and an answering whistle.",
            _ => "Something is coming.",
        };
        if (!quiet) B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = sign });
        G.Look.AddLight(p.X + Math.Cos(signAngle) * 26, 2.5, p.Z + Math.Sin(signAngle) * 26, "#ff6a3a", 3.2, 16, 0.25, 0.12, "#ff8a5a");
        if (!quiet) G.Announce(again ? new Announcement($"{BossName} stirs again", "From where the sign was, and stronger", "danger", 2.6)
            : new Announcement(Nears, "It comes from where the sign was", "danger", 2.6));
    }

    /// <summary>The half hour: what rules the people comes, a boss and no herald: on the
    /// picture from the bearing of its sign, its own kind round it, the field
    /// cleared where it stands, its weakness named.</summary>
    /// <summary>The run's boss blows taken before this fight (its chest pays for a clean one).</summary>
    int bossBlowsBefore;

    void Boss(bool again = false)
    {
        bossUp = true;
        bossShare = 0.4;
        bossBlowsBefore = B!.BossBlowsTaken;
        var p = B!.Player;
        if (!runUp) signAngle = R() * Math.PI * 2;
        var at = Around(signAngle, 13) ?? Around(R() * Math.PI * 2, 13) ?? (p.X + 8, p.Z);
        // Its ground cleared: the boss is the thing on screen.
        foreach (var o in B.Enemies.Living().ToList())
            if (o.Disposition == Disposition.Hostile && !o.Elite && (o.X - at.X) * (o.X - at.X) + (o.Z - at.Z) * (o.Z - at.Z) < 64) B.Enemies.Release(o);
        MakeWay();
        boss = Spawn(BossDef, at.X, at.Z, true, SpawnStyle.Walk);
        script = ArenaBosses.For(BossDef, this);
        if (boss != null)
        {
            boss.Boss = true;
            // Named, so its body glows as a named thing's does and its blows carry its name.
            boss.Named = new Named { Title = BossName };
            boss.MaxHp = boss.Hp = boss.MaxHp * (script?.HealthMul(Spec.Tier) ?? 12 + 2 * Spec.Tier);
            boss.Damage *= script?.DamageMul ?? 1.3;
            // Come again, it is the first fight and a part more each time, by a rule the player
            // can learn, not the night's hardening and its levels on top of the boss's own (that
            // made the first return a wall: the sweep's runs fell to it more than to anything).
            if (!again) { firstBossHp = boss.MaxHp; firstBossDmg = boss.Damage; }
            else
            {
                boss.MaxHp = boss.Hp = firstBossHp * (1 + ReturnGrowth * returns);
                boss.Damage = firstBossDmg * (1 + ReturnBite * returns);
            }
            if (script != null)
            {
                script.Begin(boss);
                Hooks.BossTick = (e, dt) => e == boss && script.Tick(e, dt);
                Hooks.OnBossHit = (e, school, dmg) => { if (e == boss) script.OnHit(e, school, dmg); };
                Hooks.OnBossStagger = e => { if (e == boss) script.OnStagger(e); };
            }
            B.Events.Emit(new Ev.Focus { X = at.X, Z = at.Z, Duration = 1.6 });
        }
        // Its own kind round it, not a random draw.
        string escort = people.Arena[0].Def;
        for (int k = 0; k < 10; k++)
        {
            double a = k * Math.PI * 2 / 10;
            double x = at.X + Math.Cos(a) * 5, z = at.Z + Math.Sin(a) * 5;
            if (map.CanStand(x, z)) Spawn(escort, x, z);
        }
        B.Events.Emit(new Ev.Shake { Amount = 0.45 });
        // The champions' oath: a champion of its people stands beside it, signed.
        if (Spec.Oaths.Contains("champions") && Around(signAngle + 0.6, 13) is var (lx, lz) && Spawn(Strongest(), lx, lz, true) is { } lieutenant)
        {
            lieutenant.MaxHp = lieutenant.Hp = lieutenant.MaxHp * 2;
            Sign(lieutenant, SignsFor(false));
            chests.Add(lieutenant.Id);
        }
        string sworn = script?.Sworn() ?? "";
        G.Announce(new Announcement(BossName, (script != null ? $"{BossTitle} · Weakness: {script.WeaknessText}" : BossTitle) + (sworn.Length > 0 ? $" · Sworn: {sworn}" : ""), "danger", 3.4,
            again ? (returns == 1 ? "Again" : $"Again, the {Ordinal(returns + 1)} time") : Comes));
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
     *                for the first hour past the half hour, where a great build
     *                has its hour; then compounding, so no build, however
     *                broken, holds for ever. A little quicker too, to a low
     *                ceiling (pace a player can still read and outrun).
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

    /// <summary>The order the dark swears the table's oaths (the table's own are passed over):
    /// first the questions of where to stand, read on the ground (burning dead, champions,
    /// bursting dead, the horde's turns twice as often); then pace and number (the hunt,
    /// the swarm); last those that grind (the winter's crawl, iron skin, the blight's
    /// poison and cut mending, levels). An early winter or iron walled the sweep's runs.</summary>
    static readonly string[] DarkDeck = ["embers", "champions", "ruin", "vigil", "hunt", "swarm", "winter", "iron", "blight", "deep"];
    /// <summary>A returning boss's health, and its blows, over the first's, per return.</summary>
    public const double ReturnGrowth = 0.35, ReturnBite = 0.25;
    double nextDark, nextReturn, firstBossHp, firstBossDmg;
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
        // Compounding from an hour past: three hundredths a minute, so by two hours past
        // nothing stands (measured: docs/team/combat.md). The square's 0.004 (from 0.006) gives
        // the tail to good builds: the median run past the half hour went 22 -> 26 minutes.
        double press = m > 60 ? Math.Pow(1.03, m - 60) : 1;
        return ((1 + 0.1 * m + 0.004 * m * m) * press, (1 + 0.035 * m) * press, 1 + Math.Min(0.15, 0.004 * m));
    }

    void LongNight()
    {
        if (Seconds >= nextDark) { nextDark += 300; DarkSwears(); }
        if (!bossUp && !returnSigned && Seconds >= nextReturn - 60) { returnSigned = true; RunUp(again: true); }
        if (!bossUp && Seconds >= nextReturn) { returns++; returnSigned = false; nextReturn += 900; Boss(again: true); }
        // Between the returns, not on one's heels: a herald, then two of the night's minibosses come
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
        G.Announce(new Announcement($"{BossName} is down again", "Back soon, and stronger.", "reward", 3.4));
        Objectives();
    }

    /// <summary>Those falling back for their ruler, until they are out of sight (by pool
    /// slot and spawn, since a slot let go is soon another creature).</summary>
    readonly Dictionary<int, double> makingWay = new();

    /// <summary>The people make way for what rules them: past the share the horde is held
    /// at while the boss lives, the crowd falls back into the dark, the farthest first
    /// (gone once out of sight), so the boss does not arrive inside a crowd it cannot be
    /// seen in, and the share is the fight's from its first second, not once the survivor
    /// has mown down the half-hour's horde.</summary>
    void MakeWay(double? share = null)
    {
        var p = B!.Player;
        var crowd = B.Enemies.Living().Where(o => o.Disposition == Disposition.Hostile && !o.Elite && o.State != EnemyState.Dying).ToList();
        // (The hush before the boss passes its own share; the boss's arrival keeps its fight's.)
        int keep = (int)(Target() * (share ?? bossShare));
        foreach (var o in crowd.OrderByDescending(o => (o.X - p.X) * (o.X - p.X) + (o.Z - p.Z) * (o.Z - p.Z)).Take(Math.Max(0, crowd.Count - keep)))
        {
            o.Status[StatusKind.Fear] = new StatusSlot(5, 1, 1, 0);
            makingWay[o.Id] = o.Seed;
        }
    }

    void MakingWay()
    {
        var p = B!.Player;
        foreach (var (id, seed) in makingWay.ToList())
        {
            var o = B.Enemies.Items[id];
            double d2 = (o.X - p.X) * (o.X - p.X) + (o.Z - p.Z) * (o.Z - p.Z);
            if (!o.Alive || o.Seed != seed || o.State == EnemyState.Dying) makingWay.Remove(id);
            else if (d2 > 25 * 25) { B.Enemies.Release(o); makingWay.Remove(id); }
            // Cornered or slow, it turns back and is one of the share.
            else if (!o.Status.Has(StatusKind.Fear)) makingWay.Remove(id);
        }
    }

    /* ------------------------------------------------- the boss's arena -- */

    Battle IBossArena.B => B!;
    int IBossArena.Tier => Spec.Tier;
    string IBossArena.BossName => BossName;
    bool IBossArena.Spare => Spec.Spare;
    bool IBossArena.Sworn(string oath) => Spec.Oaths.Contains(oath);
    double IBossArena.R() => R();
    Enemy? IBossArena.Spawn(string def, double x, double z, bool elite, SpawnStyle? style)
    {
        var e = Spawn(def, x, z, elite, style);
        // The swarm's oath: what the boss calls comes half again as many.
        if (e != null && !elite && Spec.Oaths.Contains("swarm") && R() < 0.5) Spawn(def, x + (R() - 0.5) * 1.6, z + (R() - 0.5) * 1.6, false, style);
        return e;
    }
    bool IBossArena.CanStand(double x, double z) => map.CanStand(x, z) && !B!.Collision.Blocked(x, z, 0.6);
    void IBossArena.Say(string title, string? sub, string tone) => G.Announce(new Announcement(title, sub ?? "", tone, 2.4));
    void IBossArena.Bark(double x, double z, string text, string? speaker) => B?.Events.Emit(new Ev.Bark { X = x, Z = z, Text = text, Speaker = speaker });
    double IBossArena.HordeShare { set => bossShare = value; }
    /// <summary>The night won where the survivor stands, its boss passed over (pictures of the long
    /// night, and of a fall after the win: --minute 34 --won --die 40).</summary>
    public void WinNow() { if (!won && !over && B != null) Victory(B.Player.X, B.Player.Z); }

    void IBossArena.Won(double x, double z)
    {
        if (over || !bossUp) return;
        var b = boss;
        if (b != null) foreach (var l in OnLoot(b)) B!.Spill(l, x, z);
        if (won) Felled();
        else Victory(x, z);
    }

    /* ------------------------------------------------------------ spoils -- */

    /// <summary>What a carrier leaves (docs/design/LOOT_DESIGN.md §5): gear rolled whole at the
    /// carrier's level, fewer and better than before, the people's material where it is not gear;
    /// deeper past the half hour, the better.</summary>
    List<Loot> Gear(Enemy e, DropSource source) => G.Journey.Drops(new DropCtx
    {
        Source = source, Level = e.Level, People = Spec.People, Lean = lean, Luck = B!.Stats.Get(Stat.Luck), Gear = gear,
        Depth = Beyond, Tier = Spec.Tier, StoryBoss = Spec.Story && source == DropSource.Boss, R = R,
    });

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        // Gear from what carries something (a champion's turn, a captain, a herald, a miniboss),
        // never from the champions that turn up in the crowd: those were hundreds a night, and the
        // items plan wants a handful (docs/CRAFTING_DESIGN.md).
        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));
        if (carrier && e != boss)
            o.AddRange(Gear(e, small ? DropSource.Miniboss : e == herald || e == keeper ? DropSource.Herald : DropSource.Champion));
        if (e == boss)
        {
            int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= e.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == bossBlowsBefore ? 1 : 0) + returns;
            o.Add(new Loot(PickupKind.Chest, "boss", n, true));
            o.AddRange(Gear(e, DropSource.Boss));
            var pool = Abilities.All.Values.Where(a => a.Movement && ArtBook.CanLearn(G.Journey.Ch, a.Id)).Select(a => a.Id).ToList();
            if (pool.Count > 0) o.Add(new Loot(PickupKind.Item, ArtBook.Manual(pool[(int)(R() * pool.Count)]), 1, true, 2));
        }
        return o;
    }

    /// <summary>A chest: upgrades, an evolution first if one is earned, opened as a moment of
    /// its own (the host stages it). One, three or five things; a boss's hoard more.</summary>
    bool OnPickup(Pickup p)
    {
        if (p.Kind != PickupKind.Chest || B == null) return true;
        // (Two rolls, as the old count took, so the night's dice after it fall as they did.)
        double roll = R();
        R();
        int n = p.Ref == "boss" ? (int)p.Value : p.Ref == "small" ? 1 : LevelUp.ChestCount(roll);
        var got = LevelUp.OpenChest(B, n);
        chestsOpened++;
        G.Chest(new ChestOpened(p.X, p.Z, p.Id, got, p.Ref == "boss" ? $"{BossName}'s hoard" : null, chestsOpened));
        return true;
    }

    int chestsOpened;

    /// <summary>A chest of n things opened at her feet, a hoard if asked (--chest: pictures of the opening).</summary>
    public void ChestAt(int n, bool hoard)
    {
        if (B == null) return;
        var got = LevelUp.OpenChest(B, n);
        chestsOpened++;
        G.Chest(new ChestOpened(B.Player.X + 0.8, B.Player.Z + 0.6, chestsOpened, got, hoard ? $"{BossName}'s hoard" : null, chestsOpened));
    }

    void OnKill(Enemy e, bool byPlayer)
    {
        // (Let go of the fallen: the pool gives the same body to the next of the horde.)
        if (e == herald) herald = null;
        if (e == boss && !over)
        {
            script?.Fell(e);
            if (won) Felled();
            else Victory(e.X, e.Z);
        }
    }

    /* -------------------------------------------------------------- the end -- */

    /// <summary>What rules the horde is dead: won, and told so; the way out opens
    /// where it fell, and the arena goes on for whoever wants more of it.</summary>
    void Victory(double x, double z)
    {
        won = true;
        bossUp = false;
        boss = null;
        // The long night runs in real minutes, whatever the night before it.
        B!.Rules.EmberGain /= Pace;
        nextHerald = Seconds + 300;
        nextDark = Seconds + 300;
        nextReturn = Seconds + 900;
        eventT = 20;
        Arenas.Won(G.Journey, Spec);
        // A story's night is over at its boss's fall: its people draw back into the dark.
        if (Spec.Story) { bossShare = 0; MakeWay(0); }
        // The way out opens where it fell (a story's night lets her go by itself: it needs none).
        // Its prompt waits until the fall has landed: a button over her at the peak spoiled it.
        if (!Spec.Story)
        {
            way = map.CanStand(x, z) ? (x, z) : (B!.Player.X, B.Player.Z);
            var (wx, wz) = way.Value;
            G.Look.AddLight(wx, 2.2, wz, "#8ab4ff", 3.2, 14, 0.08, 0.14, "#b8d0ff");
            Interactables.Add(new Interactable
            {
                Id = "way_out", X = wx, Z = wz, R = 2.6, Verb = "Leave", Name = "The way out",
                Hint = () => $"Won. Or stay: {Clock(Seconds - End)} {Past}",
                When = () => wayShown, Act = Leave,
            });
            G.After(2.6, () => wayShown = true);
        }
        // The night's peak: the world slows on the fall, and the people break and run for a
        // breath before they gather again (docs/EXPERIENCE_AUDIT.md, finding 2).
        B!.Events.Emit(new Ev.Victory { X = x, Z = z });
        B.Events.Emit(new Ev.Focus { X = x, Z = z, Duration = 2.2 });
        var p = B.Player;
        foreach (var o in B.Enemies.Living())
            if (o.Disposition == Disposition.Hostile && !o.Elite && o.State != EnemyState.Dying && (o.X - p.X) * (o.X - p.X) + (o.Z - p.Z) * (o.Z - p.Z) < 32 * 32)
                o.Status[StatusKind.Fear] = new StatusSlot(3.5, 1, 1, 0);
        B.Events.Emit(new Ev.Shake { Amount = 0.35 });
        // A story night ends on its beat (the bible, section 2): once the fall has landed, the
        // night gives up its spoils to the survivor, and then lets them go.
        if (Spec.Story)
        {
            G.After(2.4, () => { if (B != null && !over) foreach (var k in B.Pickups.Items) if (k.Alive) k.Pulled = true; });
            G.After(7, () => { if (won && !over) Finish(); });
        }
        // The words a beat after the blow, as time comes back, not over the flash.
        G.After(0.8, () => G.Announce(new Announcement($"{Spec.Name} is won", Spec.Story ? "The night is over, and it lets you go." : "The way out is open. Or stay: the night does not end, and it only gets harder.", "reward", 4, "Victory")));
        Objectives();
    }

    /// <summary>Out by the way out (only once the fight is won).</summary>
    public void Leave()
    {
        if (won && !over) Finish();
    }

    public override bool OnDeath(string killer)
    {
        if (!over) Finish(killer);
        return true;
    }

    void Finish(string? killer = null)
    {
        if (B == null) return;
        over = true;
        G.SetBoss(null);
        var result = Arenas.Finish(G.Journey, B, Spec, won, killer);
        G.After(B.Player.Alive ? 0.6 : 2.2, () => G.ArenaOver(result));
    }

    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    public override void Frame(double dt)
    {
        if (B == null || over) return;
        crowdSeen += (aliveNow - crowdSeen) * Math.Min(1, dt / 5);
        double t = Math.Clamp((crowdSeen - 30) / 190, 0, 1);
        double want = CameraNear + (CameraFar - CameraNear) * t * t * (3 - 2 * t);
        if (bossUp) want = Math.Max(want, CameraFar + 2);
        else if (won) want = Math.Min(34, Math.Max(want, CameraFar));
        CameraDistance += (want - CameraDistance) * Math.Min(1, dt / 2.5);
        // The way out, pulsing on the ground where the boss fell.
        if (way is var (wx, wz) && (pulseT -= dt) <= 0)
        {
            pulseT = 1.3;
            // A band of light, not a filling disc: the field round it stays readable.
            B.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Ring, X = wx, Z = wz, Inner = 1.9, Radius = 2.4, Duration = 1.2, Hostile = false });
        }
        // The core: a lump of raw ember, pulsing, brighter as it is broken.
        if (coreOrb != null && core != null)
        {
            double ct = Seconds, hurt = 1 - core.Hp / Math.Max(1, core.MaxHp);
            coreOrb.Visible = true;
            coreOrb.Place(core.X, G.Look.HeightAt(core.X, core.Z) + 0.45, core.Z, ct * 0.15, 1 + 0.03 * Math.Sin(ct * 5.1) + 0.12 * hurt);
            coreOrb.Light = Math.Min(1, hurt + 0.08 * Math.Sin(ct * 5.1));
        }
        if (boss is { Alive: true } b && b.State != EnemyState.Dying)
            G.SetBoss(script != null ? script.Bar(BossName, script is Grimtunnel g ? $"{BossTitle} · {(g.Ganger ? "lamp" : "lamps")}: {g.Lamps}" : BossTitle) : new BossBar(BossName, BossTitle, b.Hp, b.MaxHp));
        else if (CoreUp && core is { } cc)
            G.SetBoss(new BossBar("The ember-core", $"Break it: {Math.Max(0, 60 - (Seconds - kindledAt)):0} s", cc.Hp, cc.MaxHp, IsBoss: false));
        else if (herald is { Alive: true } h && h.State != EnemyState.Dying)
            G.SetBoss(new BossBar(h.Named?.Title ?? $"Herald of {people.Name}", h.Def.Signs.Length > 0 ? string.Join(", ", h.Def.Signs.Select(s => Signs.Get(s).Name)) : people.Name, h.Hp, h.MaxHp, IsBoss: false));
        else if (keeper is { Alive: true } kp && kp.State != EnemyState.Dying && kp.Named != null)
            G.SetBoss(new BossBar(kp.Def.Name, kp.Def.Lesson, kp.Hp, kp.MaxHp, IsBoss: false));
        else if (MinibossUp && miniboss is { } mb)
            G.SetBoss(new BossBar(mb.Def.Name, mb.Def.Lesson.Length > 0 ? mb.Def.Lesson : people.Name, mb.Hp, mb.MaxHp, IsBoss: false));
        else G.SetBoss(null);
        // The clock on the objectives, each second.
        if ((int)Seconds != lastSecond) { lastSecond = (int)Seconds; Objectives(); }
    }

    int lastSecond = -1;

    void Objectives()
    {
        int left = (int)Math.Max(0, End - Seconds);
        bool goesDown = script is Grimtunnel { Ganger: false };
        var steps = new List<Step>
        {
            // "Down" holds for every end a fight has: killed, let go, laid down, or sent back down the hole.
            won ? new Step(goesDown ? $"{BossName} is driven back down: the night is held" : $"{BossName} is down: the night is held", Done: true)
            : bossUp ? new Step($"{BossName} has come: {(goesDown ? "drive him back down" : "end it")}")
            : new Step($"Survive: {left / 60}:{left % 60:00} until {Maps.MapOffers.InSentence(BossName)} comes"),
        };
        if (won)
        {
            // A story's night is over at the fall: nothing comes again.
            if (Spec.Story) steps.Add(new Step("The night lets you go", Optional: true));
            else
            {
                steps.Add(new Step($"Stay as long as you dare: {Clock(Seconds - End)} {Past}", Optional: true));
                int back = (int)Math.Max(0, nextReturn - Seconds);
                steps.Add(new Step(bossUp ? $"{BossName} has come again" : $"{BossName} comes again in {back / 60}:{back % 60:00}", Optional: true));
            }
            if (dark.Count > 0 || deeper > 0)
                steps.Add(new Step($"The dark has sworn {string.Join(", ", dark.Select(o => o.Name.Replace("Oath of ", "")))}{(deeper > 0 ? $", and deepened {deeper} times" : "")}", Optional: true));
        }
        foreach (var o in oaths) steps.Add(new Step($"{o.Name}: {o.Asks.ToLowerInvariant()}", Optional: true));
        G.SetObjectives([new Tracked("arena", Spec.Name, TrackTone.Main, steps)]);
    }

    public override AmbienceMix Ambience(double x, double z) => new() { Wind = 0.4, Leaves = Spec.Theme == "blight" ? 0.1 : 0.35, Crickets = 0.3, Owl = 0.2, Fire = Warmth(x, z) };

    public override Dictionary<string, object?> Debug() => new()
    {
        ["minute"] = Math.Round(Minute, 1), ["alive"] = B?.Enemies.Living().Count() ?? 0, ["target"] = Target(), ["level"] = Level(),
        ["stones"] = B?.EmbersLying, ["hoard"] = B?.HoardStone is { } h ? Math.Round(h.Value) : 0, ["ember"] = B?.EmberLevel,
    };
}

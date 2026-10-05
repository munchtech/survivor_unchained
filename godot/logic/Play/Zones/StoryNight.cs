using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* A story night (docs/design/STORY_NIGHTS_AND_TIME.md, STORY_BOSSES.md): a
 * short night in a place made for its fight. The owner: "much more
 * specialized and fun - smaller arena - and they don't need endless - they
 * have proper arpg end bosses".
 *
 *   the way in   three stages, each ended by its goal and never by a clock;
 *                the story's sight between them, and a few quiet seconds
 *   the boss     on its own ground, a proper fight of three to four minutes;
 *                its end is the story's (let go, the knee, down the hole, the
 *                hand at the gate), and the night ends with it
 *   a fall       in Act 1, she gets up once: at the stage's start with the
 *                build she brought into it, or at the boss's opening whole.
 *                Later, only Cold, Then Not gets her up (one rise a fight,
 *                however she carries it). Otherwise the night is lost, and
 *                she wakes in town a day on (the experience lead's).
 *
 * It is still a night: the ember starts from nothing and drafts, paid about
 * two and a half times quicker, so she meets the boss with what a table night
 * has at its twentieth minute. The waves are finite and each stage's
 * creatures are at its own level, so a slow stage is no harder, a rise
 * replays the same stage, and nothing is farmed. */
public sealed class StoryNight : ZoneRuntime, IStoryArena
{
    public readonly ArenaSpec Spec;
    public readonly StoryFight Fight;
    readonly MapBuild map;
    readonly Denizens people;
    readonly string[] lean;

    /// <summary>The ember paid this much quicker than a table night's: she meets the boss with about a
    /// table night's twentieth-minute build (experience agreed).</summary>
    public const double EmberPace = 2.5;

    public enum Stage { Beat, Between, Boss, Won, Over }
    public Stage Now { get; private set; } = Stage.Beat;
    int beatIx;
    StoryBeat? beat;
    double betweenT;
    BuildSnapshot? checkpoint;
    (double X, double Z) getUp;
    bool atBoss;
    int falls;
    bool falling;
    StoryBoss? script;
    Enemy? boss;
    bool won, over;
    readonly List<Deadfall> fires = new();
    /// <summary>The place's spaces open now: where she, a leap and the crowd may be.</summary>
    readonly HashSet<string> open = new();
    readonly Dictionary<int, (double Seed, Func<Enemy, double, bool> Tick)> scripted = new();
    readonly HashSet<int> smallChests = new(), chests = new();
    readonly Dictionary<int, double> leaving = new();
    int chestsOpened;
    /// <summary>What is left of the stage's crowd, and when it next tops up.</summary>
    int crowdLeft;
    double crowdT;

    /// <summary>How each stage went, for the harness: how long, the lowest health, the falls in it.</summary>
    public sealed record StageLog(string Name, double Seconds, double LowHp, int Falls);
    public readonly List<StageLog> Log = new();
    double stageAt, stageLow = 1;
    int stageFalls;

    public StoryNight(IZoneHost host, MapBuild map, ArenaSpec spec, StoryFight fight) : base(host, map.Meta)
    {
        Spec = spec;
        Fight = fight;
        this.map = map;
        people = MapOffers.People(spec.People);
        lean = MapOffers.Lean(spec.Map, spec.People);
        Hooks = new BattleHooks
        {
            OnKill = OnKill, OnLoot = OnLoot, OnPickup = OnPickup, OnPlayerDeath = OnFall,
            BossTick = (e, dt) => standing ? Stand(e) : e == boss && script != null ? script.Tick(e, dt) : scripted.TryGetValue(e.Id, out var s) && s.Seed == e.Seed && s.Tick(e, dt),
            OnBossHit = (e, school, dmg) => { if (e == boss) script?.OnHit(e, school, dmg); },
            OnBossStagger = e => { if (e == boss) script?.OnStagger(e); },
        };
    }

    public override string Id => "arena";
    public override string Name => Spec.Name;
    public override string? Region => Spec.Sub != "" ? Spec.Sub : people.Name;
    public override bool Combat => true;
    public override bool Ember => true;
    public override (double Pitch, double Distance)? Camera => (64, CameraNear);
    const double CameraNear = 22, CameraBoss = 27;
    /// <summary>How far out the camera stands: close for the way in (the place is the fight), back a
    /// little for the boss's ground.</summary>
    public double CameraDistance { get; private set; } = CameraNear;
    public override IReadOnlyList<string> Creatures =>
        people.Arena.Select(h => h.Def).Concat(people.Stretches.SelectMany(s => s.Joins.Append(s.Miniboss))).Append(people.Champion).Append(Fight.BossDef).Distinct().ToList();
    public override TimeOfDay TimeOf(WorldState w) => TimeOfDay.Night;
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) =>
        t == TimeOfDay.Night && map.Place is { } place ? place.Night : base.AtmosphereFor(t);
    public override Arrival ArrivalFrom(string? from)
    {
        var (x, z) = Fight.Place[Fight.Arrive];
        // Facing the way in: toward the first gate.
        var g = Fight.Place.Gates.FirstOrDefault();
        double nx = g != null ? (g.X0 + g.X1) / 2 : 0, nz = g != null ? (g.Z0 + g.Z1) / 2 : 0;
        return new Arrival(x, z, Math.Atan2(nx - x, nz - z));
    }

    public bool Won => won;
    /// <summary>The share of its health the boss is made with (1; less only for pictures of its end).</summary>
    public double BossStartsAt { get; set; } = 1;
    public bool Over => over;
    public ArenaBoss? BossScript => script;
    public int Falls => falls;
    public int BeatIx => beatIx;
    public StoryBeat? Beat => beat;
    double Seconds => B?.Time ?? 0;
    string BossName => Spec.BossName ?? people.BossName;
    string BossTitle => Spec.BossTitle ?? people.BossTitle;

    /// <summary>Rises a story night gives of itself: one in Act 1, none after (the owner: "get up once
    /// i guess is ok? but only in early game"). Cold, Then Not is hers to carry beyond that.</summary>
    public static int RisesFor(WorldState w) => w.Fact("chapter.done").Truthy ? 0 : 1;

    /* ------------------------------------------------------------ begun -- */

    public override void Begin(Battle b)
    {
        base.Begin(b);
        // Until arena art builds a fight's place to its outline (PlaceBuilt), the old round arena's props
        // stand inside it: a stump in a neck the fight needs, a cart across a gate. Where the place is, they
        // go, drawn and solid both; its own cover comes with its own build.
        bool clear = !Fight.PlaceBuilt;
        foreach (var pc in map.Pieces)
            if (!clear || !Fight.Place.Inside(pc.X, pc.Z, -1.5)) G.Look.AddProp(pc.Id, pc.X, pc.Z, pc.Rot, pc.Scale);
        if (clear)
            foreach (var c in b.Collision.All().Where(c => c.Tag == null && Fight.Place.Inside(c.X, c.Z, -1.5)).ToList()) b.Collision.Remove(c.Id);
        b.Rules = MapOffers.Rules(Spec.Map);
        // The table's gold rates (crafting's economy): a night's rank and file pay a little.
        b.Rules.FodderGold = 0.0015;
        b.Rules.ChampionGold = 0.07;
        // A kill's ember grows with its level, and a story night's yardstick (a table night's twelfth minute)
        // does not: the same night gives the same build at every tier (measured: five cards more at tier 4).
        b.Rules.EmberGain *= EmberPace / Enemies.ScaleFor(Spec.Tier * 3 - 2).Xp;
        b.Rules.Light *= 1.6;
        var place = Fight.Place;
        var (ax, az) = place[Fight.Arrive];
        open.Add(place.SpaceAt(ax, az) ?? place.Spaces[0].Id);
        b.InBounds = (x, z) => map.CanStand(x, z) && place.Inside(x, z, 0.3, open);
        place.Build(b.Collision);
        Fight.Furnish(this);
        b.Charges.Spikes = false;
        b.Charges.Cap = 2;
        double burns = Fight.Burns(this);
        foreach (var id in Fight.Fires)
        {
            var (x, z) = place[id];
            // The place's own fire laid in the deadfall (arena art's: flames along the wood), or a light.
            int light = map.FireLights.TryGetValue(id, out var laid) ? laid : G.Look.AddLight(x, 1.1, z, "#ff8a3a", 2.8, 10, 0.22, 0.1, "#ffb35a");
            var f = new Deadfall { Id = id, X = x, Z = z, Burns = burns, Light = light };
            G.Look.SetLit(f.Light, false);
            fires.Add(f);
        }
        // The first great blessing, before anything moves (another as the boss's ground opens).
        b.GreatOwed = 1;
        G.Announce(new Announcement(Spec.Name, Region, "zone", 3.4, "Story night"));
        G.Say(Fight.Pull);
        StartBeat(0);
    }

    /// <summary>Pictures and probes: straight to a stage (or the boss: Fight.Beats.Length), the ground
    /// behind opened. `floors`: with the ember the stages passed over would have left her at least (their
    /// floors, drafted as she goes) and the night's first great blessing, so a picture of a later stage is
    /// of the build that meets it; otherwise the build as it stands.</summary>
    public void SkipTo(int stage, bool floors = false)
    {
        if (B == null) return;
        stage = Math.Clamp(stage, 0, Fight.Beats.Length);
        beat?.End();
        Clear(all: true);
        int floor = 0;
        for (int i = 0; i < stage && i < Fight.Beats.Length; i++)
            if (Fight.Beats[i]() is { } passed)
            {
                if (passed.Gate is { } g) Open(g);
                floor = Math.Max(floor, passed.EmberFloor);
            }
        if (floors)
            for (int k = 0; k < 200 && B.EmberLevel < floor; k++) B.GainEmber(Math.Max(1, B.EmberNext - B.EmberXp), raw: true);
        else B.GreatOwed = 0;
        if (stage >= Fight.Beats.Length) { beatIx = stage - 1; BossOpen(); }
        else StartBeat(stage);
        var (x, z) = getUp;
        B.Player.X = x; B.Player.Z = z;
    }

    /* --------------------------------------------------------- the stages -- */

    void StartBeat(int i)
    {
        beatIx = i;
        beat = Fight.Beats[i]();
        getUp = Fight.Place[beat.Start];
        checkpoint = B!.Snapshot();
        Now = Stage.Beat;
        Goal = null;
        crowdLeft = beat.CrowdPool;
        crowdT = 1;
        StageBegun();
        beat.Begin(this);
        Objectives();
    }

    void StageBegun()
    {
        stageAt = Seconds;
        stageLow = B!.Player.Hp / Math.Max(1, B.MaxHp);
        stageFalls = 0;
    }

    void StageEnded(string name) => Log.Add(new StageLog(name, Seconds - stageAt, stageLow, stageFalls));

    void EndBeat()
    {
        var b = beat!;
        b.End();
        StageEnded($"stage {beatIx + 1}");
        // What the stage's dead would have given her, if she was quicker than they were many.
        for (int k = 0; k < 200 && B!.EmberLevel < b.EmberFloor; k++) B.GainEmber(Math.Max(1, B.EmberNext - B.EmberXp), raw: true);
        if (b.Gate is { } g) Open(g);
        if (Fight.BetweenSight(this, beatIx) is { } sight) G.Say(sight);
        // The stage's leftovers fall back into the dark: the quiet between is quiet.
        MakeWay();
        B!.Charges.Calm(B, 6);
        Now = Stage.Between;
        betweenT = 6;
        Goal = beatIx + 1 < Fight.Beats.Length ? Fight.Place[Fight.Beats[beatIx + 1]().Start] : Fight.Place[Fight.BossStart];
        Objectives();
    }

    bool shutBehind;

    static double SegDist(double x, double z, double x0, double z0, double x1, double z1)
    {
        double lx = x1 - x0, lz = z1 - z0, len2 = lx * lx + lz * lz;
        double t = len2 > 0 ? Math.Clamp(((x - x0) * lx + (z - z0) * lz) / len2, -0.3, 1.3) : 0;
        return Dist(x, z, x0 + lx * t, z0 + lz * t);
    }

    /// <summary>The boss's own ground: the space its start stands in.</summary>
    string? BossGround => Fight.Place.SpaceAt(Fight.Place[Fight.BossStart].X, Fight.Place[Fight.BossStart].Z);
    /// <summary>On it, and through its gate: on the same side of every gate into it as its start, and clear of
    /// it (a gate's neck belongs to the space it opens, so in the neck she may still be on the near side).</summary>
    bool OnBossGround()
    {
        if (BossGround is not { } g || B == null) return false;
        var p = B.Player;
        if (!Fight.Place.In(g, p.X, p.Z, 1.0)) return false;
        var (sx, sz) = Fight.Place[Fight.BossStart];
        foreach (var gate in Fight.Place.Gates.Where(q => q.Into == g))
        {
            double lx = gate.X1 - gate.X0, lz = gate.Z1 - gate.Z0;
            double her = lx * (p.Z - gate.Z0) - lz * (p.X - gate.X0), start = lx * (sz - gate.Z0) - lz * (sx - gate.X0);
            if (Math.Sign(her) != Math.Sign(start) || SegDist(p.X, p.Z, gate.X0, gate.Z0, gate.X1, gate.Z1) < 2.5) return false;
        }
        return true;
    }

    /// <summary>A point on the boss's ground's side of every gate into it (as its start is).</summary>
    bool PastGates(double x, double z)
    {
        if (BossGround is not { } g) return true;
        var (sx, sz) = Fight.Place[Fight.BossStart];
        foreach (var gate in Fight.Place.Gates.Where(q => q.Into == g))
        {
            double lx = gate.X1 - gate.X0, lz = gate.Z1 - gate.Z0;
            if (Math.Sign(lx * (z - gate.Z0) - lz * (x - gate.X0)) != Math.Sign(lx * (sz - gate.Z0) - lz * (sx - gate.X0))) return false;
        }
        return true;
    }

    /// <summary>On the boss's ground, the way back shuts behind her (his people close it): the fight is
    /// on its ground, and a fight that drifts back down the way in is a fight that never ends.</summary>
    void ShutBehind()
    {
        if (shutBehind || B == null) return;
        var ground = BossGround;
        if (ground == null || !OnBossGround()) return;
        shutBehind = true;
        foreach (var g in Fight.Place.Gates.Where(g => g.Into == ground))
        {
            StoryPlace.Shut(B.Collision, g);
            if (Fight.ShutSight is { } sight) B.Events.Emit(new Ev.Bark { X = (g.X0 + g.X1) / 2, Z = (g.Z0 + g.Z1) / 2, Text = sight });
        }
        open.Clear();
        open.Add(ground);
    }

    void Open(string gate)
    {
        var g = Fight.Place.Gates.FirstOrDefault(x => x.Id == gate);
        if (g == null) return;
        StoryPlace.Open(B!.Collision, g);
        open.Add(g.Into);
        // The ember's line across the way goes out (its char stays on the ground).
        G.Look.Show($"gate:{g.Id}", false);
    }

    /* ------------------------------------------------------------- the boss -- */

    /// <summary>The boss's ground opens: a checkpoint (she gets up here whole), the night's second great
    /// blessing, its sign, and it comes.</summary>
    void BossOpen()
    {
        atBoss = true;
        if (Fight.BossGate is { } g) Open(g);
        getUp = Fight.Place[Fight.BossStart];
        B!.GreatOwed++;
        checkpoint = B.Snapshot();
        bossBlowsBefore = B.BossBlowsTaken;
        StageBegun();
        Arrive(rise: false);
    }

    void Arrive(bool rise)
    {
        var b = B!;
        Clear(all: false);
        var (x, z) = Fight.Place[Fight.BossAt];
        script = Fight.Boss(this);
        boss = Spawn(Fight.BossDef, x, z, true, SpawnStyle.Walk);
        if (boss != null)
        {
            boss.Boss = true;
            boss.Named = new Named { Title = BossName };
            boss.MaxHp = boss.Hp = boss.MaxHp * script.HealthMul(Spec.Tier) / BossEase;
            // (pictures of its end, --bosshp: a boss of a share of its health, its marks with it and its floors
            // still holding every phase; begun lower, the phases' marks healed it back up to them)
            boss.MaxHp = boss.Hp = boss.MaxHp * Math.Clamp(BossStartsAt, 0.01, 1);
            boss.Damage = script.Teeth * Character.OwnHealth(G.Journey.Ch);
            script.Begin(boss);
            b.Events.Emit(new Ev.Focus { X = x, Z = z, Duration = rise ? 1.0 : 1.6 });
        }
        b.Events.Emit(new Ev.Bark { X = x, Z = z, Text = rise ? script.ReEntry : Fight.Sign });
        if (!rise) Cinematic("arrival");
        if (Fight.Place.Points.ContainsKey("fire:c") && Fact("bane.fires"))
            foreach (var f in fires.Where(f => !f.Burning)) b.Mark(TelegraphKind.Safe, f.X, f.Z, 1.4, 30);
        Now = Stage.Boss;
        Goal = null;
        G.Announce(new Announcement(BossName, $"{BossTitle} · Weakness: {script.WeaknessText}", "danger", 3.4, rise ? "Again" : "The night's end"));
        Objectives();
    }

    /// <summary>The boss's own cinematic part (C10 to C13), where one can play.</summary>
    void Cinematic(string part)
    {
        if (Fight.Cinematic is { } c && G.CanCinematic($"{c}_{part}")) G.Cinematic($"{c}_{part}");
    }

    /* ------------------------------------------------------------- each step -- */

    public override void Step(double dt)
    {
        if (B == null || over) return;
        var p = B.Player;
        Burn(dt);
        if (falling) { p.Iframes = Math.Max(p.Iframes, 1); return; }
        stageLow = Math.Min(stageLow, p.Hp / Math.Max(1, B.MaxHp));
        switch (Now)
        {
            case Stage.Beat:
                Crowd(dt);
                beat!.Step(dt);
                if (beat.Done) EndBeat();
                break;
            case Stage.Between:
                betweenT -= dt;
                if (betweenT <= 0)
                {
                    if (beatIx + 1 < Fight.Beats.Length) StartBeat(beatIx + 1);
                    // The boss comes when she steps onto his ground (or, if she does not come, the ember
                    // takes her there after a while: a night is not lost standing at a gate).
                    else if (OnBossGround() || betweenT < -20)
                    {
                        if (!OnBossGround()) { var (gx, gz) = Fight.Place[Fight.BossStart]; B.Player.X = gx; B.Player.Z = gz; }
                        BossOpen();
                    }
                }
                break;
            case Stage.Boss:
                ShutBehind();
                script?.Grows(dt);
                script?.Step(dt);
                break;
        }
        Leaving();
        Strays(dt);
    }

    double strayT;

    /// <summary>Anything of the fight's put out of its open ground (a shove, a slide, a run) is brought back to the
    /// nearest of the place's points it may stand on: a goal out of reach is a night that never ends.</summary>
    void Strays(double dt)
    {
        if ((strayT -= dt) > 0) return;
        strayT = 0.5;
        // She is held by the place as its foes are. (Put out past the lip's wall at the Heart's turn, a night stood
        // outside its own fight until the cap.)
        var me = B!.Player;
        if (!Fight.Place.Inside(me.X, me.Z, -0.8, open) || shutBehind && !PastGates(me.X, me.Z))
        {
            var back = Home(me.X, me.Z, me.Radius, boss: true);
            if (back != default) { me.X = back.X; me.Z = back.Z; me.Vx = me.Vz = 0; }
        }
        foreach (var e in B!.Enemies.Living())
        {
            // A named foe the stage asks her to reach, or the boss, is brought back however its script moved it,
            // and whoever it is with (Whitethroat ran her drive's lane out through the den's wall, and stood there;
            // Grimtunnel was knocked out past the lip's).
            bool named = e.Named != null;
            if (!named && (e.Disposition != Disposition.Hostile || e.Scripted || e.Boss) || e.State is EnemyState.Dying or EnemyState.Burrowed) continue;
            // (The boss, once the way back is shut, on his own side of it too: pushed out of a hole of his own
            // making, Grimtunnel went through the shut gate.)
            if (Fight.Place.Inside(e.X, e.Z, -0.8, open) && !(e.Boss && shutBehind && !PastGates(e.X, e.Z))) continue;
            var home = Home(e.X, e.Z, e.Radius, e.Boss);
            if (home == default) continue;
            e.X = home.X; e.Z = home.Z; e.Kbx = e.Kbz = 0;
        }
    }

    /// <summary>Free ground nearest a point: the place's points, and ground round each (a boss is big, and his own
    /// holes fill his ground); past the shut gate for the boss (and her) once it is shut. (A point the fight has
    /// since filled is no home: Grimtunnel set down at the crack's end, in the crack, was pushed out of it
    /// through the wall, and back, and out.)</summary>
    (double X, double Z) Home(double x, double z, double radius, bool boss) => Fight.Place.Points.Values
        .SelectMany(q => Enumerable.Range(0, 17).Select(k => k == 0 ? (X: q.X, Z: q.Z)
            : (X: q.X + Math.Cos(k * Math.PI / 4) * (k <= 8 ? 2.5 : 5), Z: q.Z + Math.Sin(k * Math.PI / 4) * (k <= 8 ? 2.5 : 5))))
        .Where(q => Fight.Place.Inside(q.X, q.Z, 1, open) && (!boss || !shutBehind || PastGates(q.X, q.Z)) && !B!.Collision.Blocked(q.X, q.Z, radius))
        .OrderBy(q => Dist(q.X, q.Z, x, z)).FirstOrDefault();

    /// <summary>The stage's crowd kept standing, from its points out of her reach, until its pool is spent.</summary>
    void Crowd(double dt)
    {
        var bt = beat!;
        if (crowdLeft <= 0 || bt.Crowd.Length == 0 || (crowdT -= dt) > 0) return;
        crowdT = 0.45;
        int alive = Hostiles();
        if (alive >= bt.CrowdAlive) return;
        var p = B!.Player;
        var all = bt.CrowdFrom.Select(id => Fight.Place[id]).ToList();
        var far = all.Where(q => Dist(q.X, q.Z, p.X, p.Z) > 10).ToList();
        var (x, z) = (far.Count > 0 ? far : all)[(int)(R() * (far.Count > 0 ? far.Count : all.Count))];
        double sum = bt.Crowd.Sum(c => c.Weight), roll = R() * sum;
        string def = bt.Crowd[^1].Def;
        foreach (var c in bt.Crowd) { roll -= c.Weight; if (roll <= 0) { def = c.Def; break; } }
        int n = Math.Min(crowdLeft, Math.Min(bt.CrowdAlive - alive, 3 + (int)(R() * 4)));
        crowdLeft -= Math.Max(1, Group(def, n, x, z, 3.5).Count);
    }

    /// <summary>The deadfalls: she stands at one two seconds and the ember in her lights it; it burns
    /// a while, and what fears fire (the Pack) will not stand in its light.</summary>
    void Burn(double dt)
    {
        var p = B!.Player;
        foreach (var f in fires)
        {
            if (f.Lit > 0)
            {
                f.Lit -= dt;
                if (f.Lit <= 0) { f.Lit = 0; G.Look.SetLit(f.Light, false); }
            }
            bool at = Dist(p.X, p.Z, f.X, f.Z) < 1.9;
            if (at && (!f.Burning || f.Lit < 5))
            {
                if (f.Kindling == 0) B.Events.Emit(new Ev.Telegraph { Id = 870000 + fires.IndexOf(f), Shape = TelegraphShape.Ring, Kind = TelegraphKind.Safe, X = f.X, Z = f.Z, Inner = 1.4, Radius = 1.9, Duration = 2, Hostile = false });
                f.Kindling += dt;
                if (f.Kindling >= 2)
                {
                    f.Kindling = 0;
                    f.Lit = f.Burns;
                    if (!f.EverLit) B.Events.Emit(new Ev.Bark { X = f.X, Z = f.Z + 1, Text = "The dead wood takes the ember." });
                    f.EverLit = true;
                    G.Look.SetLit(f.Light, true);
                    B.Events.Emit(new Ev.Explosion { X = f.X, Z = f.Z, Radius = 1.6, School = School.Fire, Power = 0.6 });
                }
            }
            else f.Kindling = 0;
            if (!f.Burning) continue;
            // The Pack keeps out of a fed fire's light.
            foreach (var e in B.Enemies.Living())
            {
                if (e.Boss || e.Scripted || e.Faction != Faction.Pack || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
                double d = Dist(e.X, e.Z, f.X, f.Z);
                if (d >= f.Reach || d < 0.01) continue;
                e.X = f.X + (e.X - f.X) / d * f.Reach;
                e.Z = f.Z + (e.Z - f.Z) / d * f.Reach;
            }
        }
    }

    /// <summary>What a stage leaves falls back into the dark, and is let go once out of sight.</summary>
    void MakeWay()
    {
        foreach (var e in B!.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.Boss || e.Scripted || e.State == EnemyState.Dying) continue;
            e.Status[StatusKind.Fear] = new StatusSlot(5, 1, 1, 0);
            leaving[e.Id] = e.Seed;
        }
    }

    void Leaving()
    {
        if (leaving.Count == 0) return;
        var p = B!.Player;
        foreach (var (id, seed) in leaving.ToList())
        {
            var e = B.Enemies.Items[id];
            if (!e.Alive || e.Seed != seed || e.State == EnemyState.Dying) leaving.Remove(id);
            else if (Dist(e.X, e.Z, p.X, p.Z) > 18 || !e.Status.Has(StatusKind.Fear)) { B.Enemies.Release(e); leaving.Remove(id); }
        }
    }

    /// <summary>The field cleared: every creature of the fight (all: the boss's too), every blow still to
    /// land, everything thrown and laid on the ground.</summary>
    void Clear(bool all)
    {
        var b = B!;
        if (all || atBoss)
        {
            script?.Clear();
            if (boss is { Alive: true }) b.Enemies.Release(boss);
            boss = null;
        }
        foreach (var e in b.Enemies.Living().ToList())
            if (e.Disposition != Disposition.Ally) b.Enemies.Release(e);
        foreach (var zn in b.Zones.Living().ToList()) if (zn.Owner is Side.Enemy) b.Zones.Release(zn);
        foreach (var pr in b.Projectiles.Living().ToList()) if (pr.Owner == Side.Enemy) b.Projectiles.Release(pr);
        b.CancelBlows();
        scripted.Clear();
        leaving.Clear();
        Interactables.RemoveAll(i => i.Id.StartsWith("story:"));
        Choice = null;
    }

    /* --------------------------------------------------------------- a fall -- */

    /// <summary>She falls: the night holds (nothing reaches her) while the host stages it; then she gets
    /// up, if a rise is left her, or the night is let go.</summary>
    bool OnFall(Enemy? killer)
    {
        if (B == null || over) return false;
        if (falling) return true;
        falls++;
        stageFalls++;
        falling = true;
        var p = B.Player;
        p.Hp = 1;
        p.Iframes = 99;
        B.Charges.Calm(B, 99);
        int risesLeft = Math.Max(0, RisesFor(W) - p.Rose);
        string by = killer == null ? "the dark" : Enemies.Called(killer.Named?.Title, killer.Def.Name);
        G.StoryFall(risesLeft, Rise, () => LetGo(by));
        return true;
    }

    /// <summary>Up again: at the stage's start with what she brought into it, or at the boss's opening
    /// whole, its ground as it opened.</summary>
    void Rise()
    {
        if (B == null || over || !falling) return;
        var p = B.Player;
        falling = false;
        p.Rose++;
        B.Restore(checkpoint!);
        if (atBoss) p.Hp = B.MaxHp;
        p.Iframes = 2.5;
        B.Charges.Calm(B, 3);
        var (x, z) = getUp;
        p.X = x; p.Z = z;
        p.Vx = p.Vz = 0;
        if (atBoss) Arrive(rise: true);
        else
        {
            beat?.End();
            Clear(all: false);
            beat = Fight.Beats[beatIx]();
            beat.Begin(this);
        }
        G.Revived(x, z);
        // The prologue's words the first time ever, a little less after (story.rises).
        G.Say(G.Journey.RiseLine());
        Objectives();
    }

    void LetGo(string by)
    {
        if (B == null || over) return;
        falling = false;
        StageEnded(atBoss ? "boss" : $"stage {beatIx + 1}");
        StandDown();
        Finish(by);
    }

    /// <summary>The fight stands down where it is (UI design's finding: let go, the fight ran on under the
    /// fall's shade until the result came up, her weapons still firing and hitting): her weapons fall quiet,
    /// what was marked or thrown or laid on the ground goes, and everything on the field stands still where it
    /// is, as in the lost night's words ("None of them comes in"). Time still runs, so the result comes on its
    /// own beat.</summary>
    void StandDown()
    {
        var b = B!;
        standing = true;
        b.Combat = false;
        b.CancelBlows();
        foreach (var pr in b.Projectiles.Living().ToList()) b.Projectiles.Release(pr);
        foreach (var zn in b.Zones.Living().ToList()) b.Zones.Release(zn);
        foreach (var e in b.Enemies.Living())
        {
            e.Scripted = true;
            e.Provoked = false;
            e.Target = -1;
            if (e.Disposition != Disposition.Ally) e.Disposition = Disposition.Neutral;
            Stand(e);
        }
    }

    /// <summary>The field stood down (StandDown): a creature still where it is.</summary>
    bool standing;
    static bool Stand(Enemy e)
    {
        e.Vx = e.Vz = 0;
        if (e.State != EnemyState.Dying) { e.State = EnemyState.Idle; e.Anim = EnemyAnim.Idle; }
        return true;
    }

    public override bool OnDeath(string killer)
    {
        if (!over) Finish(killer);
        return true;
    }

    /* -------------------------------------------------------------- the end -- */

    void OnKill(Enemy e, bool byPlayer)
    {
        if (e == boss && !over && !won)
        {
            script?.Fell(e);
            Victory(e.X, e.Z, spared: false);
        }
    }

    /// <summary>The boss's end: the story told how it went, its hoard, and the night lets her go.</summary>
    void Victory(double x, double z, bool spared)
    {
        if (won || B == null) return;
        won = true;
        Now = Stage.Won;
        StageEnded("boss");
        if (boss != null) foreach (var l in Hoard()) B.Spill(l, x, z);
        script?.Clear();
        boss = null;
        // The outcome told first: the end's cinematic reads it (redcowl = spared picks its words).
        Arenas.Won(G.Journey, Spec, spared);
        foreach (var e in B.Enemies.Living().ToList())
            if (e.Disposition != Disposition.Ally && !e.Boss) e.Status[StatusKind.Fear] = new StatusSlot(4, 1, 1, 0);
        Cinematic(spared ? "spared" : "end");
        B.Events.Emit(new Ev.Victory { X = x, Z = z });
        B.Events.Emit(new Ev.Focus { X = x, Z = z, Duration = 2.2 });
        B.Events.Emit(new Ev.Shake { Amount = 0.35 });
        G.After(2.4, () => { if (B != null && !over) foreach (var k in B.Pickups.Items) if (k.Alive) k.Pulled = true; });
        G.After(7, () => { if (won && !over) Finish(); });
        G.After(0.8, () => G.Announce(new Announcement($"{Spec.Name} is won", "The night lets you go.", "reward", 4, "Victory")));
        Objectives();
    }

    void Finish(string? killer = null)
    {
        if (B == null || over) return;
        over = true;
        Now = Stage.Over;
        G.SetBoss(null);
        var result = Arenas.Finish(G.Journey, B, Spec, won, killer);
        G.After(B.Player.Alive && killer == null ? 0.6 : 2.2, () => G.ArenaOver(result));
    }

    /* --------------------------------------------------------------- spoils -- */

    /// <summary>What a carrier leaves (docs/design/LOOT_DESIGN.md §5), rolled whole at its level; the
    /// story's boss pays the survivor's first Legendary for certain.</summary>
    List<Loot> Gear(int level, DropSource source) => G.Journey.Drops(new DropCtx
    {
        Source = source, Level = level, People = Spec.People, Lean = lean, Luck = B!.Stats.Get(Stat.Luck), Tier = Spec.Tier,
        Tally = true, StoryBoss = source == DropSource.Boss, R = R,
    });

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));
        if (carrier) o.AddRange(Gear(e.Level, small ? DropSource.Miniboss : DropSource.Champion));
        return o;
    }

    /// <summary>The boss's hoard: the night's best chest (a part more for a Break past a tenth of it, and
    /// for a fight with no marked blow taken), plain gear, and an art's manual.</summary>
    IEnumerable<Loot> Hoard()
    {
        var o = new List<Loot>();
        int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= script.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == bossBlowsBefore ? 1 : 0);
        o.Add(new Loot(PickupKind.Chest, "boss", n, true));
        o.AddRange(Gear(Level, DropSource.Boss));
        return o;
    }

    int bossBlowsBefore;

    bool OnPickup(Pickup p)
    {
        if (p.Kind != PickupKind.Chest || B == null) return true;
        double roll = R();
        int n = p.Ref == "boss" ? (int)p.Value : p.Ref == "small" ? 1 : LevelUp.ChestCount(roll);
        var got = LevelUp.OpenChest(B, n);
        chestsOpened++;
        G.Chest(new ChestOpened(p.X, p.Z, p.Id, got, p.Ref == "boss" ? $"{BossName}'s hoard" : null, chestsOpened));
        return true;
    }

    /* ---------------------------------------------------- what the fight asks -- */

    double R() => G.Rng.NextDouble();

    public StoryPlace Place => Fight.Place;
    /// <summary>The creature level now: the tier's base, the stage's own over it, and a dusk on the first
    /// stage as a table night has (the tier's strength comes in over it, a level a tier above the first):
    /// she meets it with nothing drafted, and at a higher tier her bare hands fall further behind.</summary>
    public int Level => Math.Max(1, Spec.Tier * 3 - 2 + (atBoss ? Fight.BossLevel : beat?.Level ?? 0) - (!atBoss && beatIx == 0 ? Spec.Tier - 1 : 0));
    public IReadOnlyList<Deadfall> Fires => fires;
    public bool Fact(string key) => F(key).Truthy;
    public (double X, double Z)? Goal { get; set; }
    public void Script(Enemy e, Func<Enemy, double, bool> tick) { e.Scripted = true; scripted[e.Id] = (e.Seed, tick); }
    public void Line(string text, string? speaker = null) => G.Say(text, speaker);
    public Fact FactOf(string key) => F(key);
    public void Apply(string effectsJson) => G.Apply(effectsJson);
    /// <summary>The spared ending is chosen in the fight when the story's spec carries both outcomes
    /// (OnSpare); without one, a spare the story allows happens of itself, as before.</summary>
    public bool CanSpare => Spec.OnSpare != null;
    public string SpareVerb => Spec.SpareVerb ?? "Let him go";
    public void Ended(double x, double z, bool spared) => Victory(x, z, spared);

    public void Offer(string id, double x, double z, string verb, string name, Action act)
    {
        Withdraw(id);
        Interactables.Add(new Interactable { Id = $"story:{id}", X = x, Z = z, R = 3.4, Verb = verb, Name = name, Act = act });
    }

    public void Withdraw(string id) => Interactables.RemoveAll(i => i.Id == $"story:{id}");

    public void Ask(string who, string title, double x, double z, params ChoiceAnswer[] answers) => Choice = new StoryChoice(who, title, answers, x, z);
    public void Unask() => Choice = null;

    bool Standable(double x, double z) => map.CanStand(x, z) && Fight.Place.Inside(x, z, 0.6, open) && !B!.Collision.Blocked(x, z, 0.6);

    Enemy? Spawn(string def, double x, double z, bool elite = false, SpawnStyle? style = null)
    {
        if (B == null) return null;
        var st = style ?? (Enemies.Get(def).Family == Family.Undead ? SpawnStyle.Rise : Enemies.Get(def).Behavior == Behavior.Tunneler ? SpawnStyle.Burrow : SpawnStyle.Walk);
        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level + (elite ? 1 : 0), Elite = elite, Style = st });
        // The crowd softens as a table night's does by its minute: the build's growth shows as a crowd
        // that melts (ArenaRun.FodderEase). Not the named, the champions or the boss.
        if (e != null && !e.Elite) e.MaxHp = e.Hp = e.MaxHp / ArenaRun.FodderEase(atBoss ? Fight.BossMinute : beat?.Minute ?? 0);
        if (e != null) e.MaxHp = e.Hp = e.MaxHp / TierEase;
        // The way in's rank and file bite softer than a table night's: the way in should dip, not fell
        // (STORY_BOSSES.md 0.6), and the danger belongs to the boss. The named keep their own teeth.
        if (e != null && !e.Elite && !atBoss) e.Damage *= Fight.CrowdTeeth;
        // Her health grows a little slower with her level than their bite does with theirs: eased a tier.
        if (e != null) e.Damage /= TierTeeth;
        return e;
    }

    /// <summary>How hard the way in's rank and file bite, against a table night's.</summary>
    public const double CrowdTeeth = 0.75;
    /// <summary>How much slower a named foe's fists are than its kind's.</summary>
    public const double NamedFists = 2;
    public double TierTeeth => 1 + 0.2 * (Spec.Tier - 1);
    public double Teeth => Fight.CrowdTeeth / TierTeeth;

    /// <summary>A story night is the same fight at every tier: its tier is the game's guess at how strong
    /// she has grown, and its creatures' levels already follow it. Their health grows faster with level
    /// than her build's damage does (measured: a tier-3 night's stages ran twice as long as a tier-1's,
    /// and were far more dangerous for it), so it is eased back a little a tier. Unlike the table's, a
    /// story night does not ask more of the draft as the tiers climb.</summary>
    public double TierEase => 1 + 0.3 * (Spec.Tier - 1);

    /// <summary>The boss eased the more as the tiers climb: his level grows his health faster than her own
    /// level grows her blows, so with the crowd's ease alone each story boss ran a third longer at tier 4
    /// than at tier 1 (Greymuzzle 2.6 against 3.6 minutes planned), and the longer a fight, the more of his
    /// blows land. The same boss at every tier, as the same night.</summary>
    public double BossEase => 1 + 0.1 * (Spec.Tier - 1);

    public Enemy? Foe(string def, double x, double z, double hpMul = 1, string? kicker = null, bool quiet = false)
    {
        var e = Spawn(def, x, z, true, SpawnStyle.Walk);
        if (e == null) return null;
        // A named foe: a miniboss's measure at its own level (between a champion's twice and a herald's
        // five times), times what its stage asks of it. Not more a tier: its level grows it already.
        e.MaxHp = e.Hp = e.MaxHp * 2.2 * hpMul;
        e.Named = new Named { Title = e.Def.Name };
        // Its lesson is its marked move (a lunge, a slam, its pots), not its fists: in a press it strikes half as
        // often as its kind. (The Pike-Captain, Barn-Door and the pickets brawled blade builds under half on the
        // way in, a blow a second, as much as all their marked moves.)
        var fists = e.Def.Clone();
        fists.AttackEvery = (fists.AttackEvery ?? 1.0) * NamedFists;
        e.Def = fists;
        if (quiet) return e;
        smallChests.Add(e.Id);
        B!.Charges.Calm(B, 4);
        G.Announce(new Announcement(e.Def.Name, e.Def.Lesson, "danger", 3.2, kicker ?? (Fight.Kicker != "" ? Fight.Kicker : null)));
        return e;
    }

    readonly HashSet<string> marks = new();
    public void Mark(string key) => marks.Add(key);
    public bool Marked(string key) => marks.Contains(key);
    public IOrb Piece(string id, double scale) => G.Look.Piece(id, scale);
    public double HeightAt(double x, double z) => G.Look.HeightAt(x, z);
    public bool Test(Cond cond) => Rules.Test(cond, C);
    bool IStoryArena.Knows(string key) => Knows(key);
    public void After(double seconds, Action act) => G.After(seconds, act);

    public List<Enemy> Group(string def, int n, double x, double z, double spread, SpawnStyle? style = null)
    {
        var o = new List<Enemy>();
        for (int i = 0; i < n; i++)
        {
            double sx = x, sz = z;
            for (int t = 0; t < 8; t++)
            {
                double a = R() * Math.PI * 2, d = R() * spread + t * 0.4;
                sx = x + Math.Cos(a) * d; sz = z + Math.Sin(a) * d;
                if (Standable(sx, sz)) break;
            }
            if (!Standable(sx, sz)) continue;
            if (Spawn(def, sx, sz, false, style) is { } e) o.Add(e);
        }
        return o;
    }

    public int Hostiles(Func<Enemy, bool>? which = null) =>
        B?.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && !e.Scripted && (which == null || which(e))) ?? 0;

    Battle IBossArena.B => B!;
    public int Tier => Spec.Tier;
    string IBossArena.BossName => BossName;
    bool IBossArena.Spare => Spec.Spare;
    bool IBossArena.Sworn(string oath) => Spec.Oaths.Contains(oath);
    double IBossArena.R() => R();
    Enemy? IBossArena.Spawn(string def, double x, double z, bool elite, SpawnStyle? style) => Spawn(def, x, z, elite, style);
    bool IBossArena.CanStand(double x, double z) => Standable(x, z);
    public void Say(string title, string? sub, string tone) => G.Announce(new Announcement(title, sub ?? "", tone, 2.4));
    public void Bark(double x, double z, string text, string? speaker) => B?.Events.Emit(new Ev.Bark { X = x, Z = z, Text = text, Speaker = speaker });
    double IBossArena.HordeShare { set { } }
    bool IBossArena.HordeReturns => false;
    void IBossArena.Won(double x, double z) => Victory(x, z, spared: false);

    /* ------------------------------------------------------------ on screen -- */

    public override void Frame(double dt)
    {
        if (B == null || over) return;
        double want = Now == Stage.Boss ? CameraBoss : CameraNear;
        CameraDistance += (want - CameraDistance) * Math.Min(1, dt / 2.5);
        // (the bar goes while her choice waits: the fight is over, and the choice stands where it stood)
        if (Now == Stage.Boss && boss is { Alive: true } b && b.State != EnemyState.Dying && script != null && Choice == null)
            G.SetBoss(script.Bar(BossName, script.State is { } s ? $"{BossTitle} · {s}" : BossTitle));
        else if (Now == Stage.Beat && beat?.Bar is { } bar) G.SetBoss(bar);
        else G.SetBoss(null);
        if ((int)Seconds != lastSecond) { lastSecond = (int)Seconds; Objectives(); }
    }

    int lastSecond = -1;

    void Objectives()
    {
        var steps = new List<Step>();
        switch (Now)
        {
            case Stage.Beat: steps.Add(new Step(beat!.Goal)); break;
            case Stage.Between: steps.Add(new Step("Go on")); break;
            case Stage.Boss: steps.Add(new Step($"{BossName} has come: end it")); break;
            default: steps.Add(new Step(won ? $"{BossName}: it is over" : "The night is lost", Done: won)); break;
        }
        if (!won)
        {
            int left = B == null ? 0 : Math.Max(0, RisesFor(W) - B.Player.Rose);
            steps.Add(new Step(left > 0 ? "If you fall here, you get up once" : "If you fall here, the night is lost", Optional: true));
        }
        G.SetObjectives([new Tracked("arena", Spec.Name, TrackTone.Main, steps)]);
    }

    public override AmbienceMix Ambience(double x, double z) => new() { Wind = 0.4, Leaves = Spec.Theme == "blight" ? 0.1 : 0.35, Crickets = 0.3, Owl = 0.2, Fire = Warmth(x, z) };

    public override Dictionary<string, object?> Debug() => new()
    {
        ["stage"] = Now.ToString(), ["beat"] = beatIx, ["falls"] = falls, ["level"] = Level, ["ember"] = B?.EmberLevel, ["shut"] = shutBehind, ["open"] = string.Join("+", open),
        ["alive"] = B?.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile) ?? 0,
    };
}

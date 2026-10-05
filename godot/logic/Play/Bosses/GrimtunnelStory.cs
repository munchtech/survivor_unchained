using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>
/// Grimtunnel on his own lip (docs/design/STORY_BOSSES.md 3): the Boss of the
/// Dig, three lamps, a grudge, and the Warden's heart keeping him company in
/// the dark. He cannot die in a fight; it is won when he goes back down the
/// hole, delighted. Snib comments from his heap while he lives. The ground is
/// the enemy, and the Boss is in a very good mood.
///
///   the shift      his lamps flare in turn (red: blasting ember lobbed round
///                  her; blue: the deep lamp, his diggers up under her; green:
///                  a cone of slurry): hit him while one flares to break it.
///                  Under: he dives and the mound runs at her, every weapon
///                  reaches it at half; he bursts up where it stops, then
///                  stands dazed (frost on the mound: up at once, dazed long).
///                  Moths: lamplings up round whatever is brightest.
///   the collapse   every Under leaves a sinkhole. Snib rolls a barrel of
///                  blasting ember off the heap: walked into, it rolls; on him
///                  it blows and his hide cracks; left, he throws it at her.
///   the heart      the crack he came up through opens across the ground (a
///                  dash carries her over it, or round its ends); the heart's
///                  pulse runs out in three bands; in a temper, his pick.
///   his end        he tumbles into the crack, hangs by his claws, and drops.
/// Its bane is his own lamp, carried from the prologue: set down, he comes up
/// under it twice, and stands looking at it.
/// </summary>
public sealed class GrimtunnelStory : StoryBoss, IBound
{
    public GrimtunnelStory(IStoryArena a) : base(a) { }

    protected override Phase[] Phases { get; } =
    [
        new("The Shift", 0.65, 25, 75),
        new("The Collapse", 0.30, 30, 75),
        new("The Heart", 0, 25, 0),
    ];
    public override School Weakness => School.Frost;
    public override string WeaknessText => "Frost stops him under the ground, and a lamp can be broken while it flares";
    protected override string HardName => "All Downstairs";
    protected override string HardSub => "The floor goes, from the edge in";
    protected override (string Title, string Sub) SoftWords(Enemy e) => ("The holes stay open", "The moths come quicker");
    public override string ReEntry => "The crack opens again, and he climbs out of it with his arms spread.";
    /// <summary>Measured to the length, as Greymuzzle's and Redcowl's were: the same at every tier. Under the
    /// ground he takes half, and his lamps take a quarter of what is put into him.</summary>
    public override double HealthMul(int tier) => 109;
    /// <summary>His teeth are in his marked moves; his burst up (×2) about a third of her health at a story
    /// night's build.</summary>
    public override double Teeth => 0.2;
    protected override bool DiesAtZero => false;
    protected override bool OverGaps => under;

    const string Him = "Grimtunnel";
    (double X, double Z) C => S.Place["boss_at"];
    (double X, double Z) CrackA => S.Place["crack_a"];
    (double X, double Z) CrackB => S.Place["crack_b"];
    /// <summary>How far the lip's ground runs from its middle (the caving bound starts there).</summary>
    const double GroundR = 12.5;

    /* ---------------------------------------------------------------- his lamps -- */

    /// <summary>His three lamps (red, blue, green): each lit, a verb; hit while it flares to break it.</summary>
    public readonly bool[] Lit = [true, true, true];
    readonly double[] lampHp = new double[3];
    int flaring = -1, lampIx = 2;
    double flareT;
    bool lampBroken;
    /// <summary>The lamp flaring now (-1: none): hit him while it does to break it.</summary>
    public int Flaring => flaring;
    static readonly string[] LampNames = ["red", "blue", "green"];

    /* -------------------------------------------------------------- the ground -- */

    readonly List<(double X, double Z, int Id, int Mark)> pits = new();
    readonly List<int> crack = new();
    bool crackOpen;
    double seamT, caveR = GroundR, caveT, caveDrawT, caveShoveT, caveGrace;
    bool caving;

    /* ------------------------------------------------------------------- moves -- */

    double underT = 6, lampT = 3, mothT = 14, pulseT = 4, pickT = 2, barrelT = -1, side = 1, sideT, dazeT;
    bool under, frostCaught, temper;
    double underRun, underMax;
    /// <summary>Unders still drawn to his own lamp, set down (the bane).</summary>
    int toLamp;
    (double X, double Z)? lampAt;
    int lampMark = -1;
    double offerT;

    public bool Under => under;
    public bool Dazed => dazeT > 0;
    /// <summary>The lip's middle (the caving ring closes on it).</summary>
    public (double X, double Z) Middle => C;
    /// <summary>On ground that still holds (all of it, until the floor caves in from the edge).</summary>
    public bool Inside(double x, double z, double margin) => !caving || Dist(x, z, C.X, C.Z) < caveR - margin;

    protected override void Enter(int phase)
    {
        switch (phase)
        {
            case 0:
                for (int i = 0; i < 3; i++) lampHp[i] = E.MaxHp * 0.08;
                // His own lob is his red lamp's: between his moves he walks, and nips what walks into him.
                var def = E.Def.Clone();
                def.Ranged = null;
                E.Def = def;
                Arrived();
                break;
            case 1:
                S.Bark(E.X, E.Z, "Still upstairs, are we? Downstairs'll want to hear about THIS.", Him);
                break;
            case 2:
                S.Bark(E.X, E.Z, "Blue light comes up in every seam of his hide.", null);
                S.After(1.6, () => { if (!Ending) S.Bark(E.X, E.Z, "Ever so patient, downstairs is. I'm NOT.", Him); });
                Snib("Boss has gone BLUE. Boss is not well. ...Boss is VERY well.", 3.4);
                OpenCrack();
                temper = true;
                E.Speed *= 1.33;
                pulseT = 4;
                break;
        }
    }

    /// <summary>Snib's first words, and the lamp she carries (his spare) if she has it.</summary>
    void Arrived()
    {
        bool lamp = HasLamp;
        if (!lamp) Snib("BOSS! Boss is UP! Snib said Boss would come up. ...Snib did not say that.", 1.5);
        else
        {
            Snib("That is the Boss's SPARE! You cannot have the spare. ...You have the spare.", 1.5);
            S.After(4, () => { if (E is { Alive: true } && !Ending) S.Bark(E.X, E.Z, "Put that lamp DOWN, surface-m— you. That's MINE.", Him); });
        }
    }

    bool HasLamp => S.Test(new World.Cond { HasItem = "grimtunnels_lamp" });

    /// <summary>Snib, from his heap, while he lives.</summary>
    void Snib(string line, double after = 0)
    {
        if (S.Fact("snib.dead")) return;
        var (x, z) = S.Place["snib"];
        if (after <= 0) S.Bark(x, z, line, "Snib");
        else S.After(after, () => { if (E is { Alive: true }) S.Bark(x, z, line, "Snib"); });
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (goingDown) return GoDown(e, dt);
        if (Spent(e)) { StartDown(e); return true; }
        if (dazeT > 0)
        {
            dazeT -= dt;
            e.TakenMul = 1.5;
            e.Vx = e.Vz = 0;
            e.State = EnemyState.Recover;
            e.Anim = EnemyAnim.Idle;
            if (dazeT <= 0) { e.TakenMul = 1; e.State = EnemyState.Active; }
            return true;
        }
        if (under) return Burrowing(e, dt);
        // (His cracked hide holds through his moves: set back to one here each step, the barrel's crack never
        // reached a blow.)
        e.TakenMul = cracked > 0 ? 1.25 : 1;
        if (flareT > 0 && (flareT -= dt) <= 0) flaring = -1;
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        underT -= dt; lampT -= dt; mothT -= dt; pulseT -= dt; pickT -= dt;
        if (mothT <= 0) { mothT = (Soft ? 12 : 20); Moths(); }
        if (underT <= 0) { underT = (Hard ? 8 : 12) * Cadence; StartUnder(e); return true; }
        if (lampT <= 0 && Lit.Any(l => l))
        {
            lampT = 7 * Cadence;
            for (int k = 0; k < 3; k++) { lampIx = (lampIx + 1) % 3; if (Lit[lampIx]) break; }
            flaring = lampIx;
            flareT = 2.5;
            Lamp(lampIx);
            return true;
        }
        if (PhaseIx == 2)
        {
            if (pulseT <= 0) { pulseT = 10 * Cadence; Pulse(e); return true; }
            if (d < 4 && pickT <= 0) { pickT = 3 * Cadence; Hold(0.9); Cone(3.6, 90, 0.9, 1.5, "Pick"); return true; }
        }
        return Stalk(e, dt, dx, dz, d);
    }

    /// <summary>Between his moves he comes round her at five to seven metres, swinging his lamps, pleased with
    /// everything; pressed close, he ambles off round her, and cuffs only what walks across his path
    /// (StoryBoss.Cuff). His teeth are in his marked moves.</summary>
    bool Stalk(Enemy e, double dt, double dx, double dz, double d)
    {
        if ((sideT -= dt) <= 0) { sideT = 3 + S.R() * 3; side = S.R() < 0.5 ? -1 : 1; }
        double radial = Math.Clamp((d - 6) / 2, -1, 1);
        double vx = dx * radial - dz * side * 0.8, vz = dz * radial + dx * side * 0.8;
        double vl = Math.Max(1e-6, Math.Sqrt(vx * vx + vz * vz)), sp = e.Speed * 0.7;
        double nx = e.X + vx / vl * sp * dt, nz = e.Z + vz / vl * sp * dt;
        bool cornered = !S.Place.Inside(nx, nz, 1.5) || B.Collision.Blocked(nx, nz, e.Radius) || !Inside(nx, nz, 1.2);
        if (cornered)
        {
            side = -side; sideT = 2;
            double cx = C.X - e.X, cz = C.Z - e.Z, cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            vx = cx / cl; vz = cz / cl; vl = 1;
            nx = e.X + vx * sp * dt; nz = e.Z + vz * sp * dt;
            if (B.Collision.Blocked(nx, nz, e.Radius)) { nx = e.X; nz = e.Z; }
        }
        e.X = nx; e.Z = nz;
        e.Vx = vx / vl * sp; e.Vz = vz / vl * sp;
        e.State = EnemyState.Active;
        e.Anim = EnemyAnim.Move;
        Cuff(e, dt, vx, vz, dx, dz, d, cornered, 0.3, 1.6);
        return true;
    }

    /// <summary>A lamp flares: its verb, and while it flares, blows on him break it.</summary>
    void Lamp(int i)
    {
        var p = B.Player;
        switch (i)
        {
            case 0:
                // Blasting ember: three charges lobbed round her, leaving fire.
                Hold(0.6);
                for (int k = 0; k < 3; k++)
                {
                    double a = S.R() * Math.PI * 2, r = k == 0 ? 0 : 2.5 + S.R() * 2;
                    double x = p.X + Math.Cos(a) * r, z = p.Z + Math.Sin(a) * r;
                    var b = Circle(x, z, 2.2, 1.4, 1.6, k == 0 ? "Blasting ember" : "", School.Fire);
                    b.After = bb => { var zn = bb.SpawnZone(Side.Enemy, x, z, 2.0, 3, E.Damage * 0.15, School.Fire); if (zn != null) zn.Tags = [Tag.Zone, Tag.Fire]; };
                }
                break;
            case 1:
                // The deep lamp: his diggers come up under her.
                Hold(0.6);
                double tx = p.X, tz = p.Z;
                var deep = Circle(tx, tz, 1.8, 1.0, 0.8, "The deep lamp");
                deep.After = _ =>
                {
                    for (int k = 0; k < 2 + S.Tier; k++)
                    {
                        double a = S.R() * Math.PI * 2;
                        double x = tx + Math.Cos(a) * 1.5, z = tz + Math.Sin(a) * 1.5;
                        if (S.CanStand(x, z)) S.Spawn("lampling", x, z, false, SpawnStyle.Burrow);
                    }
                };
                break;
            default:
            {
                // Slurry: a sprayed cone that leaves ground that slows.
                Hold(1.2);
                var (dx, dz, _) = ToPlayer();
                double ex = E.X, ez = E.Z;
                var b = Cone(7, 60, 1.2, 1.2, "Slurry", School.Nature);
                b.After = bb =>
                {
                    for (int k = 1; k <= 3; k++)
                    {
                        var zn = bb.SpawnZone(Side.Enemy, ex + dx * k * 2, ez + dz * k * 2, 1.7, 4, E.Damage * 0.1, School.Nature);
                        if (zn != null) zn.Slow = 0.45;
                    }
                };
                break;
            }
        }
    }

    /* ------------------------------------------------------------------- Under -- */

    /// <summary>He dives: the mound runs at her (or at his own lamp, set down) for up to three seconds.</summary>
    void StartUnder(Enemy e)
    {
        S.Bark(e.X, e.Z, "Rocks in a barrel: something under the ground.", null);
        under = true;
        underRun = 0;
        underMax = 3;
        flaring = -1;
        flareT = 0;
    }

    /// <summary>The mound: half taken, every weapon reaching it, frost bringing him up at once.</summary>
    bool Burrowing(Enemy e, double dt)
    {
        e.TakenMul = 0.5;
        e.State = EnemyState.Active;
        e.Anim = EnemyAnim.Move;
        underRun += dt;
        var target = toLamp > 0 && lampAt is { } la ? la : (B.Player.X, B.Player.Z);
        double dx = target.Item1 - e.X, dz = target.Item2 - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
        double sp = 6.5 * (temper ? 1.15 : 1);
        if (frostCaught) { Surface(e, burst: false); return true; }
        if (d < 0.8 || underRun >= underMax)
        {
            Surface(e, burst: true);
            return true;
        }
        double step = Math.Min(d, sp * dt);
        double nx = e.X + dx / d * step, nz = e.Z + dz / d * step;
        // Under the lip, not under its walls: at the edge of the ground the mound stops and he comes up.
        if (!S.Place.Inside(nx, nz, e.Radius + 0.4)) { Surface(e, burst: true); return true; }
        e.X = nx; e.Z = nz;
        e.Vx = dx / d * sp; e.Vz = dz / d * sp;
        B.Collision.Resolve(ref e.X, ref e.Z, e.Radius, overGaps: true);
        e.Facing = Math.Atan2(dz, dx);
        return true;
    }

    /// <summary>Up: a burst where he comes (marked: off it), and he stands dazed. Frost brought him up before
    /// he chose where: no burst, and dazed twice as long; his own lamp, the same.</summary>
    void Surface(Enemy e, bool burst)
    {
        under = false;
        bool atLamp = toLamp > 0 && lampAt is { } la && Dist(e.X, e.Z, la.X, la.Z) < 1.5;
        if (atLamp) { toLamp--; S.Bark(e.X, e.Z, "He comes up under his own lamp, and stops to look at it.", null); }
        double bx = e.X, bz = e.Z;
        double daze = frostCaught || atLamp ? 8 : 4;
        frostCaught = false;
        if (burst && !atLamp)
        {
            var b = Circle(bx, bz, 3.5, 1.2, 2.0, "He bursts up");
            b.After = _ => Daze(daze, bx, bz);
            Hold(1.2);
        }
        else Daze(daze, bx, bz);
        if (PhaseIx >= 1) Pit(bx, bz);
    }

    void Daze(double seconds, double x, double z)
    {
        if (Ending || E is not { Alive: true }) return;
        dazeT = seconds;
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = x, Z = z, Radius = 2.6, Delay = seconds, From = E, Label = "Dazed" });
    }

    /// <summary>A sinkhole where he burst (from the Collapse on): marked a moment, then ground nothing stands on,
    /// up to five and one more a tier; the oldest fills when the next opens, until he grows wild.</summary>
    void Pit(double x, double z)
    {
        int cap = 5 + S.Tier;
        if (pits.Count >= cap && !Soft) { var old = pits[0]; pits.RemoveAt(0); B.Collision.Remove(old.Id); B.EndMark(old.Mark); }
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, X = x, Z = z, Radius = 2.6, Delay = 1.5, From = E, Label = "The ground goes" });
        S.After(1.5, () =>
        {
            if (Ending || E is not { Alive: true }) return;
            int mark = B.Mark(TelegraphKind.Wall, x, z, 2.5, 900);
            int id = B.Collision.AddCircle(x, z, 2.3, new ColliderOpts(Tag: "pit", Gap: true)).Id;
            pits.Add((x, z, id, mark));
        });
    }

    void Moths()
    {
        var p = B.Player;
        (double X, double Z) at = flaring >= 0 ? (E.X, E.Z) : (p.X, p.Z);
        S.Bark(at.X, at.Z + 2, "Lamplings flock to the light.", null);
        int n = 6 + 2 * S.Tier;
        for (int k = 0; k < n; k++)
        {
            double a = k * Math.PI * 2 / n, r = 5 + S.R() * 2;
            double x = at.X + Math.Cos(a) * r, z = at.Z + Math.Sin(a) * r;
            if (S.CanStand(x, z)) S.Spawn("lampling", x, z, false, SpawnStyle.Burrow);
        }
    }

    /* --------------------------------------------------------------- the heart -- */

    /// <summary>The crack opens across the ground's middle, marked first: a gap a dash carries her over, or she
    /// goes round its ends. He crosses it under the ground.</summary>
    void OpenCrack()
    {
        var (ax, az) = CrackA;
        var (bx, bz) = CrackB;
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Line, Kind = TelegraphKind.Wall, X = ax, Z = az, X1 = bx, Z1 = bz, Width = 4, Delay = 2, From = E, Label = "The crack opens" });
        S.After(2, () =>
        {
            if (Ending || E is not { Alive: true }) return;
            crackOpen = true;
            double lx = bx - ax, lz = bz - az, len = Math.Sqrt(lx * lx + lz * lz);
            int n = (int)Math.Ceiling(len / 0.9);
            double sx = -lz / len, sz = lx / len;
            for (int i = 0; i <= n; i++)
                foreach (double off in new[] { -1.1, 1.1 })
                {
                    double x = ax + lx * i / n + sx * off, z = az + lz * i / n + sz * off;
                    crack.Add(B.Collision.AddCircle(x, z, 1.0, new ColliderOpts(Tag: "crack", Gap: true)).Id);
                }
            // Whoever stood in it is put out to the nearer side.
            var p = B.Player;
            B.Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
        });
    }

    /// <summary>The heart's pulse: he slams the ground, and three blue bands run out from him, each clear inside.</summary>
    void Pulse(Enemy e)
    {
        Hold(0.8);
        double cx = e.X, cz = e.Z;
        for (int k = 0; k < 3; k++)
        {
            double inner = 1.5 + k * 3, outer = inner + 2;
            var b = Band(cx, cz, inner, outer, 1.0 + k * 0.6, 1.0, k == 0 ? "The heart's pulse" : "", School.Frost);
            b.Slow = 0.6; b.SlowFor = 1.5;
        }
    }

    /* ------------------------------------------------------------ Snib's barrel -- */

    /// <summary>A barrel of blasting ember on the ground: kicked by walking into it, it rolls the way she went;
    /// on him (or a flaring lamp) it blows; left, he picks it up and throws it.</summary>
    sealed class Barrel
    {
        public double X, Z, Vx, Vz, IdleT, Spin;
        public bool Rolling, Lit;
        public IOrb? View;
    }
    Barrel? barrel;
    bool barrelSaid;

    /// <summary>Where the barrel lies (null: none), and whether it is still (for the hands).</summary>
    public (double X, double Z)? BarrelAt => barrel is { Lit: false } b ? (b.X, b.Z) : null;
    public bool BarrelStill => barrel is { Rolling: false, Lit: false };

    void RollBarrel()
    {
        var (sx, sz) = S.Place["snib"];
        Snib("Boss! BOSS! Not the good stuff! It IS the good stuff.");
        double dx = C.X - sx, dz = C.Z - sz, d = Math.Max(0.1, Math.Sqrt(dx * dx + dz * dz));
        barrel = new Barrel { X = sx + dx / d * 2, Z = sz + dz / d * 2, Vx = dx / d * 5, Vz = dz / d * 5, Rolling = true };
        barrel.View = S.Piece("props/Barrel", 1.2);
        barrel.View.Visible = true;
        if (!barrelSaid) { barrelSaid = true; S.Say("Snib's barrel", "Walk into it to roll it at him", "info"); }
    }

    void StepBarrel(double dt)
    {
        if (barrel is not { } b || b.Lit) return;
        var p = B.Player;
        if (b.Rolling)
        {
            double sp = Math.Sqrt(b.Vx * b.Vx + b.Vz * b.Vz);
            double nx = b.X + b.Vx * dt, nz = b.Z + b.Vz * dt;
            if (B.Collision.Blocked(nx, nz, 0.5) || !S.Place.Inside(nx, nz, 0.6)) { b.Vx = b.Vz = 0; sp = 0; }
            else { b.X = nx; b.Z = nz; b.Spin += sp * dt / 0.45; }
            double slow = Math.Max(0, sp - 6 * dt);
            if (sp > 0) { b.Vx *= slow / sp; b.Vz *= slow / sp; }
            if (slow < 0.2) { b.Rolling = false; b.IdleT = 0; }
            // On him, or on a lamp flaring: it goes up.
            if (E is { Alive: true } && !under && Dist(b.X, b.Z, E.X, E.Z) < E.Radius + 0.9) { Light(b); return; }
        }
        else
        {
            b.IdleT += dt;
            // Walked into: kicked the way she was going, eight metres or so.
            if (Dist(b.X, b.Z, p.X, p.Z) < p.Radius + 0.6)
            {
                double vx = p.Vx, vz = p.Vz, vl = Math.Sqrt(vx * vx + vz * vz);
                if (vl < 0.5) { vx = b.X - p.X; vz = b.Z - p.Z; vl = Math.Max(0.01, Math.Sqrt(vx * vx + vz * vz)); }
                b.Vx = vx / vl * 9.5; b.Vz = vz / vl * 9.5;
                b.Rolling = true;
            }
            // Left alone, he picks it up and throws it at her.
            else if (b.IdleT >= 12 && E is { Alive: true } && !under && dazeT <= 0 && !Busy) Throw(b);
        }
        b.View?.Place(b.X, S.HeightAt(b.X, b.Z) + 0.35, b.Z, b.Spin, 1.2);
    }

    /// <summary>On him: a fuse marked a moment, and it goes up: a tenth of him, and his hide cracks.</summary>
    void Light(Barrel b)
    {
        b.Lit = true;
        double x = b.X, z = b.Z;
        var blow = B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 4, Delay = 1.2, Damage = E.Damage * 1.0, School = School.Fire, Source = "Snib's barrel", Label = "The barrel" });
        blow.After = bb =>
        {
            b.View?.Dispose();
            if (barrel == b) barrel = null;
            bb.Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = 4, School = School.Fire, Power = 1.5 });
            foreach (var e in bb.Enemies.Living().ToList())
                if (e != E && e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && Dist(e.X, e.Z, x, z) < 4)
                    bb.HitEnemy(e, e.MaxHp * 4, School.Fire, [Tag.Fire, Tag.Explosion], new HitOpts { NoCrit = true, NoProcs = true });
            if (E is { Alive: true } && !Ending && Dist(E.X, E.Z, x, z) < 4 + E.Radius)
            {
                bb.HitEnemy(E, E.MaxHp * 0.1, School.Fire, [Tag.Fire, Tag.Explosion], new HitOpts { NoCrit = true, NoProcs = true });
                cracked = 12;
                S.Say("His hide cracks", "He takes more, for a while", "boon");
                Snib("Snib did NOT roll that. ...Snib rolled that.", 1.2);
            }
        };
    }

    double cracked;
    /// <summary>His hide cracked by Snib's barrel: he takes more, for a while.</summary>
    public bool Cracked => cracked > 0;

    /// <summary>"Ooh, the GOOD stuff!": he picks it up and throws it at her, marked long.</summary>
    void Throw(Barrel b)
    {
        S.Bark(E.X, E.Z, "Ooh, the GOOD stuff! Ever so kind. ...Catch!", Him);
        b.Lit = true;
        b.View?.Dispose();
        if (barrel == b) barrel = null;
        var p = B.Player;
        Hold(0.8);
        Circle(p.X, p.Z, 4, 2.0, 3.5, "The barrel", School.Fire);
    }

    /* -------------------------------------------------------------- each step -- */

    public override void Step(double dt)
    {
        if (E == null || !E.Alive) return;
        // The seam he came up through, drawn until it opens.
        if (!crackOpen && !Ending && (seamT -= dt) <= 0)
        {
            seamT = 0.5;
            var (ax, az) = CrackA;
            var (bx, bz) = CrackB;
            B.Events.Emit(new Ev.Telegraph { Id = 883000, Shape = TelegraphShape.Line, Kind = TelegraphKind.Ground, X = ax, Z = az, X1 = bx, Z1 = bz, Width = 0.5, Duration = 0.6, Hostile = true });
        }
        if (cracked > 0 && (cracked -= dt) <= 0) cracked = 0;
        if (!under && dazeT <= 0 && E.TakenMul > 0) E.TakenMul = cracked > 0 ? 1.25 : 1;
        // His lamp, set down by a prompt: offered where she stands while she carries it.
        if (!Ending && lampAt == null && HasLamp && (offerT -= dt) <= 0)
        {
            offerT = 0.5;
            S.Withdraw("lamp");
            var p = B.Player;
            S.Offer("lamp", p.X, p.Z, "Set down his lamp", "Grimtunnel's lamp", SetLamp);
        }
        // Snib's barrel, from 55% on and every 25 s after.
        if (!Ending && barrel == null && (PhaseIx >= 1 && E.Hp < E.MaxHp * 0.55) && (barrelT -= dt) <= 0)
        {
            barrelT = 25;
            RollBarrel();
        }
        StepBarrel(dt);
        if (caving) Cave(dt);
        // The ground split: the way to him is round the crack's ends (or over it with a dash).
        S.Goal = crackOpen && !Ending && !under && Split(B.Player.X, B.Player.Z, E.X, E.Z) ? (E.X, E.Z) : null;
    }

    /// <summary>The crack lies between two points (they are on its two sides, along its length).</summary>
    bool Split(double ax, double az, double bx, double bz)
    {
        var (cx0, cz0) = CrackA;
        var (cx1, cz1) = CrackB;
        double lx = cx1 - cx0, lz = cz1 - cz0;
        double sa = lx * (az - cz0) - lz * (ax - cx0), sb = lx * (bz - cz0) - lz * (bx - cx0);
        if (Math.Sign(sa) == Math.Sign(sb)) return false;
        // Where the way between them crosses the crack's line: within its length.
        double t = sa / (sa - sb);
        double px = ax + (bx - ax) * t, pz = az + (bz - az) * t;
        double u = ((px - cx0) * lx + (pz - cz0) * lz) / (lx * lx + lz * lz);
        return u > -0.05 && u < 1.05;
    }

    void SetLamp()
    {
        var p = B.Player;
        S.Withdraw("lamp");
        lampAt = (p.X, p.Z);
        toLamp = 2;
        lampMark = B.Mark(TelegraphKind.Safe, p.X, p.Z, 1.2, 900);
    }

    public override void OnHit(Enemy e, School school, double dmg)
    {
        if (goingDown) return;
        // A lamp flaring takes the blows on it, and breaks.
        if (flaring >= 0 && Lit[flaring])
        {
            lampHp[flaring] -= dmg;
            if (lampHp[flaring] <= 0)
            {
                Lit[flaring] = false;
                B.Events.Emit(new Ev.Announce { Title = $"His {LampNames[flaring]} lamp breaks", Tone = Tone.Boon });
                B.Events.Emit(new Ev.Explosion { X = e.X, Z = e.Z, Radius = 2.5, School = flaring == 0 ? School.Fire : flaring == 1 ? School.Frost : School.Nature, Power = 1 });
                if (!lampBroken) { lampBroken = true; S.Bark(e.X, e.Z, "Nobody's! Nobody's having my lamps!", Him); }
                flaring = -1;
            }
        }
        // Frost on the mound: he comes up at once.
        if (school == Weakness && under) frostCaught = true;
        base.OnHit(e, school, dmg);
    }

    protected override void OnSoft() { }

    /// <summary>All Downstairs: the floor caves in from the edge, two metres every ten seconds.</summary>
    protected override void OnHard()
    {
        caving = true;
        caveR = GroundR;
        caveT = 10;
    }

    void Cave(double dt)
    {
        if ((caveT -= dt) <= 0) { caveT = 10; caveR = Math.Max(5, caveR - 2); }
        // The floor goes from under him too: he scrambles in off it. (Left standing out on ground that had gone,
        // he fought on from where she could not follow, and a weak build's night ran to the cap.)
        double ed = Dist(E.X, E.Z, C.X, C.Z);
        if (!goingDown && ed > caveR - 1.2)
        {
            double k = (caveR - 1.2) / Math.Max(0.01, ed);
            E.X = C.X + (E.X - C.X) * k; E.Z = C.Z + (E.Z - C.Z) * k;
            B.Collision.Resolve(ref E.X, ref E.Z, E.Radius, overGaps: true);
        }
        var p = B.Player;
        double d = Dist(p.X, p.Z, C.X, C.Z);
        // The going floor shoves her back in, and hurts only now and then, as any living wall does (Greymuzzle's
        // ring): shoved half a blow every 0.6 s, the hands took more from the edge than from him.
        caveGrace -= dt;
        if ((caveShoveT -= dt) <= 0 && d > caveR - 0.6)
        {
            caveShoveT = 0.6;
            B.ShovePlayer(C.X - p.X, C.Z - p.Z, 2.5, caveGrace <= 0 ? E.Damage * 0.5 : 0, "the floor going");
            if (caveGrace <= 0) caveGrace = 2;
        }
        if ((caveDrawT -= dt) <= 0)
        {
            caveDrawT = 0.5;
            B.Events.Emit(new Ev.Telegraph { Id = 884000, Shape = TelegraphShape.Ring, Kind = TelegraphKind.Wall, X = C.X, Z = C.Z, Inner = caveR, Radius = GroundR + 6, Duration = 0.6, Hostile = true, Boss = true });
        }
    }

    /* ----------------------------------------------------------------- his end -- */

    bool goingDown;
    double downT;

    /// <summary>Spent: he reels into the crack, and hangs there by his claws, delighted.</summary>
    void StartDown(Enemy e)
    {
        goingDown = true;
        Ending = true;
        downT = 0;
        e.TakenMul = 0;
        e.Hp = 1;
        e.Disposition = Disposition.Neutral;
        under = false;
        dazeT = 0;
        Channel = null;
        B.Events.Emit(new Ev.Focus { X = e.X, Z = e.Z, Duration = 2.4 });
        // Into the crack's middle.
        var (ax, az) = CrackA;
        var (bx, bz) = CrackB;
        DashTo((ax + bx) / 2, (az + bz) / 2, 1.2);
    }

    bool GoDown(Enemy e, double dt)
    {
        downT += dt;
        if (Running(e, dt)) return true;
        e.Vx = e.Vz = 0;
        e.State = EnemyState.Casting;
        if (downT - dt < 1.3 && downT >= 1.3) S.Bark(e.X, e.Z, "I told it about you! It went ever so QUIET!", Him);
        if (downT < 4.5) return true;
        double x = e.X, z = e.Z;
        Clear();
        foreach (var o in B.Enemies.Items.ToList())
            if (o.Alive && o != e && o.Def.Id.StartsWith("lampling") && o.State != EnemyState.Dying) B.Enemies.Release(o);
        B.Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = 4, School = School.Physical, Power = 1.5 });
        B.Events.Emit(new Ev.Shake { Amount = 0.5 });
        var (sx, sz) = S.Place["snib"];
        if (!S.Fact("snib.dead")) S.Bark(sx, sz, "Boss! Wait for Snib! ...Snib is not going down there. ...Snib is going down there.", "Snib");
        B.Enemies.Release(e);
        S.Ended(x, z, false);
        return true;
    }

    public override void Fell(Enemy e) => Clear();

    /// <summary>Everything he put on the ground goes: the crack shuts, the pits fill, the barrel and his lamp go.</summary>
    public override void Clear()
    {
        foreach (var (_, _, id, mark) in pits) { B.Collision.Remove(id); B.EndMark(mark); }
        pits.Clear();
        foreach (var id in crack) B.Collision.Remove(id);
        crack.Clear();
        crackOpen = false;
        barrel?.View?.Dispose();
        barrel = null;
        if (lampMark >= 0) { B.EndMark(lampMark); lampMark = -1; }
        S.Withdraw("lamp");
        caving = false;
        S.Goal = null;
    }

    public override string? State => crackOpen ? "the ground is split" : caving ? "the floor goes" : null;

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}

using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>
/// The Barrow Lord at the head of the stair (docs/design/STORY_BOSSES.md 4): an officer of the Seventh
/// Legion, armour green with age, an iron crest, who has held the inner door for two thousand years. He
/// gives his orders to his dead in the old tongue, one plural word each; to her he says only "Nondum", and
/// at the end "Redi" (C13). They are not beaten. They send her home. The words are the story lead's
/// (WRITING_PASS 23.3).
///
///   the drill   "Iungite!": shields rise in a line between him and her and march at her (locked shields
///               are not targets; the line breaks at its ends). Pilum down a lane: it stays in the ground
///               a while, and is cover from the next. Gladius, close.
///   testudo     "Testudo!": eight shields ring him with the standard at the heart. Break the standard and
///               the ring drops and he is held; leave it and the century charges out of the ring in
///               columns. A rank steps down off each wall at each one, and the landing narrows. Chid's bane:
///               a broken standard can be lifted, and carried, the century will not close up again.
///   nondum      the ranks come down off the walls and close round the fight in a front, a step at a
///               time; holy on him makes it give ground. "Tenete!": the press, a band round her.
///   his end     he goes down and will not lie down: stand over him to lay him down (holy twice as fast)
///               while the front's dead come to drag her off; failed, he gets up again, quicker. Laid
///               down, he gets up inside her reach, puts his hand on her breastbone, and pushes: "Redi."
/// The ranks along the walls are men: the walls of the fight, never targets.
/// </summary>
public sealed class BarrowLordStory : StoryBoss, IBound
{
    public BarrowLordStory(IStoryArena a) : base(a) { }

    protected override Phase[] Phases { get; } =
    [
        new("The Drill", 0.70, 25, 75),
        new("Testudo", 0.40, 30, 75),
        new("Nondum", 0, 25, 0),
    ];
    public override School Weakness => School.Holy;
    public override string WeaknessText => "Holy lays him down twice as fast, and the dead give ground to it";
    protected override string HardName => "The Last Watch";
    protected override string HardSub => "The front walks in";
    protected override (string Title, string Sub) SoftWords(Enemy e) => ("The drill quickens", "New lines form quicker");
    public override string ReEntry => "The dead part again. He comes up through them, and gives you the same long look.";
    /// <summary>Measured to the length, as the others were: the same at every tier.</summary>
    public override double HealthMul(int tier) => 130;
    /// <summary>His teeth are in his marked moves: a pilum or the gladius about a third of her own health.</summary>
    public override double Teeth => 0.22;
    protected override bool DiesAtZero => false;

    const string Him = "The Barrow Lord";
    /// <summary>The landing's middle (the front closes on it), and how far it runs either side.</summary>
    (double X, double Z) C => S.Place["landing"];
    const double LandingHalf = 14;

    /* ------------------------------------------------------------ his ranks -- */

    /// <summary>A man of the ranks: on the wall at attention, in a testudo's ring, or in the front.</summary>
    sealed class Man
    {
        public required Enemy E;
        public double Seed, X, Z;
    }
    /// <summary>The ranks standing along the landing's walls, east and west.</summary>
    readonly List<Man> ranks = new();
    /// <summary>The shields round him in a testudo.</summary>
    readonly List<Man> shell = new();
    /// <summary>The marching lines ("Iungite!").</summary>
    readonly List<Levy> lines = new();
    /// <summary>His dead loose in the fight (stepped down off a wall, come to drag her off him).</summary>
    readonly List<(Enemy E, double Seed)> loose = new();

    bool Here(Man m) => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying;

    /// <summary>The ranks along the walls, at attention, facing in: dressing, never targets.</summary>
    void Muster()
    {
        foreach (int side in new[] { -1, 1 })
            for (double z = C.Z + 6; z >= C.Z - 6; z -= 2)
            {
                double x = C.X + side * (halfW + 0.6);
                var e = B.SpawnEnemy("risen_warrior", x, z, new Battle.SpawnOpts { Level = S.Level, Disposition = Disposition.Neutral, Faction = Faction.Dead, Style = SpawnStyle.Rise });
                if (e == null) continue;
                var m = new Man { E = e, Seed = e.Seed, X = x, Z = z };
                ranks.Add(m);
                e.Scripted = true;
                S.Script(e, (_, dt) => Stand(m, dt));
            }
    }

    /// <summary>A man of the ranks at his place, never hurt, never a target.</summary>
    bool Stand(Man m, double dt)
    {
        var e = m.E;
        e.Provoked = false;
        e.Hp = e.MaxHp;
        e.Disposition = Disposition.Neutral;
        double dx = m.X - e.X, dz = m.Z - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
        if (d > 0.05) { double s = Math.Min(d, 3 * dt); e.X += dx / d * s; e.Z += dz / d * s; }
        e.Vx = e.Vz = 0;
        // Facing the fight; with the standard in her hands, facing it.
        var p = B.Player;
        e.Facing = carried ? Math.Atan2(p.Z - e.Z, p.X - e.X) : Math.Atan2(C.Z - e.Z, C.X - e.X);
        e.Anim = d > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
        e.State = EnemyState.Active;
        return true;
    }

    /* ---------------------------------------------------------- the ground -- */

    /// <summary>How far the landing runs either side of its middle now (the walls step in at each testudo).</summary>
    double halfW = LandingHalf;
    /// <summary>The front's ring (Nondum), and how close it may come.</summary>
    double frontR = LandingHalf, frontMin = 8, frontT, shoveT, grace, gaveT;
    bool front, gaveTold;

    public (double X, double Z) Middle => C;
    /// <summary>Where the fight may be: between the walls of men, or inside the front.</summary>
    public bool Inside(double x, double z, double margin) =>
        front ? Dist(x, z, C.X, C.Z) < frontR - margin : Math.Abs(x - C.X) < halfW - margin;

    /// <summary>The walls of men shove her back in, and bite only now and then, as any living wall does.</summary>
    void Walls(double dt)
    {
        var p = B.Player;
        grace -= dt;
        if ((shoveT -= dt) > 0) return;
        if (front)
        {
            if (Dist(p.X, p.Z, C.X, C.Z) <= frontR - 0.6) return;
            shoveT = 0.6;
            B.ShovePlayer(C.X - p.X, C.Z - p.Z, 2, grace <= 0 ? E.Damage * 0.3 : 0, "the front");
        }
        else
        {
            double off = p.X - C.X;
            if (Math.Abs(off) <= halfW - 0.6) return;
            shoveT = 0.6;
            B.ShovePlayer(-Math.Sign(off), 0, 2, grace <= 0 ? E.Damage * 0.3 : 0, "the ranks");
        }
        if (grace <= 0) grace = 2;
    }

    /// <summary>The front: the ranks round the fight, a step in every eight seconds to its least.</summary>
    void Front(double dt)
    {
        if (!front) return;
        double least = Hard ? 5 : frontMin;
        if ((frontT -= dt) <= 0) { frontT = 8; frontR = Math.Max(least, frontR - 1); Dress(); }
        gaveT -= dt;
    }

    /// <summary>The front's men to their places round the ring, evenly.</summary>
    void Dress()
    {
        var up = ranks.Where(Here).ToList();
        for (int i = 0; i < up.Count; i++)
        {
            double a = i * Math.PI * 2 / up.Count;
            up[i].X = C.X + Math.Cos(a) * (frontR + 0.5);
            up[i].Z = C.Z + Math.Sin(a) * (frontR + 0.5);
        }
    }

    /* ------------------------------------------------------------- his moves -- */

    double lineT = 5, pilumT = 4, gladiusT = 2, testudoT = 1, tenereT = 6, side = 1, sideT;
    readonly List<(int Id, double T)> pila = new();
    /// <summary>The standard in a testudo (a part), and whether one broken can be lifted, and has been.</summary>
    VaultOpened.Standard? standard;
    double chargeT = -1, heldT;
    bool carried, liftable;
    int testudos;
    (double X, double Z)? fallen;

    protected override void Enter(int phase)
    {
        switch (phase)
        {
            case 0:
                if (ranks.Count == 0) Muster();
                break;
            case 1:
                testudoT = 0.5;
                break;
            case 2:
                // The ranks come down off the walls and close round the fight.
                Unshell();
                foreach (var l in lines) l.Break();
                LooseLines();
                front = true;
                frontR = Math.Min(halfW + 0.5, LandingHalf);
                frontT = 8;
                Dress();
                S.Bark(C.X, C.Z, "The ranks come down off the walls and close round you in a front.", null);
                gladiusT = 1.5;
                tenereT = 6;
                break;
        }
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (laying) return Lay(e, dt);
        if (handT >= 0) return Hand(e, dt);
        if (Spent(e)) { StartLay(e); return true; }
        if (heldT > 0)
        {
            heldT -= dt;
            e.TakenMul = 1.25;
            e.Vx = e.Vz = 0;
            e.State = EnemyState.Recover;
            e.Anim = EnemyAnim.Idle;
            if (heldT <= 0) { e.TakenMul = 1; e.State = EnemyState.Active; }
            return true;
        }
        // Ringed in his shields, he takes half of what reaches him over the rim and through the gaps.
        e.TakenMul = shell.Any(Here) ? 0.5 : 1;
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        lineT -= dt; pilumT -= dt; gladiusT -= dt; testudoT -= dt; tenereT -= dt;
        switch (PhaseIx)
        {
            case 0:
                if (lineT <= 0 && !carried) { lineT = (Soft ? 10 : 16) * Cadence; Iungite(); return true; }
                if (d < 4.8 && gladiusT <= 0) { gladiusT = 6 * Cadence; Gladius(false); return true; }
                if (d > 5 && pilumT <= 0) { pilumT = 7 * Cadence; Pilum(); return true; }
                break;
            case 1:
                if (testudoT <= 0 && !carried) { testudoT = 22 * Cadence; Testudo(e); return true; }
                if (d < 4.8 && gladiusT <= 0) { gladiusT = 6 * Cadence; Gladius(false); return true; }
                if (d > 5 && pilumT <= 0) { pilumT = 7 * Cadence; Pilum(); return true; }
                break;
            default:
                if (Soft && lineT <= 0 && !carried) { lineT = 10 * Cadence; Iungite(); return true; }
                if (d < 4.8 && gladiusT <= 0) { gladiusT = 4 * Cadence; Gladius(true); return true; }
                if (tenereT <= 0) { tenereT = 12 * Cadence; Tenete(); return true; }
                break;
        }
        return Stalk(e, dt, dx, dz, d);
    }

    /// <summary>Between his orders he comes on at a walk, never hurried: four to six metres off her, turning
    /// round her; pressed close he steps off round her and cuffs only what walks across his path.</summary>
    bool Stalk(Enemy e, double dt, double dx, double dz, double d)
    {
        if ((sideT -= dt) <= 0) { sideT = 3 + S.R() * 3; side = S.R() < 0.5 ? -1 : 1; }
        double radial = Math.Clamp((d - 5) / 2, -1, 1);
        double vx = dx * radial - dz * side * 0.7, vz = dz * radial + dx * side * 0.7;
        double vl = Math.Max(1e-6, Math.Sqrt(vx * vx + vz * vz)), sp = e.Speed * 0.75;
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
        Cuff(e, dt, vx, vz, dx, dz, d, cornered, 0.4, 1.6);
        return true;
    }

    /// <summary>"Iungite!": shields rise in a line between him and her, and march at her.</summary>
    void Iungite()
    {
        var p = B.Player;
        S.Bark(E.X, E.Z, "\"Iungite!\"", Him);
        lines.RemoveAll(l => l.Broken);
        if (lines.Count >= 2) { Hold(0.6); return; }
        double dx = E.X - p.X, dz = E.Z - p.Z, d = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
        double at = Math.Min(7, d * 0.6);
        double lx = p.X + dx / d * at, lz = p.Z + dz / d * at;
        if (!S.CanStand(lx, lz)) (lx, lz) = (E.X, E.Z);
        var line = new Levy(S, lx, lz, p.X, p.Z, 6 + S.Tier, "risen_warrior", null, "the shields") { Wheel = 0.45 };
        lines.Add(line);
        if (!told) { told = true; S.Say("The line", "Break it at its ends", "danger"); }
        Hold(0.6);
    }
    bool told;

    /// <summary>The pilum down a lane, to just past where she stands: it stays in the ground a while, and stops
    /// the next one (cover she can make of his own spears).</summary>
    void Pilum()
    {
        var (dx, dz, d) = ToPlayer();
        double len = Math.Min(20, d + 3);
        double x1 = E.X + dx * len, z1 = E.Z + dz * len;
        // A pilum standing in the ground stops it.
        foreach (var (id, _) in pila)
        {
            var c = B.Collision.All().FirstOrDefault(q => q.Id == id);
            if (c == null) continue;
            double t = (c.X - E.X) * dx + (c.Z - E.Z) * dz;
            double across = Math.Abs((c.X - E.X) * -dz + (c.Z - E.Z) * dx);
            if (t > 1 && t < len && across < 0.65 + c.R) { len = t; x1 = E.X + dx * len; z1 = E.Z + dz * len; }
        }
        Hold(1.0);
        var b = Lane(E.X, E.Z, x1, z1, 1.3, 1.0, 1.6, "Pilum");
        b.After = bb =>
        {
            var c = bb.Collision.AddCircle(x1, z1, 0.4, new ColliderOpts(Tag: "pilum"));
            pila.Add((c.Id, 6));
        };
    }

    /// <summary>The gladius: a cone before him, and on the front a step in after it, a short lane.</summary>
    void Gladius(bool step)
    {
        Hold(0.9, () =>
        {
            if (!step) return;
            var (x, z, _) = ToPlayer();
            Lane(E.X, E.Z, E.X + x * 5, E.Z + z * 5, 2, 0.7, 1.5, "Gladius");
            Hold(0.7);
        });
        Cone(4.5, 90, 0.9, 1.5, "Gladius");
    }

    /// <summary>"Tenete!": the press, a band round her; caught in it, she is held.</summary>
    void Tenete()
    {
        var p = B.Player;
        S.Bark(E.X, E.Z, "\"Tenete!\"", Him);
        var b = Band(p.X, p.Z, 4.5, 6.5, 1.5, 0.8, "The press", School.Shadow);
        b.Slow = 0.05; b.SlowFor = 1.2;
        Hold(0.5);
    }

    /// <summary>"Testudo!": eight shields ring him, the standard at the heart. Broken, the ring drops and he is
    /// held; left, the ring opens after six seconds and the century charges out of it in columns. A rank steps
    /// down off each wall, and the landing narrows.</summary>
    void Testudo(Enemy e)
    {
        S.Bark(e.X, e.Z, "\"Testudo!\"", Him);
        testudos++;
        if (testudos == 1) S.Say("Shields round him", "Break the standard inside", "danger");
        Unshell();
        for (int k = 0; k < 8; k++)
        {
            double a = k * Math.PI / 4 + Math.PI / 8;
            double x = e.X + Math.Cos(a) * 3.6, z = e.Z + Math.Sin(a) * 3.6;
            var m = B.SpawnEnemy("risen_warrior", x, z, new Battle.SpawnOpts { Level = S.Level, Disposition = Disposition.Neutral, Faction = Faction.Dead, Style = SpawnStyle.Rise });
            if (m == null) continue;
            var man = new Man { E = m, Seed = m.Seed, X = x, Z = z };
            shell.Add(man);
            m.Scripted = true;
            S.Script(m, (_, dt) => Stand(man, dt));
        }
        var (dx, dz, _) = ToPlayer();
        standard = VaultOpened.Standard.Plant(S, e.X + dx * 1.4, e.Z + dz * 1.4, MaxHp * 0.06);
        StepDown();
        chargeT = 6;
        Hold(6.2);
    }

    /// <summary>A rank steps down off each wall into the fight, and the walls close in two metres.</summary>
    void StepDown()
    {
        if (halfW <= 8) return;
        halfW -= 2;
        foreach (int sd in new[] { -1, 1 })
        {
            var down = ranks.Where(m => Here(m) && Math.Sign(m.X - C.X) == sd).OrderBy(m => Dist(m.E.X, m.E.Z, B.Player.X, B.Player.Z)).Take(1 + S.Tier / 2).ToList();
            foreach (var m in down)
            {
                ranks.Remove(m);
                m.E.Scripted = false;
                m.E.Disposition = Disposition.Hostile;
                m.E.Target = -1;
                loose.Add((m.E, m.Seed));
            }
            foreach (var m in ranks.Where(m => Math.Sign(m.X - C.X) == sd)) m.X = C.X + sd * (halfW + 0.6);
        }
        if (testudos == 1) S.Bark(C.X + halfW, C.Z, "A rank steps down off each wall, in step.", null);
    }

    /// <summary>The ring opens: the century charges out of it in columns (two once he is past half).</summary>
    void Charge()
    {
        var (dx, dz, _) = ToPlayer();
        double a0 = Math.Atan2(dz, dx);
        int cols = E.Hp > E.MaxHp * 0.55 ? 3 : 2;
        for (int k = 0; k < cols; k++)
        {
            double a = a0 + (k - (cols - 1) / 2.0) * 0.55;
            Lane(E.X, E.Z, E.X + Math.Cos(a) * 18, E.Z + Math.Sin(a) * 18, 2.2, 1.3, 1.5, "The century charges");
        }
        Hold(1.3);
        Unshell();
    }

    /// <summary>The ring's shields go back to the walls, and an unbroken standard with them.</summary>
    void Unshell()
    {
        foreach (var m in shell) if (Here(m)) B.Enemies.Release(m.E);
        shell.Clear();
        standard?.Gone(B, true);
        standard = null;
    }

    /// <summary>The standard is broken: the ring drops, and he is held a moment. Where Chid's bane is known,
    /// it can be lifted.</summary>
    void StandardBroken(double x, double z)
    {
        S.Say("The standard breaks", null, "boon");
        foreach (var m in shell) if (Here(m)) B.Enemies.Release(m.E);
        shell.Clear();
        standard?.Gone(B, false);
        standard = null;
        chargeT = -1;
        heldT = 3;
        Channel = null;
        if (S.Fact("bane.pole") && !carried)
        {
            liftable = true;
            fallen = (x, z);
            S.Offer("standard", x, z, "Lift the standard", "The Legion's standard", Lift);
        }
    }

    /// <summary>Chid's bane: they never followed a man, they followed the pole. Carried, the century will not
    /// close up again: no more lines, no more shells, and the ranks on the walls turn to face it.</summary>
    void Lift()
    {
        if (carried) return;
        carried = true;
        liftable = false;
        S.Withdraw("standard");
        var (x, z) = fallen ?? (B.Player.X, B.Player.Z);
        S.Bark(x, z, "Along the walls, the ranks turn to face the standard in your hands.", null);
        S.Say("They follow the pole", "The century will not close up again", "boon");
        S.Mark("standard");
        foreach (var l in lines) l.Break();
        LooseLines();
    }

    /// <summary>A broken line's men are loose in the fight (his dead still).</summary>
    void LooseLines()
    {
        foreach (var l in lines) foreach (var m in l.Men) loose.Add((m, m.Seed));
        lines.Clear();
    }

    public override void Step(double dt)
    {
        if (E == null || !E.Alive) return;
        Walls(dt);
        Front(dt);
        foreach (var l in lines) l.Step(dt);
        foreach (var l in lines.Where(l => l.Broken).ToList()) { foreach (var m in l.Men) loose.Add((m, m.Seed)); lines.Remove(l); }
        for (int i = pila.Count - 1; i >= 0; i--)
        {
            var (id, t) = pila[i];
            if (t - dt <= 0) { B.Collision.Remove(id); pila.RemoveAt(i); }
            else pila[i] = (id, t - dt);
        }
        ranks.RemoveAll(m => !Here(m));
        shell.RemoveAll(m => !Here(m));
        if (standard is { Up: false } broken) StandardBroken(broken.X, broken.Z);
        if (chargeT > 0 && (chargeT -= dt) <= 0 && !Ending) Charge();
    }

    static bool Up(Enemy? e, double seed) => e is { Alive: true } x && x.Seed == seed && x.State != EnemyState.Dying;

    double holyT;

    public override void OnHit(Enemy e, School school, double dmg)
    {
        // Down, holy hastens his laying down (it is not a channel to break).
        if (laying) { if (school == School.Holy) holyT = 0.5; return; }
        // On the front, holy on him makes it give a step (once in three seconds).
        if (front && school == School.Holy && gaveT <= 0 && frontR < LandingHalf)
        {
            gaveT = 3;
            frontR += 1;
            Dress();
            if (!gaveTold) { gaveTold = true; S.Say("The front gives ground", "Holy drives it back a step", "boon"); }
        }
        base.OnHit(e, school, dmg);
    }

    /* ------------------------------------------------------------------ his end -- */

    bool laying;
    double layT, layHeld, handT = -1;
    int risings;
    /// <summary>He is down and must be stood over (the hands read it as a player does).</summary>
    public bool Laying => laying;
    /// <summary>The standard in a testudo, while it stands (the hands go in on it).</summary>
    public Enemy? Standard => standard is { Up: true } s ? s.E : null;
    /// <summary>A broken standard waiting to be lifted (Chid's bane).</summary>
    public (double X, double Z)? Liftable => liftable ? fallen : null;
    public bool Carried => carried;

    /// <summary>Spent: he goes down inside a pale circle. Stand in it three seconds to lay him down (holy twice as
    /// fast), while the front's dead come to drag her off him; or he gets up again with a quarter of himself.</summary>
    void StartLay(Enemy e)
    {
        laying = true;
        layT = 0;
        layHeld = 0;
        e.TakenMul = 0;
        e.Hp = 1;
        e.Vx = e.Vz = 0;
        Channel = "Lay him down";
        ChannelProgress = 0;
        // What he had ordered goes with him (the press still landed round her as he went down).
        B.CancelBlows();
        S.Bark(e.X, e.Z, "He goes down.", null);
        S.Say("He is down", "Stand over him to lay him down", "danger");
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = e.X, Z = e.Z, Radius = 3, Delay = 8, From = e, Label = "Lay him down" });
        // The front's dead come at the circle to drag her off him.
        var p = B.Player;
        double a0 = Math.Atan2(p.Z - e.Z, p.X - e.X);
        int n = 3 + S.Tier;
        for (int k = 0; k < n; k++)
        {
            double a = a0 + (k - (n - 1) / 2.0) * 0.5;
            double r = front ? frontR - 1 : 8;
            double x = e.X + Math.Cos(a) * r, z = e.Z + Math.Sin(a) * r;
            if (S.CanStand(x, z) && S.Spawn("risen", x, z, false, SpawnStyle.Rise) is { } dead) loose.Add((dead, dead.Seed));
        }
        S.After(1.2, () => { if (laying) S.Bark(e.X, e.Z, "The dead come to drag you off him.", null); });
    }

    bool Lay(Enemy e, double dt)
    {
        e.Vx = e.Vz = 0;
        e.State = EnemyState.Casting;
        e.Anim = EnemyAnim.Idle;
        e.TakenMul = 0;
        layT += dt;
        var p = B.Player;
        if (Dist(p.X, p.Z, e.X, e.Z) < 3) layHeld += dt * (holyT > 0 ? 2 : 1);
        if (holyT > 0) holyT -= dt;
        ChannelProgress = Math.Min(1, layHeld / 3);
        if (layHeld >= 3)
        {
            laying = false;
            Ending = true;
            Channel = null;
            e.Disposition = Disposition.Neutral;
            S.Bark(e.X, e.Z, "You lay him down.", null);
            handT = 0;
            B.Events.Emit(new Ev.Focus { X = e.X, Z = e.Z, Duration = 3.6 });
            return true;
        }
        if (layT >= 8)
        {
            laying = false;
            Channel = null;
            risings++;
            e.TakenMul = 1;
            e.Hp = e.MaxHp * 0.25;
            e.State = EnemyState.Active;
            e.Speed *= 1.2;
            S.Bark(e.X, e.Z, "He gets up.", null);
            S.Say("He will not lie down", "Again, and quicker", "danger");
            gladiusT = 1;
        }
        return true;
    }

    /// <summary>Laid down, he does not stay down: he gets up inside her reach, puts his hand flat on her
    /// breastbone, and pushes, once (C13's hand at the gate). The dead step back onto the stair together.</summary>
    bool Hand(Enemy e, double dt)
    {
        e.Vx = e.Vz = 0;
        e.TakenMul = 0;
        e.State = EnemyState.Casting;
        double was = handT;
        handT += dt;
        if (was < 1.2 && handT >= 1.2)
        {
            var p = B.Player;
            S.Bark(e.X, e.Z, "He gets up inside your reach, puts his hand flat on your breastbone, and pushes, once.", null);
            e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
        }
        if (was < 3.4 && handT >= 3.4)
        {
            S.Bark(e.X, e.Z, "\"Redi.\"", Him);
            var p = B.Player;
            B.ShovePlayer(p.X - e.X, p.Z - e.Z, 3, 0, Him);
        }
        if (handT < 5.6) return true;
        double x = e.X, z = e.Z;
        Clear();
        B.Enemies.Release(e);
        S.Ended(x, z, false);
        return true;
    }

    public override void Fell(Enemy e) => Clear();

    public override void Clear()
    {
        foreach (var m in ranks.Concat(shell)) if (Here(m)) B.Enemies.Release(m.E);
        ranks.Clear();
        shell.Clear();
        foreach (var l in lines) l.Clear();
        lines.Clear();
        foreach (var (le, seed) in loose) if (le.Alive && le.Seed == seed && le.State != EnemyState.Dying) B.Enemies.Release(le);
        loose.Clear();
        standard?.Gone(B, true);
        standard = null;
        foreach (var (id, _) in pila) B.Collision.Remove(id);
        pila.Clear();
        S.Withdraw("standard");
        front = false;
    }

    public override string? State => laying ? "down" : shell.Any(Here) ? "testudo" : front ? "the front" : lines.Any(l => !l.Broken) ? "the line" : null;

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}

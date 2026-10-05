using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/* Behind the Sealed Door (docs/design/STORY_BOSSES.md 4): the Legion's hall at the head of the stair, its roof
 * fallen in and open to the moon, its wall tops standing. She never goes down the stair: going down is Act 3,
 * and in C13 Jessop stands far below. The dead know what she is; they have been waiting for her, and she is
 * early. The words are the story lead's (WRITING_PASS 23.3).
 *
 *   the south end   the dead come up the stair in files and march the hall's length; the Decurion leads
 *                   the third rank in a shield line. Locked shields are not targets: it breaks at its ends.
 *   the hall        the Scorpion kneels at the stair's head and shoots down the hall's length: aimed lanes,
 *                   a step off is a dodge, and the fallen beams and the sarcophagi stop his bolts.
 *   the standards   the Signifer plants three down the hall. While one stands it raises a file of the dead
 *                   and quickens those round it; he falls with the last.
 *
 * The hall runs up the screen (north is -z): the door at the south, the stair's mouth in the north wall of the
 * landing beyond the hall. The place's points are where arena art builds to; the cover is the fight's. */
public sealed class VaultOpened : StoryFight
{
    public override string Id => "vault_opened";

    /// <summary>A stretch of the hall, from one z to another, 22 m wide: capsules across it, close-set, so its
    /// walls run straight.</summary>
    static Capsule[] Band(double z0, double z1, double half = 8)
    {
        var o = new List<Capsule>();
        for (double z = z0 - 3; z >= z1 + 3 - 1e-6; z -= Math.Max(0.5, (z0 - z1 - 6) / Math.Ceiling((z0 - z1 - 6) / 2.5)))
            o.Add(new Capsule(-half, z, half, z, 3));
        return o.ToArray();
    }

    public static readonly StoryPlace Ground = new()
    {
        Spaces =
        [
            new("south", Band(22.5, 5.5)),
            new("hall", Band(6.5, -20.5)),
            // The head of the stair: a landing 30 m wide before the stair's mouth in the north wall.
            new("stair", Band(-19.5, -38, 12)),
        ],
        Gates =
        [
            new("south", -11, 6, 11, 6, "hall"),
            new("hall", -11, -20, 11, -20, "stair"),
        ],
        Points = new()
        {
            ["start"] = (0, 19), ["door"] = (0, 22),
            ["south_w"] = (-8, 8.5), ["south_e"] = (8, 8.5), ["line"] = (0, 9.5),
            ["hall_in"] = (0, 4), ["hall_w"] = (-8.5, -6), ["hall_e"] = (8.5, -6), ["scorpion"] = (0, -17.5),
            ["std_a"] = (-6, 0), ["std_b"] = (6, -7), ["std_c"] = (0, -14), ["signifer"] = (0, -16),
            ["boss_start"] = (0, -22.5), ["landing"] = (0, -29), ["boss_at"] = (0, -33), ["stair"] = (0, -37),
        },
    };

    /// <summary>The fallen beams and sarcophagi down the hall: low cover that stops a lane (the Scorpion's
    /// bolts), lying across the hall. (X, Z, half-width, half-depth, a beam or not.)</summary>
    public static readonly (double X, double Z, double Hw, double Hd, bool Beam)[] Cover =
    [
        (-5.5, 1.5, 2.2, 0.35, true), (4.5, -2.5, 1.3, 0.6, false), (-3, -8, 1.3, 0.6, false), (6, -12, 2.2, 0.35, true), (-6.5, -14.5, 1.3, 0.6, false),
    ];

    public override StoryPlace Place => Ground;
    public override string Arrive => "start";
    public override Func<StoryBeat>[] Beats => [() => new SouthEnd(), () => new HallLength(), () => new Standards()];
    public override string Pull => "Through the door: a long hall, and the head of a stair. On the stair, something is coming up in step.";
    public override string[] Between =>
    [
        "The first ranks are down. The hall runs on ahead, long and straight, and at the end of it something is winding a great bow.",
        "Down the hall, three standards go up one after another, and the dead turn to face them.",
        "The last standard goes down. Along the walls, the dead stand to attention, all at once, with one sound.",
    ];
    public override string? BossGate => "hall";
    public override string BossAt => "boss_at";
    public override string BossStart => "boss_start";
    public override string Sign => "On the stair, one tread heavier than the rest, coming up.";
    public override string BossDef => "boss_dead";
    public override string? Cinematic => "c13";
    public override string Kicker => "The Seventh Legion";
    public override StoryBoss Boss(IStoryArena a) => new BarrowLordStory(a);

    /// <summary>The cover down the hall, solid and drawn.</summary>
    public override void Furnish(IStoryArena a)
    {
        foreach (var (x, z, hw, hd, beam) in Cover)
        {
            a.B.Collision.AddBox(x, z, hw, hd, 0, new ColliderOpts(Tag: "cover"));
            var v = a.Piece(beam ? "dungeon/rubble_large" : "halloween/grave_A_destroyed", beam ? 1.6 : 1.3);
            v.Place(x, a.HeightAt(x, z), z, beam ? Math.PI / 2 : 0, beam ? 1.6 : 1.3);
            v.Visible = true;
        }
    }

    /// <summary>How far a lane from one point toward another runs before the hall's cover (or a wall) stops it.</summary>
    public static double Clear(Battle b, double x0, double z0, double x1, double z1)
    {
        double len = Math.Sqrt((x1 - x0) * (x1 - x0) + (z1 - z0) * (z1 - z0));
        var hit = b.Collision.Raycast(x0, z0, x1, z1, 0.3);
        if (hit is { } h && h.Collider.Tag is "cover" or "place") return Math.Max(0.5, len * h.T);
        return len;
    }

    /* ---------------------------------------------------------- a standard -- */

    /// <summary>The Legion's standard, planted: the part (a stationary creature, holy and fire break it the
    /// sooner) and its look (a pole and its rag), which goes with it.</summary>
    public sealed class Standard
    {
        public Enemy? E;
        double seed;
        IOrb? view;
        public double X, Z;

        public static Standard? Plant(IStoryArena a, double x, double z, double hp, SpawnStyle style = SpawnStyle.Rise)
        {
            var e = a.Spawn("legion_standard", x, z, false, style);
            if (e == null) return null;
            e.MaxHp = e.Hp = hp;
            e.Named = new Named { Title = "The standard" };
            var s = new Standard { E = e, seed = e.Seed, X = x, Z = z };
            s.view = a.Piece("hex_nature/flag_red", 2.6);
            s.view.Place(x, a.HeightAt(x, z), z, 0, 2.6);
            s.view.Visible = true;
            return s;
        }

        public bool Up => E is { Alive: true } e && e.Seed == seed && e.State != EnemyState.Dying;

        /// <summary>Gone from the field (broken, or the fight's end): its look with it.</summary>
        public void Gone(Battle b, bool release)
        {
            if (release && Up) b.Enemies.Release(E!);
            if (view != null) { view.Visible = false; view.Dispose(); view = null; }
        }
    }

    /* ---------------------------------------------------------- the south end -- */

    /// <summary>The dead come up the stair in files and march the hall's length; the Decurion leads the third rank
    /// in a shield line. Locked shields are not targets: the line breaks at its ends, and he is behind it. It
    /// teaches the Barrow Lord's "Iungite!".</summary>
    sealed class SouthEnd : StoryBeat
    {
        public override string Goal => "Bring down the Decurion";
        public override string? Gate => "south";
        public override double Minute => 2;
        public override string Start => "start";
        public override (string Def, double Weight)[] Crowd => [("risen", 4), ("risen_archer", 1.5)];
        public override int CrowdAlive => 14;
        public override int CrowdPool => 420;
        public override string[] CrowdFrom => ["south_w", "south_e"];
        public override int EmberFloor => 10;
        Levy? line;
        int lines;
        Enemy? decurion;
        double decSeed, rankT = 20;
        readonly Queue<(double T, double Hp)> hurt = new();

        protected override void Open()
        {
            // The first two ranks are the crowd; the third is his, in a shield line.
            A.Bark(0, 6, "Up the stair and down the hall they come, in files, in step.", null);
        }

        void Form()
        {
            var (lx, lz) = A.Place["line"];
            var p = B.Player;
            // Eight shields at every tier: the line is the lesson, and its men grow with the tier's level already.
            line = new Levy(A, lx, lz, p.X, p.Z, 8, "risen_warrior", null, "the shields") { Wheel = 0.45 };
            lines++;
        }

        /// <summary>The Decurion behind his line, until she is round it: then he fights.</summary>
        bool Behind(Enemy e, double dt)
        {
            var p = B.Player;
            if (line == null || line.Broken || Dist(p.X, p.Z, e.X, e.Z) < 4.5 && !line.Between(p.X, p.Z, e.X, e.Z)) return false;
            var (bx, bz) = line.Behind();
            double dx = bx - e.X, dz = bz - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d > 0.2) { double s = Math.Min(d, 4.5 * dt); e.X += dx / d * s; e.Z += dz / d * s; }
            e.Vx = e.Vz = 0;
            e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
            e.Anim = d > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
            if (e.State is not (EnemyState.Stunned or EnemyState.Dying)) e.State = EnemyState.Active;
            return true;
        }

        protected override void Tick(double dt)
        {
            var p = B.Player;
            if (decurion == null)
            {
                // The third rank comes down the hall as the first two are fought.
                if ((rankT -= dt) > 0) return;
                Form();
                var (bx, bz) = line!.Behind();
                decurion = A.Foe("mb_decurion", bx, bz, 6);
                if (decurion == null) { Done = true; return; }
                decSeed = decurion.Seed;
                // His line is the lesson, not his own teeth (and its shields are his, not new ones from the ground).
                decurion.Damage *= 0.45;
                var def = decurion.Def.Clone();
                def.Summon = null;
                decurion.Def = def;
                A.Script(decurion, Behind);
                A.Say("The shields lock", "Break the line at its ends", "danger");
                return;
            }
            if (!Up(decurion, decSeed))
            {
                if (line is { Broken: false })
                {
                    line.Break();
                    A.Bark(line.X, line.Z, "The shields come apart, and the men behind them stand where they are.", null);
                }
                Done = true;
                return;
            }
            var d = decurion!;
            line?.Step(dt);
            // Through the shields little reaches him; round them, he is open.
            d.TakenMul = line != null && line.Between(p.X, p.Z, d.X, d.Z) ? 0.15 : 1;
            hurt.Enqueue((T, d.Hp));
            while (hurt.Count > 0 && T - hurt.Peek().T > 6) hurt.Dequeue();
            if (hurt.Count > 0 && hurt.Peek().Hp - d.Hp > d.MaxHp * 0.05) { line?.Waver(2.5); hurt.Clear(); }
            // Worked from its ends early, it forms again (twice).
            if (line is { Broken: true } && lines < 3 && d.Hp > d.MaxHp * 0.25) { Form(); A.Say("The line forms again", "Round its ends to the Decurion", "danger"); }
            A.Goal = line is { Broken: false } l && l.Between(p.X, p.Z, d.X, d.Z) ? l.Round(p.X, p.Z) : (d.X, d.Z);
        }

        public override void End() => line?.Clear();

        public override BossBar? Bar => Up(decurion, decSeed)
            ? new BossBar(decurion!.Def.Name, decurion.Def.Lesson, decurion.Hp, decurion.MaxHp, IsBoss: false, Shielded: decurion.TakenMul < 1)
            : null;
    }

    /* ---------------------------------------------------------- the hall's length -- */

    /// <summary>The Scorpion kneels at the stair's head and shoots down the hall's length: a ratchet winding, then
    /// his bolts down aimed lanes. A step off the line is a dodge, and the fallen beams and sarcophagi stop them.
    /// It teaches the Barrow Lord's pilum.</summary>
    sealed class HallLength : StoryBeat
    {
        public override string Goal => "Bring down the Scorpion";
        public override string? Gate => null;
        public override double Minute => 6;
        public override string Start => "hall_in";
        public override (string Def, double Weight)[] Crowd => [("risen", 4), ("bone_heap", 1)];
        public override int CrowdAlive => 10;
        public override int CrowdPool => 480;
        public override string[] CrowdFrom => ["hall_w", "hall_e"];
        public override int EmberFloor => 20;
        Enemy? scorpion;
        double scSeed, volleyT = 3, twosT = 6;
        int volleys;
        /// <summary>How near she must be to reach him past his engine.</summary>
        const double Mantlet = 9;

        protected override void Open()
        {
            var (x, z) = A.Place["scorpion"];
            scorpion = A.Foe("mb_old_quarrel", x, z, 11);
            if (scorpion == null) return;
            scSeed = scorpion.Seed;
            scorpion.Damage *= 0.5;
            // He keeps the stair's head, kneeling at his engine: his bolts are the lanes.
            var def = scorpion.Def.Clone();
            def.Speed = 0;
            def.Ranged = null;
            scorpion.Def = def;
            scorpion.Speed = 0;
            A.Script(scorpion, Kneel);
        }

        bool Kneel(Enemy e, double dt)
        {
            var p = B.Player;
            e.Vx = e.Vz = 0;
            e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
            e.Anim = EnemyAnim.Idle;
            if (e.State is not (EnemyState.Stunned or EnemyState.Dying or EnemyState.Windup)) e.State = EnemyState.Active;
            return true;
        }

        protected override void Tick(double dt)
        {
            if (!Up(scorpion, scSeed)) { Done = true; return; }
            var s = scorpion!;
            var p = B.Player;
            A.Goal = (s.X, s.Z);
            // Kneeling behind his engine's mantlet, little reaches him from down the hall: close on him under his
            // bolts, from cover to cover.
            s.TakenMul = Dist(p.X, p.Z, s.X, s.Z) > Mantlet ? 0.3 : 1;
            if ((volleyT -= dt) <= 0)
            {
                volleyT = 4.2;
                Volley(s, p);
            }
            // The dead in twos up the hall's sides.
            if ((twosT -= dt) <= 0)
            {
                twosT = 9;
                var (x, z) = A.Place[A.R() < 0.5 ? "hall_w" : "hall_e"];
                A.Group("risen", 2, x, z, 1.2, SpawnStyle.Rise);
            }
        }

        /// <summary>A ratchet winding, then three bolts down aimed lanes: at her, and either side of her.</summary>
        void Volley(Enemy s, PlayerState p)
        {
            volleys++;
            if (volleys <= 2) A.Bark(s.X, s.Z, "Down the hall, a ratchet, winding.", null);
            if (volleys == 1) A.Say("Down the hall's length", "Step off the line, or get behind stone", "info");
            double dx = p.X - s.X, dz = p.Z - s.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
            double a0 = Math.Atan2(dz, dx);
            foreach (double off in new[] { 0.0, -0.16, 0.16 })
            {
                double a = a0 + off, reach = Math.Min(30, d + 6);
                double x1 = s.X + Math.Cos(a) * reach, z1 = s.Z + Math.Sin(a) * reach;
                double len = Clear(B, s.X, s.Z, x1, z1);
                x1 = s.X + Math.Cos(a) * len; z1 = s.Z + Math.Sin(a) * len;
                B.Blow(new Battle.EnemyBlow
                {
                    Shape = TelegraphShape.Line, X = s.X, Z = s.Z, X1 = x1, Z1 = z1, Width = 1.1, Delay = 1.3, Damage = s.Damage * 1.6,
                    School = School.Physical, Source = s.Def.Name, From = s, Label = off == 0 ? "A bolt" : null,
                });
            }
        }

        public override BossBar? Bar => Up(scorpion, scSeed)
            ? new BossBar(scorpion!.Def.Name, scorpion.TakenMul < 1 ? "Behind his engine: close on him from cover to cover" : scorpion.Def.Lesson, scorpion.Hp, scorpion.MaxHp, IsBoss: false, Shielded: scorpion.TakenMul < 1)
            : null;
    }

    /* -------------------------------------------------------------- the standards -- */

    /// <summary>The Signifer plants three standards down the hall ("Signa!"). While one stands, it raises a file
    /// of the dead every ten seconds and quickens the dead round it; he falls with the last. It teaches the
    /// standard at the heart of the Barrow Lord's testudo, and Chid's bane.</summary>
    sealed class Standards : StoryBeat
    {
        public override string Goal => $"Break the standards ({Broken} of 3)";
        public override string? Gate => null;
        public override double Minute => 10;
        public override string Start => "hall_in";
        public override (string Def, double Weight)[] Crowd => [("risen", 4), ("risen_warrior", 1.5), ("risen_archer", 1)];
        public override int CrowdAlive => 12;
        public override int CrowdPool => 600;
        public override string[] CrowdFrom => ["hall_w", "hall_e"];
        public override int EmberFloor => 28;
        readonly List<Standard> standards = new();
        readonly List<double> fileT = new();
        int Broken => 3 - standards.Count(s => s.Up);
        Enemy? signifer;
        double sigSeed, doneT = -1;

        protected override void Open()
        {
            var (sx, sz) = A.Place["signifer"];
            signifer = A.Foe("mb_ford_bell", sx, sz, 3);
            if (signifer != null)
            {
                sigSeed = signifer.Seed;
                signifer.Damage *= 0.5;
                // His standards raise the dead: his own raising would be twice over.
                var def = signifer.Def.Clone();
                def.Raise = null;
                signifer.Def = def;
                signifer.TakenMul = 0.25;
            }
            double t = 0;
            // Each standard about as stout as a named foe of its stage (holy and fire break it the sooner).
            double hp = signifer != null ? signifer.MaxHp * 0.85 : 4800;
            foreach (var id in new[] { "std_a", "std_b", "std_c" })
            {
                var (x, z) = A.Place[id];
                if (Standard.Plant(A, x, z, hp) is { } s) { standards.Add(s); fileT.Add(4 + t); }
                t += 1.5;
            }
        }

        protected override void Tick(double dt)
        {
            if (doneT >= 0) { if ((doneT -= dt) <= 0) Done = true; return; }
            var p = B.Player;
            for (int i = 0; i < standards.Count; i++)
            {
                var s = standards[i];
                if (s.E == null) continue;
                if (!s.Up)
                {
                    A.Bark(s.X, s.Z, "The standard goes down. The dead round it stop where they stand, and look about them.", null);
                    foreach (var e in B.Enemies.Living())
                        if (e.Disposition == Disposition.Hostile && !e.Elite && Dist(e.X, e.Z, s.X, s.Z) < 6) e.Status[StatusKind.Fear] = new StatusSlot(3, 1, 1, 0);
                    s.Gone(B, false);
                    s.E = null;
                    continue;
                }
                // A file of the dead out of the ground round it.
                if ((fileT[i] -= dt) <= 0)
                {
                    fileT[i] = 10;
                    A.Group("risen", 2 + A.Tier, s.X, s.Z + 1.5, 1.6, SpawnStyle.Rise);
                }
            }
            if (Broken >= 3)
            {
                // He falls with the last.
                if (Up(signifer, sigSeed)) { signifer!.TakenMul = 1; B.KillEnemy(signifer, true, null); }
                doneT = 1.5;
                return;
            }
            var next = standards.Where(s => s.Up).OrderBy(s => Dist(s.X, s.Z, p.X, p.Z)).FirstOrDefault();
            A.Goal = next != null ? (next.X, next.Z) : null;
            if (Up(signifer, sigSeed)) signifer!.TakenMul = 0.25;
        }

        public override void End()
        {
            foreach (var s in standards) s.Gone(B, true);
        }

        public override BossBar? Bar => Up(signifer, sigSeed)
            ? new BossBar(signifer!.Def.Name, "He falls with the last standard", signifer.Hp, signifer.MaxHp, IsBoss: false, Shielded: true)
            : null;
    }
}

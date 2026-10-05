using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/* The Dig Boils Over (docs/design/STORY_BOSSES.md 3): every lamp in the hole
 * coming up at once. Along the edge, up the tub-way, to the pump-house, and out
 * onto the lip, where the ground splits and the Boss hauls himself up. The
 * words are the story lead's (WRITING_PASS 23.2). Snib comments from the
 * heaps, while he lives.
 *
 *   the edge      three shaft heads boil lamplings until each windlass is
 *                 broken (she stands at it); the shaft falls in round it, and
 *                 leaves a hole. The Wick-Mother comes up with the second.
 *   the tub-way   ore tubs run down the rails at her (marked lanes that flatten
 *                 lamplings in them too), the Chucker lobbing from the
 *                 brake-house: out of reach until she has climbed to him.
 *   the pump      running: the Perfect of Fuses sends fuse-runners from the
 *                 pump-house steps, four waves, then comes down; his last crate
 *                 rolls into the pump and it goes up. Stopped: the Lamplighter
 *                 holds the wreck, the same way, with lamp-throwers.
 *
 * The way runs up the screen (north is -z), the great pit to the east of the
 * tub-way and south of the lip. The place's points are where arena art builds to. */
public sealed class DigBoilsOver : StoryFight
{
    public override string Id => "dig_boils";

    public static readonly StoryPlace Ground = new()
    {
        Spaces =
        [
            new("edge", [Capsule.Circle(-14, 24, 10)]),
            new("tubs", [new Capsule(-14, 6, -14, -14, 5), new Capsule(-14, 15, -14, 8, 3.2)]),
            new("pump", [Capsule.Circle(-12, -29, 8.5), new Capsule(-14, -16, -13, -22, 3.2)]),
            new("lip", [Capsule.Circle(13, -27, 12.5), new Capsule(-4.5, -29, 2, -28, 3.4)]),
        ],
        Gates =
        [
            new("edge", -17.2, 12.5, -10.8, 12.5, "tubs"),
            new("tubs", -16.6, -19.5, -10.2, -19.5, "pump"),
            new("pump", -1.5, -32.2, -1.5, -25.4, "lip"),
        ],
        Points = new()
        {
            ["start"] = (-14, 31), ["edge_w"] = (-21, 25), ["edge_s"] = (-14, 32),
            // The windlasses, at the shaft heads along the edge's rim; each shaft's mouth a step further out.
            ["edge"] = (-14, 24), ["shaft_a"] = (-9, 28.2), ["shaft_b"] = (-7.5, 24), ["shaft_c"] = (-9, 19.8),
            ["tubs_in"] = (-14, 9), ["tubs_mid"] = (-14, -2), ["heap_w"] = (-18, -4), ["heap_e"] = (-10, 2),
            ["brake"] = (-14, -15),
            ["pump_in"] = (-13, -21), ["pump"] = (-12, -31), ["pump_door"] = (-15, -35), ["pump_w"] = (-18, -27), ["pump_e"] = (-6, -31),
            ["boss_start"] = (3, -28), ["boss_at"] = (14, -27), ["headframe"] = (4, -19), ["snib"] = (23, -36),
            // The crack he comes up through, from the pit's lip toward the heaps (its ends stand clear of the edge).
            ["crack_a"] = (10.2, -20), ["crack_b"] = (16.8, -34),
        },
    };

    public override StoryPlace Place => Ground;
    public override string Arrive => "start";
    public override Func<StoryBeat>[] Beats => [() => new Edge(), () => new TubWay(), () => new PumpHouse()];
    public override string Pull => "The ember takes you to the edge of the Dig. Every lamp in the hole is coming up at once.";
    public override string[] Between => [];
    public override string BetweenSight(IStoryArena a, int stage) => stage switch
    {
        0 => "The last windlass goes over. Down the tub-way the brake-house lamp is lit, and the rails are singing.",
        1 => Running(a)
            ? "Past the brake-house stands the pump-house, and every lampling between you and it is carrying a crate."
            : "Past the brake-house stands the pump-house. Somebody inside is lighting lamps, one after another.",
        _ => "Every lampling left on the lip lies down flat, with its hands over its lamp.",
    };
    public override string BossAt => "boss_at";
    public override string BossStart => "boss_start";
    public override string ShutSight => "Behind you, the tub-way falls in.";
    public override string Sign => "Under the lip, something knocks twice. A line of blue light shows in the ground.";
    public override string BossDef => "grimtunnel_roused";
    public override string? Cinematic => "c12";
    public override string Kicker => "The Dig";
    public override StoryBoss Boss(IStoryArena a) => new GrimtunnelStory(a);

    /// <summary>The pump still runs (it is blown in this fight); stopped already, broken, blown or moved.</summary>
    public static bool Running(IStoryArena a) => a.FactOf("dig.pump").Str is not ("broken" or "blown" or "moved");

    /// <summary>Snib, from the nearest heap, while he lives (`snib.dead` unset).</summary>
    public static void Snib(IStoryArena a, string line)
    {
        if (a.Fact("snib.dead")) return;
        var p = a.B.Player;
        a.Bark(p.X + 3, p.Z - 4, line, "Snib");
    }

    /* ---------------------------------------------------------------- the edge -- */

    /// <summary>Three shaft heads along the edge, each boiling lamplings until its windlass is broken: she
    /// stands at it, and it goes over, and the shaft falls in on itself (a ring marked round it: step off it).
    /// The Wick-Mother comes up with the second shaft's wave, and her wicks from below. It teaches what comes
    /// up under her (his deep lamp, his Under) and ground that goes (his sinkholes).</summary>
    sealed class Edge : StoryBeat
    {
        public override string Goal => Broken < shafts.Count ? $"Break the windlasses ({Broken} of {shafts.Count})" : "Bring down the Wick-Mother";
        public override string? Gate => "edge";
        public override double Minute => 2;
        public override string Start => "start";
        public override (string Def, double Weight)[] Crowd => [("lampling", 3), ("lampling_wick", 3)];
        public override int CrowdAlive => 14;
        public override int CrowdPool => 420;
        public override string[] CrowdFrom => ["edge_w", "edge_s"];
        public override int EmberFloor => 10;

        sealed class Shaft
        {
            public required string Point;
            public required StandBy Windlass;
            public double BoilT;
            public int Boils;
        }
        readonly List<Shaft> shafts = new();
        int Broken => shafts.Count(s => s.Windlass.Broken);
        Enemy? mother;
        double motherSeed;
        bool told, snibbed;
        /// <summary>How often an open shaft boils, and how many times before it has nothing left.</summary>
        const double BoilEvery = 7;
        const int BoilsMost = 8;

        protected override void Open()
        {
            double t = 1;
            foreach (var id in new[] { "shaft_a", "shaft_b", "shaft_c" })
            {
                var (x, z) = A.Place[id];
                shafts.Add(new Shaft { Point = id, Windlass = new StandBy { X = x, Z = z, Reach = 2.6, Takes = 9 }, BoilT = t });
                t += 2.3;
            }
            A.Say("The shafts are boiling", "Break a windlass, and its shaft falls in", "info");
        }

        /// <summary>Where a shaft's mouth is: a step out from its windlass toward the rim.</summary>
        (double X, double Z) Mouth(Shaft s)
        {
            var (cx, cz) = A.Place["edge"];
            var (x, z) = A.Place[s.Point];
            double dx = x - cx, dz = z - cz, d = Math.Max(0.1, Math.Sqrt(dx * dx + dz * dz));
            return (x + dx / d * 1.8, z + dz / d * 1.8);
        }

        protected override void Tick(double dt)
        {
            var p = B.Player;
            for (int i = 0; i < shafts.Count; i++)
            {
                var s = shafts[i];
                if (s.Windlass.Broken) continue;
                if ((s.BoilT -= dt) <= 0 && s.Boils < BoilsMost)
                {
                    s.BoilT = BoilEvery;
                    s.Boils++;
                    var (mx, mz) = Mouth(s);
                    A.Group("lampling", 2 + A.Tier, mx, mz, 2, SpawnStyle.Burrow);
                }
                if (!told && s.Windlass.At(B)) { told = true; A.Say("Stand by the windlass", "Your weapons break the one you stand by", "info"); }
                if (s.Windlass.Step(B, dt, 874000 + i)) Fell(s);
            }
            if (Up(mother, motherSeed)) A.Goal = shafts.All(s => s.Windlass.Broken) || Dist(mother!.X, mother.Z, p.X, p.Z) < 5 ? (mother!.X, mother.Z) : NextWindlass();
            else A.Goal = NextWindlass();
            if (shafts.All(s => s.Windlass.Broken) && called && !Up(mother, motherSeed)) Done = true;
        }

        /// <summary>She has come up (or could not: nothing to wait for).</summary>
        bool called;

        (double X, double Z)? NextWindlass()
        {
            var p = B.Player;
            var s = shafts.Where(q => !q.Windlass.Broken).OrderBy(q => Dist(q.Windlass.X, q.Windlass.Z, p.X, p.Z)).FirstOrDefault();
            return s == null ? null : (s.Windlass.X, s.Windlass.Z);
        }

        /// <summary>The windlass goes over, and the shaft falls in on itself: the ground round its mouth goes
        /// (marked a moment: off it), and leaves a hole. The first brings the Wick-Mother up out of the next.</summary>
        void Fell(Shaft s)
        {
            var (mx, mz) = Mouth(s);
            A.Bark(mx, mz, "The windlass goes over, and the shaft falls in on itself.", null);
            B.Blow(new Battle.EnemyBlow
            {
                Shape = TelegraphShape.Circle, X = mx, Z = mz, Radius = 2.8, Delay = 1.2, Damage = B.MaxHp * 0.15, School = School.Physical,
                Source = "the shaft", Label = "The shaft falls in",
                After = bb => bb.Collision.AddCircle(mx, mz, 1.3, new ColliderOpts(Tag: "shaft")),
            });
            if (!snibbed) { snibbed = true; Snib(A, "Not the WINDLASS! Snib has to wind that! Snib does not wind it. The lads wind it."); }
            if (!called)
            {
                called = true;
                var next = shafts.Where(q => !q.Windlass.Broken).OrderBy(q => Dist(q.Windlass.X, q.Windlass.Z, B.Player.X, B.Player.Z)).FirstOrDefault();
                var (x, z) = next != null ? Mouth(next) : (mx, mz);
                mother = A.Foe("mb_wick_mother", x, z, 3.6);
                // Her wicks are the lesson, not her own teeth.
                if (mother != null) mother.Damage *= 0.55;
                motherSeed = mother?.Seed ?? 0;
            }
        }

        public override BossBar? Bar => Up(mother, motherSeed)
            ? new BossBar(mother!.Def.Name, mother.Def.Lesson, mother.Hp, mother.MaxHp, IsBoss: false)
            : null;
    }

    /* ------------------------------------------------------------- the tub-way -- */

    /// <summary>The tub-way climbs to the brake-house, where the Chucker lobs his pots three at a time. Up there
    /// he is out of her reach (his pots arc down the rails; hers fall short) until she has climbed to him. Ore
    /// tubs come down the rails on their own time, each lane marked as the rails start to sing, and a tub
    /// flattens whatever is on its rail, lamplings too. It teaches lanes and lobs, and that his crew's hazards
    /// hurt his own crew (Snib's barrel, at the boss).</summary>
    sealed class TubWay : StoryBeat
    {
        public override string Goal => "Bring down the Chucker at the brake-house";
        public override string? Gate => "tubs";
        public override double Minute => 6;
        public override string Start => "tubs_in";
        public override (string Def, double Weight)[] Crowd => [("lampling", 3), ("lampling_sapper", 1)];
        public override int CrowdAlive => 12;
        public override int CrowdPool => 480;
        public override string[] CrowdFrom => ["heap_w", "heap_e"];
        public override int EmberFloor => 20;
        Enemy? chucker;
        double chuckSeed, tubT = 3.5;
        bool sung;
        /// <summary>The rails, either side of the tub-way's middle, and how far up she must be to reach him.</summary>
        static readonly double[] Rails = [-16.2, -11.8];
        const double Reach = 11;

        protected override void Open()
        {
            var (x, z) = A.Place["brake"];
            chucker = A.Foe("mb_bombardier", x, z, 4);
            if (chucker == null) return;
            chuckSeed = chucker.Seed;
            // Three pots at a time are his lesson; each need not be a third of a life.
            chucker.Damage *= 0.4;
            // He keeps the brake-house and throws down the whole of the tub-way from it.
            var def = chucker.Def.Clone();
            def.Speed = 0;
            def.Ranged = def.Ranged!.Clone();
            def.Ranged.Range = 18;
            chucker.Def = def;
            chucker.Speed = 0;
        }

        protected override void Tick(double dt)
        {
            if (!Up(chucker, chuckSeed)) { Done = true; return; }
            var c = chucker!;
            var p = B.Player;
            // Up on the brake-house while its tubs run (the stage's own time, not his health); then the brake is
            // off, the rails go quiet, and he is in reach of whoever has climbed to him.
            bool roof = tubs < RoofTubs;
            c.TakenMul = roof ? 0 : Dist(p.X, p.Z, c.X, c.Z) > Reach ? 0.25 : 1;
            // While he holds the roof the way is the fight on the rails; then up to him.
            A.Goal = roof ? A.Place["tubs_mid"] : (c.X, c.Z);
            // The tubs come on their own time, whether she is on the rails or not: the stage is theirs.
            if ((tubT -= dt) <= 0)
            {
                tubT = roof ? 5.5 : 8;
                tubs++;
                Tub(p.X);
                if (tubs == RoofTubs) A.Bark(c.X, c.Z, "The brake-house lamp goes out. Up top, somebody is climbing down onto the rails.", null);
            }
        }

        int tubs;
        /// <summary>Tubs run while he keeps the brake-house roof.</summary>
        const int RoofTubs = 10;

        /// <summary>A tub down the rail nearer her: its lane marked as the rails sing, the length of the way.</summary>
        void Tub(double atX)
        {
            double rx = Rails.OrderBy(r => Math.Abs(r - atX)).First();
            var (bx, bz) = A.Place["brake"];
            double z0 = bz - 2, z1 = A.Place["tubs_in"].Z + 3;
            if (!sung)
            {
                sung = true;
                A.Bark(bx, bz, "The rails start to sing.", null);
                Snib(A, "Mind the tubs! Tubs are EXPENSIVE. Tubs are Boss's.");
            }
            B.Blow(new Battle.EnemyBlow
            {
                Shape = TelegraphShape.Line, X = rx, Z = z0, X1 = rx, Z1 = z1, Width = 2.2, Delay = 1.5, Damage = B.MaxHp * 0.22,
                Source = "a tub", Label = "A tub",
                // It flattens whatever is on its rail, the Dig's own too.
                After = bb =>
                {
                    foreach (var e in bb.Enemies.Living().ToList())
                        if (e.Disposition == Disposition.Hostile && !e.Elite && !e.Boss && e.State != EnemyState.Dying
                            && Math.Abs(e.X - rx) < 1.1 + e.Radius && e.Z > z0 && e.Z < z1)
                            bb.HitEnemy(e, e.MaxHp * 4, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true, NoProcs = true });
                },
            });
        }

        public override BossBar? Bar => Up(chucker, chuckSeed)
            ? new BossBar(chucker!.Def.Name, chucker.Def.Lesson, chucker.Hp, chucker.MaxHp, IsBoss: false, Shielded: chucker.TakenMul < 1)
            : null;
    }

    /* ---------------------------------------------------------------- the pump -- */

    /// <summary>The pump-house. While the pump runs, the Perfect of Fuses stands on its steps out of reach and
    /// sends fuse-runners at her in threes, lit crates carried at a run (kill them far off, or step off as one
    /// goes); after four waves he comes down himself. When he falls his last crate rolls on into the pump, and
    /// it goes up (a wide ring, marked: everyone out). With the pump already stopped, the Lamplighter holds its
    /// wreck the same way with lamp-throwers. It teaches the crates' burst: Snib's barrel.</summary>
    sealed class PumpHouse : StoryBeat
    {
        bool running;
        public override string Goal => running ? "Bring down the Perfect of Fuses" : "Bring down the Lamplighter";
        public override string? Gate => "pump";
        public override double Minute => 10;
        public override string Start => "pump_in";
        public override (string Def, double Weight)[] Crowd => [("lampling", 3), ("lampling_sapper", 1)];
        public override int CrowdAlive => 12;
        public override int CrowdPool => 560;
        public override string[] CrowdFrom => ["pump_w", "pump_e"];
        public override int EmberFloor => 28;
        Enemy? foe;
        double foeSeed, waveT = 3, blowT = -1, doneT = -1;
        int waves;
        bool down, told;
        /// <summary>Waves from the steps before he comes down, and how often.</summary>
        const int Waves = 8;
        const double WaveEvery = 9;

        protected override void Open()
        {
            running = Running(A);
            var (x, z) = A.Place["pump_door"];
            foe = A.Foe(running ? "mb_fuse_boss" : "mb_lamplighter", x, z, 3.4);
            if (foe == null) return;
            foeSeed = foe.Seed;
            foe.Damage *= 0.45;
            foe.HomeX = x; foe.HomeZ = z;
            foe.Disposition = Disposition.Neutral;
            foe.TakenMul = 0;
            A.Script(foe, Steps);
        }

        /// <summary>On the steps, calling them on: he keeps his place until his waves are spent.</summary>
        bool Steps(Enemy e, double dt)
        {
            if (down) return false;
            var p = B.Player;
            double hx = e.HomeX - e.X, hz = e.HomeZ - e.Z, hd = Math.Sqrt(hx * hx + hz * hz);
            if (hd > 0.2) { double s = Math.Min(hd, 3 * dt); e.X += hx / hd * s; e.Z += hz / hd * s; }
            e.Vx = e.Vz = 0;
            e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
            e.Anim = hd > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
            if (e.State is not (EnemyState.Stunned or EnemyState.Dying)) e.State = EnemyState.Active;
            return true;
        }

        protected override void Tick(double dt)
        {
            var p = B.Player;
            if (doneT >= 0) { if ((doneT -= dt) <= 0) Done = true; return; }
            if (blowT >= 0) { if ((blowT -= dt) <= 0) Blow(); return; }
            if (!Up(foe, foeSeed)) { Fell(); return; }
            var f = foe!;
            if ((waveT -= dt) <= 0)
            {
                waveT = down ? WaveEvery * 1.5 : WaveEvery;
                Wave(down ? 2 : 3);
                if (!down && ++waves >= Waves)
                {
                    down = true;
                    f.Disposition = Disposition.Hostile;
                    f.TakenMul = 1;
                    f.Target = -1;
                }
            }
            A.Goal = down ? (f.X, f.Z) : null;
        }

        /// <summary>A wave from the pump-house: fuse-runners carrying their crates lit, or lamp-throwers.</summary>
        void Wave(int n)
        {
            var (dx, dz) = A.Place["pump_door"];
            foreach (var at in new[] { "pump_door", "pump_w", "pump_e" }.Take(n))
            {
                var (x, z) = A.Place[at];
                A.Group(running ? "lampling_fuse" : "lampling_lamp", 1, (x + dx) / 2, (z + dz) / 2, 1.5);
            }
            if (!told && running) { told = true; A.Say("They carry it lit", "Kill the runners, or step off as one goes", "danger"); }
        }

        /// <summary>He is down: his crate rolls on without him, into the pump (or the Boss's light is out).</summary>
        void Fell()
        {
            if (!running)
            {
                Snib(A, "That is the Boss's LIGHT! Nobody puts out the Boss's light. ...You put out the Boss's light.");
                doneT = 1.5;
                return;
            }
            var (px, pz) = A.Place["pump"];
            A.Bark(px, pz, "His crate rolls on without him, into the pump.", null);
            A.Say("The pump is going up", "Get clear", "danger");
            B.Blow(new Battle.EnemyBlow
            {
                Shape = TelegraphShape.Circle, X = px, Z = pz, Radius = 10, Delay = 3, Damage = B.MaxHp * 0.45, School = School.Fire,
                Source = "the pump", Label = "The pump",
            });
            blowT = 3;
        }

        void Blow()
        {
            var (px, pz) = A.Place["pump"];
            foreach (var e in B.Enemies.Living().ToList())
                if (e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && Dist(e.X, e.Z, px, pz) < 10)
                    B.HitEnemy(e, e.MaxHp * 4, School.Fire, [Tag.Fire, Tag.Explosion], new HitOpts { NoCrit = true, NoProcs = true });
            B.Events.Emit(new Ev.Explosion { X = px, Z = pz, Radius = 10, School = School.Fire, Power = 2 });
            B.Events.Emit(new Ev.Shake { Amount = 0.6 });
            Snib(A, "The PUMP! Who will pump? Snib will not pump.");
            A.Bark(px, pz, "The pump-house goes up. Down the hill, the slurry stops.", null);
            A.Mark("pump");
            doneT = 2;
        }

        public override BossBar? Bar => Up(foe, foeSeed)
            ? new BossBar(foe!.Def.Name, foe.Def.Lesson, foe.Hp, foe.MaxHp, IsBoss: false, Shielded: !down)
            : null;
    }
}

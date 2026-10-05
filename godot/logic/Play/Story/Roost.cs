using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/* Raid on the Roost (docs/design/STORY_BOSSES.md 2): the Missing Caravan
 * settled by force. Up the ruts in the dark, through the cage yard, across the
 * camp where the levy still drills, to Redcowl's own fire with his children
 * asleep behind the carts. The words are the story lead's (WRITING_PASS 23.1);
 * the Kerchiefs never say the town's name.
 *
 *   the ruts       a ravine road climbing north, three pickets on its lips:
 *                  each whistle calls footpads off both banks at once (the
 *                  pincer). Firepot Nan comes with the third whistle.
 *   the cage yard  a lock breaks for the one who stands by it (his cage, at
 *                  the boss); Barn-Door holds the row. The last lock frees the
 *                  teamsters, as by day.
 *   the camp       the levy in step, not a target while locked; the
 *                  Pike-Captain behind it is. Six crates under a torch, while
 *                  they are still there, and a prompt to fire them.
 *
 * The place's points are where arena art builds to. */
public sealed class RaidOnTheRoost : StoryFight
{
    public override string Id => "roost_raid";

    public static readonly StoryPlace Ground = new()
    {
        Spaces =
        [
            new("ruts", [new Capsule(0, -46, 0, -24, 7)]),
            new("yard", [Capsule.Circle(-19, -17, 8.5), new Capsule(-12, -20, -5, -24, 3.4)]),
            new("camp", [Capsule.Circle(-5, 4, 12), new Capsule(-17, -10, -12, -4, 3.4)]),
            new("fire", [Capsule.Circle(0, 33, 14.5), new Capsule(-3, 13, -1, 20, 3.8)]),
        ],
        Gates =
        [
            new("ruts", -10.4, -25.6, -6.6, -18.4, "yard"),
            new("yard", -18.2, -4.5, -11.4, -10.2, "camp"),
            new("camp", -6.6, 18.4, 2.6, 14.6, "fire"),
        ],
        Points = new()
        {
            ["start"] = (0, -48),
            ["picket_a"] = (-5.8, -41), ["picket_b"] = (5.8, -34), ["picket_c"] = (-5.8, -27), ["nan"] = (4.8, -21),
            ["ruts_n"] = (0, -22), ["ruts_mid"] = (0, -34),
            ["yard_in"] = (-8, -22), ["yard"] = (-19, -17), ["store"] = (-15, -10.5),
            ["cage_1"] = (-25.5, -13), ["cage_2"] = (-26, -19.5), ["cage_3"] = (-21, -24.5), ["cage_4"] = (-13.5, -23.5),
            ["camp_in"] = (-13, -4), ["camp"] = (-5, 4), ["levy"] = (-3, 12), ["camp_w"] = (-15, 6), ["camp_e"] = (5, 2), ["camp_n"] = (-5, 14),
            ["crates"] = (4, -4),
            ["boss_start"] = (-1, 22), ["fire_c"] = (0, 33), ["boss_at"] = (0, 43), ["big_fire"] = (0, 45),
            ["carts_w"] = (-11, 33), ["carts_e"] = (11, 33),
        },
    };

    public override StoryPlace Place => Ground;
    public override string Arrive => "start";
    public override Func<StoryBeat>[] Beats => [() => new Ruts(), () => new CageYard(), () => new CampYard()];
    public override string Pull => "The ember takes you up the ruts below the Roost. Somewhere above, a whistle, and another answering.";
    public override string[] Between => [];
    /// <summary>The sights between stages read the world: who is in the cages, and whether the crates went up.</summary>
    public override string BetweenSight(IStoryArena a, int stage) => stage switch
    {
        0 => a.FactOf("caravan.survivors").Str switch
        {
            "rescued" => "Three whistles, and none answering. Ahead, the cage yard: four empty cages, and somebody very big still standing guard on them.",
            "dead" => "Three whistles, and none answering. Ahead, the cage yard: four empty cages, and three mounds of new earth beside them.",
            _ => "Three whistles, and none answering. Ahead, the cage yard: four cages, and the fourth stands open with nobody in it.",
        },
        1 => "Past the cages, the camp's fires, and the levy forming up the way they were taught: in step, pikes level.",
        _ => a.Marked("crates")
            ? "Where the crates stood there is a hole in the yard. Beyond it, the Kerchiefs fall back to the big fire and stand there with their torches up. Then they part."
            : "The Kerchiefs fall back to the big fire and stand there with their torches up. Then they part.",
    };
    public override string? BossGate => null;
    public override string BossAt => "boss_at";
    public override string ShutSight => "Behind you, his people drag a cart across the way you came.";
    public override string BossStart => "boss_start";
    public override string Sign => "A laugh from behind the big fire, in no hurry at all.";
    public override string BossDef => "boss_kerchiefs";
    public override string? Cinematic => "c11";
    public override string Kicker => "The Kerchiefs";
    public override StoryBoss Boss(IStoryArena a) => new Redcowl(a);

    /* ---------------------------------------------------------------- the ruts -- */

    /// <summary>Three pickets on the lips of the ruts, torch and whistle each, lit one after another up the
    /// road: a picket silenced, the next answers further up. His whistle calls footpads off both banks at
    /// once, either side of her (the pincer: get out from between them). Up on the lip he is out of her
    /// reach until his pincer is broken; then he comes down to it, and his whistle goes on calling them.
    /// Firepot Nan comes with the third, and lobs from the lip with her throwers. It teaches his thrown
    /// torch: the lobbed circle, and fire left burning.</summary>
    sealed class Ruts : StoryBeat
    {
        public override string Goal => OnLip ? $"Break the pincer ({Got} of {Need})" : $"Silence the pickets ({Silenced} of 3)";
        /// <summary>The pincer his whistle called as he lit his torch: while it stands he is up on the lip.</summary>
        readonly List<(Enemy E, double Seed)> wave = new();
        int Need => Math.Max(0, wave.Count - 1);
        int Got => Math.Min(Need, wave.Count(w => !Up(w.E, w.Seed)));
        bool onLip;
        /// <summary>Whistles from the lip: he comes down to her only when three pincers have been broken.</summary>
        int fromLip;
        bool OnLip => onLip && (fromLip < 3 || Got < Need);
        public override string? Gate => "ruts";
        public override double Minute => 2;
        public override string Start => "start";
        public override (string Def, double Weight)[] Crowd => [("footpad", 5), ("pillager", 1)];
        public override int CrowdAlive => 14;
        public override int CrowdPool => 400;
        public override string[] CrowdFrom => ["ruts_n", "ruts_mid"];
        public override int EmberFloor => 10;
        readonly List<(Enemy E, double Seed, string Post)> pickets = new();
        Enemy? nan;
        double nanSeed, whistleT = 2, lightT = -1;
        int lit;
        bool seen, pincered;
        static readonly string[] Posts = ["picket_a", "picket_b", "picket_c"];
        int Silenced => lit - pickets.Count(p => Up(p.E, p.Seed));

        protected override void Open() => Light();

        /// <summary>The next picket up the road takes up his torch.</summary>
        void Light()
        {
            var (x, z) = A.Place[Posts[lit++]];
            var e = A.Foe("footpad", x, z, 3, quiet: true);
            if (e == null) return;
            e.Named = new Named { Title = "Kerchief Picket" };
            e.HomeX = x; e.HomeZ = z;
            pickets.Add((e, e.Seed, Posts[lit - 1]));
            A.Script(e, Hold);
            // Up on the lip, out of her reach, he whistles at once.
            onLip = true;
            fromLip = 0;
            wave.Clear();
            e.Disposition = Disposition.Neutral;
            e.TakenMul = 0;
            whistleT = 0.5;
        }

        /// <summary>A picket keeps his post on the lip, torch up, and fights only what comes up to him.</summary>
        bool Hold(Enemy e, double dt)
        {
            var p = B.Player;
            double d = Dist(p.X, p.Z, e.X, e.Z);
            if (d < 3.5 && !OnLip) return false;
            double hx = e.HomeX - e.X, hz = e.HomeZ - e.Z, hd = Math.Sqrt(hx * hx + hz * hz);
            if (hd > 0.2) { double s = Math.Min(hd, 3.5 * dt); e.X += hx / hd * s; e.Z += hz / hd * s; }
            e.Vx = e.Vz = 0;
            e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
            e.Anim = hd > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
            if (e.State is not (EnemyState.Stunned or EnemyState.Dying)) e.State = EnemyState.Active;
            return true;
        }

        protected override void Tick(double dt)
        {
            var p = B.Player;
            var up = pickets.Where(k => Up(k.E, k.Seed)).ToList();
            if (!seen && up.Any(k => Dist(k.E.X, k.E.Z, p.X, p.Z) < 14))
            {
                seen = true;
                var k = up.OrderBy(k => Dist(k.E.X, k.E.Z, p.X, p.Z)).First();
                A.Bark(k.E.X, k.E.Z, "Lights! Lights on the ruts!", "A Kerchief");
            }
            // A picket silenced: his torch goes down the bank, and the next answers further up.
            if (up.Count == 0 && lightT < 0 && lit < Posts.Length)
            {
                var (sx, sz) = A.Place[Posts[lit - 1]];
                A.Bark(sx, sz, "The torch tumbles down the bank. That whistle will not answer again.", null);
                lightT = 2.5;
            }
            if (lightT > 0 && (lightT -= dt) <= 0) { lightT = -1; Light(); up = pickets.Where(k => Up(k.E, k.Seed)).ToList(); }
            // His pincer broken, he comes down off the lip to it.
            if (onLip && !OnLip && up.Count > 0)
            {
                onLip = false;
                var k = up[0];
                k.E.Disposition = Disposition.Hostile;
                k.E.TakenMul = 1;
                A.Bark(k.E.X, k.E.Z, "The picket comes down the bank at you, torch first.", null);
            }
            // His whistle, on its own time: each calls the pincer. Nan comes with the third picket's first.
            if (up.Count > 0 && (whistleT -= dt) <= 0)
            {
                whistleT = 9;
                var k = up[0];
                A.Bark(k.E.X, k.E.Z, "(A whistle, short and sharp. Another answers it, further up.)", null);
                var called = Pincer();
                if (onLip) { fromLip++; wave.AddRange(called.Select(c => (c, c.Seed))); whistleT = 7; }
                if (lit == 3 && nan == null) Nan();
            }
            var next = up.FirstOrDefault();
            A.Goal = OnLip ? null : next.E != null ? (next.E.X, next.E.Z) : Up(nan, nanSeed) ? (nan!.X, nan.Z) : null;
            if (!onLip && wave.Count > 0 && up.Count == 0) wave.Clear();
            if (Silenced == Posts.Length && lit == Posts.Length && nan == null) Nan();
            if (Silenced == Posts.Length && lit == Posts.Length && nan != null && !Up(nan, nanSeed)) Done = true;
        }

        /// <summary>Off both banks at once, level with her: two knots of footpads, one each side.</summary>
        List<Enemy> Pincer()
        {
            var p = B.Player;
            int n = 2 + A.Tier;
            double z = Math.Clamp(p.Z, -44, -25);
            var o = A.Group("footpad", n, -5.6, z, 1.5);
            o.AddRange(A.Group("footpad", n, 5.6, z, 1.5));
            if (!pincered) { pincered = true; A.Say("Off both banks at once", "Get out from between them", "danger"); }
            return o;
        }

        /// <summary>Firepot Nan, at the lip by the ruts' head, with her throwers.</summary>
        void Nan()
        {
            var (x, z) = A.Place["nan"];
            nan = A.Foe("mb_firepot_nan", x, z, 3.5);
            nanSeed = nan?.Seed ?? 0;
            // Three pots at a time is her lesson; each of them need not be a third of a life.
            if (nan != null) nan.Damage *= 0.6;
            if (nan != null) A.Bark(x, z, "Hot ones! Mind your backs!", nan.Def.Name);
            A.Group("pillager", 2, x - 2, z, 1.5);
        }

        public override BossBar? Bar => OnLip ? new BossBar("The pincer", "The picket is out of reach until it breaks", Need - Got, Math.Max(1, Need), Shielded: true, IsBoss: false)
            : Up(nan, nanSeed) ? new BossBar(nan!.Def.Name, nan.Def.Lesson, nan.Hp, nan.MaxHp, IsBoss: false)
            : null;
    }

    /* ----------------------------------------------------------- the cage yard -- */

    /// <summary>The cage row, held by Barn-Door. A lock gives for the one who stands by it (her weapons
    /// break the one she stands by: his cage, at the boss), but not while he stands in front of it: bring
    /// him down, or draw him off (he is slow, and will not leave the yard). The last lock frees the
    /// teamsters as by day; the fourth cage stands open and empty. With the cages empty, it is Barn-Door
    /// alone.</summary>
    sealed class CageYard : StoryBeat
    {
        public override string Goal => Caged && Freed < Locks.Count ? $"Break the cage locks ({Freed} of {Locks.Count})" : "Bring down Barn-Door";
        public override string? Gate => "yard";
        public override double Minute => 6;
        public override string Start => "yard_in";
        public override (string Def, double Weight)[] Crowd => [("footpad", 5), ("bruiser", 1)];
        public override int CrowdAlive => 16;
        public override int CrowdPool => 600;
        public override string[] CrowdFrom => ["store"];
        public override int EmberFloor => 20;
        readonly List<StandBy> Locks = new();
        bool Caged;
        int Freed => Locks.Count(l => l.Broken);
        Enemy? door;
        double doorSeed, storeT = 6;
        bool told, blocked;

        protected override void Open()
        {
            Caged = A.FactOf("caravan.survivors").IsNull;
            if (Caged)
                foreach (var c in new[] { "cage_1", "cage_2", "cage_3" })
                {
                    var (x, z) = A.Place[c];
                    Locks.Add(new StandBy { X = x, Z = z, Reach = 3.2, Takes = 10 });
                }
            var (bx, bz) = A.Place["yard"];
            door = A.Foe("mb_barn_door", bx, bz, 3.5);
            doorSeed = door?.Seed ?? 0;
            // He holds the cage row: he does not follow her down the ruts. His door and his slam are the
            // lesson (go round it, off the ground it brings down), not his fists.
            if (door != null) { door.HomeX = bx; door.HomeZ = bz; door.Leash = 7; door.Damage *= 0.6; }
            A.Group("bruiser", 1, bx + 2, bz, 1);
        }

        protected override void Tick(double dt)
        {
            var p = B.Player;
            for (int i = 0; i < Locks.Count; i++)
            {
                var l = Locks[i];
                if (!told && l.At(B)) { told = true; A.Say("Stand by a lock", "Your weapons break the one you stand by", "info"); }
                // Not while he stands in front of it.
                if (Up(door, doorSeed) && Dist(door!.X, door.Z, l.X, l.Z) < 4)
                {
                    if (!blocked && l.At(B)) { blocked = true; A.Say("Barn-Door is in the way", "Draw him off the lock, then break it", "info"); }
                    continue;
                }
                if (l.Step(B, dt, 871000 + i))
                {
                    // The cage rescue's own lines, as by day.
                    A.Line(Zones.Verge.CageLines[i]);
                    if (i == 2) A.Line("Jory. Jory Coyle. Is my uncle—? Is he—?", "Jory Coyle");
                    if (Freed == Locks.Count)
                    {
                        A.Bark(l.X, l.Z, "The freed men run for the ruts, and nobody stops them.", null);
                        A.Apply(Zones.Verge.TeamstersFreed);
                    }
                }
            }
            // Footpads out of the store while she works at the cages.
            if ((storeT -= dt) <= 0)
            {
                storeT = 11;
                var (sx, sz) = A.Place["store"];
                A.Group("footpad", 2 + A.Tier, sx, sz, 2);
            }
            var next = Locks.Where(l => !l.Broken).OrderBy(l => Dist(l.X, l.Z, p.X, p.Z)).FirstOrDefault();
            // The lock, unless he stands in front of it: then him.
            bool guarded = next != null && Up(door, doorSeed) && Dist(door!.X, door.Z, next.X, next.Z) < 4;
            A.Goal = next != null && !guarded ? (next.X, next.Z) : Up(door, doorSeed) ? (door!.X, door.Z) : null;
            if (Freed == Locks.Count && !Up(door, doorSeed)) Done = true;
        }

        public override BossBar? Bar => Up(door, doorSeed)
            ? new BossBar(door!.Def.Name, door.Def.Lesson, door.Hp, door.MaxHp, IsBoss: false)
            : null;
    }

    /* ------------------------------------------------------------ the camp yard -- */

    /// <summary>The levy forms and marches in step: a locked line, not a target, its ends breakable. The
    /// Pike-Captain walks behind it and is the target: hurt hard he makes it waver, and it breaks when he
    /// falls. Shots through the line reach him at half. While the six crates are still in the yard, a
    /// torch burns on a post beside them, and a prompt fires them. It teaches the levy he calls.</summary>
    sealed class CampYard : StoryBeat
    {
        public override string Goal => "Bring down the Pike-Captain, behind the line";
        public override string? Gate => "camp";
        public override double Minute => 10;
        public override string Start => "camp_in";
        public override (string Def, double Weight)[] Crowd => [("footpad", 5), ("bruiser", 1)];
        public override int CrowdAlive => 12;
        public override int CrowdPool => 650;
        public override string[] CrowdFrom => ["camp_w", "camp_e"];
        public override int EmberFloor => 28;
        Levy? levy;
        int lines;
        Enemy? captain;
        double capSeed, flankT = 8;
        readonly Queue<(double T, double Hp)> hurt = new();
        bool cratesOffered, cratesLit;
        double cratesT = -1;

        protected override void Open()
        {
            var (lx, lz) = A.Place["levy"];
            var (px, pz) = A.Place["camp_in"];
            Form();
            var (bx, bz) = levy!.Behind();
            captain = A.Foe("mb_pike_captain", bx, bz, 4);
            if (captain != null)
            {
                // His line is the lesson, not his own teeth: less of them when she gets round to him.
                captain.Damage *= 0.5;
                capSeed = captain.Seed;
                var def = captain.Def.Clone();
                def.Summon = null;
                captain.Def = def;
                A.Script(captain, Captain);
            }
            A.Say("The levy", "Round its ends, to the captain behind it", "danger");
            // The crates, while they are still in the yard (a prompt, never a stray shot).
            var crates = A.FactOf("be.crates");
            if (crates.IsNull || crates.Str == "redcowl")
            {
                var (cx, cz) = A.Place["crates"];
                cratesOffered = true;
                A.Offer("crates", cx, cz, "Fire the crates", A.Knows("clue.blasting_ember") ? "The six B.E. crates" : "Six crates, under a torch", Fire);
            }
        }

        void Form()
        {
            var (lx, lz) = A.Place["levy"];
            var p = B.Player;
            levy = new Levy(A, lx, lz, p.X, p.Z, 8 + A.Tier, caller: "The Pike-Captain") { Wheel = 0.5 };
            lines++;
        }

        /// <summary>The Pike-Captain behind his line, until she is round it: then he fights.</summary>
        bool Captain(Enemy e, double dt)
        {
            var p = B.Player;
            if (levy == null || levy.Broken || Dist(p.X, p.Z, e.X, e.Z) < 4.5 && !levy.Between(p.X, p.Z, e.X, e.Z)) return false;
            var (bx, bz) = levy.Behind();
            double dx = bx - e.X, dz = bz - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d > 0.2) { double s = Math.Min(d, 5.5 * dt); e.X += dx / d * s; e.Z += dz / d * s; }
            e.Vx = e.Vz = 0;
            e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
            e.Anim = d > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
            if (e.State is not (EnemyState.Stunned or EnemyState.Dying)) e.State = EnemyState.Active;
            return true;
        }

        /// <summary>Fire the crates: a torch to them, a ring marked three seconds, then a crater.</summary>
        void Fire()
        {
            if (cratesLit) return;
            cratesLit = true;
            A.Withdraw("crates");
            var (cx, cz) = A.Place["crates"];
            A.Bark(cx, cz, "DOWN! Get DOWN!", "A Kerchief");
            cratesT = 3;
            B.Blow(new Battle.EnemyBlow
            {
                Shape = TelegraphShape.Circle, X = cx, Z = cz, Radius = 12, Delay = 3, Damage = B.MaxHp * 0.6, School = School.Fire,
                Source = "the crates", Label = "The crates",
            });
        }

        void Blow()
        {
            var (cx, cz) = A.Place["crates"];
            // The arena-mechanics band (×4) on everything in it: the line breaks, the captain is left a quarter.
            foreach (var e in B.Enemies.Living().ToList())
            {
                if (e.Disposition == Disposition.Ally || e.State == EnemyState.Dying || Dist(e.X, e.Z, cx, cz) > 12) continue;
                if (e == captain) { e.Hp = Math.Min(e.Hp, e.MaxHp * 0.25); continue; }
                e.Disposition = Disposition.Hostile;
                B.HitEnemy(e, e.MaxHp * 4, School.Fire, [Tag.Fire, Tag.Explosion], new HitOpts { NoCrit = true, NoProcs = true, Provoke = true });
            }
            levy?.Break();
            B.Events.Emit(new Ev.Explosion { X = cx, Z = cz, Radius = 12, School = School.Fire, Power = 2 });
            B.Events.Emit(new Ev.Shake { Amount = 0.6 });
            A.Bark(cx, cz, "Where the crates stood there is a hole in the yard. The levy is on the ground round it.", null);
            A.Apply("""[{ "set": { "be.crates": "burned" } }]""");
            A.Mark("crates");
        }

        protected override void Tick(double dt)
        {
            if (cratesT > 0 && (cratesT -= dt) <= 0) Blow();
            var p = B.Player;
            if (!Up(captain, capSeed))
            {
                if (levy is { Broken: false })
                {
                    levy.Break();
                    A.Say("The levy breaks", null, "boon");
                    A.Bark(levy.X, levy.Z, "Pikes go down in the mud, and the men behind them back off to the fires.", null);
                }
                A.Withdraw("crates");
                Done = true;
                return;
            }
            var c = captain!;
            levy?.Step(dt);
            // Through the line little reaches him; round it, he is open.
            bool behind = levy != null && levy.Between(p.X, p.Z, c.X, c.Z);
            c.TakenMul = behind ? 0.15 : 1;
            // Hurt hard (a twentieth of him in six seconds), the line wavers.
            hurt.Enqueue((T, c.Hp));
            while (hurt.Count > 0 && T - hurt.Peek().T > 6) hurt.Dequeue();
            if (hurt.Count > 0 && hurt.Peek().Hp - c.Hp > c.MaxHp * 0.05) { levy?.Waver(2.5); hurt.Clear(); }
            // Broken early (the crates, or worked from its ends), it forms again once.
            if (levy is { Broken: true } && lines < 3 && c.Hp > c.MaxHp * 0.25 && !cratesLit) { Form(); A.Say("The levy forms again", "Round its ends to the captain", "danger"); }
            // Footpads at its flanks.
            if ((flankT -= dt) <= 0)
            {
                flankT = 12;
                if (levy is { Broken: false } l)
                {
                    var (rx, rz) = l.Round(p.X, p.Z);
                    A.Group("footpad", 1 + A.Tier, rx, rz, 1.5);
                }
            }
            A.Goal = levy is { Broken: false } lv && lv.Between(p.X, p.Z, c.X, c.Z) ? lv.Round(p.X, p.Z) : (c.X, c.Z);
        }

        public override void End()
        {
            A.Withdraw("crates");
            if (levy is { Broken: false }) levy.Break();
        }

        public override BossBar? Bar => Up(captain, capSeed)
            ? new BossBar(captain!.Def.Name, "Round the line's ends to him", captain.Hp, captain.MaxHp, IsBoss: false, Shielded: levy is { Broken: false })
            : null;
    }
}

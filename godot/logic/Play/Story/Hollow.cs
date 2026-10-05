using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/* The Hollow by Night (docs/design/STORY_BOSSES.md 1): the Beast Problem
 * settled with blood. Down the clough, past the sick water, to the den's
 * floor, where Greymuzzle comes out of the dark. The Pack is sick, not
 * wicked: no human bones, and nothing here is cruel for its own sake.
 *
 *   the clough      a cut fourteen metres wide, Old Blue howling from the
 *                   rock at its head: silence him (fire breaks a howl)
 *   the sick water  the stream pools; the shallows slow and poison. Light the
 *                   two deadfalls on the far bank (the ember lights dead
 *                   wood, and the Pack will not cross its light);
 *                   Greenbelly comes for the first light
 *   the den floor   Whitethroat runs the drive: go through the wolves, never
 *                   the gap. Then the sick in the den's mouth, the ring, and
 *                   the old wolf.
 *
 * The place's points are where arena art builds to: the same outline. */
public sealed class HollowByNight : StoryFight
{
    public override string Id => "hollow_by_night";

    public static readonly StoryPlace Ground = new()
    {
        Spaces =
        [
            new("clough", [new Capsule(-18, -36, -18, -15, 7)]),
            new("water", [Capsule.Circle(0, 0, 11), new Capsule(-18, -15, -8, -6, 3.5)]),
            new("den", [Capsule.Circle(19, 25, 15), new Capsule(6, 8, 13, 16, 3.5)]),
        ],
        Gates =
        [
            new("clough", -15.8, -7, -10.2, -14),
            new("water", 6.1, 15, 12.9, 9),
        ],
        Points = new()
        {
            ["start"] = (-18, -38), ["rock"] = (-18, -18), ["head"] = (-18, -21),
            ["water_in"] = (-9, -7), ["reeds_w"] = (-8, 5), ["reeds_s"] = (5, -7), ["reeds_n"] = (-1, 8),
            ["shallow_a"] = (-2, -1), ["shallow_b"] = (5, 3),
            ["fire:a"] = (2, 9), ["fire:b"] = (9, 2),
            ["den_in"] = (11, 14), ["den"] = (19, 25), ["den_mouth"] = (21, 39), ["boss_start"] = (19, 16),
            ["fire:c"] = (12, 18), ["fire:d"] = (26, 18), ["fire:e"] = (12, 32), ["fire:f"] = (26, 32),
        },
    };

    public override StoryPlace Place => Ground;
    public override string Arrive => "start";
    public override Func<StoryBeat>[] Beats => [() => new Clough(), () => new SickWater(), () => new Drive()];
    public override string Pull => "The ember takes you down the clough, into the Hollow. The stream is loud here, and it smells wrong.";
    public override string[] Between =>
    [
        "The howling stops. In the quiet you can hear the stream, and something in the brush coughing.",
        "The deadfalls burn. Past them is the den's mouth, and in it, grey shapes that do not get up.",
        "The wolves back away from you, low, into a ring. Something is coming out of the den.",
    ];
    public override string BossAt => "den_mouth";
    public override string BossStart => "boss_start";
    public override string Sign => "A howl from the den's mouth, old and cracking at the top.";
    public override string BossDef => "boss_pack";
    public override string? Cinematic => "c10";
    public override StoryBoss Boss(IStoryArena a) => new Greymuzzle(a);
    public override string[] Fires => ["fire:a", "fire:b", "fire:c", "fire:d", "fire:e", "fire:f"];
    /// <summary>Maeca's fed fires (bane.fires): a deadfall fed burns longer.</summary>
    public override double Burns(IStoryArena a) => a.Fact("bane.fires") ? 35 : 20;

    /* -------------------------------------------------------------- the clough -- */

    /// <summary>Old Blue howls from the rock at the clough's head; each howl he finishes calls five
    /// of the Pack. Damage, a stagger or one hit of fire breaks a howl. It teaches the moon-howl.</summary>
    sealed class Clough : StoryBeat
    {
        public override string Goal => "Silence Old Blue";
        public override string? Gate => "clough";
        public override int Level => 1;
        public override string Start => "start";
        Enemy? blue;
        double blueSeed, waveT = 7, howlT = 6, howlHp, howling = -1;
        School lastSchool;
        bool ringed;

        protected override void Open()
        {
            var (x, z) = A.Place["rock"];
            blue = A.Foe("mb_caller", x, z, 1, "The Pack");
            if (blue != null)
            {
                blueSeed = blue.Seed;
                // His howl is the stage's (a channel, broken), not his own summons.
                var def = blue.Def.Clone();
                def.Summon = null;
                blue.Def = def;
                blue.Scripted = true;
                A.Script(blue, Howl);
            }
            Head(3);
            Head(3);
        }

        void Head(int n)
        {
            var (x, z) = A.Place["head"];
            A.Group("wolf", n, x, z, 3);
        }

        /// <summary>His howl, held: true while it holds him.</summary>
        bool Howl(Enemy e, double dt)
        {
            if (howling < 0) return false;
            howling += dt;
            e.Vx = e.Vz = 0;
            e.State = EnemyState.Casting;
            e.Cast = CastKind.Aura;
            e.Anim = EnemyAnim.Cast;
            bool fire = e.LastSchool == School.Fire && lastSchool != School.Fire && e.Hp < howlHp;
            lastSchool = e.LastSchool;
            if (howlHp - e.Hp >= e.MaxHp * 0.05 || fire || e.Status.Has(StatusKind.Stun) || e.Status.Has(StatusKind.Frozen))
            {
                howling = -1;
                e.State = EnemyState.Stunned;
                e.StateT = 2;
                B.Events.Emit(new Ev.Announce { Title = "The howl is broken", Subtitle = fire ? "Fire breaks it" : null, Tone = Tone.Boon });
                return true;
            }
            if (howling >= 4)
            {
                howling = -1;
                e.State = EnemyState.Active;
                A.Bark(e.X, e.Z, "(Old Blue howls from the rock, and every wolf in the clough answers.)", null);
                Head(5);
            }
            return true;
        }

        protected override void Tick(double dt)
        {
            if (!Up(blue, blueSeed)) { Done = true; return; }
            A.Goal = (blue!.X, blue.Z);
            waveT -= dt; howlT -= dt;
            if (waveT <= 0)
            {
                waveT = 9;
                if (A.Hostiles(e => e.Def.Id == "wolf") < 8) Head(2 + A.Tier / 2);
            }
            if (howlT <= 0 && howling < 0)
            {
                howlT = 11;
                howling = 0;
                howlHp = blue.Hp;
                lastSchool = blue.LastSchool;
                A.Bark(blue.X, blue.Z, "Old Blue lifts his head to howl.", null);
            }
            // Once, the runners ring her (the ring verb, read before the boss's ring).
            if (!ringed && blue.Hp < blue.MaxHp * 0.5)
            {
                ringed = true;
                var p = B.Player;
                for (int k = 0; k < 6; k++)
                {
                    double a = k * Math.PI / 3;
                    A.Group("wolf_runner", 1, p.X + Math.Cos(a) * 9, p.Z + Math.Sin(a) * 9, 0.5);
                }
                A.Say("They run a ring round you", "Break it, and go through", "danger");
            }
        }

        public override BossBar? Bar => Up(blue, blueSeed)
            ? new BossBar(blue!.Def.Name, "His howl calls the Pack: break it", blue.Hp, blue.MaxHp, null, howling >= 0 ? ("The howl: break it!", howling / 4) : null, IsBoss: false)
            : null;
    }

    /* ---------------------------------------------------------- the sick water -- */

    /// <summary>Light the two deadfalls on the far bank; Greenbelly comes for the first light. It
    /// teaches the fires: the ember lights dead wood, and the Pack will not cross its light.</summary>
    sealed class SickWater : StoryBeat
    {
        public override string Goal => greenbelly == null
            ? $"Light the deadfalls on the far bank ({Lit} of 2)"
            : Up(greenbelly, gbSeed) ? "Bring down Greenbelly" : $"Light the deadfalls on the far bank ({Lit} of 2)";
        public override string? Gate => "water";
        public override int Level => 4;
        public override string Start => "water_in";
        Enemy? greenbelly;
        double gbSeed, waveT = 4;
        readonly List<GroundZone> shallows = new();
        Deadfall[] fires = [];
        int Lit => fires.Count(f => f.EverLit);

        protected override void Open()
        {
            fires = A.Fires.Where(f => f.Id is "fire:a" or "fire:b").ToArray();
            foreach (var (pt, r) in new[] { ("shallow_a", 3.5), ("shallow_b", 2.6) })
            {
                var (x, z) = A.Place[pt];
                // Slurry underfoot: a quarter of a blighted wolf's bite a second, and it slows (Tick).
                double dps = Enemies.Get("wolf_blighted").Damage * Enemies.ScaleFor(A.Level).Damage * 0.25;
                var zn = B.SpawnZone(Side.Enemy, x, z, r, 9999, dps, School.Nature);
                if (zn != null) { zn.Tags = [Tag.Zone, Tag.Nature]; shallows.Add(zn); }
            }
            Reeds(2);
            Reeds(2);
        }

        void Reeds(int n)
        {
            var pts = new[] { "reeds_w", "reeds_s", "reeds_n" };
            var (x, z) = A.Place[pts[(int)(A.R() * pts.Length)]];
            A.Group("wolf_blighted", n, x, z, 2.5);
        }

        protected override void Tick(double dt)
        {
            var p = B.Player;
            // The shallows: slurry underfoot slows as well as poisons.
            foreach (var zn in shallows)
                if (zn.Alive && Dist(p.X, p.Z, zn.X, zn.Z) < zn.Radius) B.SlowPlayer(0.6, 0.3);
            waveT -= dt;
            if (waveT <= 0)
            {
                waveT = 10;
                if (A.Hostiles(e => e.Def.Id == "wolf_blighted") < 9) Reeds(3);
            }
            // Greenbelly comes for the first light (or when she has waited long enough for it).
            if (greenbelly == null && (Lit > 0 || T > 40))
            {
                var (x, z) = A.Place["reeds_n"];
                greenbelly = A.Foe("mb_blight_mother", x, z, 1, "The Pack");
                gbSeed = greenbelly?.Seed ?? 0;
            }
            var unlit = fires.Where(f => !f.EverLit).OrderBy(f => Dist(f.X, f.Z, p.X, p.Z)).FirstOrDefault();
            A.Goal = unlit != null ? (unlit.X, unlit.Z) : Up(greenbelly, gbSeed) ? (greenbelly!.X, greenbelly.Z) : null;
            if (Lit == fires.Length && greenbelly != null && !Up(greenbelly, gbSeed)) Done = true;
        }

        public override void End()
        {
            foreach (var zn in shallows) if (zn.Alive) B.Zones.Release(zn);
            shallows.Clear();
        }

        public override BossBar? Bar => Up(greenbelly, gbSeed)
            ? new BossBar(greenbelly!.Def.Name, greenbelly.Def.Lesson, greenbelly.Hp, greenbelly.MaxHp, IsBoss: false)
            : null;
    }

    /* --------------------------------------------------------------- the drive -- */

    /// <summary>Whitethroat runs the drive at the den's mouth: the Pack closes in a crescent on one side
    /// and she runs the gap it leaves. Go through the wolves, never the gap. When her run misses she
    /// stands panting, open. It teaches the ring, and that a wolf who misses is open.</summary>
    sealed class Drive : StoryBeat
    {
        public override string Goal => "Bring down Whitethroat";
        public override int Level => 6;
        public override string Start => "den_in";
        Enemy? white;
        double whiteSeed, driveT = 5, runT = -1, pantT;
        double laneX0, laneZ0, laneX1, laneZ1;
        Battle.EnemyBlow? lane;
        bool hit;

        protected override void Open()
        {
            var (x, z) = A.Place["den"];
            white = A.Foe("mb_whitethroat", x, z + 6, 1, "The Pack");
            if (white != null)
            {
                whiteSeed = white.Seed;
                white.Scripted = true;
                A.Script(white, Run);
            }
            A.Group("wolf", 4, x, z + 2, 3);
        }

        /// <summary>Her run down the gap, and the pant after a miss: true while the drive moves her.</summary>
        bool Run(Enemy e, double dt)
        {
            if (pantT > 0)
            {
                pantT -= dt;
                e.Vx = e.Vz = 0;
                e.State = EnemyState.Recover;
                e.Anim = EnemyAnim.Idle;
                e.TakenMul = 1.5;
                if (pantT <= 0) { e.TakenMul = 1; e.State = EnemyState.Active; }
                return true;
            }
            if (runT < 0) return false;
            runT += dt;
            if (runT < 1.0)
            {
                // Waiting across the gap, marked.
                e.Vx = e.Vz = 0;
                e.State = EnemyState.Windup;
                e.Anim = EnemyAnim.Windup;
                e.Facing = Math.Atan2(laneZ1 - laneZ0, laneX1 - laneX0);
                return true;
            }
            double k = Math.Min(1, (runT - 1.0) / 0.45);
            e.X = laneX0 + (laneX1 - laneX0) * k;
            e.Z = laneZ0 + (laneZ1 - laneZ0) * k;
            B.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
            e.State = EnemyState.Lunging;
            e.Anim = EnemyAnim.Move;
            if (k >= 1)
            {
                runT = -1;
                e.State = EnemyState.Active;
                // A run that missed leaves her open, panting (a pale-blue ring).
                if (!hit)
                {
                    pantT = 2;
                    B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = e.X, Z = e.Z, Radius = 2.4, Delay = 2, From = e, Label = "She missed" });
                }
            }
            return true;
        }

        /// <summary>The drive: a crescent of the Pack on the far side of her, closing; Whitethroat
        /// waits across the gap and runs it.</summary>
        void Drive_()
        {
            var p = B.Player;
            var w = white!;
            double away = Math.Atan2(p.Z - w.Z, p.X - w.X);
            int n = 7 + A.Tier;
            for (int k = 0; k < n; k++)
            {
                double a = away + (k / (double)Math.Max(1, n - 1) - 0.5) * Math.PI * 1.1;
                A.Group("wolf", 1, p.X + Math.Cos(a) * 10, p.Z + Math.Sin(a) * 10, 0.4);
            }
            A.Bark(w.X, w.Z, "A rising howl: the Pack wheels.", null);
            double dx = p.X - w.X, dz = p.Z - w.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
            double len = Math.Min(18, d + 6);
            laneX0 = w.X; laneZ0 = w.Z; laneX1 = w.X + dx / d * len; laneZ1 = w.Z + dz / d * len;
            hit = false;
            lane = B.Blow(new Battle.EnemyBlow
            {
                Shape = TelegraphShape.Line, X = laneX0, Z = laneZ0, X1 = laneX1, Z1 = laneZ1, Width = 2.4, Delay = 1.0,
                Damage = w.Damage * 1.6, Source = w.Def.Name, From = w, Label = "The drive",
            });
            // Missed if she is out of the lane when it lands (a dash through it is a miss as well).
            var marked = lane;
            lane.After = bb => hit = marked.Hit(bb.Player.X, bb.Player.Z, bb.Player.Radius) && bb.Player.HurtT > 0.25;
            runT = 0;
        }

        protected override void Tick(double dt)
        {
            if (!Up(white, whiteSeed)) { Done = true; return; }
            A.Goal = (white!.X, white.Z);
            driveT -= dt;
            if (driveT <= 0 && runT < 0 && pantT <= 0)
            {
                driveT = 14;
                Drive_();
            }
        }

        public override BossBar? Bar => Up(white, whiteSeed)
            ? new BossBar(white!.Def.Name, "Go through the wolves, never the gap", white.Hp, white.MaxHp, IsBoss: false)
            : null;
    }
}

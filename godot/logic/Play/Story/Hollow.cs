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
    /// <summary>Built to this outline by arena art (Maps/Arenas/HollowNight.cs): its deadfalls, root
    /// plate, reeds and cover are its own.</summary>
    public override bool PlaceBuilt => true;

    // The way runs up the screen, away from the camera (which stands to the +z side): in at
    // the clough at the bottom, the den's mouth at the top of the picture, where the boss
    // comes out of it toward her and the root plate over it never stands between her and
    // the camera (arena art).
    public static readonly StoryPlace Ground = new()
    {
        Spaces =
        [
            new("clough", [new Capsule(-18, 36, -18, 15, 7)]),
            new("water", [Capsule.Circle(0, 0, 11), new Capsule(-18, 15, -8, 6, 3.5)]),
            new("den", [Capsule.Circle(19, -25, 15), new Capsule(6, -8, 13, -16, 3.5)]),
        ],
        Gates =
        [
            new("clough", -15.8, 7, -10.2, 14, "water"),
            new("water", 6.1, -15, 12.9, -9, "den"),
        ],
        Points = new()
        {
            ["start"] = (-18, 38), ["rock"] = (-18, 18), ["rock_low"] = (-21, 31), ["rock_mid"] = (-15, 25), ["head"] = (-18, 21), ["head_w"] = (-22, 20), ["head_e"] = (-14, 20),
            ["water_in"] = (-9, 7), ["reeds_w"] = (-8, -5), ["reeds_s"] = (5, 7), ["reeds_n"] = (-1, -8),
            ["shallow_a"] = (-2, 1), ["shallow_b"] = (5, -3),
            ["fire:a"] = (2, -9), ["fire:b"] = (9, -2),
            ["den_in"] = (11, -14), ["den"] = (19, -25), ["den_mouth"] = (21, -39), ["boss_start"] = (19, -16),
            ["den_w"] = (7, -26), ["den_e"] = (31, -24), ["den_n"] = (15, -36),
            ["fire:c"] = (12, -18), ["fire:d"] = (26, -18), ["fire:e"] = (12, -32), ["fire:f"] = (26, -32),
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
    public override string ShutSight => "Behind you, the Pack fills the way you came.";
    public override string BossStart => "boss_start";
    public override string Sign => "A howl from the den's mouth, old and cracking at the top.";
    public override string BossDef => "boss_pack";
    public override string? Cinematic => "c10";
    public override StoryBoss Boss(IStoryArena a) => new Greymuzzle(a);
    public override string[] Fires => ["fire:a", "fire:b", "fire:c", "fire:d", "fire:e", "fire:f"];
    /// <summary>The Pack bites at its full weight: its wolves in twos and threes are the Hollow's danger, as the
    /// Kerchiefs' pots and pikes are the Roost's. (With its named foes' fists slowed, three nights in a hundred
    /// dipped under half on the way in at the story's usual three quarters: a stroll.)</summary>
    public override double CrowdTeeth => 1.0;
    /// <summary>Maeca's fed fires (bane.fires): a deadfall fed burns longer.</summary>
    public override double Burns(IStoryArena a) => a.Fact("bane.fires") ? 35 : 20;

    /* -------------------------------------------------------------- the clough -- */

    /// <summary>Old Blue howls from his rocks up the clough; each howl he finishes calls five of the
    /// Pack. Damage, a stagger or one hit of fire breaks a howl. It teaches the moon-howl: his voice
    /// is the fight, so his voice sets its pace. Four howls broken on a rock and he gives ground up
    /// the cut (he will not leave it hurt, only shamed), and each time the Pack stands between: first
    /// the yearlings run a ring round her (the ring, read before the boss's), then the whole clough
    /// comes down at her in files. While they stand he is out of reach on his rock; through them, he
    /// is hers again. On the rock at the clough's head there is nowhere left to go: silence him.</summary>
    sealed class Clough : StoryBeat
    {
        enum Part { LowRock, Ring, MidRock, Rush, HeadRock }
        Part part = Part.LowRock;
        public override string Goal => part switch
        {
            Part.LowRock or Part.MidRock => $"Break Old Blue's howls ({broken} of {Breaks})",
            Part.Ring => $"Break the ring round you ({Got} of {Need})",
            Part.Rush => $"Break the rush down the cut ({Got} of {Need})",
            _ => "Silence Old Blue",
        };
        public override string? Gate => "clough";
        public override double Minute => 2;
        public override string Start => "start";
        public override (string Def, double Weight)[] Crowd => [("wolf", 5), ("wolf_runner", 1)];
        public override int CrowdAlive => 18;
        public override int CrowdPool => 400;
        public override string[] CrowdFrom => ["head", "head_w", "head_e"];
        public override int EmberFloor => 10;
        Enemy? blue;
        double blueSeed, howlT = 5, howlHp, howlOver, howling = -1;
        School lastSchool;
        /// <summary>Howls broken on this rock, and how many shame him off it.</summary>
        int broken, howls;
        /// <summary>Four broken shame him off his rock; six howled (the Pack called by those she let
        /// finish) and he goes on anyway, so a build that cannot stop him is crowded, not stuck.</summary>
        const int Breaks = 4, Howls = 6;
        /// <summary>How long a howl takes, and how long between them.</summary>
        const double HowlFor = 4, HowlEvery = 9;
        /// <summary>His health held on each rock until he leaves it: hurt is not what moves him.</summary>
        static readonly double[] Holds = [0.7, 0.4, 0];
        /// <summary>What stands between her and him now (the ring, the rush): each with its seed.</summary>
        readonly List<(Enemy E, double Seed)> wave = new();
        int files;
        double fileT;
        const int Files = 5;
        int RushSize => Files * (3 + A.Tier);
        int Down => wave.Count(w => !Up(w.E, w.Seed));
        /// <summary>How many of what stands between must go down (the last one or two may run), and how
        /// many have.</summary>
        int Need => part == Part.Ring ? Math.Max(0, wave.Count - 1) : Math.Max(0, (files == Files ? wave.Count : RushSize) - 2);
        int Got => Math.Min(Down, Need);
        bool OutOfReach => part is Part.Ring or Part.Rush;

        protected override void Open()
        {
            var (x, z) = A.Place["rock_low"];
            blue = A.Foe("mb_caller", x, z, 3, "The Pack");
            if (blue != null)
            {
                blueSeed = blue.Seed;
                // His howl is the stage's (a channel, broken), not his own summons.
                var def = blue.Def.Clone();
                def.Summon = null;
                blue.Def = def;
                blue.Scripted = true;
                blue.HpFloor = blue.MaxHp * Holds[0];
                blue.HomeX = x; blue.HomeZ = z;
                A.Script(blue, Howl);
            }
            Head(3);
            Head(3);
        }

        void Head(int n, string at = "head")
        {
            var (x, z) = A.Place[at];
            A.Group("wolf", n, x, z, 3);
        }

        /// <summary>His howl, held: true while it holds him. He keeps to his rock; out of reach behind the
        /// Pack, he stands on it and watches.</summary>
        bool Howl(Enemy e, double dt)
        {
            if (OutOfReach || howling < 0)
            {
                // On his rock, turned to her: he is a voice, not a biter.
                e.Vx = e.Vz = 0;
                double dx = e.HomeX - e.X, dz = e.HomeZ - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
                if (d > 0.1) { double s = Math.Min(d, 6 * dt); e.X += dx / d * s; e.Z += dz / d * s; }
                if (e.State is not (EnemyState.Stunned or EnemyState.Dying)) e.State = EnemyState.Active;
                e.Anim = d > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
                var p = B.Player;
                e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
                return true;
            }
            howling += dt;
            e.Vx = e.Vz = 0;
            e.State = EnemyState.Casting;
            e.Cast = CastKind.Aura;
            e.Anim = EnemyAnim.Cast;
            bool fire = e.LastSchool == School.Fire && lastSchool != School.Fire && (e.Hp < howlHp || e.Overflow > howlOver);
            lastSchool = e.LastSchool;
            // Hurt enough (counting what his rock's mark held off him), staggered, held, or one hit of fire.
            bool hurt = howlHp - e.Hp + e.Overflow - howlOver >= e.MaxHp * 0.03;
            if (hurt || fire || e.Status.Has(StatusKind.Stun) || e.Status.Has(StatusKind.Frozen))
            {
                howling = -1;
                e.State = EnemyState.Stunned;
                e.StateT = 2;
                if (part is Part.LowRock or Part.MidRock) broken++;
                B.Events.Emit(new Ev.Announce { Title = "The howl is broken", Subtitle = fire ? "Fire breaks it" : null, Tone = Tone.Boon });
                return true;
            }
            if (howling >= HowlFor)
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
            var b = blue!;
            switch (part)
            {
                case Part.LowRock when (broken >= Breaks || howls >= Howls) && howling < 0:
                    GiveGround(b, "rock_mid", 1, "Old Blue gives ground, up the cut to the next rock, and leaves his yearlings to you.");
                    part = Part.Ring;
                    Ring();
                    break;
                case Part.Ring when Got >= Need:
                    InReach(b, Part.MidRock, "The ring is broken", "Old Blue is on the next rock: break his howls");
                    break;
                case Part.MidRock when (broken >= Breaks || howls >= Howls) && howling < 0:
                    GiveGround(b, "rock", 2, "Old Blue goes up to the last rock, at the clough's head. Above him, the whole cut is wolves.");
                    part = Part.Rush;
                    files = 0;
                    fileT = 0;
                    A.Say("The Pack comes down the cut", "Break the rush, and he is yours", "danger");
                    break;
                case Part.Rush:
                    // Four files down the cut, one every five seconds; through them, he is hers again.
                    if (files < Files && (fileT -= dt) <= 0)
                    {
                        fileT = 5;
                        var (fx, fz) = A.Place[(files % 3) switch { 0 => "head", 1 => "head_w", _ => "head_e" }];
                        foreach (var e in A.Group("wolf", 3 + A.Tier, fx, fz, 2.5)) wave.Add((e, e.Seed));
                        files++;
                    }
                    if (files == Files && Got >= Need) InReach(b, Part.HeadRock, "The rush is broken", "Old Blue is alone on his rock: silence him");
                    break;
            }
            A.Goal = OutOfReach ? null : (b.X, b.Z);
            if (OutOfReach) return;
            howlT -= dt;
            if (howlT <= 0 && howling < 0 && b.State != EnemyState.Stunned)
            {
                howlT = HowlEvery;
                howls++;
                howling = 0;
                howlHp = b.Hp;
                howlOver = b.Overflow;
                lastSchool = b.LastSchool;
                A.Bark(b.X, b.Z, "Old Blue lifts his head to howl.", null);
            }
        }

        /// <summary>Shamed off his rock, he goes up the cut to the next, out of reach behind the Pack.</summary>
        void GiveGround(Enemy b, string rock, int hold, string line)
        {
            var (rx, rz) = A.Place[rock];
            howling = -1;
            broken = howls = 0;
            b.X = rx; b.Z = rz;
            b.Kbx = b.Kbz = 0;
            b.HomeX = rx; b.HomeZ = rz;
            b.HpFloor = b.MaxHp * Holds[hold];
            b.TakenMul = 0;
            b.Disposition = Disposition.Neutral;
            b.Target = -1;
            wave.Clear();
            B.Events.Emit(new Ev.Bark { X = rx, Z = rz, Text = line });
        }

        void InReach(Enemy b, Part next, string title, string sub)
        {
            part = next;
            b.TakenMul = 1;
            b.Disposition = Disposition.Hostile;
            howlT = 2;
            A.Say(title, sub, "boon");
        }

        /// <summary>The yearlings run a ring round her (the ring verb): eight and the tier, nine metres out.</summary>
        void Ring()
        {
            var p = B.Player;
            int n = 8 + A.Tier;
            for (int k = 0; k < n; k++)
            {
                double a = k * Math.PI * 2 / n;
                foreach (var e in A.Group("wolf_runner", 1, p.X + Math.Cos(a) * 9, p.Z + Math.Sin(a) * 9, 0.5)) wave.Add((e, e.Seed));
            }
            A.Say("They run a ring round you", "Break it, and go through", "danger");
        }

        public override BossBar? Bar => !Up(blue, blueSeed) ? null
            : part == Part.Ring ? new BossBar("The ring", "Old Blue is out of reach until it breaks", Need - Got, Math.Max(1, Need), Shielded: true, IsBoss: false)
            : part == Part.Rush ? new BossBar("The rush", "Old Blue is out of reach until it breaks", Need - Got, Math.Max(1, Need), Shielded: true, IsBoss: false)
            : new BossBar(blue!.Def.Name, part == Part.HeadRock ? "Nowhere left to go: silence him" : "Break his howls, and he gives ground", blue.Hp, blue.MaxHp,
                part == Part.HeadRock ? null : [Holds[part == Part.LowRock ? 0 : 1]], howling >= 0 ? ("The howl: break it!", howling / HowlFor) : null, IsBoss: false);
    }

    /* ---------------------------------------------------------- the sick water -- */

    /// <summary>Light the two deadfalls on the far bank. The first light wakes the reeds: the sick come
    /// out of them at her seven times, on the reeds' own time, and a fed fire's light is the room she
    /// has (it burns twenty seconds, and she feeds it by standing at it). With the fourth, Greenbelly
    /// wades out of the shallows. It teaches the fires: the ember lights dead wood, the Pack will not
    /// cross its light, and a fire is kept, not lit once.</summary>
    sealed class SickWater : StoryBeat
    {
        public override string Goal =>
            Lit == 0 ? "Light a deadfall on the far bank"
            : Up(greenbelly, gbSeed) ? "Bring down Greenbelly"
            : Reeding ? $"Keep a fire fed while the reeds empty ({pulses} of {Pulses})"
            : $"Light the deadfalls on the far bank ({Lit} of 2)";
        bool Reeding => pulses < Pulses || PulseLeft > 2;
        public override string? Gate => "water";
        public override double Minute => 6;
        public override string Start => "water_in";
        public override (string Def, double Weight)[] Crowd => [("wolf_blighted", 1), ("wolf", 4), ("boar", 1)];
        public override int CrowdAlive => 20;
        public override int CrowdPool => 650;
        public override string[] CrowdFrom => ["reeds_w", "reeds_s", "reeds_n"];
        public override int EmberFloor => 20;
        /// <summary>The reeds empty seven times, one every seventeen seconds from the first light.</summary>
        const int Pulses = 7;
        const double PulseEvery = 17;
        Enemy? greenbelly;
        double gbSeed, pulseT;
        int pulses;
        readonly List<(Enemy E, double Seed)> pulse = new();
        int PulseLeft => pulse.Count(w => Up(w.E, w.Seed));
        readonly List<GroundZone> shallows = new();
        Deadfall[] fires = [];
        int Lit => fires.Count(f => f.EverLit);

        protected override void Open()
        {
            fires = A.Fires.Where(f => f.Id is "fire:a" or "fire:b").ToArray();
            foreach (var (pt, r) in new[] { ("shallow_a", 3.5), ("shallow_b", 2.6) })
            {
                var (x, z) = A.Place[pt];
                // Slurry underfoot: it slows (Tick), and stings: a twelfth of a blighted wolf's bite a
                // second. A lesson in where to put her feet, not a death in the water.
                double dps = Enemies.Get("wolf_blighted").Damage * Enemies.ScaleFor(A.Level).Damage * A.Teeth / 12;
                var zn = B.SpawnZone(Side.Enemy, x, z, r, 9999, dps, School.Nature);
                if (zn != null) { zn.Tags = [Tag.Zone, Tag.Nature]; shallows.Add(zn); }
            }
            Reeds(2);
            Reeds(2);
        }

        List<Enemy> Reeds(int n, string? at = null, string def = "wolf_blighted")
        {
            var pts = new[] { "reeds_w", "reeds_s", "reeds_n" };
            var (x, z) = A.Place[at ?? pts[(int)(A.R() * pts.Length)]];
            return A.Group(def, n, x, z, 2.5);
        }

        /// <summary>The reeds empty at her: the sick from two of the reed beds at once.</summary>
        void Pulse()
        {
            pulses++;
            pulseT = PulseEvery;
            var pts = new[] { "reeds_w", "reeds_s", "reeds_n" };
            int skip = (int)(A.R() * 3);
            // Every other time, one bed gives up the sick (they burst), the other the whole: a lesson, not a minefield.
            bool sick = pulses % 2 == 1;
            int each = (5 + A.Tier + 1) / 2;
            for (int k = 0; k < 3; k++)
                if (k != skip)
                {
                    foreach (var e in Reeds(each, pts[k], sick ? "wolf_blighted" : "wolf")) pulse.Add((e, e.Seed));
                    sick = false;
                }
            A.Bark(B.Player.X, B.Player.Z + 2, pulses == 1 ? "The reeds stir, and the sick come out of them at you." : "The reeds stir again.", null);
            // With the fourth, the mother of them wades out of the shallows.
            if (pulses == 4 && greenbelly == null)
            {
                var (x, z) = A.Place["shallow_b"];
                A.Bark(x, z, "Out in the shallows, something heavy gets up.", null);
                greenbelly = A.Foe("mb_blight_mother", x, z, 3, "The Pack");
                if (greenbelly != null)
                {
                    gbSeed = greenbelly.Seed;
                    // In her own water her trail is thinner (the stream carries it off): the lesson is
                    // her burst, not ground that kills whoever fights her close.
                    var def = greenbelly.Def.Clone();
                    if (def.Trail is { } tr) def.Trail = tr with { Life = 2, DpsPct = tr.DpsPct * 0.35 };
                    greenbelly.Def = def;
                    // Her bite is not the lesson either: half of it. Her burst (and her litter's) is.
                    greenbelly.Damage *= 0.5;
                }
            }
        }

        protected override void Tick(double dt)
        {
            var p = B.Player;
            // The shallows: slurry underfoot slows as well as stings.
            foreach (var zn in shallows)
                if (zn.Alive && Dist(p.X, p.Z, zn.X, zn.Z) < zn.Radius) B.SlowPlayer(0.6, 0.3);
            // The first light wakes the reeds (or her waiting long enough at the water's edge); then they
            // empty on their own time.
            if (pulses == 0 && (Lit > 0 || T > 45)) Pulse();
            else if (pulses > 0 && pulses < Pulses && (pulseT -= dt) <= 0) Pulse();
            var unlit = fires.Where(f => !f.EverLit).OrderBy(f => Dist(f.X, f.Z, p.X, p.Z)).FirstOrDefault();
            // While the reeds empty, the stage asks her to keep a fire: the nearest going out.
            var feed = fires.Where(f => f.EverLit && f.Lit < 5).OrderBy(f => Dist(f.X, f.Z, p.X, p.Z)).FirstOrDefault();
            A.Goal = Lit == 0 ? (unlit!.X, unlit.Z)
                : Reeding && feed != null && !fires.Any(f => f.Lit >= 5) ? (feed.X, feed.Z)
                : Up(greenbelly, gbSeed) ? (greenbelly!.X, greenbelly.Z)
                : unlit != null ? (unlit.X, unlit.Z)
                : null;
            if (Lit == fires.Length && !Reeding && greenbelly != null && !Up(greenbelly, gbSeed)) Done = true;
        }

        public override void End()
        {
            foreach (var zn in shallows) if (zn.Alive) B.Zones.Release(zn);
            shallows.Clear();
        }

        public override BossBar? Bar => Up(greenbelly, gbSeed)
            ? new BossBar(greenbelly!.Def.Name, greenbelly.Def.Lesson, greenbelly.Hp, greenbelly.MaxHp, IsBoss: false)
            : pulses > 0 && Reeding ? new BossBar("The reeds", "The sick will not cross a fed fire's light", PulseLeft, Math.Max(1, pulse.Count), IsBoss: false)
            : null;
    }

    /* --------------------------------------------------------------- the drive -- */

    /// <summary>Whitethroat runs the drive at the den's mouth: the Pack closes in a crescent on one side
    /// and she runs the gap it leaves. Go through the wolves, never the gap. Her yearlings take the
    /// blows for her while she drives; when her run misses she stands panting, open, and that is when
    /// she is hurt. Hurt to half, the whole Pack wheels: wider crescents, and quicker. It teaches the
    /// ring, and that a wolf who misses is open (his age, at the boss).</summary>
    sealed class Drive : StoryBeat
    {
        public override string Goal => Ringed ? $"Break the yearlings' ring ({yearlings.Count - YearlingsUp} of {yearlings.Count - 1})" : "Bring down Whitethroat";
        public override double Minute => 10;
        public override string Start => "den_in";
        public override (string Def, double Weight)[] Crowd => [("wolf", 4), ("wolf_runner", 2), ("wolf_blighted", 1), ("boar", 1)];
        public override int CrowdAlive => 20;
        public override int CrowdPool => 650;
        public override string[] CrowdFrom => ["den_w", "den_e", "den_n"];
        public override int EmberFloor => 28;
        Enemy? white;
        double whiteSeed, driveT = 5, runT = -1, pantT;
        double laneX0, laneZ0, laneX1, laneZ1;
        Battle.EnemyBlow? lane;
        bool hit, wheeled, missedOnce, hitOnce, spent;
        int drives;
        /// <summary>How long a drive's lane is marked before she runs it (the first, longer: a lesson).</summary>
        double mark = 1.0;
        /// <summary>Her drives are numbered: after this many she has nothing left to run with, and her guard
        /// is gone (the stage is bounded by her drives, so hands that run into the gap are hurt, not held).</summary>
        const int Drives = 7;
        /// <summary>Her yearlings take blows for her while she runs her drive: she is open when she misses.</summary>
        const double Guarded = 0.08, Opened = 2.0, Pant = 2.5;
        /// <summary>Her drive's lane, over her bite: the gap is hers, and caught in it is a wound. (At 4.5 her
        /// fists did eight times the drive's harm; with a named foe's fists slowed, the stage hurt no one.)</summary>
        const double DriveTeeth = 7;

        protected override void Open()
        {
            var (x, z) = A.Place["den"];
            // She lives through her seven drives: a practised reader made her miss, and her pants (twice taken) ended
            // the stage in under a minute, three drives short (the experience director's 1:40 drive at the screen).
            white = A.Foe("mb_whitethroat", x, z + 6, 12, "The Pack");
            // Her teeth between drives are not the lesson: the drive is (its lane keeps its weight).
            if (white != null) white.Damage *= 0.35;
            if (white != null)
            {
                whiteSeed = white.Seed;
                white.Scripted = true;
                A.Script(white, Run);
            }
            A.Group("wolf", 4, x, z + 2, 3);
        }

        /// <summary>Her run down the gap, and the pant after a miss: true while the drive moves her. (The
        /// pant's clock and her guard are the stage's, kept in Tick: a creature held by frost or a stun
        /// does not think, and a pant must not last as long as a stun-lock.)</summary>
        bool Run(Enemy e, double dt)
        {
            // The first drive's lesson is said while she crouches across from her, before its lane is marked.
            if (sayT > 0)
            {
                e.Vx = e.Vz = 0;
                e.State = EnemyState.Windup;
                e.Anim = EnemyAnim.Windup;
                e.Facing = Math.Atan2(B.Player.Z - e.Z, B.Player.X - e.X);
                return true;
            }
            if (pantT > 0)
            {
                e.Vx = e.Vz = 0;
                e.State = EnemyState.Recover;
                e.Anim = EnemyAnim.Idle;
                return true;
            }
            if (runT < 0) return false;
            runT += dt;
            if (runT < mark)
            {
                // Waiting across the gap, marked.
                e.Vx = e.Vz = 0;
                e.State = EnemyState.Windup;
                e.Anim = EnemyAnim.Windup;
                e.Facing = Math.Atan2(laneZ1 - laneZ0, laneX1 - laneX0);
                return true;
            }
            double k = Math.Min(1, (runT - mark) / 0.45);
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
                    pantT = Pant;
                    B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = e.X, Z = e.Z, Radius = 2.4, Delay = Pant, From = e, Label = "She missed" });
                    if (!missedOnce)
                    {
                        missedOnce = true;
                        A.Bark(e.X, e.Z, "She misses, and stands with her head down, blowing.", null);
                        A.Say("She is open", "Hit her while she blows", "boon");
                    }
                }
                else if (!hitOnce) { hitOnce = true; A.Say("The gap is hers", "Through the wolves, never the gap", "danger"); }
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
            int n = (wheeled ? 9 : 6) + A.Tier;
            double arc = wheeled ? 1.4 : 1.1;
            for (int k = 0; k < n; k++)
            {
                double a = away + (k / (double)Math.Max(1, n - 1) - 0.5) * Math.PI * arc;
                A.Group("wolf", 1, p.X + Math.Cos(a) * 10, p.Z + Math.Sin(a) * 10, 0.4);
            }
            // The first is a lesson: said first, alone, while she crouches (a second to read it before anything
            // moves), then marked longer. The words and the lane at once were four things to read in 1.7 s.
            if (drives++ == 0)
            {
                A.Say("The drive", "Out of her line, into the wolves", "danger");
                sayT = 1.0;
                return;
            }
            A.Bark(w.X, w.Z, "A rising howl: the Pack wheels.", null);
            Mark(1.0);
        }

        /// <summary>A second's lesson before the first drive's lane (0: none waiting).</summary>
        double sayT;

        /// <summary>Her lane, aimed at her now, and her run down it after `seconds`.</summary>
        void Mark(double seconds)
        {
            var p = B.Player;
            var w = white!;
            mark = seconds;
            double dx = p.X - w.X, dz = p.Z - w.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
            double len = Math.Min(18, d + 6);
            // Her run ends inside the place: run out past its wall, she stood outside it out of reach, and the
            // stage never ended (one night in thirty, in the harness).
            while (len > 3 && !A.Place.Inside(w.X + dx / d * len, w.Z + dz / d * len, 1.5)) len -= 0.5;
            laneX0 = w.X; laneZ0 = w.Z; laneX1 = w.X + dx / d * len; laneZ1 = w.Z + dz / d * len;
            hit = false;
            lane = B.Blow(new Battle.EnemyBlow
            {
                Shape = TelegraphShape.Line, X = laneX0, Z = laneZ0, X1 = laneX1, Z1 = laneZ1, Width = 2.4, Delay = mark,
                Damage = w.Damage * DriveTeeth, Source = w.Def.Name, From = w, Label = "The drive",
            });
            // Missed if she is out of the lane when it lands (a dash through it is a miss as well).
            var marked = lane;
            lane.After = bb => hit = marked.Hit(bb.Player.X, bb.Player.Z, bb.Player.Radius) && bb.Player.HurtT > 0.25;
            runT = 0;
        }

        /// <summary>Near her end she calls her yearlings round her (the ring again, closer): out of reach
        /// behind them until it is broken.</summary>
        readonly List<(Enemy E, double Seed)> yearlings = new();
        bool called;
        int YearlingsUp => yearlings.Count(y => Up(y.E, y.Seed));
        bool Ringed => called && YearlingsUp > 1;

        protected override void Tick(double dt)
        {
            if (!Up(this.white, whiteSeed) || this.white is not { } white) { Done = true; return; }
            if (sayT > 0 && (sayT -= dt) <= 0) Mark(1.7);
            if (!called && white.Hp < white.MaxHp * 0.25 && runT < 0 && pantT <= 0 && sayT <= 0)
            {
                called = true;
                var p = B.Player;
                int n = 6 + A.Tier;
                for (int k = 0; k < n; k++)
                {
                    double a = k * Math.PI * 2 / n;
                    foreach (var e in A.Group("wolf_runner", 1, p.X + Math.Cos(a) * 8, p.Z + Math.Sin(a) * 8, 0.5)) yearlings.Add((e, e.Seed));
                }
                white.Disposition = Disposition.Neutral;
                white.Target = -1;
                A.Bark(white.X, white.Z, "Whitethroat yips, and her yearlings come round you in a ring.", null);
                A.Say("The yearlings ring you", "Whitethroat is behind them: break the ring", "danger");
            }
            if (called && !Ringed && white!.Disposition == Disposition.Neutral)
            {
                white.Disposition = Disposition.Hostile;
                driveT = Math.Min(driveT, 1.5);
                A.Say("The yearlings scatter", "Whitethroat is in reach again", "boon");
            }
            A.Goal = Ringed ? null : (white!.X, white.Z);
            if (pantT > 0 && (pantT -= dt) <= 0 && white.State == EnemyState.Recover) white.State = EnemyState.Active;
            if (!spent && drives >= Drives && runT < 0 && pantT <= 0 && sayT <= 0)
            {
                spent = true;
                A.Say("Whitethroat is spent", "She has nothing left to run with", "boon");
            }
            white.TakenMul = Ringed ? 0 : pantT > 0 ? Opened : spent ? 1.25 : Guarded;
            if (Ringed) return;
            if (!wheeled && white.Hp < white.MaxHp * 0.5)
            {
                wheeled = true;
                driveT = Math.Min(driveT, 2);
                A.Say("The whole Pack wheels", "Wider and quicker: still through the wolves, never the gap", "danger");
            }
            driveT -= dt;
            if (!spent && driveT <= 0 && runT < 0 && pantT <= 0 && sayT <= 0)
            {
                driveT = wheeled ? 9 : 11;
                Drive_();
            }
        }

        public override BossBar? Bar => Up(white, whiteSeed)
            ? Ringed ? new BossBar("The yearlings", "Whitethroat is out of reach until it breaks", YearlingsUp - 1, Math.Max(1, yearlings.Count - 1), Shielded: true, IsBoss: false)
            : new BossBar(white!.Def.Name, "Go through the wolves, never the gap", white.Hp, white.MaxHp, IsBoss: false)
            : null;
    }
}

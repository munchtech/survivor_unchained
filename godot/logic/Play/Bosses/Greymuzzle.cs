using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>
/// Greymuzzle in his own Hollow (docs/design/STORY_BOSSES.md 1): an old wolf
/// in his own house. The Pack is his walls, the cold his weapon, his age his
/// only opening.
///
///   the ring     about twenty of the Pack stand shoulder to shoulder round
///                the den floor, never a target; touched, a wolf snaps and
///                shoves her back in. A lit deadfall bows the ring out round
///                its light: fires are room.
///   the old way  he circles and lunges; after every second lunge he stands
///                and pants, open (a pale-blue ring), and the ring bites
///   the moon     at the den's mouth behind a guard, he howls: the cold
///                closes in from the ring, his dead run lanes across her, and
///                only a fire's light is clear. Hurt him, stagger him or burn
///                him to stop it.
///   on his feet  no more howls: a shake, chains of three lunges, and at the
///                last the ring breaks and comes in
///   the end      down on his side; let go if she promised and chooses to,
///                or dead
/// He is wordless: what is heard is the Pack.
/// </summary>
public sealed class Greymuzzle : StoryBoss, IBound
{
    public Greymuzzle(IStoryArena a) : base(a) { }

    protected override Phase[] Phases { get; } =
    [
        new("The Old Way", 0.65, 25, 75),
        new("The Moon", 0.30, 30, 75),
        new("On His Feet", 0, 25, 0),
    ];
    public override School Weakness => School.Fire;
    public override string WeaknessText => "Fire breaks his moon-howl, and the Pack will not cross a fed fire's light";
    protected override string HardName => "The Long Hunt";
    protected override string HardSub => "The light goes, and he hunts you in the dark";
    protected override (string Title, string Sub) SoftWords(Enemy e) => ("The ring draws in", "It bites quicker now");
    public override string ReEntry => "The ring forms again, and the old wolf walks out through it.";
    // The table's Pack-Mother is 41 + 6.8 a tier against a thirtieth-minute build in about 85 s. Here
    // the build is a table's twelfth minute and the fight three to four minutes, his time at the den
    // with it. The same at every tier: his level grows him, and the night eases the tiers (TierEase, BossEase).
    public override double HealthMul(int tier) => 100;
    // His teeth are in his marked moves and not a brawl (Stalk), so each must mean it: a lunge about a third of
    // her calling's own health, the hamstring's lunge after it given time to be walked out of lamed.
    public override double Teeth => 0.38;
    protected override bool DiesAtZero => false;

    /// <summary>The den floor's middle, and the den's mouth (the place's points).</summary>
    (double X, double Z) C => S.Place["den"];
    (double X, double Z) Mouth => S.Place["den_mouth"];
    /// <summary>In front of the den's mouth, where he stands to howl: out far enough that his flanks are open
    /// ground (2.2 m out, behind a guard 4 m out, they were a metre's pocket against the ring, and a blade
    /// never reached him in the Moon: it ran to its ceiling, and left On His Feet twice as long).</summary>
    (double X, double Z) Porch
    {
        get
        {
            var (mx, mz) = Mouth;
            var (cx, cz) = C;
            double d = Math.Max(0.1, Dist(mx, mz, cx, cz));
            return (mx + (cx - mx) / d * PorchOut, mz + (cz - mz) / d * PorchOut);
        }
    }

    /// <summary>How far out of the mouth he stands at the den, and how far before him his guard stands.</summary>
    const double PorchOut = 3.5, GuardOut = 2.4;

    /* ------------------------------------------------------------ the ring -- */

    sealed class Wolf
    {
        public required Enemy E;
        public double Seed, Angle;
        /// <summary>Running a lane (the ring's bite): where from, where to, how far along.</summary>
        public double FromX, FromZ, ToX, ToZ, RunT = -1;
    }
    readonly List<Wolf> ring = new(), guard = new();
    /// <summary>The ring's wolves once it has broken and come in: ordinary wolves, but still his Pack.</summary>
    readonly List<(Enemy E, double Seed)> loose = new();
    double ringR = 12, biteT = 9, shoveT, biteGrace, frostR = 99, frostDrawT, ringDrawT;
    /// <summary>The dashes its edge is drawn in.</summary>
    const int RingMarks = 36;
    bool ringBroken, longHunt, lyingDown;
    int lunges;
    double lungeT = 4, hamT = 3, howlT, sortieT, shakeT = 2, chainT = 3, turnT = 10, howlHp;
    /// <summary>The first moon-howl of the Moon cannot be stopped: the moon clears, and the fires are
    /// what she has (the sick water taught them). Those after can be broken.</summary>
    bool moonCleared;
    bool atDen;

    /// <summary>Shoulder to shoulder as near as a crowd allows (twenty stood four metres apart).</summary>
    public const int RingWolves = 30;
    /// <summary>The ring's reach round a fed fire: its light and a metre (two more with the bane).</summary>
    double FireRoom => Bane ? 7 : 1;
    bool Bane => S.Fact("bane.fires");

    /// <summary>How far out the ring stands on a bearing from the den floor's middle: its radius, bowed
    /// out round every fed fire's light, and open (to the wall) before the den while he holds it.</summary>
    public double RingAt(double angle)
    {
        double r = ringR;
        if (atDen && PhaseIx == 1)
        {
            double ma = Math.Atan2(Mouth.Z - C.Z, Mouth.X - C.X);
            if (Math.Abs(Wrap(angle - ma)) < 0.75) return ringR + 3;
        }
        foreach (var f in S.Fires)
        {
            if (!f.Burning) continue;
            double df = Dist(f.X, f.Z, C.X, C.Z), fa = Math.Atan2(f.Z - C.Z, f.X - C.X), da = Wrap(angle - fa);
            if (Math.Abs(da) >= Math.PI / 2) continue;
            double room = f.Reach + FireRoom, off = df * Math.Abs(Math.Sin(da));
            if (off < room) r = Math.Max(r, df * Math.Cos(da) + Math.Sqrt(room * room - off * off));
        }
        return r;
    }

    void MakeRing()
    {
        var lvl = S.Level;
        for (int k = 0; k < RingWolves; k++)
        {
            double a = k * Math.PI * 2 / RingWolves;
            var e = B.SpawnEnemy("wolf", C.X + Math.Cos(a) * ringR, C.Z + Math.Sin(a) * ringR,
                new Battle.SpawnOpts { Level = lvl, Disposition = Disposition.Neutral, Faction = Faction.Pack, Style = SpawnStyle.Walk });
            if (e == null) continue;
            var w = new Wolf { E = e, Seed = e.Seed, Angle = a };
            ring.Add(w);
            e.Scripted = true;
            S.Script(e, (_, dt) => Keep(w, dt));
        }
    }

    /// <summary>A wolf of the ring (or the guard) at its place: never a target, never hurt.</summary>
    bool Keep(Wolf w, double dt)
    {
        var e = w.E;
        e.Provoked = false;
        e.Hp = e.MaxHp;
        e.Disposition = Disposition.Neutral;
        double tx, tz;
        if (w.RunT >= 0)
        {
            w.RunT += dt;
            double k = Math.Min(1, w.RunT / 0.45);
            tx = w.FromX + (w.ToX - w.FromX) * k; tz = w.FromZ + (w.ToZ - w.FromZ) * k;
            if (w.RunT > 1.4) w.RunT = -1;
            e.X = tx; e.Z = tz;
            e.Facing = Math.Atan2(w.ToZ - w.FromZ, w.ToX - w.FromX);
            e.Anim = EnemyAnim.Move;
            return true;
        }
        if (guard.Contains(w)) { tx = w.FromX; tz = w.FromZ; }
        else
        {
            double r = lyingDown ? RingAt(w.Angle) : RingAt(w.Angle) + 0.4;
            tx = C.X + Math.Cos(w.Angle) * r; tz = C.Z + Math.Sin(w.Angle) * r;
        }
        double dx = tx - e.X, dz = tz - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
        double step = Math.Min(d, 5.5 * dt);
        if (d > 0.05) { e.X += dx / d * step; e.Z += dz / d * step; }
        e.Vx = e.Vz = 0;
        e.Facing = Math.Atan2(C.Z - e.Z, C.X - e.X);
        e.Anim = d > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
        e.State = lyingDown ? EnemyState.Idle : EnemyState.Active;
        return true;
    }

    bool Here(Wolf w) => w.E.Alive && w.E.Seed == w.Seed && w.E.State != EnemyState.Dying;

    /* ---------------------------------------------------------- each step -- */

    public override void Step(double dt)
    {
        if (E == null || ringBroken) return;
        ring.RemoveAll(w => !Here(w));
        guard.RemoveAll(w => !Here(w));
        var p = B.Player;
        shoveT -= dt;
        // The ring holds her in: past it, a wolf snaps and shoves her back.
        double pd = Dist(p.X, p.Z, C.X, C.Z), pa = Math.Atan2(p.Z - C.Z, p.X - C.X);
        if (!lyingDown && pd > RingAt(pa) - 0.8 && shoveT <= 0)
        {
            shoveT = 0.6;
            // A snap, then a warning: pressed against the ring she is shoved, but bitten only now and then.
            B.ShovePlayer(C.X - p.X, C.Z - p.Z, 2.5, biteGrace <= 0 ? E.Damage * 0.3 : 0, "the Pack");
            if (biteGrace <= 0) biteGrace = 2;
            S.Bark(p.X, p.Z, "A wolf of the ring snaps, and shoves you back in.", null);
        }
        // The guard before the den: inside two metres, shoved back onto the den floor (never into the ring).
        foreach (var w in guard)
            if (shoveT <= 0 && Dist(p.X, p.Z, w.E.X, w.E.Z) < 2)
            {
                shoveT = 0.6;
                B.ShovePlayer(C.X - p.X, C.Z - p.Z, 3, biteGrace <= 0 ? E.Damage * 0.3 : 0, "the Pack");
                if (biteGrace <= 0) biteGrace = 2;
            }
        biteGrace -= dt;
        // The ring's edge on the ground, where a step further is a shove: a pale line round the den floor that
        // bows out round every fed fire. Seen at the screen, twenty wolves twelve metres out read as a scatter
        // of wolves at the picture's edges, not as a wall.
        if (!lyingDown && (ringDrawT -= dt) <= 0)
        {
            ringDrawT = 0.5;
            for (int k = 0; k < RingMarks; k++)
            {
                double a0 = k * Math.PI * 2 / RingMarks, a1 = (k + 0.62) * Math.PI * 2 / RingMarks;
                double r0 = RingAt(a0) - 0.8, r1 = RingAt(a1) - 0.8;
                B.Events.Emit(new Ev.Telegraph { Id = 882000 + k, Shape = TelegraphShape.Line, Kind = TelegraphKind.Wall,
                    X = C.X + Math.Cos(a0) * r0, Z = C.Z + Math.Sin(a0) * r0, X1 = C.X + Math.Cos(a1) * r1, Z1 = C.Z + Math.Sin(a1) * r1,
                    Width = 0.3, Duration = 0.6, Hostile = true });
            }
        }
        // The cold: while he howls it closes in from the ring, and only a fed fire's light is clear.
        if (Channel != null && PhaseIx == 1)
        {
            frostR = Math.Max(0, frostR - 1.2 * dt);
            bool lit = S.Fires.Any(f => f.InLight(p.X, p.Z));
            if (pd > frostR && !lit)
            {
                // The moon cleared bites in earnest: there is no stopping it, only the fires.
                B.HurtByGround(E.Damage * (unbreakable ? 0.45 : 0.15) * dt, School.Frost, dt, "the cold");
                B.SlowPlayer(0.7, 0.3);
            }
            if ((frostDrawT -= dt) <= 0)
            {
                frostDrawT = 0.5;
                B.Events.Emit(new Ev.Telegraph { Id = 880000 + E.Id, Shape = TelegraphShape.Ring, Kind = TelegraphKind.Ground, X = C.X, Z = C.Z, Inner = frostR, Radius = ringR + 3, Duration = 0.6, Hostile = true, Boss = true });
            }
        }
        else frostR = ringR + 3;
    }

    /* ------------------------------------------------------------ his moves -- */

    protected override void Enter(int phase)
    {
        switch (phase)
        {
            case 0:
                if (ring.Count == 0) MakeRing();
                E.Speed *= 4.6 / 5.4;
                break;
            case 1:
                howlT = 1.5;
                sortieT = 99;
                atDen = false;
                DashTo(Porch.X, Porch.Z, 1.6, () => { atDen = true; Guard(); });
                break;
            case 2:
                // The guard goes back into the ring; the ring closes.
                foreach (var w in guard) { w.Angle = Math.Atan2(w.E.Z - C.Z, w.E.X - C.X); ring.Add(w); }
                guard.Clear();
                atDen = false;
                ringR = Soft ? 7 : 9;
                shakeT = 2; chainT = 3;
                break;
        }
    }

    /// <summary>Five of the Pack shoulder to shoulder in a short arc before him, open at both ends: his front is
    /// walled, his flanks are a blade's way in.</summary>
    void Guard()
    {
        var (px, pz) = Porch;
        double toC = Math.Atan2(C.Z - pz, C.X - px);
        for (int k = 0; k < 5; k++)
        {
            double a = toC + (k - 2) * 0.3;
            double x = px + Math.Cos(a) * GuardOut, z = pz + Math.Sin(a) * GuardOut;
            var e = B.SpawnEnemy("wolf", x, z, new Battle.SpawnOpts { Level = S.Level, Disposition = Disposition.Neutral, Faction = Faction.Pack, Style = SpawnStyle.Walk });
            if (e == null) continue;
            var w = new Wolf { E = e, Seed = e.Seed, FromX = x, FromZ = z, Angle = a };
            guard.Add(w);
            e.Scripted = true;
            S.Script(e, (_, dt) => Keep(w, dt));
        }
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (lyingDown) return Lying(e, dt);
        if (Spent(e)) { LieDown(e); return true; }
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        lungeT -= dt; hamT -= dt; biteT -= dt; howlT -= dt; sortieT -= dt; shakeT -= dt; chainT -= dt; turnT -= dt;
        if (!ringBroken && biteT <= 0 && PhaseIx < 2) { biteT = (Soft ? 5 : 9) * Cadence; Bite(); }
        // The Pack's turn: the ring wheels and three of it cut across her, one after another.
        if (!ringBroken && turnT <= 0 && PhaseIx != 1) { turnT = TurnEvery * Cadence; Turn(); }
        switch (PhaseIx)
        {
            case 0:
                if (lungeT <= 0) { lungeT = (Hard ? 3 : 4.5) * Cadence; Lunge(); return true; }
                if (d < 5 && hamT <= 0) { hamT = 5 * Cadence; Hamstring(); return true; }
                return Stalk(e, dt, dx, dz, d);
            case 1:
                if (!atDen) return true;
                if (howlT <= 0) { howlT = 22 * Cadence; Howl(e); return true; }
                if (sortieT <= 0) { sortieT = 99; Sortie(2); return true; }
                // At the den, between howls, he stands his ground.
                e.Vx = e.Vz = 0;
                e.Facing = Math.Atan2(dz, dx);
                return true;
            default:
                if (!ringBroken && e.Hp < e.MaxHp * 0.15) BreakRing();
                // The shake is his heaviest blow, so it is marked as one (1.2 s: SURVIVORS_BOSSES.md 0.9).
                if (d < 5.5 && shakeT <= 0) { shakeT = 6 * Cadence; Hold(1.2); Cone(5, 120, 1.2, 1.8, "Shake"); return true; }
                if (chainT <= 0) { chainT = (Hard ? 3 : 8) * Cadence; Chain(3, () => Pant(3)); return true; }
                return Stalk(e, dt, dx, dz, d);
        }
    }

    double side = 1, sideT;

    /// <summary>Between his moves he circles her at seven to nine metres, limping: an old wolf keeps a
    /// young one at the end of his reach and goes in only when he means it (a marked move). Pressed
    /// close, he breaks off round her; walked into across his path, he snaps (StoryBoss.Cuff).</summary>
    bool Stalk(Enemy e, double dt, double dx, double dz, double d)
    {
        if ((sideT -= dt) <= 0) { sideT = 3 + S.R() * 3; side = S.R() < 0.5 ? -1 : 1; }
        double radial = Math.Clamp((d - 8) / 2, -1, 1);
        double vx = dx * radial - dz * side * 0.8, vz = dz * radial + dx * side * 0.8;
        double vl = Math.Max(1e-6, Math.Sqrt(vx * vx + vz * vz)), sp = e.Speed * 0.75;
        double nx = e.X + vx / vl * sp * dt, nz = e.Z + vz / vl * sp * dt;
        // The ring is his wall too: he slips along it, not into it; only cornered (with nowhere along it to
        // go) does he turn on her. (Stopped dead at it, a blade that followed him there pinned him, and was
        // snapped at every second and a half.)
        bool backed = !Inside(nx, nz, 1.6);
        if (backed)
        {
            double rx = e.X - C.X, rz = e.Z - C.Z, rl = Math.Max(0.01, Math.Sqrt(rx * rx + rz * rz));
            double tx = -rz / rl, tz = rx / rl;
            if (tx * dx + tz * dz > 0) { tx = -tx; tz = -tz; }
            // Along it, and a little in off it, so the slip does not carry him out onto it (more, if a body
            // pressed against him has already put him there).
            double lean = Inside(e.X, e.Z, 1.6) ? 0.3 : 1;
            tx -= rx / rl * lean; tz -= rz / rl * lean;
            double tl = Math.Sqrt(tx * tx + tz * tz);
            tx /= tl; tz /= tl;
            double sx = e.X + tx * sp * dt, sz = e.Z + tz * sp * dt;
            if (Inside(sx, sz, 1.6) || Dist(sx, sz, C.X, C.Z) < rl) { vx = tx; vz = tz; vl = 1; nx = sx; nz = sz; backed = false; }
            else { side = -side; sideT = 2; nx = e.X; nz = e.Z; }
        }
        e.X = nx; e.Z = nz;
        B.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
        e.Vx = vx / vl * sp; e.Vz = vz / vl * sp;
        e.State = EnemyState.Active;
        e.Anim = EnemyAnim.Move;
        Cuff(e, dt, vx, vz, dx, dz, d, backed, 0.3, 1.5);
        return true;
    }

    /// <summary>How often the ring turns (it does not while he holds the den).</summary>
    const double TurnEvery = 13;

    /// <summary>The Pack's turn: a growl goes round the ring, and three of it cut across her from three
    /// sides, a breath apart, each in a marked lane. The ground between the lanes is the answer, and it
    /// moves as each one lands.</summary>
    void Turn()
    {
        var p = B.Player;
        var free = ring.Where(r => r.RunT < 0).ToList();
        if (free.Count < 3) return;
        double a0 = S.R() * Math.PI * 2;
        S.Bark(p.X, p.Z, "A growl goes round the ring. The Pack turns.", null);
        for (int k = 0; k < 3; k++)
        {
            double a = a0 + k * Math.PI * 2 / 3;
            var w = free.OrderBy(r => Math.Abs(Wrap(Math.Atan2(r.E.Z - p.Z, r.E.X - p.X) - a))).First();
            free.Remove(w);
            double dx = p.X - w.E.X, dz = p.Z - w.E.Z, dl = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
            double len = Math.Min(20, dl + 5);
            double fx = w.E.X, fz = w.E.Z, x1 = fx + dx / dl * len, z1 = fz + dz / dl * len;
            var b = B.Blow(new Battle.EnemyBlow
            {
                Shape = TelegraphShape.Line, X = fx, Z = fz, X1 = x1, Z1 = z1, Width = 1.8, Delay = 1.1 + k * 0.4, Damage = E.Damage * 1.5,
                Source = "the Pack's turn", From = E, Label = "The Pack turns",
            });
            b.After = _ => { w.FromX = fx; w.FromZ = fz; w.ToX = x1; w.ToZ = z1; w.RunT = 0; };
        }
    }

    /// <summary>A lane through her and four metres past; he runs it. Every second one, he pants. On her lamed
    /// he takes his time, and the lane is marked long enough to be limped out of: the hamstring's price is the
    /// lunge's threat, not a second wound she cannot answer (marked as any other, a lamed walk never cleared
    /// it, and one bite cost her half her health).</summary>
    void Lunge()
    {
        var (dx, dz, d) = ToPlayer();
        double len = Math.Min(16, d + 4);
        double x1 = E.X + dx * len, z1 = E.Z + dz * len;
        double mark = B.Player.SlowT > 0 ? LamedMark : 0.9;
        Lane(E.X, E.Z, x1, z1, 2.2, mark, 1.6, "Lunge");
        Hold(mark, () => DashTo(x1, z1, 0.35, () => { if (++lunges % 2 == 0) Pant(2.5); else Hold(Landing); }));
    }

    /// <summary>The lunge's mark on her lamed; and how long he stands where a lunge ends, landed heavy on the
    /// bad leg: a blade's moment at his flank between his pants (he keeps away otherwise, and blade builds
    /// took half again as long to bring him down as bows did).</summary>
    const double LamedMark = 1.4, Landing = 0.6;

    /// <summary>A snap at her legs. It is how an old wolf hunts: lamed, she is his, and his lunge comes
    /// while she is slow (the hamstring answered by staying out of his reach, or by the dash).</summary>
    void Hamstring()
    {
        Hold(0.8);
        var b = Cone(4.2, 70, 0.8, 1.5, "Hamstring");
        b.Slow = 0.55; b.SlowFor = 2;
        b.After = bb => { if (bb.Player.SlowT > 0 && PhaseIx == 0) lungeT = Math.Min(lungeT, 0.5); };
    }

    /// <summary>His age: he stands and pants, his breath thick, open and hurt the more for it.</summary>
    void Pant(double seconds)
    {
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = E.X, Z = E.Z, Radius = 2.6, Delay = seconds, From = E, Label = "His age" });
        Hold(seconds, () => E.TakenMul = 1, _ => { E.TakenMul = 1.25; return true; });
    }

    /// <summary>The ring's bite: the wolf of the ring nearest her runs a lane across, and goes back.</summary>
    void Bite()
    {
        var p = B.Player;
        var w = ring.Where(r => r.RunT < 0).OrderBy(r => Dist(r.E.X, r.E.Z, p.X, p.Z)).FirstOrDefault();
        if (w == null) return;
        double dx = p.X - w.E.X, dz = p.Z - w.E.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
        double len = Math.Min(18, d + 5);
        double x1 = w.E.X + dx / d * len, z1 = w.E.Z + dz / d * len;
        S.Bark(w.E.X, w.E.Z, "A growl behind you.", null);
        var b = B.Blow(new Battle.EnemyBlow
        {
            Shape = TelegraphShape.Line, X = w.E.X, Z = w.E.Z, X1 = x1, Z1 = z1, Width = 1.6, Delay = 1.0, Damage = E.Damage * 1.2,
            Source = "the ring's bite", From = E, Label = "The ring bites",
        });
        double fx = w.E.X, fz = w.E.Z;
        b.After = _ => { w.FromX = fx; w.FromZ = fz; w.ToX = x1; w.ToZ = z1; w.RunT = 0; };
    }

    /// <summary>The moon-howl: the moon clears, the cold comes in from the ring, his dead run lanes.
    /// Damage of 6% of his health in it, a stagger, or one hit of fire stops it.</summary>
    void Howl(Enemy e)
    {
        // The first is the moon clearing: it is not stopped, it is lived through, in a fire's light.
        unbreakable = !moonCleared;
        moonCleared = true;
        Channel = unbreakable ? "The moon clears: into a fire's light!" : "The moon-howl: break it!";
        ChannelProgress = 0;
        howlHp = e.Hp;
        frostR = ringR + 3;
        S.Bark(e.X, e.Z, unbreakable
            ? "He sits back and howls, and the cloud slides off the moon. The cold comes in off the ring."
            : "He sits back and howls at the moon, and the ring howls with him.", null);
        double nextLane = 0.6, every = unbreakable ? 1.5 : 2;
        Hold(8, () => { Channel = null; unbreakable = false; sortieT = 2.5; }, t =>
        {
            ChannelProgress = t / 8;
            if (!unbreakable && howlHp - E.Hp >= E.MaxHp * 0.06) { BreakChannel(E, "Hurt enough to stop"); sortieT = 3.5; return false; }
            if (t >= nextLane)
            {
                nextLane += every;
                DeadRun();
            }
            return true;
        });
    }

    bool unbreakable;

    public override void OnHit(Enemy e, School school, double dmg) { if (!unbreakable) base.OnHit(e, school, dmg); }
    public override void OnStagger(Enemy e) { if (!unbreakable) base.OnStagger(e); }

    /// <summary>One of his dead runs a lane across her (never through a fed fire's light: they swerve).</summary>
    void DeadRun()
    {
        var p = B.Player;
        for (int tries = 0; tries < 8; tries++)
        {
            double a = S.R() * Math.PI * 2;
            double x0 = p.X + Math.Cos(a) * 12, z0 = p.Z + Math.Sin(a) * 12, x1 = p.X - Math.Cos(a) * 12, z1 = p.Z - Math.Sin(a) * 12;
            if (S.Fires.Any(f => f.Burning && SegDist(f.X, f.Z, x0, z0, x1, z1) < f.Reach)) continue;
            Lane(x0, z0, x1, z1, 1.8, 1.2, 1.5, "His dead run", School.Frost);
            return;
        }
    }

    /// <summary>Out from the den: lunges at her, then back to the porch, and he pants.</summary>
    void Sortie(int n)
    {
        atDen = false;
        Chain(n, () => DashTo(Porch.X, Porch.Z, 1.4, () => { atDen = true; Pant(2.5); }));
    }

    /// <summary>Lunges in a chain, the later ones aimed where she is going.</summary>
    void Chain(int n, Action? then = null)
    {
        if (n <= 0) { then?.Invoke(); return; }
        var p = B.Player;
        double lead = n >= 3 ? 0 : 0.6;
        double tx = p.X + p.Vx * lead, tz = p.Z + p.Vz * lead;
        double dx = tx - E.X, dz = tz - E.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
        double len = Math.Min(14, d + 3);
        double x1 = E.X + dx / d * len, z1 = E.Z + dz / d * len;
        // On his feet the old way is wider: he has nothing left to save it for. (Not quicker: a single blow is
        // never marked under 0.8 s, SURVIVORS_BOSSES.md 0.9, and his chain at 0.7 could not be walked.)
        double mark = 0.8, width = PhaseIx == 2 ? 2.6 : 2.2;
        Lane(E.X, E.Z, x1, z1, width, mark, 1.6, "Lunge");
        Hold(mark, () => DashTo(x1, z1, 0.35, () => Chain(n - 1, then)));
    }

    /// <summary>The last of the Pack: the ring breaks and comes in, ordinary wolves now.</summary>
    void BreakRing()
    {
        ringBroken = true;
        S.Say("The last of the Pack", "The ring breaks and comes in", "danger");
        int n = 0;
        foreach (var w in ring)
        {
            if (!Here(w)) continue;
            if (n++ < 12) { w.E.Scripted = false; w.E.Disposition = Disposition.Hostile; w.E.Target = -1; loose.Add((w.E, w.Seed)); }
            else B.Enemies.Release(w.E);
        }
        ring.Clear();
    }

    protected override void OnSoft()
    {
        ringR = Math.Max(7, ringR - 2);
    }

    protected override void OnHard()
    {
        if (longHunt) return;
        longHunt = true;
        B.Rules.Light *= 0.5;
    }

    /* ------------------------------------------------------------- his end -- */

    /// <summary>Spent: down on his side, breathing hard. The ring lies down where it stands. Where she
    /// promised (and the stream runs clean) she chooses; otherwise he dies (C10).</summary>
    void LieDown(Enemy e)
    {
        lyingDown = true;
        Ending = true;
        Channel = null;
        e.Hp = 1;
        e.TakenMul = 0;
        e.Vx = e.Vz = 0;
        // Lying, not stunned: a stunned creature's mind (and so this script) does not run.
        e.State = EnemyState.Idle;
        e.Anim = EnemyAnim.Idle;
        e.Disposition = Disposition.Neutral;
        // What he had marked goes with him (his pant's ring lay on under the choice).
        B.CancelBlows();
        B.Events.Emit(new Ev.Focus { X = e.X, Z = e.Z, Duration = 2.4 });
        S.Bark(e.X, e.Z, "His legs go. He lies on his side, breathing hard, and the ring lies down where it stands.", null);
        // A broken ring's wolves lie down where they stand too: the fight is over, however long she takes to
        // choose (they fought on, and a player weighing his life was bitten while she did).
        foreach (var (le, seed) in loose)
        {
            if (!le.Alive || le.Seed != seed || le.State == EnemyState.Dying) continue;
            le.Scripted = true;
            le.Target = -1;
            S.Script(le, (x, _) =>
            {
                x.Provoked = false;
                x.Disposition = Disposition.Neutral;
                x.Vx = x.Vz = 0;
                x.State = EnemyState.Idle;
                x.Anim = EnemyAnim.Idle;
                return true;
            });
        }
        // Her choice, named on the screen and answered from wherever she stands (not a prompt at his side).
        if (S.CanSpare)
            S.Ask("Greymuzzle", $"{S.SpareVerb}, or finish it", e.X, e.Z, new ChoiceAnswer("let_go", S.SpareVerb, () => Choose(true)), new ChoiceAnswer("finish", "Finish it", () => Choose(false)));
        else if (A.Spare) Choose(true);
        else Choose(false);
    }

    double goT = -1;

    void Choose(bool spare)
    {
        S.Unask();
        if (!spare)
        {
            E.HpFloor = 0;
            E.TakenMul = 1;
            E.Disposition = Disposition.Hostile;
            E.State = EnemyState.Active;
            B.KillEnemy(E, true, null);
            return;
        }
        goT = 0;
    }

    /// <summary>Let go: he gets up, slowly, back legs first, and walks past her to the den, and lies
    /// down among his sick in the mouth of it. The ring goes in after him.</summary>
    bool Lying(Enemy e, double dt)
    {
        e.TakenMul = 0;
        if (goT < 0 || (goT += dt) < 2.4) { e.Vx = e.Vz = 0; e.State = EnemyState.Idle; e.Anim = EnemyAnim.Idle; return true; }
        if (goT - dt < 2.4)
        {
            e.State = EnemyState.Active;
            S.Bark(e.X, e.Z, "He gets up, slowly, and goes to his sick. You let him.", null);
            DashTo(Mouth.X, Mouth.Z, 6);
        }
        if (Running(e, dt) && goT < 8.6) return true;
        double x = e.X, z = e.Z;
        Clear();
        B.Enemies.Release(e);
        S.Ended(x, z, true);
        return true;
    }

    public override void Fell(Enemy e) => Clear();

    public override void Clear()
    {
        foreach (var w in ring.Concat(guard)) if (Here(w)) B.Enemies.Release(w.E);
        foreach (var (le, seed) in loose) if (le.Alive && le.Seed == seed && le.State != EnemyState.Dying) B.Enemies.Release(le);
        ring.Clear();
        guard.Clear();
        loose.Clear();
        S.Unask();
        if (longHunt) { B.Rules.Light /= 0.5; longHunt = false; }
    }

    public override string? State => Cold ? "the cold closes in" : null;

    /* ------------------------------------------- what the hands read of him (BossSense) -- */

    /// <summary>The moon-howl's cold is closing in.</summary>
    public bool Cold => PhaseIx == 1 && Channel != null && !lyingDown;
    /// <summary>Inside the ring, with a margin: a step past it is a shove.</summary>
    public bool Inside(double x, double z, double margin) => ringBroken || lyingDown || Dist(x, z, C.X, C.Z) < RingAt(Math.Atan2(z - C.Z, x - C.X)) - margin;
    public IReadOnlyList<Deadfall> Fires => S.Fires;
    /// <summary>Where the guard before the den stands (a wall of the Pack: round its ends, not into it).</summary>
    public IEnumerable<(double X, double Z)> Guarding => guard.Where(Here).Select(w => (w.E.X, w.E.Z));
    /// <summary>The den floor's middle: the ring stands round it.</summary>
    public (double X, double Z) Middle => C;

    static double Wrap(double a)
    {
        while (a > Math.PI) a -= Math.PI * 2;
        while (a < -Math.PI) a += Math.PI * 2;
        return a;
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    static double SegDist(double x, double z, double x0, double z0, double x1, double z1)
    {
        double lx = x1 - x0, lz = z1 - z0, len2 = lx * lx + lz * lz;
        double t = len2 > 0 ? Math.Clamp(((x - x0) * lx + (z - z0) * lz) / len2, 0, 1) : 0;
        return Dist(x, z, x0 + lx * t, z0 + lz * t);
    }
}

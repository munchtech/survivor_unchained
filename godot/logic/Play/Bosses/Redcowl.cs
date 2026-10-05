using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>
/// Redcowl at his own fire (docs/design/STORY_BOSSES.md 2): Dunstan Cutwell,
/// the last captain of a levy whose town he will not name, feeding forty-one
/// mouths off the road. He comes into a fight like a host into his own camp:
/// the laugh is the bait, and "Mind where you swing" is the hook (C11).
///
///   the host       he swaggers round her; the Greeting, a wide sweep; then the
///                  laugh, and only then the Hook's mark: the laugh is always
///                  the hook. The axe sticks, and he is open. Keep away and one
///                  of his people hands him a torch.
///   forty-one      "Red to me! Up, my lot!": a rally (storm breaks it before
///   mouths         his people hear). The carts are dragged into walls, a pen.
///                  His people cage her in posts with one door, and he waits at
///                  it with the Hook. Once, his levy under the old red standard.
///   mind where     the laugh is gone. Chains: the Hook, the Greeting, the
///   you swing      charge. A child cries behind the carts; he stops, and
///                  listens; then, cold, "Mind where you swing."
///   his end        down on one knee, laughing: spare him or finish it.
/// His people stand round with torches: watchers, not fighters, not targets.
/// </summary>
public sealed class Redcowl : StoryBoss
{
    public Redcowl(IStoryArena a) : base(a) { }

    protected override Phase[] Phases { get; } =
    [
        new("The Host", 0.65, 25, 75),
        new("Forty-One Mouths", 0.30, 30, 75),
        new("Mind Where You Swing", 0, 25, 0),
    ];
    public override School Weakness => School.Storm;
    public override string WeaknessText => "Storm breaks his rally before his people hear it";
    protected override string HardName => "All Forty-One";
    protected override string HardSub => "The whole camp turns out";
    protected override (string Title, string Sub) SoftWords(Enemy e) => ("His lot close in", "Quicker, and more of them");
    public override string ReEntry => "The torches part again, and he comes back through them, laughing.";
    /// <summary>The Red Hand's body (until Redcowl's own, with the greataxe, exists). His health is measured to
    /// the length, as Greymuzzle's was: the same at every tier. His blows are measured against her (Teeth).</summary>
    public override double HealthMul(int tier) => 103;
    public override double Teeth => 0.4;
    protected override bool DiesAtZero => false;

    const string Him = "Redcowl";
    (double X, double Z) C => S.Place["fire_c"];

    /* ------------------------------------------------------------ his people -- */

    /// <summary>His people round the yard with torches up: they watch; they hand him a torch; his lot step
    /// out of them two at a time.</summary>
    sealed class Watcher
    {
        public required Enemy E;
        public double Seed, X, Z;
    }
    readonly List<Watcher> watchers = new();
    readonly List<(Enemy E, double Seed)> lot = new();
    const int Watchers = 12;
    const double WatchR = 13.5;

    void Gather()
    {
        for (int k = 0; k < Watchers; k++)
        {
            double a = k * Math.PI * 2 / Watchers + 0.13;
            double x = C.X + Math.Cos(a) * WatchR, z = C.Z + Math.Sin(a) * WatchR;
            var e = B.SpawnEnemy("footpad", x, z, new Battle.SpawnOpts { Level = S.Level, Disposition = Disposition.Neutral, Faction = Faction.Kerchief, Style = SpawnStyle.Walk });
            if (e == null) continue;
            var w = new Watcher { E = e, Seed = e.Seed, X = x, Z = z };
            watchers.Add(w);
            e.Scripted = true;
            S.Script(e, (_, dt) => Watch(w, dt));
        }
    }

    bool Watch(Watcher w, double dt)
    {
        var e = w.E;
        e.Provoked = false;
        e.Hp = e.MaxHp;
        e.Disposition = Disposition.Neutral;
        double dx = w.X - e.X, dz = w.Z - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
        if (d > 0.05) { double s = Math.Min(d, 3 * dt); e.X += dx / d * s; e.Z += dz / d * s; }
        e.Vx = e.Vz = 0;
        e.Facing = Math.Atan2(C.Z - e.Z, C.X - e.X);
        e.Anim = d > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
        e.State = EnemyState.Active;
        return true;
    }

    bool Here(Watcher w) => w.E.Alive && w.E.Seed == w.Seed && w.E.State != EnemyState.Dying;
    int Lot => lot.Count(l => l.E.Alive && l.E.Seed == l.Seed && l.E.State != EnemyState.Dying);

    /// <summary>Two of his lot step out of the watchers nearest her (four out at most).</summary>
    void HisLot(int most = 4)
    {
        var p = B.Player;
        var near = watchers.Where(Here).OrderBy(w => Dist(w.E.X, w.E.Z, p.X, p.Z)).Take(2).ToList();
        foreach (var w in near)
        {
            if (Lot >= most) break;
            var e = S.Spawn("footpad", w.E.X + (C.X - w.E.X) * 0.1, w.E.Z + (C.Z - w.E.Z) * 0.1, false, SpawnStyle.Walk);
            if (e != null) lot.Add((e, e.Seed));
        }
    }

    /* --------------------------------------------------------------- the ground -- */

    readonly List<int> carts = new(), posts = new();
    readonly List<StandBy> postParts = new();
    double postsT;
    (double X, double Z) door;
    bool cartsUp;

    /// <summary>The carts dragged across: two short walls, east and west, and the yard is a pen.</summary>
    void Carts()
    {
        if (cartsUp) return;
        cartsUp = true;
        foreach (double side in new[] { -1.0, 1.0 })
        {
            double x = C.X + side * 11;
            B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Line, Kind = TelegraphKind.Wall, X = x, Z = C.Z - 6, X1 = x, Z1 = C.Z + 6, Width = 1.8, Delay = 1.5, From = E });
        }
        S.Bark(C.X, C.Z, "His people drag the carts across, and the yard is a pen.", null);
        S.After(1.5, () =>
        {
            if (!cartsUp) return;
            foreach (double side in new[] { -1.0, 1.0 }) carts.Add(B.Collision.AddBox(C.X + side * 11, C.Z, 0.9, 6, 0, new ColliderOpts(Tag: "carts")).Id);
            // Anyone the carts were dragged onto is put inside the pen.
            var p = B.Player;
            if (Math.Abs(p.X - C.X) > 9.8) p.X = C.X + Math.Sign(p.X - C.X) * 9.6;
        });
    }

    /// <summary>The cage: ten posts round her, five metres out, with one gap (the door) facing him. A post
    /// gives to the one who stands by it from inside; he waits at the door with the Hook.</summary>
    void Cage()
    {
        var p = B.Player;
        double cx = p.X, cz = p.Z;
        double toHim = Math.Atan2(E.Z - cz, E.X - cx);
        door = (cx + Math.Cos(toHim) * 5, cz + Math.Sin(toHim) * 5);
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Ring, Kind = TelegraphKind.Wall, X = cx, Z = cz, Inner = 4.4, Radius = 5.6, Delay = 1.5, From = E, Label = "The cage" });
        if (!caged) { caged = true; S.Say("They cage you", "Stand by a post to break it, or chance the door", "danger"); }
        S.After(1.5, () =>
        {
            if (Ending || E == null || !E.Alive) return;
            ClearPosts();
            for (int k = 0; k < 10; k++)
            {
                double a = toHim + Math.PI * 2 * (k + 0.5) / 11;
                double x = cx + Math.Cos(a) * 5, z = cz + Math.Sin(a) * 5;
                posts.Add(B.Collision.AddCircle(x, z, 0.65, new ColliderOpts(Tag: "cage")).Id);
                postParts.Add(new StandBy { X = x, Z = z, Reach = 1.7, Takes = 1.2 });
            }
            postsT = 8;
            cageX = cx; cageZ = cz;
            for (int k = 0; k < 2; k++)
            {
                double a = S.R() * Math.PI * 2;
                if (S.CanStand(cx + Math.Cos(a) * 2.5, cz + Math.Sin(a) * 2.5)) S.Spawn("footpad", cx + Math.Cos(a) * 2.5, cz + Math.Sin(a) * 2.5);
            }
            // He waits at the door, the Hook down its lane.
            doorHook = 1.6;
        });
    }

    double cageX, cageZ, doorHook = -1;
    bool caged;

    void ClearPosts()
    {
        foreach (var id in posts) B.Collision.Remove(id);
        posts.Clear();
        postParts.Clear();
    }

    /// <summary>Inside the cage now.</summary>
    public bool InCage => posts.Count > 0 && Dist(B.Player.X, B.Player.Z, cageX, cageZ) < 4.6;
    /// <summary>For the hands: the cage's middle and its door.</summary>
    public (double X, double Z) CageAt => (cageX, cageZ);
    public (double X, double Z) Door => door;
    public IReadOnlyList<StandBy> Posts => postParts;

    /* --------------------------------------------------------------- each step -- */

    Levy? levy;
    readonly Queue<(double T, double Hp)> hurt = new();

    void StepGround(double dt)
    {
        if (E == null) return;
        watchers.RemoveAll(w => !Here(w));
        if (postsT > 0)
        {
            postsT -= dt;
            // A post gives to the one who stands by it, from inside.
            for (int i = 0; i < postParts.Count; i++)
            {
                var pp = postParts[i];
                if (pp.Broken || Dist(B.Player.X, B.Player.Z, cageX, cageZ) > 5) continue;
                if (pp.Step(B, dt, 872000 + i) && i < posts.Count) { B.Collision.Remove(posts[i]); posts[i] = -1; }
            }
            if (postsT <= 0) ClearPosts();
        }
        if (levy != null)
        {
            levy.Step(dt);
            // Hurt hard (a twentieth of him in six seconds) or staggered, it breaks: it followed him.
            hurt.Enqueue((FightT, E.Hp));
            while (hurt.Count > 0 && FightT - hurt.Peek().T > 6) hurt.Dequeue();
            if (!levy.Broken && hurt.Count > 0 && hurt.Peek().Hp - E.Hp > E.MaxHp * 0.05) BreakLevy();
            if (levy.Broken) levy = null;
        }
    }

    void BreakLevy()
    {
        if (levy == null || levy.Broken) return;
        levy.Break();
        S.Say("The levy breaks", null, "boon");
    }

    /* --------------------------------------------------------------- his moves -- */

    double greetT = 3, hookT = 6, torchT, farT, lotT = 2, cageT, chainT = 3, levyT = 15, side = 1, sideT;
    bool laughed, rallied, rallyBroken, bairns, levied;
    double cadence = 1;
    double Cad => Cadence * cadence;

    protected override void Enter(int phase)
    {
        switch (phase)
        {
            case 0:
                if (watchers.Count == 0) Gather();
                break;
            case 1:
                Rally();
                cageT = 5;
                hookT = 8;
                break;
            case 2:
                S.Bark(E.X, E.Z, "He stops laughing.", null);
                chainT = 2;
                break;
        }
    }

    /// <summary>"Red to me! Up, my lot!": a rallying call, three seconds. Storm breaks it before his people
    /// hear it: the carts still come, the levy does not.</summary>
    void Rally()
    {
        rallied = true;
        S.Bark(E.X, E.Z, "Red to me! Up, my lot!", Him);
        Channel = "His rally: break it!";
        ChannelProgress = 0;
        Hold(3, () => { Channel = null; Carts(); }, t => { ChannelProgress = t / 3; return true; });
    }

    public override void OnHit(Enemy e, School school, double dmg)
    {
        if (Channel != null && school == Weakness && PhaseIx == 1 && !rallyBroken)
        {
            rallyBroken = true;
            base.OnHit(e, school, dmg);
            S.Bark(e.X, e.Z, "His people never hear it.", null);
            Carts();
            return;
        }
        base.OnHit(e, school, dmg);
    }

    public override void OnStagger(Enemy e)
    {
        base.OnStagger(e);
        if (levy is { Broken: false }) BreakLevy();
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (lyingDown) return Kneeling(e, dt);
        if (Spent(e)) { Kneel(e); return true; }
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        greetT -= dt; hookT -= dt; torchT -= dt; lotT -= dt; cageT -= dt; chainT -= dt; levyT -= dt;
        farT = d > 9 ? farT + dt : 0;
        // His lot, two at a time out of the watchers (four out at most; more once he is wild).
        if (lotT <= 0 && PhaseIx < 2) { lotT = (Soft ? 6 : 9) * Cad; HisLot(Soft ? 6 : 4); }
        // Keep away from him and one of his people hands him a torch.
        if (farT > 4 && torchT <= 0 && PhaseIx < 2) { torchT = 7; farT = 0; Torch(); return true; }
        switch (PhaseIx)
        {
            case 0:
                if (hookT <= 0) { hookT = 10 * Cad; Hook(laugh: true); return true; }
                if (d < 5 && greetT <= 0) { greetT = 5 * Cad; Greeting(); return true; }
                return Stalk(e, dt, dx, dz, d);
            case 1:
                if (!levied && !rallyBroken && e.Hp < e.MaxHp * 0.5) { levied = true; Levy(); }
                if (Hard && levyT <= 0 && levy == null) { levyT = 15; Levy(); }
                if (cageT <= 0 && posts.Count == 0) { cageT = (Soft ? 12 : 18) * Cad; Cage(); return true; }
                if (doorHook > 0 && (doorHook -= dt) <= 0) { DoorHook(); return true; }
                if (hookT <= 0) { hookT = 12 * Cad; Hook(laugh: true); return true; }
                if (d < 5 && greetT <= 0) { greetT = 5 * Cad; Greeting(); return true; }
                return Stalk(e, dt, dx, dz, d);
            default:
                if (!bairns && e.Hp < e.MaxHp * 0.15) { bairns = true; Bairns(e); return true; }
                if (chainT <= 0) { chainT = (Hard ? 5 : 7) * Cad; Chain(); return true; }
                return Stalk(e, dt, dx, dz, d);
        }
    }

    /// <summary>Between his moves he walks round her like a host round his own fire, at six to eight
    /// metres. Pressed close, he steps off round her; walked into across his path, he shoulders her off
    /// (StoryBoss.Cuff).</summary>
    bool Stalk(Enemy e, double dt, double dx, double dz, double d)
    {
        if ((sideT -= dt) <= 0) { sideT = 3 + S.R() * 3; side = S.R() < 0.5 ? -1 : 1; }
        double radial = Math.Clamp((d - 7) / 2, -1, 1);
        double vx = dx * radial - dz * side * 0.8, vz = dz * radial + dx * side * 0.8;
        double vl = Math.Max(1e-6, Math.Sqrt(vx * vx + vz * vz)), sp = e.Speed * 0.7;
        double nx = e.X + vx / vl * sp * dt, nz = e.Z + vz / vl * sp * dt;
        bool cornered = !S.Place.Inside(nx, nz, 1.5) || B.Collision.Blocked(nx, nz, e.Radius);
        if (cornered)
        {
            // Into a corner: he turns, and steps back toward the middle of his yard.
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
        Cuff(e, dt, vx, vz, dx, dz, d, cornered, 0.2, 2);
        return true;
    }

    /// <summary>The Greeting: a wide sweep of the greataxe, half round him.</summary>
    void Greeting(Action? then = null)
    {
        Hold(1.0, then);
        Cone(4.5, 150, 1.0, 1.4, "The Greeting");
    }

    /// <summary>The laugh, and only then the Hook: the axe overhead and down a lane. It sticks, and he is open.
    /// (With the leg's bane, he wrenches it out on the sewn leg: open the longer.)</summary>
    void Hook(bool laugh, double mark = 1.2, Action? then = null)
    {
        if (laugh && PhaseIx < 2) { S.Bark(E.X, E.Z, "Ha! HA.", Him); laughed = true; }
        var (dx, dz, _) = ToPlayer();
        Hold(laugh && PhaseIx < 2 ? 0.6 : 0.01, () =>
        {
            var (ex, ez) = (E.X, E.Z);
            Lane(ex, ez, ex + dx * 7, ez + dz * 7, 2.2, mark, 2.0, "The Hook");
            Hold(mark, () => { if (then != null) then(); else Stuck(null); });
        });
    }

    /// <summary>The axe sticks in the ground: he is open a moment, and takes more.</summary>
    void Stuck(Action? then, double seconds = 1.8)
    {
        bool leg = S.Test(new World.Cond { NpcFlag = new World.NpcFlagCond { Npc = "rav", Key = "once:redcowl", Eq = true } });
        if (leg) seconds += 0.8;
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = E.X, Z = E.Z, Radius = 2.6, Delay = seconds, From = E, Label = "The axe sticks" });
        if (leg && !wrenched) { wrenched = true; S.Bark(E.X, E.Z, "He wrenches the axe free, and his weight goes on the sewn leg.", null); }
        Hold(seconds, () => { E.TakenMul = 1; then?.Invoke(); }, _ => { E.TakenMul = 1.25; return true; });
    }

    bool wrenched;

    /// <summary>One of his people hands him a torch, and he throws it: a circle, and fire left burning.</summary>
    void Torch()
    {
        var p = B.Player;
        S.Bark(E.X, E.Z, "One of his people hands him a torch.", null);
        double tx = p.X + p.Vx * 0.4, tz = p.Z + p.Vz * 0.4;
        Hold(0.5);
        var b = Circle(tx, tz, 2.4, 1.2, 1.2, "A torch", School.Fire);
        b.After = bb => { var z = bb.SpawnZone(Side.Enemy, tx, tz, 2.2, 3, E.Damage * 0.25, School.Fire); if (z != null) z.Tags = [Tag.Zone, Tag.Fire]; };
    }

    /// <summary>At the cage's door: the Hook down its lane, into the cage.</summary>
    void DoorHook()
    {
        double ox = door.X - cageX, oz = door.Z - cageZ, ol = Math.Max(0.01, Math.Sqrt(ox * ox + oz * oz));
        double sx = door.X + ox / ol * 2.5, sz = door.Z + oz / ol * 2.5;
        DashTo(sx, sz, 0.5, () =>
        {
            S.Bark(sx, sz, "He fills the door.", null);
            Lane(sx, sz, cageX - ox / ol * 2, cageZ - oz / ol * 2, 2.2, 1.2, 2.0, "The Hook");
            Hold(1.2, () => Stuck(null));
        });
    }

    /// <summary>His levy, once at half (and on a loop when the whole camp turns out): six pikes in step out of
    /// the cart line, under the old red standard.</summary>
    void Levy()
    {
        var p = B.Player;
        double lx = C.X, lz = C.Z + 9;
        S.Bark(lx, lz, "Out of the carts come six pikes in step, under an old red standard.", null);
        S.Say("The levy", "Hurt him hard, and it breaks", "danger");
        levy = new Story.Levy(S, lx, lz, p.X, p.Z, 6, caller: Him);
    }

    /// <summary>On his feet, with no laugh: the Hook (marked longer now), the Greeting, the charge; the axe
    /// sticks at the end.</summary>
    void Chain() => Hook(laugh: false, mark: 1.3, then: () => Greeting(Charge));

    /// <summary>The charge: a shoulder down a lane eight metres long.</summary>
    void Charge()
    {
        var (dx, dz, _) = ToPlayer();
        double x1 = E.X + dx * 8, z1 = E.Z + dz * 8;
        Lane(E.X, E.Z, x1, z1, 2.0, 0.8, 1.6, "The Charge");
        Hold(0.8, () => DashTo(x1, z1, 0.4, () => Stuck(null, 1.5)));
    }

    /// <summary>A child cries behind the carts. He stops and turns his head to the tents: open, and the fight
    /// stopped for him. Then, cold, and quicker to the end.</summary>
    void Bairns(Enemy e)
    {
        S.Bark(C.X, C.Z + 12, "(A child, crying for its mam.)", null);
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = e.X, Z = e.Z, Radius = 2.6, Delay = 3, From = e, Label = "He listens" });
        Hold(3, () =>
        {
            E.TakenMul = 1;
            S.Bark(E.X, E.Z, "Mind where you swing.", Him);
            S.Bark(C.X, C.Z, "His people lower their torches.", null);
            cadence = 0.85;
            B.Rules.Light *= 0.8;
            lightDown = true;
        }, _ => { E.TakenMul = 1.5; return true; });
    }

    bool lightDown;

    protected override void OnSoft() { }

    /// <summary>All Forty-One: the whole camp turns out. His watchers come in as his lot, the levy forms
    /// again and again, and he hits the harder the longer it goes: it is the end of it, one way or the other.</summary>
    protected override void OnHard()
    {
        levyT = 0;
        foreach (var w in watchers.Where(Here).ToList())
        {
            w.E.Scripted = false;
            w.E.Disposition = Disposition.Hostile;
            w.E.Target = -1;
            lot.Add((w.E, w.Seed));
        }
        watchers.Clear();
    }

    public override void Step(double dt)
    {
        if (Hard && E != null && !Ending) E.Damage *= 1 + 0.03 * dt;
        StepGround(dt);
    }

    /* ---------------------------------------------------------------- his end -- */

    bool lyingDown;

    /// <summary>Spent: down on one knee, the axe-head in the dirt, laughing. Spare him, or finish it.</summary>
    void Kneel(Enemy e)
    {
        lyingDown = true;
        Ending = true;
        Channel = null;
        e.Hp = 1;
        e.TakenMul = 0;
        e.Vx = e.Vz = 0;
        e.State = EnemyState.Idle;
        e.Anim = EnemyAnim.Idle;
        e.Disposition = Disposition.Neutral;
        levy?.Break();
        foreach (var l in lot) if (l.E.Alive && l.E.Seed == l.Seed) l.E.Status[StatusKind.Fear] = new StatusSlot(6, 1, 1, 0);
        B.Events.Emit(new Ev.Focus { X = e.X, Z = e.Z, Duration = 2.4 });
        S.Bark(e.X, e.Z, "He goes down on one knee, the axe-head in the dirt, and laughs. It costs him.", null);
        if (S.CanSpare)
        {
            S.Offer("let_go", e.X, e.Z, S.SpareVerb, Him, () => Choose(true));
            S.Offer("finish", e.X, e.Z, "Finish it", Him, () => Choose(false));
        }
        else Choose(false);
    }

    double goT = -1;

    void Choose(bool spare)
    {
        S.Withdraw("let_go");
        S.Withdraw("finish");
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

    /// <summary>Spared: he gets up on the sewn leg, and it holds; he walks back through his people.</summary>
    bool Kneeling(Enemy e, double dt)
    {
        e.TakenMul = 0;
        if (goT < 0 || (goT += dt) < 1.5) { e.Vx = e.Vz = 0; e.State = EnemyState.Idle; e.Anim = EnemyAnim.Idle; return true; }
        if (goT - dt < 1.5)
        {
            e.State = EnemyState.Active;
            S.Bark(e.X, e.Z, "He gets up on the sewn leg, and it holds.", null);
            var (bx, bz) = S.Place["boss_at"];
            DashTo(bx, bz, 5);
        }
        if (Running(e, dt) && goT < 7) return true;
        double x = e.X, z = e.Z;
        Clear();
        B.Enemies.Release(e);
        S.Ended(x, z, true);
        return true;
    }

    public override void Fell(Enemy e) => Clear();

    public override void Clear()
    {
        foreach (var w in watchers) if (Here(w)) B.Enemies.Release(w.E);
        watchers.Clear();
        foreach (var l in lot) if (l.E.Alive && l.E.Seed == l.Seed && l.E.State != EnemyState.Dying) l.E.Status[StatusKind.Fear] = new StatusSlot(6, 1, 1, 0);
        lot.Clear();
        foreach (var id in carts) B.Collision.Remove(id);
        carts.Clear();
        cartsUp = false;
        ClearPosts();
        levy?.Clear();
        levy = null;
        S.Withdraw("let_go");
        S.Withdraw("finish");
        if (lightDown) { B.Rules.Light /= 0.8; lightDown = false; }
    }

    public override string? State => InCage ? "caged" : levy != null ? "the levy marches" : null;

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}

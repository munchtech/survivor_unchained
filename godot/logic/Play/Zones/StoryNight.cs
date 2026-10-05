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
            BossTick = (e, dt) => e == boss && script != null ? script.Tick(e, dt) : scripted.TryGetValue(e.Id, out var s) && s.Seed == e.Seed && s.Tick(e, dt),
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
        foreach (var pc in map.Pieces) G.Look.AddProp(pc.Id, pc.X, pc.Z, pc.Rot, pc.Scale);
        b.Rules = MapOffers.Rules(Spec.Map);
        // The table's gold rates (crafting's economy): a night's rank and file pay a little.
        b.Rules.FodderGold = 0.0015;
        b.Rules.ChampionGold = 0.07;
        b.Rules.EmberGain *= EmberPace;
        b.Rules.Light *= 1.6;
        var place = Fight.Place;
        var (ax, az) = place[Fight.Arrive];
        open.Add(place.SpaceAt(ax, az) ?? place.Spaces[0].Id);
        b.InBounds = (x, z) => map.CanStand(x, z) && place.Inside(x, z, 0.3, open);
        place.Build(b.Collision);
        b.Charges.Spikes = false;
        b.Charges.Cap = 2;
        double burns = Fight.Burns(this);
        foreach (var id in Fight.Fires)
        {
            var (x, z) = place[id];
            var f = new Deadfall { Id = id, X = x, Z = z, Burns = burns, Light = G.Look.AddLight(x, 1.1, z, "#ff8a3a", 2.8, 10, 0.22, 0.1, "#ffb35a") };
            G.Look.SetLit(f.Light, false);
            fires.Add(f);
        }
        // The first great blessing, before anything moves (another as the boss's ground opens).
        b.GreatOwed = 1;
        G.Announce(new Announcement(Spec.Name, Region, "zone", 3.4, "Story night"));
        G.Say(Fight.Pull);
        StartBeat(0);
    }

    /// <summary>Pictures and probes: straight to a stage (or the boss: Fight.Beats.Length), the build
    /// as it stands, the ground behind opened.</summary>
    public void SkipTo(int stage)
    {
        if (B == null) return;
        stage = Math.Clamp(stage, 0, Fight.Beats.Length);
        beat?.End();
        Clear(all: true);
        for (int i = 0; i < stage && i < Fight.Beats.Length; i++)
            if (Fight.Beats[i]() is { Gate: { } g }) Open(g);
        B.GreatOwed = 0;
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
        if (beatIx < Fight.Between.Length) G.Say(Fight.Between[beatIx]);
        // The stage's leftovers fall back into the dark: the quiet between is quiet.
        MakeWay();
        B!.Charges.Calm(B, 6);
        Now = Stage.Between;
        betweenT = 6;
        Goal = beatIx + 1 < Fight.Beats.Length ? Fight.Place[Fight.Beats[beatIx + 1]().Start] : Fight.Place[Fight.BossStart];
        Objectives();
    }

    void Open(string gate)
    {
        var g = Fight.Place.Gates.FirstOrDefault(x => x.Id == gate);
        if (g != null) { StoryPlace.Open(B!.Collision, g); open.Add(g.Into); }
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
            boss.MaxHp = boss.Hp = boss.MaxHp * script.HealthMul(Spec.Tier);
            boss.Damage *= script.DamageMul;
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
                    else BossOpen();
                }
                break;
            case Stage.Boss:
                script?.Step(dt);
                break;
        }
        Leaving();
        Strays(dt);
    }

    double strayT;

    /// <summary>Anything of the fight's put out of its open ground (a shove, a slide) is brought back to the
    /// nearest of the place's points it may stand on: a goal out of reach is a night that never ends.</summary>
    void Strays(double dt)
    {
        if ((strayT -= dt) > 0) return;
        strayT = 0.5;
        foreach (var e in B!.Enemies.Living())
        {
            if (e.Disposition != Disposition.Hostile || e.Scripted || e.Boss || e.State is EnemyState.Dying or EnemyState.Burrowed) continue;
            if (Fight.Place.Inside(e.X, e.Z, -0.8, open)) continue;
            var home = Fight.Place.Points.Values.Where(q => Fight.Place.Inside(q.X, q.Z, 1, open)).OrderBy(q => Dist(q.X, q.Z, e.X, e.Z)).FirstOrDefault();
            if (home == default) continue;
            e.X = home.X; e.Z = home.Z; e.Kbx = e.Kbz = 0;
        }
    }

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
        G.Say("You get up.");
        Objectives();
    }

    void LetGo(string by)
    {
        if (B == null || over) return;
        falling = false;
        StageEnded(atBoss ? "boss" : $"stage {beatIx + 1}");
        Finish(by);
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
        if (boss != null) foreach (var l in Hoard()) B.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);
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

    static readonly string[] PlainGear = ["iron_helm", "leather_cap", "chain_shirt", "padded_jerkin", "silver_ring", "copper_ring", "bone_amulet", "travelers_cloak", "watch_buckler"];

    int Rarity(double luck)
    {
        double roll = R() / luck;
        return roll < 0.04 + Spec.Tier * 0.01 ? 3 : roll < 0.2 + Spec.Tier * 0.02 ? 2 : roll < 0.65 ? 1 : 0;
    }

    IEnumerable<Loot> OnLoot(Enemy e)
    {
        var o = new List<Loot>();
        bool small = smallChests.Remove(e.Id), carrier = chests.Remove(e.Id) || small;
        if (carrier) o.Add(new Loot(PickupKind.Chest, small ? "small" : null, 1, true));
        if (carrier && R() < 0.6) o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Rarity(1), lean));
        return o;
    }

    /// <summary>The boss's hoard: the night's best chest (a part more for a Break past a tenth of it, and
    /// for a fight with no marked blow taken), plain gear, and an art's manual.</summary>
    IEnumerable<Loot> Hoard()
    {
        var o = new List<Loot>();
        int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= script.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == bossBlowsBefore ? 1 : 0);
        o.Add(new Loot(PickupKind.Chest, "boss", n, true));
        for (int k = 0; k < 2 + Spec.Tier / 2; k++)
            o.Add(new Loot(PickupKind.Item, PlainGear[(int)(R() * PlainGear.Length)], 1, true, Math.Max(1, Rarity(1.5)), lean));
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
    public int Level => Math.Max(1, Spec.Tier * 3 - 2 + (atBoss ? Fight.BossLevel : beat?.Level ?? 0));
    public IReadOnlyList<Deadfall> Fires => fires;
    public bool Fact(string key) => F(key).Truthy;
    public (double X, double Z)? Goal { get; set; }
    public void Script(Enemy e, Func<Enemy, double, bool> tick) { e.Scripted = true; scripted[e.Id] = (e.Seed, tick); }
    public void Line(string text) => G.Say(text);
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

    bool Standable(double x, double z) => map.CanStand(x, z) && Fight.Place.Inside(x, z, 0.6, open) && !B!.Collision.Blocked(x, z, 0.6);

    Enemy? Spawn(string def, double x, double z, bool elite = false, SpawnStyle? style = null)
    {
        if (B == null) return null;
        var st = style ?? (Enemies.Get(def).Family == Family.Undead ? SpawnStyle.Rise : Enemies.Get(def).Behavior == Behavior.Tunneler ? SpawnStyle.Burrow : SpawnStyle.Walk);
        var e = B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Level = Level + (elite ? 1 : 0), Elite = elite, Style = st });
        // The crowd softens as a table night's does by its minute: the build's growth shows as a crowd
        // that melts (ArenaRun.FodderEase). Not the named, the champions or the boss.
        if (e != null && !e.Elite) e.MaxHp = e.Hp = e.MaxHp / ArenaRun.FodderEase(atBoss ? Fight.BossMinute : beat?.Minute ?? 0);
        return e;
    }

    public Enemy? Foe(string def, double x, double z, double hpMul = 1, string? kicker = null)
    {
        var e = Spawn(def, x, z, true, SpawnStyle.Walk);
        if (e == null) return null;
        // A named foe: a miniboss's measure (between a champion's twice and a herald's five times).
        e.MaxHp = e.Hp = e.MaxHp * (1.6 + 0.6 * Spec.Tier) * hpMul;
        e.Named = new Named { Title = e.Def.Name };
        smallChests.Add(e.Id);
        B!.Charges.Calm(B, 4);
        G.Announce(new Announcement(e.Def.Name, e.Def.Lesson, "danger", 3.2, kicker));
        return e;
    }

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
    void IBossArena.Won(double x, double z) => Victory(x, z, spared: false);

    /* ------------------------------------------------------------ on screen -- */

    public override void Frame(double dt)
    {
        if (B == null || over) return;
        double want = Now == Stage.Boss ? CameraBoss : CameraNear;
        CameraDistance += (want - CameraDistance) * Math.Min(1, dt / 2.5);
        if (Now == Stage.Boss && boss is { Alive: true } b && b.State != EnemyState.Dying && script != null)
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
        ["stage"] = Now.ToString(), ["beat"] = beatIx, ["falls"] = falls, ["level"] = Level, ["ember"] = B?.EmberLevel,
        ["alive"] = B?.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile) ?? 0,
    };
}

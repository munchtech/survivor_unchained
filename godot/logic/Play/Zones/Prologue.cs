using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* The prologue: one night on the Low Ford road (the web game's
 * game/zones/prologue.ts).
 *
 * It is a tutorial that never stops to be one. Each thing the game needs
 * you to know arrives as the road puts it in front of you:
 *
 *   wake      the dead climb out of the ground around your fire     (move)
 *   rising    their stones hold light; the ember rises     (ember, the draft)
 *   road      up the road; shieldmen, bowmen             (build, positioning)
 *   ambush    the dead rise out of the ditch by a broken cart     (the horde)
 *   post      a Barrow Knight over a dead watchman's chest (elites, equipment)
 *   barrow    a Grave-Caller raising the dead                     (ability)
 *   ford      the Ford-Warden                                        (boss)
 *   dawn      what took the Warden's heart; the sun comes up and the ember
 *             goes out, and all it built with it: it burns only in the dark
 *             (the story is walked by day; the ember is for the night's
 *             arenas); the gate opens                               (the world)
 *
 * Dying here is forgiven: the ember is not done with you, and you get up
 * again at the last place you were safe. That is the only place in the game
 * where that is true. */
public sealed class Prologue : ZoneRuntime
{
    public enum Stage { Wake, Rising, Road, Ambush, Road2, Post, Barrow, ToFord, Intro, Boss, Victory, Dawn, Exit }

    public override string Id => "lowford";
    public override string Name => "The Low Ford Road";
    public override string? Region => "Thornhollow, south";
    public override bool Combat => true;
    /// <summary>The night's: the ember burns until the dawn puts it out.</summary>
    public override bool Ember => !F("prologue.done").Truthy;
    public override IReadOnlyList<string> Creatures { get; } = ["risen", "risen_warrior", "risen_archer", "barrow_knight", "grave_caller", "grimtunnel", "ford_warden"];

    sealed class WardenAI
    {
        public string Mode = "sleep";
        public double T, CleaveCd = 3, ChargeCd = 6, ChannelCd = 30, DirX, DirZ = 1, Travelled, ChannelHp, RaiseT, ContactT, HitX, HitZ;
        public List<double> Thresholds = [0.7, 0.4];
    }

    static readonly double[] Ward = [1, 0.7, 0.55, 0.4];
    const string Draft = "Each time the ember rises, choose one: a combat skill (they fire on their own) or a passive skill. A combat skill at rank 8, with one rank of the passive it names, evolves.";

    public Stage Now { get; private set; } = Stage.Wake;
    double stageT, spawnT = 2, cutT, dawnK, envT, deadT = -1;
    XZ checkpoint;
    readonly HashSet<string> shown = new();
    readonly List<(double X, double Z, int Light, string Flame)> pylons = new();
    readonly bool[] litPylons;
    readonly double[] pylonHp;
    Enemy? warden, caller, knight, grim;
    bool wardenGone, chestOpened, finished, coreShown, doused;
    /// <summary>A cinematic is playing the Warden with its own body (C02, C03): ours waits, hidden.</summary>
    bool wardenInCine;
    readonly XZ wardenHome;
    (double X, double Z, double Facing) wardenPos;
    readonly WardenAI ai = new();
    IBossView wardenView = null!;
    IOrb core = null!;
    INpcView? watchman;
    readonly double waterY;
    double coreY, coreSpin;
    (double X, double Z) corePos;

    XZ L(string place) => P("LOWFORD", place);
    double ExitZ => Meta.Places["LOWFORD"].GetProperty("exitZ").GetDouble();

    /// <summary>Where the river runs (the web game's riverZ).</summary>
    public static double RiverZ(double x) => -44 + Math.Sin(x * 0.032) * 4.5 + Math.Sin(x * 0.011 + 1) * 3;

    public Prologue(IZoneHost host, ZoneMeta meta) : base(host, meta)
    {
        foreach (var p in meta.Refs.GetProperty("pylons").EnumerateArray())
            pylons.Add((p.GetProperty("x").GetDouble(), p.GetProperty("z").GetDouble(), p.GetProperty("light").GetInt32(), p.GetProperty("flame").GetString()!));
        litPylons = pylons.Select(_ => true).ToArray();
        pylonHp = pylons.Select(_ => 260.0).ToArray();
        waterY = meta.Places["WATER_Y"].GetDouble();
        var camp = L("camp");
        checkpoint = new XZ(camp.X + 1.5, camp.Z - 1.5);
        var ford = L("ford");
        wardenHome = new XZ(ford.X + 1, ford.Z - 2);
        wardenPos = (wardenHome.X, wardenHome.Z, 0);
        Hooks = new BattleHooks
        {
            BossTick = (e, dt) => e.Tag == "warden" && WardenTick(e, dt),
            OnKill = OnKill,
            OnHitProp = (tag, _, _, dmg, _, _) =>
            {
                if (!tag.StartsWith("pylon:") || Now != Stage.Boss || !int.TryParse(tag[6..], out int i) || !litPylons[i]) return;
                pylonHp[i] -= dmg;
                if (pylonHp[i] <= 0) Snuff(i, "broken");
            },
        };
        var chest = L("chest"); var man = L("watchman"); var fire = L("fire");
        Interactables.Add(new()
        {
            Id = "chest", X = chest.X, Z = chest.Z, R = 2.6, Verb = "Open", Name = "Watch Chest",
            When = () => !chestOpened,
            Locked = () => knight != null ? "The Barrow Knight stands over it" : null,
            Act = () =>
            {
                chestOpened = true;
                G.Apply("""[{ "give": "padded_jerkin", "rarity": 1 }, { "give": "health_draught", "qty": 2 }, { "gold": 15 }]""");
                G.SetHint(null);
                G.After(0.6, () => Tip("pack", "Your pack", "What you find, you keep. The ember will not outlast the night; gear, gold and what you learn will. Open your pack to wear the jerkin.", [Key("inventory")], 14));
                Objective([("Search the old Watch-post", true, false), ("Wear what you found", false, true), ("Follow the road north", false, false)]);
            },
        });
        Interactables.Add(new()
        {
            Id = "watchman", X = man.X, Z = man.Z, R = 2.4, Verb = "Examine", Name = "Dead Watchman",
            Act = () =>
            {
                G.Say("A Watchman, grey-bearded and a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes: \"Lamps at the Low Ford lit again, and not by us. Not oil. Wrong colour.\" \"Sent Dannet for the captain. Dannet not back.\" \"The Warden is walking. I can hear it singing in the water.\"", null, 10);
                // The book is the first page of the lamps' mystery.
                G.Apply("""[{ "learn": "lore.warden", "text": "The lamps at the ford burn ember, and the Warden drinks it." }, { "quest": { "id": "lamps", "status": "active", "entry": "book" } }]""");
                // The devout hear the dead, a little.
                if (G.Journey.Ch.Knowledge.Contains("faith"))
                {
                    G.After(10.2, () => G.Say("...and for you alone, the dead man's jaw moves.", null, 3));
                    G.After(13.4, () => G.Say("It broke its own lamps, coming for me. Twice.", "The dead Watchman", 5));
                }
            },
        });
        Interactables.Add(new()
        {
            Id = "fire", X = fire.X, Z = fire.Z, R = 2.2, Verb = "Warm your hands", Name = "Campfire",
            When = () => Now is Stage.Rising or Stage.Wake,
            Act = () => G.Say("The fire is almost out. It will not hold them back.", null, 3.5),
        });
    }

    /* ------------------------------------------------------------- helpers -- */

    void Objective((string Text, bool Done, bool Optional)[] steps) =>
        G.SetObjectives([new Tracked("pro", "The Low Ford", TrackTone.Tutorial, steps.Select(s => new Step(s.Text, s.Optional, s.Done)).ToList())]);

    void Tip(string id, string title, string text, List<string>? keys = null, double life = 9)
    {
        if (!shown.Add(id)) return;
        G.SetHint(new Hint(id, title, text, keys ?? new()));
        if (life > 0) G.After(life, () => { if (G.CurrentHint?.Id == id) G.SetHint(null); });
    }

    string Key(string action) => G.KeyLabel(action);
    void Go(Stage s) { Now = s; stageT = 0; }

    bool OpenGround(double x, double z)
    {
        if (B == null || B.Collision.Blocked(x, z, 0.6)) return false;
        if (Math.Abs(z - RiverZ(x)) < 9 && Math.Abs(x) > 14) return false;
        return Math.Abs(x) < 72 && Math.Abs(z) < 122;
    }

    /// <summary>Some of the dead, somewhere around the survivor. `ahead` biases north.</summary>
    void SpawnAround(string def, int n, double rMin, double rMax, double ahead = 0, int level = 1)
    {
        if (B == null) return;
        var p = B.Player;
        for (int i = 0; i < n; i++)
            for (int tries = 0; tries < 8; tries++)
            {
                double a = B.Rng.Next() * Math.PI * 2;
                if (ahead > 0 && B.Rng.Next() < ahead) a = -Math.PI / 2 + (B.Rng.Next() - 0.5) * 1.8;
                double d = rMin + B.Rng.Next() * (rMax - rMin);
                double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
                if (!OpenGround(x, z)) continue;
                B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Style = def is "risen" or "risen_warrior" ? SpawnStyle.Rise : SpawnStyle.Walk, Level = level });
                break;
            }
    }

    int Hostiles() => B?.Enemies.Living().Count(e => e.State != EnemyState.Dying && e.Disposition == Disposition.Hostile) ?? 0;

    void ClearAround(double x, double z, double r)
    {
        if (B == null) return;
        foreach (var e in B.Enemies.Living().ToList())
            if (!e.Boss && e != grim && Dist(e.X, e.Z, x, z) < r) B.KillEnemy(e, false, null);
    }

    /* ---------------------------------------------------- the Ford-Warden -- */

    public int LitCount => litPylons.Count(l => l);

    void Snuff(int i, string how)
    {
        if (!litPylons[i] || B == null) return;
        litPylons[i] = false;
        var p = pylons[i];
        G.Look.SetLit(p.Light, false);
        B.Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = 3.2, School = School.Frost, Power = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.6 });
        B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z, Text = how == "charge" ? "The lamp shatters!" : "The lamp goes dark" });
        int left = LitCount;
        if (left > 0) G.Toast(new Toast(ToastKind.World, $"A lamp goes out — {left} still burn{(left == 1 ? "s" : "")}"));
        else G.Announce(new Announcement("The lamps are dark", "The Warden is laid bare", "boon", 3.2));
    }

    void Relight()
    {
        int i = Array.IndexOf(litPylons, false);
        if (i < 0) return;
        litPylons[i] = true;
        pylonHp[i] = 200;
        G.Look.SetLit(pylons[i].Light, true);
        B?.Events.Emit(new Ev.Nova { X = pylons[i].X, Z = pylons[i].Z, Radius = 4, School = School.Frost, Duration = 0.8 });
        G.Toast(new Toast(ToastKind.Warning, "The drowned rekindle a lamp"));
    }

    BossBar? bar;
    void Bar(BossBar? b) { bar = b; G.SetBoss(b); }

    bool WardenTick(Enemy e, double dt)
    {
        if (B == null) return true;
        var p = B.Player;
        ai.T += dt;
        e.Vx = e.Vz = 0;
        double dx = p.X - e.X, dz = p.Z - e.Z;
        double dist = Math.Sqrt(dx * dx + dz * dz);
        if (dist == 0) dist = 0.001;
        double hpK = e.Hp / e.MaxHp;
        // The ward: the lamps take most of every blow.
        double mul = Ward[LitCount];
        if (ai.Mode == "stun") mul *= 1.5;
        e.TakenMul = mul;
        ai.CleaveCd -= dt; ai.ChargeCd -= dt; ai.ChannelCd -= dt;
        // Interrupted mid-channel (Battle.Interrupt sets this).
        if (ai.Mode == "channel" && e.State == EnemyState.Stunned)
        {
            ai.Mode = "stun"; ai.T = 0; e.StateT = 0;
            wardenView.SetPose("stunned");
            B.Events.Emit(new Ev.Announce { Title = "Channel broken", Tone = Tone.Boon });
        }
        e.State = ai.Mode == "channel" ? EnemyState.Casting : ai.Mode is "windup" or "chargeWind" ? EnemyState.Windup : EnemyState.Active;

        switch (ai.Mode)
        {
            case "sleep":
            case "wake":
                return true;
            case "walk":
            {
                e.Facing = Math.Atan2(dz, dx);
                // Channel at thresholds, or when it has been a while.
                double? th = ai.Thresholds.Count > 0 ? ai.Thresholds[0] : null;
                if ((th is double t0 && hpK < t0) || ai.ChannelCd <= 0)
                {
                    if (th is double t1 && hpK < t1) ai.Thresholds.RemoveAt(0);
                    ai.Mode = "channel"; ai.T = 0; ai.ChannelHp = e.Hp; ai.ChannelCd = 34; ai.RaiseT = 0.6;
                    wardenView.SetPose("channel");
                    B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "RISE, YOU WHO DROWNED HERE.", Speaker = "The Ford-Warden" });
                    return true;
                }
                if (dist < 5.2 && ai.CleaveCd <= 0)
                {
                    ai.Mode = "windup"; ai.T = 0; ai.DirX = dx / dist; ai.DirZ = dz / dist;
                    ai.HitX = e.X + ai.DirX * 3; ai.HitZ = e.Z + ai.DirZ * 3;
                    B.Events.Emit(new Ev.Telegraph { Id = e.Id * 10 + 1, Shape = TelegraphShape.Circle, X = ai.HitX, Z = ai.HitZ, Radius = 3.4, Duration = 1.05, Hostile = true });
                    wardenView.SetPose("windup");
                    return true;
                }
                if (dist > 6.5 && ai.ChargeCd <= 0)
                {
                    ai.Mode = "chargeWind"; ai.T = 0; ai.DirX = dx / dist; ai.DirZ = dz / dist;
                    double len = Math.Min(24, dist + 8);
                    B.Events.Emit(new Ev.Telegraph { Id = e.Id * 10 + 2, Shape = TelegraphShape.Line, X = e.X, Z = e.Z, X1 = e.X + ai.DirX * len, Z1 = e.Z + ai.DirZ * len, Radius = 0, Width = 3, Duration = 1.3, Hostile = true });
                    ai.Travelled = len;
                    wardenView.SetPose("charge-windup");
                    B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "It lowers its head..." });
                    return true;
                }
                if (dist > e.Radius + 1.2)
                {
                    double sp = e.Speed * (LitCount == 0 ? 1.25 : 1);
                    e.Vx = dx / dist * sp; e.Vz = dz / dist * sp;
                    e.X += e.Vx * dt; e.Z += e.Vz * dt;
                    B.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
                }
                wardenView.SetPose("walk");
                // Contact.
                ai.ContactT -= dt;
                if (dist < e.Radius + p.Radius + 0.4 && ai.ContactT <= 0)
                {
                    ai.ContactT = 1.2;
                    B.HurtPlayer(e.Damage * 0.6, School.Physical, "The Ford-Warden", e);
                }
                return true;
            }
            case "windup":
                if (ai.T >= 1.05)
                {
                    ai.Mode = "cleave"; ai.T = 0;
                    wardenView.SetPose("cleave");
                    if (Dist(p.X, p.Z, ai.HitX, ai.HitZ) < 3.4 + p.Radius) B.HurtPlayer(e.Damage * 1.5, School.Physical, "The Ford-Warden", e);
                    B.Events.Emit(new Ev.Explosion { X = ai.HitX, Z = ai.HitZ, Radius = 3.4, School = School.Physical, Power = 1.2 });
                    B.Events.Emit(new Ev.Shake { Amount = 0.55 });
                }
                return true;
            case "cleave":
                if (ai.T > 0.8) { ai.Mode = "walk"; ai.CleaveCd = 3.2; wardenView.Release(); }
                return true;
            case "chargeWind":
                e.Facing = Math.Atan2(ai.DirZ, ai.DirX);
                if (ai.T >= 1.3) { ai.Mode = "charge"; ai.T = 0; wardenView.SetPose("charge"); }
                return true;
            case "charge":
            {
                const double sp = 17;
                double step = Math.Min(sp * dt, ai.Travelled);
                double x0 = e.X, z0 = e.Z;
                e.X += ai.DirX * step; e.Z += ai.DirZ * step;
                e.Vx = ai.DirX * sp; e.Vz = ai.DirZ * sp;
                ai.Travelled -= step;
                // A lamp in the way: it goes through it, and it hurts.
                for (int i = 0; i < pylons.Count; i++)
                {
                    var py = pylons[i];
                    if (litPylons[i] && Dist(py.X, py.Z, e.X, e.Z) < e.Radius + 0.9)
                    {
                        Snuff(i, "charge");
                        ai.Mode = "stun"; ai.T = -1.5;
                        wardenView.SetPose("stunned");
                        B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "The Warden reels!" });
                        return true;
                    }
                }
                // Anything else solid stops it short.
                B.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
                double moved = Dist(e.X, e.Z, x0, z0);
                if (moved < step * 0.4)
                {
                    ai.Mode = "stun"; ai.T = 0.8;
                    wardenView.SetPose("stunned");
                    B.Events.Emit(new Ev.Shake { Amount = 0.5 });
                }
                else if (Dist(p.X, p.Z, e.X, e.Z) < e.Radius + p.Radius + 0.3 && p.Iframes <= 0)
                    B.HurtPlayer(e.Damage * 1.4, School.Physical, "The Ford-Warden", e);
                if (ai.Travelled <= 0.01 && ai.Mode == "charge") { ai.Mode = "walk"; ai.ChargeCd = 8 + B.Rng.Next() * 3; wardenView.Release(); }
                return true;
            }
            case "stun":
                if (ai.T >= 2.5) { ai.Mode = "walk"; ai.ChargeCd = Math.Max(ai.ChargeCd, 5); ai.CleaveCd = 1.5; wardenView.Release(); }
                return true;
            case "channel":
            {
                double k = ai.T / 6;
                if (bar != null) Bar(bar with { Channel = ("Calling the drowned — break it!", Math.Min(1, k)) });
                ai.RaiseT -= dt;
                if (ai.RaiseT <= 0)
                {
                    ai.RaiseT = 0.9;
                    for (int i = 0; i < 2; i++)
                    {
                        double a = B.Rng.Next() * Math.PI * 2, d = 4 + B.Rng.Next() * 6;
                        double x = e.X + Math.Cos(a) * d, z = e.Z + Math.Sin(a) * d;
                        if (OpenGround(x, z)) B.SpawnEnemy("risen", x, z, new Battle.SpawnOpts { Style = SpawnStyle.Rise, Level = 2 });
                    }
                }
                // Hurt it badly enough and the channel breaks.
                if (ai.ChannelHp - e.Hp > e.MaxHp * 0.09)
                {
                    ai.Mode = "stun"; ai.T = 0;
                    wardenView.SetPose("stunned");
                    B.Events.Emit(new Ev.Announce { Title = "Channel broken", Tone = Tone.Boon });
                }
                else if (ai.T >= 6)
                {
                    e.Hp = Math.Min(e.MaxHp, e.Hp + e.MaxHp * 0.06);
                    Relight();
                    ai.Mode = "walk";
                    wardenView.Release();
                }
                if (ai.Mode != "channel" && bar != null) Bar(bar with { Channel = null });
                return true;
            }
            default:
                return true;
        }
    }

    /* ------------------------------------------------------------- stages -- */

    void Director(double dt)
    {
        if (B == null) return;
        var p = B.Player;
        stageT += dt;
        spawnT -= dt;
        int n = Hostiles();
        switch (Now)
        {
            case Stage.Wake:
                if (stageT > 1.2) Tip("move", "Move", "Keep moving. Your weapon strikes on its own.", ["W", "A", "S", "D"], 11);
                if (stageT > 3) { Go(Stage.Rising); spawnT = 0; }
                break;
            case Stage.Rising:
            {
                // Keep the clearing full: more of them the longer it goes on.
                double want = Math.Min(40, 16 + stageT * 0.3);
                if (spawnT <= 0 && n < want) { SpawnAround("risen", 2 + (stageT > 40 ? 1 : 0), 9, 14); spawnT = stageT > 30 ? 0.8 : 1.1; }
                // The first rise of the ember brings a great blessing, before its first card.
                if (B.EmberLevel >= 2 && shown.Add("great"))
                {
                    B.GreatOwed++;
                    G.SetDraftTip("A great blessing, first: it changes how the fight works, from now until the ember goes out. Anyone can take any of them.");
                }
                if (stageT > 14) Tip("dash", "Dash", $"{Key("dash")}: a quick roll that nothing can touch. It has two charges, and they come back.", [Key("dash")]);
                if ((B.EmberLevel >= 4 && stageT > 70) || stageT > 110)
                {
                    Go(Stage.Road);
                    checkpoint = new XZ(p.X, p.Z);
                    G.Say("The ground goes still. For now. The road runs north, toward the Waystation.", null, 5);
                    Objective([("Survive the night", true, false), ("Follow the road north", false, false)]);
                    Tip("road", "The road north", "Follow the road. The dead keep coming; let them come to your weapons, and keep your feet moving.");
                }
                break;
            }
            case Stage.Road:
            case Stage.Road2:
            {
                if (spawnT <= 0 && n < 24)
                {
                    var def = Now == Stage.Road2 && B.Rng.Next() < 0.2 ? "risen_warrior" : B.Rng.Next() < 0.12 ? "risen_archer" : "risen";
                    SpawnAround(def, 1 + (B.Rng.Next() < 0.5 ? 1 : 0), 10, 15, 0.55, Now == Stage.Road2 ? 2 : 1);
                    spawnT = 1.3;
                    if (def == "risen_warrior") Tip("shield", "Shieldmen", "Bolts and arrows glance off a raised shield. Get to its side, or hit it with something that is not a projectile.");
                }
                var cart = L("cart"); var post = L("post");
                if (Now == Stage.Road && p.Z < cart.Z + 7)
                {
                    Go(Stage.Ambush);
                    checkpoint = new XZ(cart.X - 3, cart.Z + 8);
                    G.Say("A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting.", null, 5);
                    Objective([("Follow the road north", true, false), ("Survive the ambush at the wagon", false, false)]);
                    for (int i = 0; i < 10; i++) SpawnAround(i % 4 == 0 ? "risen_warrior" : "risen", 1, 5, 9, 0, 2);
                }
                if (Now == Stage.Road2 && Dist(p.X, p.Z, post.X, post.Z) < 18)
                {
                    Go(Stage.Post);
                    checkpoint = new XZ(post.X - 6, post.Z + 4);
                    knight = B.SpawnEnemy("barrow_knight", post.X - 1, post.Z - 1.5, new Battle.SpawnOpts { Level = 1, Tag = "knight", Style = SpawnStyle.Rise });
                    for (int i = 0; i < 4; i++) SpawnAround("risen", 1, 5, 9, 0, 2);
                    G.Say("Something in old armour is standing guard over the dead watchman. It turns to look at you.", null, 5);
                    Objective([("Survive the ambush at the wagon", true, false), ("Put down the Barrow Knight", false, false), ("Search the old Watch-post", false, false)]);
                    Tip("elite", "Elites", "Bigger, tougher, and worth it: elites carry better things. When a red line appears on the ground, it is about to come down it. Be off the line.", null, 12);
                }
                break;
            }
            case Stage.Ambush:
            {
                double want = Math.Min(46, 26 + stageT * 0.5);
                if (spawnT <= 0 && n < want)
                {
                    double r = B.Rng.Next();
                    SpawnAround(r < 0.22 ? "risen_warrior" : r < 0.32 ? "risen_archer" : "risen", 3 + (B.Rng.Next() < 0.5 ? 1 : 0), 8, 14, 0, 2);
                    spawnT = 1.05;
                }
                if (stageT > 48)
                {
                    Go(Stage.Road2);
                    checkpoint = new XZ(p.X, p.Z);
                    G.Say("The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.", null, 5);
                    Objective([("Survive the ambush at the wagon", true, false), ("Follow the road north", false, false)]);
                }
                break;
            }
            case Stage.Post:
                if (stageT > 8 && spawnT <= 0 && n < 16) { SpawnAround("risen", 1, 12, 16, 0.3, 2); spawnT = 2.5; }
                if (knight == null && !chestOpened)
                {
                    Tip("chest", "The Watch-post", "The watchman's chest is unguarded now.", [Key("interact")]);
                    Objective([("Put down the Barrow Knight", true, false), ("Search the old Watch-post", false, false)]);
                }
                if (p.Z < 21 && knight == null)
                {
                    Go(Stage.Barrow);
                    checkpoint = new XZ(p.X, p.Z);
                    StartBarrow();
                }
                break;
            case Stage.Barrow:
                if (caller != null)
                {
                    if (Dist(caller.X, caller.Z, p.X, p.Z) < 16 && B.Ability is AbilityKind ak)
                    {
                        var ab = Abilities.All[ak];
                        Tip("ability", ab.Name, $"{ab.Description} The Grave-Caller is raising the dead{(ab.Interrupts ? " — this will break its channel" : " — kill it before it raises too many")}.", [Key("ability")], 14);
                    }
                    if (spawnT <= 0 && n < 16 && stageT > 8) { SpawnAround("risen", 1, 11, 15, 0, 2); spawnT = 2.5; }
                }
                else if (stageT > 1)
                {
                    Go(Stage.ToFord);
                    var barrow = L("barrow");
                    checkpoint = new XZ(barrow.X + 10, barrow.Z - 6);
                    Objective([("Put down the Grave-Caller", true, false), ("Cross at the Low Ford", false, false)]);
                    G.Say("The dead go quiet. Somewhere ahead, water, and a cold blue light.", null, 5);
                }
                break;
            case Stage.ToFord:
                if (spawnT <= 0 && n < 18) { SpawnAround(B.Rng.Next() < 0.25 ? "risen_archer" : "risen", 1, 11, 15, 0.5, 2); spawnT = 2.4; }
                if (p.Z < L("ford").Z + 17) StartIntro();
                break;
            case Stage.Intro:
                RunIntro(dt);
                break;
            case Stage.Boss:
                if (warden is { Alive: true })
                {
                    int lit = LitCount;
                    Bar(new BossBar("The Ford-Warden", "Keeper of the Low Crossing", warden.Hp, warden.MaxHp, [0.7, 0.4], bar?.Channel, lit > 0));
                    if (stageT > 3) Tip("lamps", "The lamps", "While the three lamps burn, the Warden shrugs off most of every blow. Stand in front of a lamp when it charges — or break the lamps yourself.", null, 14);
                    if (ai.Mode == "channel")
                    {
                        bool breaks = B.Ability is AbilityKind k && Abilities.All[k].Interrupts;
                        Tip("channel", "Break the channel", $"It is calling up the drowned. {(breaks ? $"{Key("ability")} breaks it." : "Hurt it hard enough and it breaks.")} If it finishes, a lamp is lit again.", [Key("ability")], 10);
                    }
                    if (stageT > 40 && lit == 3) { shown.Remove("lamps2"); Tip("lamps2", "The lamps", "Lure its charge into a lamp: stand before one, and step aside at the last moment.", [Key("dash")], 10); }
                }
                if (p.Hp < B.MaxHp * 0.4) Tip("quaff", "Draughts", $"{Key("ultimate")}: drink a health draught.", [Key("ultimate")], 8);
                break;
            case Stage.Victory:
                RunVictory(dt);
                break;
            case Stage.Dawn:
            {
                // C04 A (docs/cinematics/shoot/c04a.md): the sun waits for her on the
                // north bank (or 25 s, if she stays to loot the ford), and comes up in it.
                if (!doused && G.CanCinematic("c04a"))
                {
                    if (p.Z < -50 || stageT > 25) FirstLight(p.Z >= -50);
                    break;
                }
                dawnK = Math.Min(1, dawnK + dt / 10);
                // The sun clears the trees, and the ember goes out.
                if (!doused && dawnK > 0.3) { doused = true; Douse(); }
                envT -= dt;
                G.SetAtmosphere(Atmospheres.Blend(Atmospheres.Night, Atmospheres.Dawn, dawnK * dawnK * (3 - 2 * dawnK)), envT <= 0);
                if (envT <= 0) envT = 1.2;
                if (dawnK >= 1 && stageT > 10) Go(Stage.Exit);
                break;
            }
            case Stage.Exit:
                if (p.Z < ExitZ && !finished) { finished = true; Finish(); }
                break;
        }
    }

    void StartBarrow()
    {
        if (B == null) return;
        Objective([("Search the old Watch-post", true, false), ("Put down the Grave-Caller", false, false)]);
        var barrow = L("barrow");
        caller = B.SpawnEnemy("grave_caller", barrow.X - 3, barrow.Z, new Battle.SpawnOpts { Level = 2, Tag = "caller", Elite = true });
        for (int i = 0; i < 5; i++)
        {
            double a = i / 5.0 * Math.PI * 2;
            B.SpawnEnemy(i % 3 == 0 ? "risen_warrior" : "risen", barrow.X + Math.Cos(a) * 4, barrow.Z + Math.Sin(a) * 4, new Battle.SpawnOpts { Style = SpawnStyle.Rise, Level = 2 });
        }
        G.Say("Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.", null, 6);
    }

    /* ------------------------------------------------------------- intro -- */

    void StartIntro()
    {
        if (B == null) return;
        Go(Stage.Intro);
        cutT = 0;
        checkpoint = new XZ(0, L("ford").Z + 19);
        G.Capture(true);
        var ford = L("ford");
        ClearAround(ford.X, ford.Z, 30);
        B.WorldRate = 0.001; B.WorldRateT = 1e9;
        G.SetHint(null);
        // C02 (docs/cinematics/shoot/c02.md): its last cue spawns him where it
        // leaves him (CineEvent "warden_up"); without it, the captions and barks.
        if (G.Cinematic("c02", () => { if (Now == Stage.Intro) WardenUp(); })) { introByCine = true; return; }
        G.Showcase((wardenHome.X + 9, G.Look.HeightAt(wardenHome.X, wardenHome.Z) + 7, wardenHome.Z + 15), (wardenHome.X, 0.4, wardenHome.Z));
    }

    bool introByCine;

    /// <summary>C02's end: the Warden up and facing her an arm's length off, the fight on.</summary>
    void WardenUp()
    {
        if (B == null || warden != null) return;
        wardenInCine = false;
        var p = B.Player;
        // Where the cinematic leaves him (its mark warden_end), facing her.
        var (wx, _, wz, _) = CineFile.Load("c02").Mark("warden_end");
        warden = B.SpawnEnemy("ford_warden", wx, wz, new Battle.SpawnOpts { Level = 1, Tag = "warden" });
        if (warden != null) { warden.Facing = Math.Atan2(p.Z - wz, p.X - wx); ai.Mode = "walk"; ai.T = 0; }
        wardenPos = (wx, wz, Math.PI / 2 - (warden?.Facing ?? 0));
        wardenView.Release();
        Go(Stage.Boss);
        Objective([("Cross at the Low Ford", false, false), ("Put out the lamps", false, true)]);
    }



    void RunIntro(double dt)
    {
        if (B == null || introByCine) return;
        cutT += dt;
        if (cutT > 0.8 && shown.Add("intro1")) G.Say("Something lies in the ford, larger than any man, with a lamp in its fist.", null, 3.6);
        if (cutT > 1.4 && shown.Add("intro1b")) B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "Lamps are lit... stay where they reach...", Speaker = "The Ford-Warden" });
        if (cutT > 3.4 && shown.Add("intro2b")) B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "Lie down.", Speaker = "The Ford-Warden" });
        if (cutT > 2.6 && shown.Add("intro2"))
        {
            wardenView.SetPose("wake");
            B.Events.Emit(new Ev.Shake { Amount = 0.5 });
            foreach (var py in pylons) B.Events.Emit(new Ev.Nova { X = py.X, Z = py.Z, Radius = 3, School = School.Frost, Duration = 0.9 });
        }
        if (cutT > 4.2 && shown.Add("intro3"))
        {
            G.Announce(new Announcement("The Ford-Warden", "Keeper of the Low Crossing", "danger", 3.4));
            B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "NONE CROSS AFTER DARK.", Speaker = "The Ford-Warden" });
        }
        if (cutT > 6.4)
        {
            G.Showcase(null);
            G.Capture(false);
            B.WorldRate = 1; B.WorldRateT = 0;
            warden = B.SpawnEnemy("ford_warden", wardenPos.X, wardenPos.Z, new Battle.SpawnOpts { Level = 1, Tag = "warden" });
            if (warden != null) { warden.Facing = Math.PI / 2; ai.Mode = "walk"; ai.T = 0; }
            wardenView.Release();
            Go(Stage.Boss);
            Objective([("Cross at the Low Ford", false, false), ("Put out the lamps", false, true)]);
        }
    }

    /* ----------------------------------------------------------- victory -- */

    void OnWardenDown(Enemy e)
    {
        if (B == null) return;
        ai.Mode = "dead";
        wardenView.SetPose("dead");
        wardenPos = (e.X, e.Z, Math.PI / 2 - e.Facing);
        Bar(null);
        B.Events.Emit(new Ev.Shake { Amount = 0.9 });
        G.Announce(new Announcement("The Ford-Warden falls", null, "boon", 3.2));
        for (int i = 0; i < pylons.Count; i++) if (litPylons[i]) { litPylons[i] = false; G.Look.SetLit(pylons[i].Light, false); }
        ClearAround(e.X, e.Z, 40);
        // What it leaves.
        B.SpawnPickup(PickupKind.Item, e.X + 1.5, e.Z + 1, 1, "wardens_lampiron");
        B.SpawnPickup(PickupKind.Item, e.X - 1.2, e.Z + 1.6, 3, "ember_shard");
        for (int i = 0; i < 12; i++) B.SpawnPickup(PickupKind.Gold, e.X + (B.Rng.Next() - 0.5) * 4, e.Z + (B.Rng.Next() - 0.5) * 4, 4);
        Go(Stage.Victory);
        cutT = 0;
        Objective([("Cross at the Low Ford", true, false)]);
        // C03 (docs/cinematics/shoot/c03.md), where he fell: he kneels where he
        // is, facing south, and she is put 4 m before him on the cut after the
        // blow. What it sets is set at the hand-back, so a skip sets it too.
        var marks = new Dictionary<string, double[]> { ["w"] = [e.X, e.Z, 0], ["her"] = [e.X, e.Z + 4, Math.PI] };
        if (G.Cinematic("c03", HeartGone, marks)) { victoryByCine = true; wardenInCine = true; }
    }

    bool victoryByCine;

    /// <summary>C03's events: Grimtunnel coming up under her hand, and going down with the heart.</summary>
    void GrimUp()
    {
        if (B == null) return;
        grim = B.Enemies.Living().FirstOrDefault(x => x.Tag == "grim");
        if (grim == null) return;
        grim.State = EnemyState.Surfacing; grim.StateT = 0.55;
        grimByCine = true;
        grim.Facing = Math.Atan2(B.Player.Z - grim.Z, B.Player.X - grim.X);
        B.Events.Emit(new Ev.Spawn { Enemy = grim.Id, X = grim.X, Z = grim.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
    }

    bool grimByCine;

    /// <summary>Gone down the hole: nothing of him left above the mud.</summary>
    void GrimGone()
    {
        GrimDown();
        if (grim != null) { if (grim.Alive) B?.Enemies.Release(grim); grim = null; }
    }

    void GrimDown()
    {
        if (B == null || (grim ??= B.Enemies.Living().FirstOrDefault(x => x.Tag == "grim")) is not { Alive: true } g) return;
        g.State = EnemyState.Burrowed;
        B.Events.Emit(new Ev.Spawn { Enemy = g.Id, X = g.X, Z = g.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
        B.Events.Emit(new Ev.Shake { Amount = 0.4 });
    }

    /// <summary>C03 handed back (or skipped): the heart is gone, and the dawn is coming.</summary>
    void HeartGone()
    {
        wardenInCine = false;
        GrimGone();
        shown.Add("grimGone");
        Taken();
        // The cinematic began the dawn (a fifth of the way); the road holds there until C04 finishes it.
        dawnK = 0.287;
        Dawnbreak();
    }

    void RunVictory(double dt)
    {
        if (B == null || victoryByCine) return;
        cutT += dt;
        double cx = wardenPos.X, cz = wardenPos.Z;
        // C03 (cin_heart_goes_down): a tired man's voice, the Order's question at the end of a watch.
        if (cutT > 0.3 && shown.Add("morning")) B.Events.Emit(new Ev.Bark { X = cx, Z = cz, Text = "Is it morning?", Speaker = "The Ford-Warden" });
        double cy = Math.Max(G.Look.HeightAt(cx, cz), waterY);
        if (cutT > 1.6 && !coreShown)
        {
            coreShown = true;
            core.Visible = true;
            corePos = (cx, cz); coreY = cy + 0.8;
            core.Light = 18;
            G.Say("Where the Warden fell, its heart is still burning: a stone the size of a fist, full of cold light.", null, 5);
            G.Showcase((cx + 6, cy + 6, cz + 11), (cx, cy + 1, cz));
            G.Capture(true);
        }
        if (core.Visible)
        {
            coreSpin += dt * 1.4;
            double pulse = 1 + Math.Sin(cutT * 5) * 0.08;
            if (grim == null) coreY = Math.Min(cy + 1.6, coreY + dt * 0.3);
            core.Place(corePos.X, coreY, corePos.Z, coreSpin, pulse);
            core.Light = 16 + Math.Sin(cutT * 7) * 3;
        }
        if (cutT > 4.2 && grim == null && !shown.Contains("grimGone"))
        {
            B.Events.Emit(new Ev.Shake { Amount = 0.7 });
            grim = B.SpawnEnemy("grimtunnel", cx + 2.2, cz + 1.2, new Battle.SpawnOpts { Style = SpawnStyle.Burrow, Disposition = Disposition.Neutral, Tag = "grim" });
            if (grim != null) { grim.State = EnemyState.Surfacing; grim.StateT = 0.55; }
            B.Events.Emit(new Ev.Spawn { Enemy = grim?.Id ?? -1, X = cx + 2.2, Z = cz + 1.2, Def = "grimtunnel", Style = SpawnStyle.Burrow });
        }
        if (grim is { Alive: true })
        {
            grim.Facing = Math.Atan2(cz - grim.Z, cx - grim.X);
            if (grim.State == EnemyState.Surfacing) { grim.StateT -= dt; if (grim.StateT <= 0) grim.State = EnemyState.Active; }
        }
        if (cutT > 5.4 && shown.Add("grim1")) B.Events.Emit(new Ev.Bark { X = cx + 2.2, Z = cz + 1.2, Text = "Ooh, still lit! Nobody's, is it? Nobody's!", Speaker = "Grimtunnel" });
        if (cutT > 6.9 && shown.Add("grim1b")) B.Events.Emit(new Ev.Bark { X = cx + 2.2, Z = cz + 1.2, Text = "...You smell like downstairs.", Speaker = "Grimtunnel" });
        if (cutT > 8.4 && shown.Add("grim2")) B.Events.Emit(new Ev.Bark { X = cx + 2.2, Z = cz + 1.2, Text = "Finders keepers, surface-m— (a sniff) ...Downstairs'll be ever so grateful.", Speaker = "Grimtunnel" });
        if (core.Visible && grim != null && cutT > 9.6)
        {
            double k = Math.Min(1, dt * 4);
            corePos = (corePos.X + (grim.X - corePos.X) * k, corePos.Z + (grim.Z - corePos.Z) * k);
            coreY += (cy + 1.2 - coreY) * k;
        }
        if (cutT > 11 && grim is { Alive: true } && grim.State != EnemyState.Burrowed)
        {
            grim.State = EnemyState.Burrowed;
            B.Events.Emit(new Ev.Spawn { Enemy = grim.Id, X = grim.X, Z = grim.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
            B.Events.Emit(new Ev.Shake { Amount = 0.4 });
            core.Visible = false;
            core.Light = 0;
        }
        if (cutT > 12 && grim != null)
        {
            if (grim.Alive) B.Enemies.Release(grim);
            grim = null;
            shown.Add("grimGone");
            Taken();
        }
        if (cutT > 13)
        {
            G.Showcase(null);
            G.Capture(false);
            dawnK = 0;
            Dawnbreak();
        }
    }

    /// <summary>What the night's end leaves: the Warden's heart is Grimtunnel's, and you know it.</summary>
    void Taken()
    {
        G.Apply("""
            [
              { "learn": "grimtunnel", "text": "You have seen Grimtunnel. The lamplings are digging for something." },
              { "history": { "id": "ford_warden_slain", "text": "put down the Ford-Warden at the Low Ford", "tags": ["deed", "undead"], "spread": 2, "sentiment": { "respect": 10 } } },
              { "history": { "id": "core_stolen", "text": "let a lampling steal the Warden's heart", "tags": ["lampling"], "spread": 1 } },
              { "give": "grimtunnels_lamp" }
            ]
            """);
        G.Toast(new Toast(ToastKind.Lore, "Grimtunnel took the Warden's heart", "They went down, not away. In the churned mud where he went: a lamp on a snapped strap, still warm. His.", Life: 8));
    }

    /// <summary>The gate opens and the night is over: the walk to the Waystation.</summary>
    void Dawnbreak()
    {
        if (B == null) return;
        Go(Stage.Dawn);
        B.Collision.RemoveTagged("gate");
        G.Say("Grey light, then gold. Up the road, the Waystation's gate is opening.", null, 6);
        Objective([("Walk up the road to the Waystation", false, false)]);
        W.Time = TimeOfDay.Dawn;
    }

    /// <summary>The dawn puts the ember out: the cards, the blessing, all it
    /// built. What the survivor carries, and what they learned, stay.</summary>
    /// <summary>C04 A: the ember goes out in it (its "douse" event), and the narrator says what Douse's caption did.</summary>
    void FirstLight(bool south)
    {
        doused = true;
        W.Facts["prologue.dawn_south"] = south;
        if (!G.Cinematic("c04a", () => { dawnK = 1; G.SetAtmosphere(Atmospheres.Dawn); if (!dousedByCine) Douse(false); })) { Douse(); return; }
    }

    bool dousedByCine;

    public override void CineEvent(string name)
    {
        switch (name)
        {
            // The cinematic's Warden is on: ours hides until it hands him back.
            case "warden_cine": wardenInCine = true; break;
            case "warden_up": WardenUp(); break;
            case "grim_up": GrimUp(); break;
            case "grim_down": GrimDown(); break;
            case "grim_gone": GrimGone(); break;
            case "douse": dousedByCine = true; Douse(false); break;
            // The ford after the night: nothing of the Warden left in it (already so in play).
            case "ford_clear": wardenView.Hide(); wardenGone = true; core.Visible = false; break;
        }
    }

    void Douse(bool caption = true)
    {
        if (B == null) return;
        var p = B.Player;
        B.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = 3.4, School = School.Fire, Duration = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.25 });
        int taught = G.Journey.Douse(B);
        G.Announce(new Announcement("The ember goes out", "It burns only in the dark", "zone", 4.2, "Dawn"));
        // What the night taught her, paid now the ember has gone: the first character level, on
        // its own, where it can be understood.
        if (taught > 0)
            G.After(4.6, () =>
            {
                var ch = G.Journey.Ch;
                G.Announce(new Announcement($"Level {ch.Level}", ch.TraitPicks > 0 ? "A new trait can be chosen (C)" : "Attribute points to spend (C)", "boon", 4.5, "What the night taught you"));
                G.Journey.Grew();
            });
        // Without C04 A the narrator's words are a caption; with it, they were said in it.
        if (caption) G.After(1.2, () => G.Say("As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again, from nothing. You try to call up your mother's face, and find it is not quite where you left it. Her voice is still there. \"Lamp's lit, Spark. Stay where it reaches.\"", null, 14));
        G.After(caption ? 11.5 : 9.5, () => Tip("day", "By day", $"By day the ember sleeps: you fight with what you carry, your art and your feet, and every fight teaches you ({Key("character")}). The ember is for the night.", [Key("character")], 14));
    }

    void Finish()
    {
        G.Apply("""[{ "set": { "prologue.done": true } }, { "quest": { "id": "prologue", "status": "resolved", "outcome": "resolved" } }]""");
        G.SetHint(null);
        G.SetObjectives(new());
        G.Travel("waystation", "The Waystation", "Where the three roads meet");
    }

    void OnKill(Enemy e, bool byPlayer)
    {
        // Pooled creatures are reused: forget them the moment they die.
        if (e.Tag == "warden") { OnWardenDown(e); warden = null; }
        if (e.Tag == "caller") { caller = null; G.Toast(new Toast(ToastKind.World, "The Grave-Caller is still", "The graves have stopped listening.")); }
        if (e.Tag == "knight" && B != null)
        {
            knight = null;
            B.SpawnPickup(PickupKind.Item, e.X, e.Z, 2, "ember_shard");
            B.SpawnPickup(PickupKind.Item, e.X + 1, e.Z - 0.5, 1, "bone_amulet");
            for (int i = 0; i < 6; i++) B.SpawnPickup(PickupKind.Gold, e.X + (G.Rng.NextDouble() - 0.5) * 3, e.Z + (G.Rng.NextDouble() - 0.5) * 3, 3);
        }
    }

    /* ------------------------------------------------------------ runtime -- */

    public override Arrival ArrivalFrom(string? from)
    {
        var gate = L("gate"); var camp = L("camp");
        // Back down the road from the Waystation: arrive at the north end, by the gate.
        return from == "waystation" ? new(gate.X + 0.5, ExitZ + 9, 0) : new(camp.X + 1.5, camp.Z - 1.5, Math.PI);
    }

    public override TimeOfDay TimeOf(WorldState w) => Now is Stage.Dawn or Stage.Exit ? TimeOfDay.Dawn : TimeOfDay.Night;
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) => t == TimeOfDay.Dawn ? Atmospheres.Dawn : Atmospheres.Night;

    public override void Begin(Battle b)
    {
        base.Begin(b);
        wardenView = G.Look.BossView("ford_warden");
        wardenView.SetPose("sleep");
        core = G.Look.Orb("#bfe6ff", 0.42);
        core.Visible = false;
        // The dead watchman at the post, where he fell: the fall played out and held.
        var man = L("watchman");
        watchman = G.Look.Fallen(new PersonSpec
        {
            Sex = Sex.Male, Outfit = Lore.OutfitFor(Sex.Male, "ranger", true, true), Beard = true, HairColor = "#4a3a2a", Skin = "#c8b0a0",
            Dye = new Dye { Cloth = "#4a5064" },
        }, new Held { Forearm = "shield_round" }, man.X, man.Z, 2.2, "Death_A");
        G.SetDraftTip(Draft);
        if (F("prologue.done").Truthy)
        {
            // Loaded after the prologue: the road at dawn, the dead at rest.
            Now = Stage.Exit; stageT = 0; dawnK = 1; doused = true;
            G.SetAtmosphere(Atmospheres.Dawn);
            b.Collision.RemoveTagged("gate");
            foreach (var p in pylons) G.Look.SetLit(p.Light, false);
            ai.Mode = "dead"; wardenGone = true;
            wardenView.Hide();
            return;
        }
        G.SetAtmosphere(Atmospheres.Night);
        // C01, the opening (docs/cinematics/shoot/c01.md), once a journey: it
        // wakes her by the fire and hands back as the dead come up. Where no
        // cinematic can play (the tests, a quick start), its lines are captions.
        bool woke = F("prologue.woke").Truthy;
        W.Facts["prologue.woke"] = true;
        if (!woke && G.Cinematic("c01", Woken)) return;
        Woken();
        if (woke) return;
        G.Say("Your bedroll has not been slept in.", null, 3);
        G.After(3.2, () => G.Say("Prints in the frost, your own. They come up from the river. None go down to it.", null, 5));
        G.After(8.4, () => G.Say("Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder.", null, 5.5));
        // Vonnra, unnamed: the fortune opens on the same words (docs/STORY_BIBLE.md, "Who tells it").
        G.After(14.1, () => G.Say("Come up, traveller. ...No charge, this once.", "A voice up the road", 4));
        G.After(18.3, () => G.Say("Past the firelight, the frost is breaking.", null, 3.5));
    }

    /// <summary>Awake by the fire, the dead coming up: the night begins.</summary>
    void Woken()
    {
        Objective([("Survive the night", false, false)]);
        G.AnnounceZone();
    }

    public override void Step(double dt) => Director(dt);

    public override void Frame(double dt)
    {
        // C03's Grimtunnel comes up while the zone's director waits: his surfacing is kept here.
        if (grimByCine && grim is { Alive: true, State: EnemyState.Surfacing } gs) { gs.StateT -= dt; if (gs.StateT <= 0) gs.State = EnemyState.Active; }
        if (wardenGone) return;
        if (wardenInCine) { wardenView.Hide(); return; }
        if (warden is { Alive: true } && warden.State != EnemyState.Dying) wardenPos = (warden.X, warden.Z, Math.PI / 2 - warden.Facing);
        double wy = Math.Max(G.Look.HeightAt(wardenPos.X, wardenPos.Z), waterY - 0.25);
        wardenView.Glow = Math.Clamp(0.3 + LitCount * 0.25, 0, 1);
        wardenView.Update(warden is { Alive: true } ? warden : null, wardenPos.X, wy, wardenPos.Z, wardenPos.Facing, dt);
        if (ai.Mode == "dead")
        {
            if (deadT < 0) deadT = 0;
            deadT += dt;
            if (deadT > 9) { wardenView.Hide(); wardenGone = true; }
        }
    }

    public override bool OnDeath(string killer)
    {
        // The ember is not done with you. Up again where you were last safe.
        if (B == null) return true;
        var battle = B;
        G.After(2.6, () =>
        {
            G.Say("The ember will not let you go so easily.", null, 3.5);
            battle.Over = null;
            var p = battle.Player;
            p.Alive = true;
            p.Hp = battle.MaxHp;
            p.Iframes = 3;
            p.X = checkpoint.X; p.Z = checkpoint.Z;
            ClearAround(p.X, p.Z, 16);
            G.Revived(p.X, p.Z);
            if (warden is { Alive: true } && Now == Stage.Boss)
            {
                warden.Hp = Math.Min(warden.MaxHp, warden.Hp + warden.MaxHp * 0.25);
                warden.X = wardenHome.X; warden.Z = wardenHome.Z;
                ai.Mode = "walk";
                if (bar != null) Bar(bar with { Channel = null });
            }
        });
        return true;
    }

    public override List<MapMark> MapMarks()
    {
        XZ at(string k) => L(k);
        return
        [
            new(at("camp").X, at("camp").Z, "Your camp", MarkKind.Place), new(at("cart").X, at("cart").Z, "Broken cart", MarkKind.Place),
            new(at("post").X, at("post").Z, "Watch-post", MarkKind.Place), new(at("barrow").X, at("barrow").Z, "The Barrow", MarkKind.Place),
            new(at("ford").X, at("ford").Z, "The Low Ford", wardenGone ? MarkKind.Place : MarkKind.Danger),
            new(at("gate").X, at("gate").Z + 4, "North, to the Waystation", MarkKind.Exit),
        ];
    }

    public override AmbienceMix Ambience(double x, double z)
    {
        bool dawn = Now is Stage.Dawn or Stage.Exit;
        return new AmbienceMix
        {
            Wind = 0.55, Leaves = 0.35, Fire = Warmth(x, z), Water = Math.Clamp(1 - Math.Abs(z - RiverZ(x)) / 26, 0, 1),
            Crickets = dawn ? 0.15 : 0.75, Owl = dawn ? 0 : 0.6, Birds = dawn ? 0.7 : 0,
        };
    }

    public override Dictionary<string, object?> Debug() => new()
    {
        ["stage"] = Now.ToString(), ["stageT"] = stageT, ["chestOpened"] = chestOpened, ["lit"] = LitCount, ["wardenHp"] = warden?.Hp,
        ["wardenMode"] = ai.Mode, ["checkpoint"] = $"{checkpoint.X:0.0},{checkpoint.Z:0.0}",
    };

    public override void Dispose()
    {
        base.Dispose();
        watchman?.Dispose();
        wardenView?.Dispose();
        core?.Dispose();
        G.SetHint(null);
        G.SetBoss(null);
    }
}

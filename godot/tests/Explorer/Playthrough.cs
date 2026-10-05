using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Stage = SurvivorUnchained.Play.Zones.Prologue.Stage;

namespace SurvivorUnchained.Tests.Explorer;

/// <summary>A journey being played by the explorer: the zone it is in, as
/// the game would have built it, and whatever conversation or screen is
/// open. Everything is done through the game's own logic (the zone's
/// interactables, the dialogue runner, the journey's shops and beds, the
/// arena's reckoning); the explorer only chooses.</summary>
sealed class Playthrough
{
    public Journey J = null!;
    public ExplorerHost? Host;
    public ZoneRuntime? Zone;
    public Battle? B;
    public ZoneMeta? Meta;
    public Visit Visit = null!;
    public Mode Mode;
    public string? Npc;
    public DialogueRunner? Runner;
    public ArenaSpec? Arena;
    /// <summary>Somebody is told what went wrong (null while replaying).</summary>
    public Action<string, string, string, string>? Report;

    void Tell(string kind, string key, string text, string file) => Report?.Invoke(kind, key, text, file);

    /* ------------------------------------------------------------ zones -- */

    static readonly Dictionary<string, ZoneMeta> metas = new();
    static readonly Dictionary<string, Heightfield> grounds = new();
    static readonly Dictionary<string, CollisionWorld> walls = new();

    static ZoneMeta MetaOf(string id) => metas.TryGetValue(id, out var m) ? m : metas[id] = ZoneMeta.Load(id);
    static Heightfield GroundOf(string id) => grounds.TryGetValue(id, out var g) ? g : grounds[id] = Heightfield.Load(MetaOf(id));

    /// <summary>The zone's colliders, copied from one built once: building
    /// them is most of what entering a zone costs.</summary>
    static CollisionWorld WallsOf(string id)
    {
        if (!walls.TryGetValue(id, out var w)) walls[id] = w = MetaOf(id).Collision();
        var copy = (CollisionWorld)typeof(object).GetMethod("MemberwiseClone", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(w, null)!;
        foreach (var f in typeof(CollisionWorld).GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic))
        {
            object? v = f.GetValue(w);
            object? c = v switch
            {
                Dictionary<int, Collider> d => new Dictionary<int, Collider>(d),
                Dictionary<long, List<int>> d => d.ToDictionary(kv => kv.Key, kv => new List<int>(kv.Value)),
                byte[] a => a.Clone(),
                List<Collider> => new List<Collider>(),
                HashSet<int> => new HashSet<int>(),
                _ => v,
            };
            if (!ReferenceEquals(c, v)) f.SetValue(copy, c);
        }
        return copy;
    }

    static ZoneRuntime Make(string id, IZoneHost host, ZoneMeta meta) => id switch
    {
        "lowford" => new Prologue(host, meta),
        "waystation" => new Waystation(host, meta),
        "verge" => new Verge(host, meta),
        _ => throw new ArgumentException($"no zone {id}"),
    };

    public static Journey Load(string save)
    {
        return Journey.From(Json.Parse<SaveData>(save), 0);
    }
    public string Save() => Json.Write(J.ToSave(new SaveLocation { Zone = Visit.Zone }));

    /// <summary>A zone built the way the game builds it (Game.EnterZone and
    /// EnterPlay): its runtime, the walk or fight, its people stood up.</summary>
    static Playthrough Build(Journey j, string zone, string? from, (double X, double Z, double Facing)? at)
    {
        var p = new Playthrough { J = j, Meta = MetaOf(zone) };
        j.World.Arena = null;
        var host = new ExplorerHost(j, p.Meta, GroundOf(zone));
        var z = Make(zone, host, p.Meta);
        var start = at is var (ax, az, af) ? new Arrival(ax, az, af) : z.ArrivalFrom(from);
        var walls = WallsOf(zone);
        var b = j.StartBattle(z.Combat, walls, GroundOf(zone).HeightAt, start.X, start.Z, start.Facing, 11, ember: z.Ember);
        var zh = z.Hooks;
        b.Hooks = new BattleHooks
        {
            OnLoot = zh.OnLoot, BossTick = zh.BossTick, OnHitProp = zh.OnHitProp,
            OnKill = (e, by) => { host.Journey.Killed(e, by); zh.OnKill?.Invoke(e, by); },
            OnPickup = pk => (zh.OnPickup == null || zh.OnPickup(pk)) && host.Journey.PickedUp(pk),
        };
        host.Battle = b;
        p.Host = host; p.Zone = z; p.B = b;
        z.Begin(b);
        j.World.Facts["player.zone"] = z.Id;
        return p;
    }

    /// <summary>Arrive in a zone: the journey as it came is kept, to build the
    /// visit again from.</summary>
    public static Playthrough Enter(Journey j, string zone, string? from, (double X, double Z, double Facing)? at, Action<string, string, string, string>? report)
    {
        var save = Json.Write(j.ToSave(new SaveLocation { Zone = zone }));
        var p = Build(j, zone, from, at);
        p.Report = report;
        p.Visit = new Visit(zone, from, at, save, null, "");
        p.Settle();
        p.Visit = p.Visit with { ZoneMark = p.Mark() };
        return p;
    }

    /// <summary>A visit rebuilt: the zone entered as it was, and everything
    /// done since done again.</summary>
    public static Playthrough Rebuild(Visit v, Action<string, string, string, string>? report = null)
    {
        var p = Build(Load(v.EntrySave), v.Zone, v.From, v.At);
        p.Visit = v with { Done = null };
        p.Settle();
        foreach (var s in Steps.List(v.Done))
            if (p.Do(s.Key) is not { } r || r.Kind != Kind.Stay)
                throw new InvalidOperationException($"replay went astray at {s.Key} ({s.Words}) in {v.Zone}");
        p.Report = report;
        p.Visit = v;
        return p;
    }

    /// <summary>The night on the Low Ford road, played through by a survivor
    /// nothing can hurt: it goes where the night's script waits for it, puts
    /// down whatever stands up (not in the cut-scenes), and opens and reads
    /// whatever is there. Null (and why) if the night never ends.</summary>
    public static (Playthrough? Play, string? Stuck) Night(Journey j, Action<string, string, string, string>? report)
    {
        var p = Build(j, "lowford", null, null);
        p.Report = report;
        p.Visit = new Visit("lowford", null, null, "", null, "");
        var z = (SurvivorUnchained.Play.Zones.Prologue)p.Zone!;
        var b = p.B!;
        var host = p.Host!;
        var used = new HashSet<string>();
        const double dt = 1 / 30.0;
        var stage = z.Now;
        double since = 0;
        XZ L(string k) => p.Meta!.Place("LOWFORD", k);
        for (double t = 0; t < 20 * 60; t += dt)
        {
            b.Player.Hp = b.MaxHp;
            var now = z.Now;
            if (now != stage) { stage = now; since = 0; }
            if ((since += dt) > 180) return (null, $"the night stood still at {now} for three minutes");
            // Where the script waits for the survivor.
            XZ to = now switch
            {
                Stage.Road or Stage.Ambush => L("cart"),
                Stage.Road2 => L("post"),
                Stage.Post => b.Enemies.Living().Any(e => e.Tag == "knight") || z.Interactables.Any(i => !used.Contains(i.Id) && (i.When?.Invoke() ?? true) && Dist(i.X, i.Z, b.Player.X, b.Player.Z) < 40)
                    ? L("post") : L("barrow"),
                Stage.Barrow => L("barrow"),
                Stage.ToFord or Stage.Intro or Stage.Boss
                    or Stage.Victory or Stage.Dawn => L("ford"),
                Stage.Exit => new XZ(L("gate").X, p.Meta!.Places["LOWFORD"].GetProperty("exitZ").GetDouble() - 4),
                _ => L("camp"),
            };
            // Whatever can be opened or read nearby, once.
            foreach (var it in z.Interactables.ToList())
            {
                if (used.Contains(it.Id) || Dist(it.X, it.Z, b.Player.X, b.Player.Z) > 40) continue;
                if ((it.When != null && !it.When()) || it.Locked?.Invoke() != null) continue;
                used.Add(it.Id);
                b.Player.X = it.X; b.Player.Z = it.Z;
                it.Act();
            }
            b.Player.X = to.X; b.Player.Z = to.Z;
            bool fighting = now is not (Stage.Wake or Stage.Intro or Stage.Victory
                or Stage.Dawn or Stage.Exit);
            if (fighting)
                foreach (var e in b.Enemies.Living().ToList())
                    if (b.Targetable(e) && Dist(e.X, e.Z, b.Player.X, b.Player.Z) < 45) b.KillEnemy(e, true, b.Weapons.FirstOrDefault());
            z.Step(dt);
            b.Tick(dt, 0, 0);
            b.Events.Drain();
            z.Frame(dt);
            host.Pass(dt);
            foreach (var pk in b.Pickups.Living().Where(k => k.Kind is not (PickupKind.Heal or PickupKind.Magnet)).ToList()) Collect.Invoke(b, [pk]);
            if (host.Travelled is { } tr)
            {
                host.Travelled = null;
                p.Move(tr.Zone, "lowford", null);
                return (p, null);
            }
        }
        return (null, $"the night was not over after twenty minutes (at {z.Now})");
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    /// <summary>A journey alone, in a conversation or a screen: no zone is
    /// needed until the survivor is walking about again.</summary>
    public static Playthrough Paused(Node n, Action<string, string, string, string>? report)
    {
        var p = new Playthrough { J = Load(n.Save), Visit = n.Visit, Mode = n.Mode, Npc = n.Npc, Report = report };
        if (n.Mode == Mode.Talk)
        {
            p.Runner = new DialogueRunner(Dialogue.Find(n.Npc!)!, p.J.Ctx);
            NodeField.SetValue(p.Runner, p.Runner.Convo.Nodes[n.At!]);
        }
        if (n.Arena != null) p.Arena = Json.Parse<ArenaSpec>(n.Arena);
        return p;
    }

    static readonly FieldInfo NodeField = typeof(DialogueRunner).GetField("<Node>k__BackingField", BindingFlags.Instance | BindingFlags.NonPublic)!;

    /// <summary>The swap: the same zone, a fresh copy of the journey (the
    /// zone reads the world through its host each time it looks).</summary>
    public void Swap(string save, double x, double z)
    {
        J = Load(save);
        Host!.Journey = J;
        Host.Clear();
        B!.Player.X = x; B.Player.Z = z;
        Mode = Mode.Roam; Npc = null; Runner = null; Arena = null;
    }

    /* ------------------------------------------------------- time passes -- */

    /// <summary>The world runs on a little (the game's frames and steps): what
    /// was put off comes due, a lit fuse burns down, people go where the hour
    /// sends them. Nothing fights: the explorer chooses its fights.</summary>
    public void Settle()
    {
        if (Zone == null) return;
        for (int i = 0; i < 40 && (i < 4 || Host!.Pending); i++)
        {
            Zone.Step(1);
            Zone.Frame(1);
            Host!.Pass(1);
            if (Host.Travelled != null || Host.Entered != null) break;
        }
    }

    /* ----------------------------------------------- what can be done -- */

    static readonly Random Lucky = new LuckyRandom();
    /// <summary>The best of every roll: every line a shop might stock is on its shelf.</summary>
    sealed class LuckyRandom : Random
    {
        public override double NextDouble() => 0;
        public override int Next(int max) => 0;
        public override int Next(int min, int max) => min;
        public override int Next() => 0;
        protected override double Sample() => 0;
    }

    /// <summary>The things that matter to the story: what a condition asks
    /// for, what a choice takes, what carries a tag something asks about.</summary>
    public static HashSet<string> StoryItems = new();

    public int MaxDay = 8;

    /// <summary>Everything the survivor could do now, by key and in words.</summary>
    public List<Step> Choices()
    {
        var list = new List<Step>();
        var w = J.World;
        switch (Mode)
        {
            case Mode.Roam:
            {
                var shown = new List<Interactable>();
                foreach (var it in Zone!.Interactables.ToList())
                {
                    if (it.When != null && !it.When()) continue;
                    shown.Add(it);
                    if (it.Locked?.Invoke() is { } why) { Locks?.Invoke($"{Zone.Id}:{it.Id}", why); continue; }
                    list.Add(new Step($"use:{it.Id}", $"{it.Verb}: {it.Name} ({Zone.Id})"));
                }
                // The zone's named places, for what notices you only when you
                // come near (going to an interactable goes near it already).
                foreach (var (table, places) in Meta!.Places)
                {
                    if (places.ValueKind != System.Text.Json.JsonValueKind.Object) continue;
                    foreach (var pl in places.EnumerateObject())
                    {
                        if (pl.Value.ValueKind != System.Text.Json.JsonValueKind.Object) continue;
                        var at = Meta.Place(table, pl.Name);
                        if (shown.Any(i => Dist(i.X, i.Z, at.X, at.Z) < 20)) continue;
                        list.Add(new Step($"go:{table}.{pl.Name}", $"Walk to {pl.Name} ({Zone.Id})"));
                    }
                }
                if (Zone.Combat)
                {
                    foreach (var g in Groups().Keys) list.Add(new Step($"fight:{g}", $"Fight and win: {g} ({Zone.Id})"));
                    list.Add(new Step("fall", $"Fall in a fight ({Zone.Id})"));
                    // Things in the world a blow can break, or fire can light.
                    bool fire = Fire();
                    foreach (var g in Props().Keys)
                    {
                        list.Add(new Step($"strike:{g}", $"Strike the {g.Replace('@', ' ').Replace(" ", " by the ")} ({Zone.Id})"));
                        if (fire) list.Add(new Step($"burn:{g}", $"Set fire to the {g.Replace('@', ' ').Replace(" ", " by the ")} ({Zone.Id})"));
                    }
                }
                // What the survivor makes of themselves: a trait the story asks
                // about, something worn that the story notices.
                if (J.Ch.TraitPicks > 0)
                    foreach (var t in Callings.LevelupTraits.Where(t => StoryTraits.Contains(t) && !J.Ch.Traits.Contains(t)))
                        list.Add(new Step($"trait:{t}", $"Become: {t}"));
                foreach (var it in J.Ch.Pack.Where(i => i != null && Tagged(i.Def)).GroupBy(i => i!.Def).Select(g => g.First()!))
                    if (Items.SlotFor(Items.Get(it.Def)) != null) list.Add(new Step($"wear:{it.Def}", $"Wear {it.Def}"));
                foreach (var slot in Items.EquipSlots)
                    if (slot != EquipSlot.Weapon && J.Ch.Equipment[slot] is { } worn && Tagged(worn.Def)) list.Add(new Step($"doff:{slot}", $"Take off {worn.Def}"));
                break;
            }
            case Mode.Talk:
            {
                var p = Runner!.Present()!;
                if (p.Choices.Count == 0) list.Add(new Step("next", $"{Npc}.{p.Node.Id}: (continue)"));
                foreach (var c in p.Choices.Where(c => c.Enabled))
                    list.Add(new Step($"say:{c.Index}", $"{Npc}.{p.Node.Id}: \"{c.Text}\""));
                break;
            }
            case Mode.Shop:
            {
                var stock = w.Shops.GetValueOrDefault(Npc!)?.Stock ?? new();
                // What the story asks for, if not already carried; and what of the
                // story's own things the shop will take (a quest item sold is gone).
                foreach (var it in stock.Where(i => StoryItems.Contains(i.Def) && Inventory.Count(J.Ch, i.Def) == 0).GroupBy(i => i.Def).Select(g => g.First()))
                    if (J.PriceOf(Npc!, it.Uid, true) is int price && price <= J.Ch.Gold)
                        list.Add(new Step($"buy:{it.Def}", $"Buy {it.Def} from {Npc} for {price} gold"));
                foreach (var it in J.Ch.Pack.Where(i => i != null && StoryItems.Contains(i.Def) && Items.Get(i.Def).Kind is ItemKind.Quest or ItemKind.Material).GroupBy(i => i!.Def).Select(g => g.First()!))
                    if (J.PriceOf(Npc!, it.Uid, false) is int price)
                        list.Add(new Step($"sell:{it.Def}", $"Sell {it.Def} to {Npc} for {price} gold"));
                list.Add(new Step("leave", $"Leave {Npc}'s wares"));
                break;
            }
            case Mode.Rest:
                if (w.Day < MaxDay && J.Ch.Gold >= J.RestCost) list.Add(new Step("sleep", $"Sleep at the inn ({J.RestCost} gold): day {w.Day + 1} dawns"));
                if (w.Time != TimeOfDay.Night) list.Add(new Step("night", "Wait for nightfall"));
                list.Add(new Step("leave", "Leave the bed for later"));
                break;
            case Mode.Maps:
                foreach (var r in w.Rematches)
                {
                    list.Add(new Step($"again:{r.Id}:won", $"Take {r.Name} again, and win"));
                    list.Add(new Step($"again:{r.Id}:lost", $"Take {r.Name} again, and lose"));
                }
                list.Add(new Step("table:won", "Take the Wayfinder's first map, and win"));
                list.Add(new Step("table:lost", "Take the Wayfinder's first map, and lose"));
                list.Add(new Step("leave", "Leave the Wayfinder's table"));
                break;
            case Mode.Arena:
                list.Add(new Step("won", $"Win the arena: {Arena!.Name}"));
                list.Add(new Step("lost", $"Lose the arena: {Arena!.Name}"));
                break;
        }
        return list;
    }

    /// <summary>A choice or interactable shown but refused, and why.</summary>
    public Action<string, string>? Locks;

    /// <summary>What there is to fight here: the wood's creatures by who they are.</summary>
    Dictionary<string, List<Enemy>> Groups()
    {
        var g = new Dictionary<string, List<Enemy>>();
        foreach (var e in B!.Enemies.Living())
        {
            if (e.State == EnemyState.Dying || e.Disposition == Disposition.Ally) continue;
            var k = e.Tag ?? e.Def.Family.ToString().ToLowerInvariant();
            if (!g.TryGetValue(k, out var l)) g[k] = l = new();
            l.Add(e);
        }
        return g;
    }

    /* ----------------------------------------------------------- doing -- */

    /// <summary>What a step came to: invalid (null), or done (Moved when the
    /// survivor went to another zone or back to walking from a screen).</summary>
    public enum Kind { Stay, NeedZone, Moved }
    public sealed record Result(Kind Kind);
    static readonly Result Stay = new(Kind.Stay), NeedZone = new(Kind.NeedZone), Moved = new(Kind.Moved);

    /// <summary>Do one thing. Null if it could not be done after all.</summary>
    public Result? Do(string key)
    {
        switch (Mode)
        {
            case Mode.Roam: return Roam(key);
            case Mode.Talk: return Talk(key);
            case Mode.Shop:
                if (key.StartsWith("buy:"))
                {
                    var it = J.World.Shops.GetValueOrDefault(Npc!)?.Stock.FirstOrDefault(i => i.Def == key[4..]);
                    if (it == null) return null;
                    J.Buy(Npc!, it.Uid);
                    return Stay;
                }
                if (key.StartsWith("sell:"))
                {
                    var it = J.Ch.Pack.FirstOrDefault(i => i?.Def == key[5..]);
                    if (it == null) return null;
                    J.Sell(Npc!, it.Uid);
                    return Stay;
                }
                return key == "leave" ? Walk() : null;
            case Mode.Rest:
                if (key == "sleep")
                {
                    CheckDawn();
                    if (J.Sleep(B, () => 0.5) == null) return null;
                }
                else if (key == "night") J.Nightfall();
                else if (key != "leave") return null;
                return Walk();
            case Mode.Maps:
            {
                if (key == "leave") return Walk();
                var at = Waystation.AtTable;
                ArenaSpec spec;
                if (key.StartsWith("table:"))
                {
                    int won = (int)J.World.Fact("arena.best").Number;
                    var o = Maps.MapOffers.Today(J.World.Day, Math.Max(1, won), (int)J.World.Fact("map.drawn").Number)[0];
                    spec = Arenas.FromTable(o, Visit.Zone, at.X, at.Z, at.Facing);
                }
                else
                {
                    var id = key[6..key.LastIndexOf(':')];
                    var lost = J.World.Rematches.FirstOrDefault(r => r.Id == id);
                    if (lost == null) return null;
                    spec = Arenas.Again(lost, Visit.Zone, at.X, at.Z, at.Facing);
                }
                Arenas.Begin(J.World, spec);
                Arena = spec;
                return Reckon(key.EndsWith(":won"));
            }
            case Mode.Arena:
                return key is "won" or "lost" ? Reckon(key == "won") : null;
        }
        return null;
    }

    Result? Roam(string key)
    {
        var host = Host!;
        var b = B!;
        host.Clear();
        if (key.StartsWith("use:"))
        {
            var it = Zone!.Interactables.FirstOrDefault(i => i.Id == key[4..]);
            if (it == null) return null;
            // Walk up to it: whatever notices you there, notices you.
            b.Player.X = it.X; b.Player.Z = it.Z;
            Zone.Step(1 / 60.0);
            if (host.Travelled != null || host.Entered != null) return Followed();
            if ((it.When != null && !it.When()) || it.Locked?.Invoke() != null) return null;
            it.Act();
            return Followed();
        }
        if (key.StartsWith("go:"))
        {
            var dot = key.IndexOf('.');
            var at = Meta!.Place(key[3..dot], key[(dot + 1)..]);
            b.Player.X = at.X; b.Player.Z = at.Z;
            Settle();
            return Followed();
        }
        if (key.StartsWith("fight:"))
        {
            if (!Groups().TryGetValue(key[6..], out var foes)) return null;
            foreach (var e in foes)
            {
                b.Player.X = e.X + 1.5; b.Player.Z = e.Z;
                if (e.Alive && e.State != EnemyState.Dying) b.KillEnemy(e, true, b.Weapons.FirstOrDefault());
            }
            // What they dropped, picked up.
            foreach (var pk in b.Pickups.Living().Where(k => k.Kind is not (PickupKind.Ember or PickupKind.Heal or PickupKind.Magnet)).ToList()) Collect.Invoke(b, [pk]);
            J.BankGold(b);
            Settle();
            return Followed();
        }
        if (key.StartsWith("strike:") || key.StartsWith("burn:"))
        {
            bool burn = key.StartsWith("burn:");
            if (burn && !Fire()) return null;
            if (!Props().TryGetValue(key[(key.IndexOf(':') + 1)..], out var hit)) return null;
            foreach (var c in hit)
            {
                b.Player.X = c.X + c.R + 1; b.Player.Z = c.Z;
                Zone!.Hooks.OnHitProp?.Invoke(c.Tag!, c.Id, burn ? School.Fire : School.Physical, 1000, c.X, c.Z);
            }
            return WalkOn();
        }
        if (key.StartsWith("trait:"))
        {
            if (J.Ch.TraitPicks <= 0) return null;
            J.PickTrait(key[6..], b);
            return WalkOn();
        }
        if (key.StartsWith("wear:"))
        {
            var it = J.Ch.Pack.FirstOrDefault(i => i?.Def == key[5..]);
            if (it == null) return null;
            J.Equip(it.Uid, null, b);
            return WalkOn();
        }
        if (key.StartsWith("doff:"))
        {
            if (!Enum.TryParse<EquipSlot>(key[5..], out var slot)) return null;
            J.Unequip(slot, b);
            return WalkOn();
        }
        if (key == "fall")
        {
            J.Ch.Stats.Deaths++;
            if (Zone!.OnDeath("the wood")) { Settle(); return Followed(); }
            J.Fell(Zone.Id, Zone.Name, "the wood", b.Player, new Random(7));
            return Move("waystation", "death", null);
        }
        return null;
    }

    /// <summary>Can the survivor set something alight (a fire skill carried)?</summary>
    bool Fire()
    {
        var kit = Character.Kit(J.Ch);
        return kit.Weapons.Concat(kit.Learned).Any(w => Content.Weapons.All.TryGetValue(w.Id, out var d) && d.School == School.Fire);
    }

    /// <summary>The tagged things in the zone a blow lands on, by what they
    /// are and the named place they are nearest.</summary>
    Dictionary<string, List<Collider>> Props()
    {
        var g = new Dictionary<string, List<Collider>>();
        var named = Meta!.Places.Where(t => t.Value.ValueKind == System.Text.Json.JsonValueKind.Object)
            .SelectMany(t => t.Value.EnumerateObject().Where(p => p.Value.ValueKind == System.Text.Json.JsonValueKind.Object).Select(p => (p.Name, At: Meta.Place(t.Key, p.Name)))).ToList();
        foreach (var c in B!.Collision.All().Where(c => c.Tag != null))
        {
            var near = named.OrderBy(n => Dist(n.At.X, n.At.Z, c.X, c.Z)).Select(n => n.Name).FirstOrDefault() ?? "";
            var k = $"{c.Tag!.Split(':')[0]}@{near}";
            if (!g.TryGetValue(k, out var l)) g[k] = l = new();
            l.Add(c);
        }
        return g;
    }

    public static HashSet<string> StoryTags = new(), StoryTraits = new();
    static bool Tagged(string def) => Items.Find(def)?.Tags?.Any(StoryTags.Contains) ?? false;

    static readonly MethodInfo Collect = typeof(Battle).GetMethod("Collect", BindingFlags.Instance | BindingFlags.NonPublic)!;

    /// <summary>What the zone asked the game for, done: a conversation, the
    /// table, an arena, another zone. Otherwise time runs on a little.</summary>
    Result? Followed()
    {
        var host = Host!;
        if (host.Talked is { } npc)
        {
            host.Talked = null;
            return StartTalk(npc) ? Stay : WalkOn();
        }
        if (host.Opened is { } o)
        {
            host.Opened = null;
            if (o == "maps") { Mode = Mode.Maps; return Stay; }
            Tell("broken", $"open:{o}", $"The zone opens a screen the game does not know: {o}", "logic/Play/Zones");
            return WalkOn();
        }
        if (host.Entered is { } spec)
        {
            host.Entered = null;
            Arenas.Begin(J.World, spec);
            Arena = spec;
            Mode = Mode.Arena;
            return Stay;
        }
        if (host.Travelled is { } t)
        {
            host.Travelled = null;
            return Move(t.Zone, Zone!.Id, null);
        }
        return WalkOn();
    }

    Result WalkOn()
    {
        Settle();
        if (Host!.Travelled != null || Host.Entered != null) return Followed()!;
        return Stay;
    }

    /// <summary>Off to another zone (Game.Travel): the wounds come along.</summary>
    Result Move(string zone, string from, (double, double, double)? at)
    {
        J.Capture(B);
        var next = Enter(J, zone, from, at, Report);
        next.MaxDay = MaxDay; next.Locks = Locks;
        J = next.J; Host = next.Host; Zone = next.Zone; B = next.B; Meta = next.Meta; Visit = next.Visit;
        Mode = Mode.Roam; Npc = null; Runner = null; Arena = null;
        return Moved;
    }

    /// <summary>An arena over (Arenas.Won and Finish): the story told how it
    /// went, and back to where the survivor was pulled from.</summary>
    Result Reckon(bool won)
    {
        var spec = Arena!;
        var b = J.StartBattle(true, new CollisionWorld(64), (_, _) => 0, 0, 0, 0, (uint)spec.Seed, arena: true);
        b.Time = spec.Minutes * 60 * (won ? 1 : 0.5);
        if (won) Arenas.Won(J, spec);
        Arenas.Finish(J, b, spec, won);
        J.Capture(b);
        return Move(spec.ReturnZone, "arena", (spec.ReturnX, spec.ReturnZ, spec.ReturnFacing));
    }

    /// <summary>Back from a screen to walking about: needs the zone again.</summary>
    Result Walk()
    {
        Mode = Mode.Roam; Npc = null; Runner = null;
        return Zone == null ? NeedZone : WalkOn();
    }

    /* ---------------------------------------------------- conversations -- */

    /// <summary>The game's Talk: nothing happens if there is nobody to talk to.</summary>
    bool StartTalk(string npc)
    {
        var convo = Dialogue.Find(npc);
        if (convo == null)
        {
            Tell("broken", $"talk:{npc}", $"Something offers a conversation with {npc}, and there is none", "data/content/dialogue.json");
            return false;
        }
        Dead(npc);
        var r = new DialogueRunner(convo, J.Ctx);
        var entry = convo.Entry.Find(e => Rules.Test(e.When, J.Ctx));
        if (entry != null && convo.Nodes.TryGetValue(entry.Node, out var first)) Effects(first.Effects, $"{npc}.{entry.Node}");
        var p = r.Start();
        if (p == null)
        {
            Tell("deadend", $"{npc}:nobody", $"{npc} is offered to talk to, and no way into the conversation holds", "data/content/dialogue.json");
            return false;
        }
        Mode = Mode.Talk; Npc = npc; Runner = r;
        Shown(p);
        return true;
    }

    /// <summary>The game's Choose and Advance (GameMenus.cs): an action the
    /// game handles ends the conversation or opens a screen.</summary>
    Result? Talk(string key)
    {
        var r = Runner!;
        var npc = Npc!;
        var node = r.Node!;
        if (key == "next")
        {
            if (node.Next != null && r.Convo.Nodes.TryGetValue(node.Next, out var nx)) Effects(nx.Effects, $"{npc}.{node.Next}");
            var p = r.Advance();
            if (p == null) return Walk();
            Shown(p);
            return Stay;
        }
        if (!key.StartsWith("say:") || !int.TryParse(key[4..], out int index)) return null;
        var c = node.Choices?.ElementAtOrDefault(index);
        if (c == null || !Rules.Test(c.When, J.Ctx)) return null;
        var effects = new List<Change>(c.Effects ?? new());
        bool goes = !(c.End || (c.Goto == null && c.Action == null)) && !(c.Action != null && c.Goto == null);
        if (goes && c.Goto != null)
        {
            if (!r.Convo.Nodes.TryGetValue(c.Goto, out var to))
                Tell("broken", $"{npc}.{node.Id}#{index}:goto", $"\"{Text(c)}\" goes to {c.Goto}, which is not there", "data/content/dialogue.json");
            else Effects(c.Effects, $"{npc}.{node.Id}#{index}", to.Effects);
        }
        else Effects(c.Effects, $"{npc}.{node.Id}#{index}");
        var (next, action) = r.Choose(index);
        if (action != null && !Action(action, npc, $"{npc}.{node.Id}#{index}")) return Mode == Mode.Talk ? Walk() : Stay;
        if (next != null) { Shown(next); return Stay; }
        if (action == null) return Walk();
        if (r.Node != null && r.Present() is { } again) { Shown(again); return Stay; }
        return Walk();
    }

    string Text(DChoice c) => Dialogue.Template(Dialogue.PickText(c.Text, J.Ctx), J.Ctx);

    /// <summary>What a conversation opens (GameMenus.DialogueAction). True to stay in it.</summary>
    bool Action(string a, string npc, string where)
    {
        switch (a)
        {
            case "trade": case "sell":
                if (J.OpenShop(npc, Lucky) != null) { Mode = Mode.Shop; return false; }
                Tell("broken", $"{where}:trade", $"A choice opens {npc}'s wares, and {npc} has no shop", "data/content/dialogue.json");
                return false;
            case "stash": return false;
            case "maps": Mode = Mode.Maps; return false;
            case "rest": Mode = Mode.Rest; return false;
            case "fortune": Chapter(where); return false;
            case "craft": case "still": return false;
            case "sellpelts": case "bounty": case "slurry": return J.Service(a, B);
        }
        Tell("broken", $"{where}:action", $"A choice asks the game for '{a}', which it does not know", "data/content/dialogue.json");
        return J.Service(a, B);
    }

    /// <summary>The chapter's page, read (the fortune opens it): it must read.</summary>
    public void Chapter(string where)
    {
        try { World.Chapter.Summary(J.Ch, J.World); }
        catch (Exception e) { Tell("crash", $"chapter:{e.GetType().Name}:{e.Message}", $"The chapter's page cannot be written ({where}): {e.GetType().Name}: {e.Message}", "logic/World/Chapter.cs"); }
    }

    /* ----------------------------------------------------------- checks -- */

    static readonly System.Text.RegularExpressions.Regex FactRef = new(@"\{fact:([\w.]+)\}");
    static readonly System.Text.RegularExpressions.Regex Brace = new(@"\{[^{}\s]*\}");

    /// <summary>A line on screen: every token in it has a value, nothing is
    /// left in braces, and there are words to read.</summary>
    void Shown(Presented p)
    {
        var where = $"{Npc}.{p.Node.Id}";
        void Look(List<Variant> text, string what)
        {
            var raw = Dialogue.PickText(text, J.Ctx);
            foreach (System.Text.RegularExpressions.Match m in FactRef.Matches(raw))
                if (J.World.Fact(m.Groups[1].Value).IsNull)
                    Tell("text", $"{where}:{m.Value}", $"{what} quotes {m.Value}, which has no value here", "data/content/dialogue.json");
            var done = Dialogue.Template(raw, J.Ctx);
            foreach (System.Text.RegularExpressions.Match m in Brace.Matches(done))
                Tell("text", $"{where}:{m.Value}", $"{what} shows {m.Value} unfilled", "data/content/dialogue.json");
            if (done.Trim().Length == 0) Tell("text", $"{where}:{what}:empty", $"{what} has no words here", "data/content/dialogue.json");
        }
        Look(p.Node.Text, "The line");
        var list = p.Node.Choices ?? new();
        foreach (var c in p.Choices) Look(list[c.Index].Text, $"Choice {c.Index}");
        if (p.Choices.Count > 0 && !p.Choices.Any(c => c.Enabled))
            Tell("deadend", $"{where}:locked", $"Every choice is shown locked ({string.Join("; ", p.Choices.Select(c => c.Locked))}), and Escape only takes an open way out", "data/content/dialogue.json");
        foreach (var c in p.Choices.Where(c => !c.Enabled)) Locks?.Invoke($"{where}#{c.Index}", c.Locked ?? "");
        Offered?.Invoke(where, p);
    }

    /// <summary>What was on show, for the gates.</summary>
    public Action<string, Presented>? Offered;

    /// <summary>Talking to somebody the story has killed.</summary>
    void Dead(string npc)
    {
        var w = J.World;
        if (w.Fact(npc).Str == "dead" || w.Fact($"{npc}.dead").Truthy || (w.Npcs.TryGetValue(npc, out var s) && !s.Alive))
            Tell("contradiction", $"dead:{npc}", $"{npc} is dead, and can be talked to", "data/content/dialogue.json");
    }

    /// <summary>Changes about to be made, made first on a copy, one by one:
    /// each must be able to happen (a thing taken must be there, a price paid
    /// must be in the purse, news told must be news that happened).</summary>
    public void Effects(List<Change>? first, string where, List<Change>? then = null)
    {
        if (Report == null || (first == null && then == null)) return;
        var all = (first ?? new()).Concat(then ?? new()).ToList();
        if (!all.Any(Risky)) return;
        var copy = Load(Json.Write(J.ToSave(new SaveLocation())));
        foreach (var c in all) Check(c, copy, where);
    }

    static bool Risky(Change c) => c.Take != null || c.Gold < 0 || c.Tell != null || c.If != null;

    public void Check(Change c, Journey j, string where)
    {
        var ch = j.Ch; var w = j.World;
        if (c.If != null)
        {
            foreach (var x in (Rules.Test(c.If, j.Ctx) ? c.Then : c.Else) ?? new()) Check(x, j, where);
            return;
        }
        if (c.Take != null && Inventory.Count(ch, c.Take) < (c.Qty ?? 1))
            Tell("broken", $"{where}:take:{c.Take}", $"{where} takes {c.Qty ?? 1}× {c.Take}, and the survivor has {Inventory.Count(ch, c.Take)}", "data/content");
        if (c.Gold is < 0 && ch.Gold < -c.Gold.Value)
            Tell("broken", $"{where}:gold", $"{where} costs {-c.Gold} gold, and the survivor has {ch.Gold}", "data/content");
        if (c.Tell != null && !w.History.Exists(h => h.Id == c.Tell.Event))
            Tell("broken", $"{where}:tell:{c.Tell.Event}", $"{where} tells {c.Tell.Npc} of {c.Tell.Event}, which has not happened", "data/content");
        Rules.Apply(c, j.Ctx);
    }

    /// <summary>Before a night's sleep: the rules that will fire at dawn,
    /// checked the same way.</summary>
    void CheckDawn()
    {
        if (Report == null) return;
        var copy = Load(Json.Write(J.ToSave(new SaveLocation())));
        var w = copy.World;
        w.Day++;
        foreach (var s in w.Scheduled.Where(s => s.Day <= w.Day)) foreach (var c in s.Effect) Check(c, copy, $"rules.json (later: {s.Id})");
        var fired = (w.Fact("_rules.fired").Str ?? "").Split(',');
        foreach (var r in Simulation.DailyRules)
        {
            if (r.Once && fired.Contains(r.Id)) continue;
            if (!Rules.Test(r.When, copy.Ctx)) continue;
            foreach (var c in r.Effect) Check(c, copy, $"rules.json {r.Id}");
        }
    }

    /* ------------------------------------------------------ fingerprint -- */

    /// <summary>What the zone holds that the journey does not (a cage opened,
    /// a camp roused, a fire lit, who is out): two visits with the same mark
    /// and the same journey go on the same way.</summary>
    /// <summary>The zone's own progress, as flags (a cage open, a place found):
    /// each flag up, ';'-separated.</summary>
    public string Flags()
    {
        if (Zone == null) return "";
        var sb = new StringBuilder();
        foreach (var f in Zone.GetType().GetFields(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.DeclaredOnly))
            switch (f.GetValue(Zone))
            {
                case bool b: if (b) { sb.Append(Zone.Id).Append(':').Append(f.Name).Append(';'); } break;
                case bool[] a:
                    for (int i = 0; i < a.Length; i++) if (a[i]) { sb.Append(Zone.Id).Append(':').Append(f.Name).Append(i).Append(';'); }
                    break;
                case HashSet<string> h:
                    foreach (var x in h.OrderBy(x => x, StringComparer.Ordinal)) { sb.Append(Zone.Id).Append(':').Append(f.Name).Append(':').Append(x).Append(';'); }
                    break;
            }
        return sb.ToString();
    }

    public string Mark()
    {
        if (Zone == null) return "";
        var sb = new StringBuilder(Zone.Id).Append('|');
        for (var t = Zone.GetType(); t != null && t != typeof(object); t = t.BaseType)
            foreach (var f in t.GetFields(BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.DeclaredOnly))
            {
                var v = f.GetValue(Zone);
                string? s = v switch
                {
                    bool or int or string or Enum => v.ToString(),
                    bool[] a => string.Concat(a.Select(x => x ? '1' : '0')),
                    HashSet<string> h => string.Join(",", h.OrderBy(x => x, StringComparer.Ordinal)),
                    Enemy e => e.Alive && e.State != EnemyState.Dying ? $"up:{e.Disposition}" : "down",
                    List<Enemy> l => l.Count(e => e.Alive && e.State != EnemyState.Dying).ToString(),
                    _ => null,
                };
                if (v == null) s = "-";
                if (s != null) sb.Append(f.Name).Append('=').Append(s).Append(';');
            }
        sb.Append("|i:").Append(string.Join(",", Zone.Interactables.Select(i => i.Id)));
        sb.Append("|a:").Append(string.Join(",", Zone.Actors.Select(a => $"{a.Key}{(a.Value.Hidden ? "-" : "+")}")));
        var look = Host!.FakeLook;
        sb.Append("|l:").Append(string.Concat(Enumerable.Range(0, Meta!.Lights.Count).Select(i => look.IsLit(i) ? '1' : '0')));
        sb.Append("|h:").Append(string.Join(",", look.Hidden.OrderBy(x => x, StringComparer.Ordinal)));
        sb.Append("|s:").Append(string.Join(",", look.Stopped.OrderBy(x => x, StringComparer.Ordinal)));
        sb.Append("|e:").Append(string.Join(",", B!.Enemies.Living().Where(e => e.State != EnemyState.Dying)
            .Select(e => $"{e.Def.Id}/{e.Tag}/{e.Disposition}{(e.Provoked ? "!" : "")}").OrderBy(x => x, StringComparer.Ordinal)));
        sb.Append("|c:").Append(B.Collision.All().Count);
        return sb.ToString();
    }
}

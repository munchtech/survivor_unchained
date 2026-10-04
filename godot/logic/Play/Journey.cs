using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* A survivor's journey as the game keeps it (the web game's game.ts, what
 * of it is not drawing): the character and the world, the logic context
 * every rule runs in, the ember carried between zones, the save, the fight's
 * hooks, gear, shops, the storeroom, rest, a death and what it costs, and
 * the ground walked on each zone's map. The Godot game holds one and shows
 * it; the tests drive one without a screen. */

public enum ToastKind { Loot, Gold, Relation, Quest, World, Lore, Level, Warning }

/// <summary>A line for the interface's notices.</summary>
public sealed record Toast(ToastKind Kind, string Text, string? Sub = null, string? Icon = null, int? Rarity = null, double? Life = null);

/// <summary>A heading for the interface: a new level, a place.</summary>
public sealed record Announcement(string Title, string? Sub, string Kind, double Seconds, string? Kicker = null);

/// <summary>What the road has taken out of the survivor, carried between
/// zones until they rest (the ember is an arena's, and stays in it).</summary>
public sealed class Expedition
{
    public double Hp;
}

public sealed partial class Journey
{
    public CharacterData Ch;
    public WorldState World;
    public Ctx Ctx;
    public int Slot;
    public double Playtime;
    public Expedition? Expedition;
    /// <summary>The weapons the gear gives (they come and go with it).</summary>
    public HashSet<string> GearWeapons = new();
    /// <summary>The fight running is an ember arena's.</summary>
    public bool InArena;

    /// <summary>Notices for the interface (the game shows them).</summary>
    public Action<Toast> OnToast = _ => { };
    public Action<Announcement> OnAnnounce = _ => { };
    /// <summary>Something the interface shows changed (the pack, the gold).</summary>
    public Action OnTouch = () => { };

    /// <summary>The map's fog of war: cells per side.</summary>
    public const int FogN = 48;

    Journey(CharacterData ch, WorldState world)
    {
        Ch = ch;
        World = world;
        Ctx = Lore.Context(world, ch, Notify);
    }

    /* ------------------------------------------------------------ begin -- */

    /// <summary>A new survivor on the Low Ford road.</summary>
    public static Journey Begin(CreationChoice c, uint seed)
    {
        var world = WorldState.Fresh(seed);
        var ch = Character.Create(c, world.Day, seed);
        // Where you came from decides how the world first reads you.
        var bg = Callings.Background(c.Background);
        foreach (var (f, v) in bg.Standing) world.Factions[f] = new FactionState { Id = f, Standing = v, Strength = 50 };
        foreach (var (id, rel) in bg.Npc)
        {
            var n = world.Npc(id);
            if (rel.Trust is double t) n.Trust = t;
            if (rel.Affection is double a) n.Affection = a;
            if (rel.Fear is double f2) n.Fear = f2;
            if (rel.Respect is double r) n.Respect = r;
        }
        world.Facts["beasts.population"] = 60;
        Inventory.AddToPack(ch, Inventory.Make(ch, "health_draught", 1));
        return new Journey(ch, world);
    }

    /// <summary>A journey as it was saved.</summary>
    public static Journey From(SaveData d, int slot) => new(d.Character, d.World)
    {
        Slot = slot, Playtime = d.Playtime,
        Expedition = d.Ember is { } e ? new Expedition { Hp = e.Hp ?? double.MaxValue } : null,
    };

    public SaveData ToSave(SaveLocation at) => new()
    {
        Playtime = Playtime, Character = Ch, World = World, Location = at,
        Ember = Expedition is { } e ? new EmberCarry { Hp = e.Hp } : null,
    };

    /* ----------------------------------------------------------- notices -- */

    static ToastKind KindOf(NoticeTone t) => t switch
    {
        NoticeTone.Item => ToastKind.Loot, NoticeTone.Gold => ToastKind.Gold, NoticeTone.Rel => ToastKind.Relation,
        NoticeTone.Journal => ToastKind.Quest, NoticeTone.Learn => ToastKind.Lore, NoticeTone.Trait => ToastKind.Level,
        NoticeTone.Warn => ToastKind.Warning, _ => ToastKind.World,
    };

    public void Notify(Notice n)
    {
        if (n.Tone == NoticeTone.Journal)
        {
            // "Quest: what you learned" reads as a title and a line.
            int i = n.Text.IndexOf(": ", StringComparison.Ordinal);
            if (i > 0 && !n.Text.StartsWith("New")) OnToast(new Toast(ToastKind.Quest, n.Text[..i], n.Text[(i + 2)..], Life: 8));
            else OnToast(new Toast(ToastKind.Quest, n.Text, Life: 6));
        }
        else if (n.Tone == NoticeTone.Item)
        {
            var def = Items.All.Values.FirstOrDefault(d => n.Text.StartsWith(d.Name));
            OnToast(new Toast(ToastKind.Loot, n.Text, Icon: def?.Icon, Rarity: def?.Rarity));
        }
        else OnToast(new Toast(KindOf(n.Tone), n.Text));
    }

    void Warn(string text) => OnToast(new Toast(ToastKind.Warning, text));

    /// <summary>World effects, with their notices.</summary>
    public void Apply(IEnumerable<Change> e)
    {
        Rules.Apply(e, Ctx);
        OnTouch();
    }

    public void Apply(string changesJson) => Apply(Json.Parse<List<Change>>(changesJson));

    /* ------------------------------------------------------------ battle -- */

    /// <summary>A fight (or a walk) in a zone, from the survivor's gear, level
    /// and the wounds they carry. By day, in the story, the ember does not
    /// burn: the survivor fights with what they are (their gear's skills, the
    /// art, the dash) and grows by experience.</summary>
    /// <param name="arena">An ember arena: the ember burns, from nothing, whatever is carried.</param>
    /// <param name="ember">The ember burns here (the night: the prologue, an arena).</param>
    public Battle StartBattle(bool combat, CollisionWorld col, Func<double, double, double> heightAt, double x, double z, double facing, uint seed, bool arena = false, bool ember = false)
    {
        var kit = Character.Kit(Ch);
        InArena = arena;
        var exp = combat && !arena ? Expedition : null;
        var b = new Battle(new BattleSetup
        {
            Seed = seed, Combat = combat, Collision = col, HeightAt = heightAt, Stats = kit.Stats,
            StartX = x, StartZ = z, StartFacing = facing, Weapons = kit.Weapons, Triggers = kit.Triggers, Ability = kit.Ability,
            ArtRank = kit.ArtRank, Facets = kit.Facets,
            Hp = exp != null ? Math.Min(exp.Hp, kit.Stats.Get(Stat.MaxHealth)) : null,
        });
        b.EmberOn = combat && (arena || ember);
        EmberLit = b.EmberOn && !arena;
        b.Night = arena || ember || World.Time == TimeOfDay.Night;
        GearWeapons = kit.Weapons.Select(w => w.Id).ToHashSet();
        b.Favours.UnionWith(Callings.Archetype(Ch.Archetype).Favours);
        b.Calling = Ch.Archetype;
        b.CallingPaths.UnionWith(Content.Paths.All.Where(p => p.Callings.Contains(Ch.Archetype)).Select(p => p.Id));
        // What is carried by day is attuned for the night (offered first, a
        // rank or two up); what is only learned comes a little more often.
        if (b.EmberOn)
        {
            foreach (var id in SkillBook.Attuned(Ch)) b.Attuned[id] = SkillBook.NightRank(Ch);
            b.Familiar.UnionWith(Ch.Skills.Where(id => Content.Weapons.All.ContainsKey(id) && !b.Attuned.ContainsKey(id)));
        }
        b.GearIds.UnionWith(kit.GearIds);
        b.GearStatuses.UnionWith(kit.GearStatuses);
        b.Rerolls = kit.Rerolls;
        b.Banishes = 2 + kit.Banishes;
        b.Stands.UnionWith(kit.Stands);
        b.Roads = kit.Roads;
        b.Omens = kit.Omens;
        b.Player.Revives = kit.Revives;
        if (b.EmberOn)
            for (int i = 0; i < kit.StartLevels; i++) b.GainEmber(b.EmberNext);
        // By day, the skills learned for it.
        else if (combat)
            foreach (var (id, rank) in kit.Learned) b.AddWeapon(id, rank);
        return b;
    }

    /// <summary>The kinds of play that tell the story (the rest are the endgame's arenas: table
    /// nights, ember scars, maps).</summary>
    public static readonly string[] StoryModes = ["prologue", "town", "wild", "story night"];

    /// <summary>Time played, booked to its kind of play.</summary>
    public void Clock(double dt, string mode) => World.TimeIn[mode] = World.TimeIn.GetValueOrDefault(mode) + dt;

    /// <summary>The story's share of the time played so far (0..1), with the town counted as story
    /// (its people, its quests) and without it (only the prologue, the wild and the story's nights).</summary>
    public (double WithTown, double Strict) StoryShare
    {
        get
        {
            double all = World.TimeIn.Values.Sum();
            if (all <= 0) return (0, 0);
            double story = StoryModes.Sum(m => World.TimeIn.GetValueOrDefault(m));
            return (story / all, (story - World.TimeIn.GetValueOrDefault("town")) / all);
        }
    }

    /// <summary>The ember burns here and this is no arena (the prologue's night): what kills teach
    /// is banked for the dawn.</summary>
    public bool EmberLit { get; private set; }

    /// <summary>The dawn: the ember goes out, and what it built with it; what the night taught is
    /// paid. The levels it came to.</summary>
    public int Douse(Battle b)
    {
        var kit = Character.Kit(Ch);
        b.Douse(kit.Weapons);
        GearWeapons = kit.Weapons.Select(w => w.Id).ToHashSet();
        EmberLit = false;
        if (World.NightLessons <= 0) return 0;
        int levels = Character.GainXp(Ch, World.NightLessons);
        World.NightLessons = 0;
        return levels;
    }

    /// <summary>Leaving a zone: the wounds come along (an arena's are left in it).</summary>
    public void Capture(Battle? b)
    {
        BankArt(b);
        BankGold(b);
        if (b == null || !b.Combat || InArena) return;
        Expedition = new Expedition { Hp = b.Player.Hp };
    }

    /// <summary>A kill: the survivor grows too, more slowly than the ember;
    /// the bestiary and the weapon's mastery remember it.</summary>
    public void Killed(Enemy e, bool byPlayer)
    {
        if (!byPlayer) return;
        Ch.Stats.Kills++;
        if (e.LastWeapon != null) Ch.Mastery[e.LastWeapon] = Ch.Mastery.GetValueOrDefault(e.LastWeapon) + 1;
        World.Bestiary[e.Def.Id] = World.Bestiary.GetValueOrDefault(e.Def.Id) + 1;
        if (e.Boss) Ch.Stats.BossesSlain++;
        // An arena pays its experience at the end, for the time survived; a
        // fight in the story teaches as it goes, the more the stronger the foe.
        if (InArena) return;
        double xp = 2 * e.Def.Xp * Content.Enemies.ScaleFor(e.Level).Xp * (e.Boss ? 3 : e.Elite ? 2 : 1);
        // While the ember drafts outside an arena (the prologue's night) the lessons wait for dawn:
        // a character level popping up while the ember levelled taught two systems at once in the
        // first minute (docs/EXPERIENCE_AUDIT.md, finding 4).
        if (EmberLit) { World.NightLessons += xp; return; }
        int levels = Character.GainXp(Ch, xp);
        if (levels > 0)
        {
            OnAnnounce(new Announcement($"Level {Ch.Level}", Ch.TraitPicks > 0 ? "A new trait can be chosen (C)" : "Attribute points to spend (C)", "boon", 3.2, "You grow stronger"));
            Grew();
            OnTouch();
        }
    }

    /// <summary>The survivor has grown: their calling may teach them a skill
    /// they have seen burn (every third level). What it taught, or null.</summary>
    public string? Grew()
    {
        if (SkillBook.Calling(Ch) is not { } id) return null;
        var wd = Content.Weapons.All[id];
        OnAnnounce(new Announcement(wd.Name, $"Your calling teaches it to you. Carry it by day (K)", "boon", 3.8, "A new skill"));
        return id;
    }

    /// <summary>A pickup reached the survivor: gear, materials and quest
    /// things into the pack. False leaves it on the ground (a full pack).</summary>
    public bool PickedUp(Pickup p)
    {
        if (p.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Quest && p.Ref != null)
        {
            // Gear on the ground was rolled when it fell; its light said how good it is.
            int? rolled = p.Kind == PickupKind.Item && Items.Find(p.Ref)?.Base != null ? p.Tier : null;
            return GiveItem(p.Ref, Math.Max(1, MathX.RoundInt(p.Value)), rolled, p.Lean, dropped: true);
        }
        return true;
    }

    /// <summary>Something found in the field. False if there is no room.</summary>
    /// <param name="dropped">It fell in the world (its heat is rolled: docs/CRAFTING_DESIGN.md 5.1).</param>
    public bool GiveItem(string defId, int qty = 1, int? rarity = null, IReadOnlyCollection<string>? lean = null, bool dropped = false)
    {
        var it = Inventory.Make(Ch, defId, qty, rarity, lean: lean, dropped: dropped);
        var def = Items.Get(defId);
        if (!Inventory.AddToPack(Ch, it)) { OnToast(new Toast(ToastKind.Warning, "Your pack is full", def.Name)); return false; }
        OnToast(new Toast(ToastKind.Loot, $"{Inventory.Name(it)}{(qty > 1 ? $" ×{qty}" : "")}",
            def.Kind == ItemKind.Material ? null : it.Rarity > def.Rarity ? $"{Inventory.RarityName(it)} {def.Kind.Key()}" : def.Description,
            def.Icon, it.Rarity));
        OnTouch();
        return true;
    }

    /// <summary>A particular thing come back (what a nemesis took): the same
    /// item, affixes and all; a full pack sends it to Rook's storeroom.</summary>
    public void ReturnItem(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        if (Inventory.AddToPack(Ch, it)) OnToast(new Toast(ToastKind.Loot, Inventory.Name(it), "Yours again", def.Icon, it.Rarity));
        else
        {
            int j = World.Stash.IndexOf(null);
            if (j >= 0) { World.Stash[j] = it; OnToast(new Toast(ToastKind.Loot, Inventory.Name(it), "Your pack is full: Rook will keep it for you", def.Icon, it.Rarity)); }
            else Warn($"{Inventory.Name(it)} is lost: no room anywhere");
        }
        OnTouch();
    }

    /// <summary>The survivor fell in a zone: their gold stays where they fell;
    /// one thing they carried goes with whatever killed them, and it is not the
    /// same creature any more. The world remembers.</summary>
    public void Fell(string zoneId, string zoneName, string killer, PlayerState? p, Random rng)
    {
        var w = World;
        var k = p?.LastKiller;
        double gold = Math.Floor(Ch.Gold / 2);
        Ch.Gold -= gold;
        w.Corpse = new CorpseState { Zone = zoneId, X = p?.X ?? 0, Z = p?.Z ?? 0, Gold = gold, Day = w.Day, Killer = killer, HeroName = Ch.Name };
        if (k != null && !k.Boss && k.Def.Id != "grimtunnel")
        {
            // Only something that will carry it away takes a thing from you.
            var pool = Ch.Pack.Select((it, i) => (it, i)).Where(x => x.it != null && Items.Get(x.it.Def).Kind is not (ItemKind.Quest or ItemKind.Consumable)).ToList();
            ItemInstance? took = null;
            if (pool.Count > 0)
            {
                var pick = pool[rng.Next(pool.Count)];
                took = pick.it;
                Ch.Pack[pick.i] = null;
            }
            // A nemesis still out there is not forgotten: the new one has what it had, too.
            var before = w.Nemesis is { Killed: false } n ? n.Carries : new List<ItemInstance>();
            w.Nemesis = new NemesisState
            {
                Zone = zoneId, Def = k.Def.Id, Title = $"{NemesisName(k.Def.Family, rng)}, Who Took Your Light", Level = k.Level + 2,
                Carries = [.. before, .. took != null ? [took] : Array.Empty<ItemInstance>()], HeroName = Ch.Name,
            };
        }
        Ch.Conditions.RemoveAll(c => c.Id == ConditionId.Rested);
        int deaths = Ch.Stats.Deaths;
        Apply($$"""
            [
              { "condition": { "id": "wounded", "days": 2, "note": "You fell in {{zoneName}}" } },
              { "if": { "not": { "trait": "risen_once" } }, "then": [{ "trait": "risen_once" }] },
              { "history": { "id": "fell_{{w.Day}}_{{deaths}}", "text": "fell in {{zoneName}} to {{Esc(killer)}}", "tags": ["death"], "spread": 2,
                "sentiment": { "respect": -3 }, "reactions": { "chid": { "affection": 10 } } } },
              { "set": { "player.just_died": true } },
              { "add": { "player.deaths": 1 } }
            ]
            """);
        Expedition = null;
    }

    static string Esc(string s) => s.Replace("\\", "\\\\").Replace("\"", "\\\"");

    /// <summary>What the thing that killed you is called now.</summary>
    static string NemesisName(Family family, Random rng)
    {
        string[] list = family switch
        {
            Family.Wolf => ["Ash-Fang", "Hollow-Eye", "Old Greyback", "Split-Ear"],
            Family.Boar => ["Old Tusk", "the Hedge-Breaker"],
            // Never a name the story has spent: Wat is the drowned carter, and the
            // dead watchman at the ford is Corran.
            Family.Kerchief => ["Red Hob", "Knuckles Marro", "Sly Dell"],
            Family.Lampling => ["Wick", "Soot-Tooth"],
            Family.Undead => ["the Unburied", "the Ditch-Walker"],
            _ => ["the Thing in the Wood"],
        };
        return list[rng.Next(list.Length)];
    }

    /* -------------------------------------------------------------- gear -- */

    int Draughts => Inventory.Count(Ch, "health_draught");

    /// <summary>R: drink a health draught.</summary>
    public void Quaff(Battle? b)
    {
        if (b == null || !b.Player.Alive) return;
        if (Draughts == 0) { Warn("No draughts left"); return; }
        if (b.Player.Hp >= b.MaxHp - 0.5) { Warn("You are unhurt"); return; }
        Inventory.Take(Ch, "health_draught", 1);
        b.HealPlayer(b.MaxHp * (Items.Get("health_draught").Consumable?.Heal ?? 0.4), "draught");
        OnTouch();
    }

    public void Equip(string uid, EquipSlot? slot, Battle? b)
    {
        if (Inventory.Find(Ch, uid) is not { } loc) return;
        var def = Items.Get(loc.Item.Def);
        var target = slot ?? Items.SlotFor(def);
        if (target is not EquipSlot t) return;
        // Rings go to whichever hand is free.
        if (slot == null && t == EquipSlot.Ring1 && Ch.Equipment.Ring1 != null && Ch.Equipment.Ring2 == null) t = EquipSlot.Ring2;
        if (!Items.Fits(def, t)) return;
        if (!Inventory.Equip(Ch, loc.Item, t)) { Warn("No room in your pack for what you are wearing"); return; }
        OnToast(new Toast(ToastKind.Loot, $"Wearing {Inventory.Name(loc.Item)}", Icon: def.Icon, Rarity: loc.Item.Rarity));
        RefreshKit(b);
    }

    public void Unequip(EquipSlot slot, Battle? b)
    {
        if (slot == EquipSlot.Weapon) { Warn("You will not walk this road unarmed"); return; }
        if (!Inventory.Unequip(Ch, slot)) { Warn("Your pack is full"); return; }
        RefreshKit(b);
    }

    public void Use(string uid, Battle? b)
    {
        if (Inventory.Find(Ch, uid) is not { InPack: true } loc) return;
        var def = Items.Get(loc.Item.Def);
        if (def.Kind != ItemKind.Consumable || def.Consumable is not { } c) { Equip(uid, null, b); return; }
        if (c.Heal is double heal && b != null)
        {
            if (b.Player.Hp >= b.MaxHp - 0.5) { Warn("You are unhurt"); return; }
            b.HealPlayer(b.MaxHp * heal, "draught");
        }
        if (c.Teaches is { } art)
        {
            var ad = Abilities.ById(art);
            if (ArtBook.Knows(Ch, art))
            {
                // Read again: the art is surer for it.
                ArtBook.Grow(Ch, art, 20);
                OnToast(new Toast(ToastKind.Level, $"{ad.Name}: you know it better", "Read again, the art comes more easily", ad.Icon));
            }
            else if (!ArtBook.Learn(Ch, art)) { Warn($"{ad.Name} is not a {Callings.Archetype(Ch.Archetype).Name}'s art"); return; }
            else OnAnnounce(new Announcement(ad.Name, "Learned. Take it in hand at the Waystation (K)", "boon", 3.6, "A new art"));
        }
        if (c.Skill is { } skill)
        {
            var wd = Content.Weapons.All[skill];
            if (SkillBook.Knows(Ch, skill)) { Warn($"You already know {wd.Name}"); return; }
            if (!SkillBook.Learn(Ch, skill)) { Warn($"The words mean nothing yet: {wd.Name} has to be seen burning in an arena first"); return; }
            OnAnnounce(new Announcement(wd.Name, SkillBook.Meets(Ch, skill) ? "Learned for the day. Carry it from your skills (K)" : $"Learned, but it asks {SkillBook.Need} {SkillBook.Attribute(skill)} of you", "boon", 3.6, "A new skill"));
        }
        foreach (var cure in c.Cure ?? new())
        {
            if (cure == "poisoned" && b != null) b.Player.PoisonT = 0;
            if (EnumKey<ConditionId>.TryParse(cure, out var cid)) Ch.Conditions.RemoveAll(x => x.Id == cid);
        }
        loc.Item.Qty--;
        if (loc.Item.Qty <= 0) Ch.Pack[loc.Index] = null;
        OnToast(new Toast(ToastKind.World, $"{def.Name} used"));
        OnTouch();
    }

    /// <summary>A quest thing whose part in the story is not yet played.</summary>
    public bool StillNeeded(ItemInstance it) => Items.Get(it.Def) is { Kind: ItemKind.Quest } d && Rules.Test(d.Needed, Ctx);

    public void Drop(string uid)
    {
        if (Inventory.FromPouch(uid) is { } mat && Ch.Materials.Remove(mat))
        {
            OnToast(new Toast(ToastKind.World, $"Left behind: {Items.Get(mat).Name}"));
            OnTouch();
            return;
        }
        if (Inventory.Find(Ch, uid) is not { InPack: true } loc) return;
        if (StillNeeded(loc.Item)) { Warn("You might need that"); return; }
        Ch.Pack[loc.Index] = null;
        OnToast(new Toast(ToastKind.World, $"Left behind: {Inventory.Name(loc.Item)}"));
        OnTouch();
    }

    /// <summary>Gear changed: fold it into the running fight at once.</summary>
    public void RefreshKit(Battle? b)
    {
        OnTouch();
        if (b == null) return;
        var kit = Character.Kit(Ch);
        static bool FromKit(string src) => src.StartsWith("item:") || src == "attributes" || src.StartsWith("trait:") || src.StartsWith("cond:");
        b.Stats.RemoveWhere(FromKit);
        b.Stats.SetBase(kit.Stats.GetBase());
        b.Stats.AddAll(kit.Stats.List().Where(m => FromKit(m.Source)).ToList());
        b.Triggers = b.Triggers.Where(t => !t.Source.StartsWith("item:") && !t.Source.StartsWith("trait:")).ToList();
        foreach (var (def, src) in kit.Triggers) b.AddTrigger(def, src);
        var kitIds = kit.Weapons.Select(w => w.Id).ToHashSet();
        foreach (var id in GearWeapons) if (!kitIds.Contains(id)) b.RemoveWeapon(id);
        foreach (var (id, rank) in kit.Weapons) if (!b.Weapons.Any(x => x.Id == id)) b.AddWeapon(id, rank);
        GearWeapons = kitIds;
        b.GearIds.Clear(); b.GearIds.UnionWith(kit.GearIds);
        b.GearStatuses.Clear(); b.GearStatuses.UnionWith(kit.GearStatuses);
        b.Player.Hp = Math.Min(b.Player.Hp, b.MaxHp);
    }

    /* -------------------------------------------------------------- arts -- */

    /// <summary>Gold picked up in the fight, into the purse as it comes.</summary>
    public void BankGold(Battle? b)
    {
        if (b == null) return;
        double d = b.GoldGained - b.GoldBanked;
        if (d <= 0) return;
        b.GoldBanked = b.GoldGained;
        Ch.Gold += d;
        Ch.Stats.GoldEarned += d;
    }

    /// <summary>What the art in hand grew by in the fight, written to the
    /// survivor; a new rank strengthens it at once and may open a facet.</summary>
    public void BankArt(Battle? b)
    {
        if (b == null || b.ArtXp <= 0 || Ch.Ability == "") return;
        double xp = b.ArtXp;
        b.ArtXp = 0;
        int rank = ArtBook.Grow(Ch, Ch.Ability, xp);
        if (rank == 0) return;
        b.ArtRank = rank;
        var def = Abilities.ById(Ch.Ability);
        bool open = ArtBook.OpenSlots(Ch, Ch.Ability) > 0;
        OnAnnounce(new Announcement($"{def.Name}, rank {rank}", open ? "A facet can be chosen (K)" : "Stronger, and sooner ready", "boon", 3.2, "Your art grows"));
        OnTouch();
    }

    /// <summary>Carry another known art (somewhere safe).</summary>
    public void HoldArt(string id, Battle? b)
    {
        BankArt(b);
        if (!ArtBook.Hold(Ch, id)) return;
        var def = Abilities.ById(id);
        b?.SetArt(def.Kind, ArtBook.Rank(Ch, id), ArtBook.Facets(Ch, id));
        if (b != null) { b.Art.Clear(); b.Player.AbilityCd = 0; }
        OnToast(new Toast(ToastKind.Level, $"In hand: {def.Name}", Icon: def.Icon));
        OnTouch();
    }

    /// <summary>Choose a facet newly opened, or change one (somewhere safe).</summary>
    public void ChooseFacet(string id, string facet, bool on, Battle? b)
    {
        bool changed = on ? ArtBook.Choose(Ch, id, facet) : ArtBook.Unchoose(Ch, id, facet);
        if (!changed) return;
        if (id == Ch.Ability && b != null) b.SetArt(Abilities.ById(id).Kind, ArtBook.Rank(Ch, id), ArtBook.Facets(Ch, id));
        OnTouch();
    }

    public void SpendPoint(string attr, Battle? b)
    {
        if (Ch.Points <= 0) return;
        Ch.Points--;
        switch (attr)
        {
            case "might": Ch.Attributes.Might++; break;
            case "finesse": Ch.Attributes.Finesse++; break;
            case "wits": Ch.Attributes.Wits++; break;
            case "resolve": Ch.Attributes.Resolve++; break;
            default: Ch.Points++; return;
        }
        RefreshKit(b);
    }

    public void PickTrait(string id, Battle? b)
    {
        if (Ch.TraitPicks <= 0 || Ch.Traits.Contains(id)) return;
        Ch.TraitPicks--;
        Ch.Traits.Add(id);
        OnToast(new Toast(ToastKind.Level, $"You have become: {Callings.Trait(id)?.Name ?? id}"));
        RefreshKit(b);
    }

    /* --------------------------------------------------- conversations -- */

    /// <summary>A service a conversation opens that is done in the
    /// conversation itself. True to stay in it.</summary>
    public bool Service(string action, Battle? b)
    {
        var w = World;
        switch (action)
        {
            case "sellpelts":
            {
                int pelts = Inventory.Count(Ch, "wolf_pelt"), hides = Inventory.Count(Ch, "boar_hide");
                if (pelts == 0 && hides == 0) { Warn("You have nothing he wants"); return true; }
                Apply($$"""
                    [
                      { "take": "wolf_pelt", "qty": {{pelts}} }, { "take": "boar_hide", "qty": {{hides}} }, { "gold": {{pelts * 8 + hides * 6}} },
                      { "add": { "beasts.pelts_sold": {{pelts}} } }, { "quest": { "id": "beasts", "entry": "pelts_sold" } },
                      { "history": { "id": "sold_pelts", "text": "sold wolf pelts to Brannoc", "tags": ["beasts", "trade"], "spread": 1, "reactions": { "maeca": { "affection": -10 } } } }
                    ]
                    """);
                return true;
            }
            case "bounty":
            {
                int pelts = Inventory.Count(Ch, "wolf_pelt");
                if (pelts == 0) return true;
                bool sold = w.Fact("beasts.pelts_sold").Number > 0;
                Apply($$"""
                    [
                      { "take": "wolf_pelt", "qty": {{pelts}} }, { "gold": {{pelts * 5}} }, { "set": { "beasts.bounty_claimed": true } },
                      { "quest": { "id": "beasts", "entry": "bounty_claimed" } }, { "rel": { "npc": "holloway", "respect": {{Math.Min(15, pelts * 2)}} } }
                    ]
                    """);
                if (sold)
                    Apply("""
                        [{ "history": { "id": "double_dipped", "text": "sold pelts to Brannoc and claimed Holloway's bounty on the same wolves",
                           "tags": ["greed", "beasts"], "spread": 2, "reactions": { "holloway": { "trust": -30 }, "brannoc": { "trust": -20 } } } }]
                        """);
                return true;
            }
        }
        return true;
    }

    /* ------------------------------------------------------------- shops -- */

    /// <summary>A shop's stock, restocked when its days are up. Null if
    /// there is no such shop.</summary>
    public ShopState? OpenShop(string id, Random rng)
    {
        if (!Lore.Shops.TryGetValue(id, out var def)) return null;
        if (!World.Shops.TryGetValue(id, out var st) || World.Day >= st.RestockDay)
        {
            st = new ShopState { RestockDay = World.Day + def.RestockDays };
            st.Stock = RollStock(def, rng, st.Offered);
            World.Shops[id] = st;
        }
        else
        {
            // Between restocks, a line that has become true since (Pell's
            // blasting ember, once the survivor knows the Dig) goes on the shelf now.
            st.Offered ??= new();
            st.Stock.AddRange(RollLines(def, rng, st.Offered));
        }
        OnTouch();
        return st;
    }

    static string LineKey(ShopDef def, int i) => $"{i}:{def.Lines[i].Id}";

    /// <summary>The conditional lines that hold now and have not been rolled
    /// this restock: rolled (their chance as at a restock) and written down.</summary>
    List<ItemInstance> RollLines(ShopDef def, Random rng, List<string> offered)
    {
        var out_ = new List<ItemInstance>();
        for (int i = 0; i < def.Lines.Count; i++)
        {
            var l = def.Lines[i];
            if (l.When == null || offered.Contains(LineKey(def, i)) || !Rules.Test(l.When, Ctx)) continue;
            offered.Add(LineKey(def, i));
            if (l.Chance is double c && rng.NextDouble() > c) continue;
            if (Items.Find(l.Id) == null) continue;
            out_.Add(Inventory.Make(Ch, l.Id, l.Qty ?? 1, l.Rarity));
        }
        return out_;
    }

    List<ItemInstance> RollStock(ShopDef def, Random rng, List<string> offered)
    {
        var out_ = new List<ItemInstance>();
        for (int i = 0; i < def.Lines.Count; i++)
        {
            var l = def.Lines[i];
            if (l.When != null && !Rules.Test(l.When, Ctx)) continue;
            if (l.When != null) offered.Add(LineKey(def, i));
            if (l.Chance is double c && rng.NextDouble() > c) continue;
            if (Items.Find(l.Id) == null) continue;
            out_.Add(Inventory.Make(Ch, l.Id, l.Qty ?? 1, l.Rarity));
        }
        // Vonnra's curiosities: a tome or two of what the survivor has seen burn.
        if (def.Id == "vonnra")
            foreach (var id in Ch.Discovered.Where(id => SkillBook.CanLearn(Ch, id)).OrderBy(_ => rng.Next()).Take(2))
                out_.Add(Inventory.Make(Ch, SkillBook.Tome(id), 1));
        return out_;
    }

    /// <summary>How much a seller likes you, as a price multiplier.</summary>
    public double PriceMod(string npcId)
    {
        var s = World.Npc(npcId);
        double m = 1;
        if (s.Trust >= 30 || s.Affection >= 30) m *= 0.9;
        if (s.Trust <= -30) m *= 1.25;
        if (s.Fear >= 40) m *= 0.85;
        if (Ch.Traits.Contains("silver_tongue")) m *= 0.9;
        if (npcId == "harlan" && s.Flags.TryGetValue("discount", out var d) && d.Truthy) m *= 0.8;
        // A road the Kerchiefs work is a road wagons do not come down: everything costs more.
        double raids = World.Fact("kerchief.raids").Number;
        if (raids >= 2) m *= 1 + Math.Min(0.3, raids * 0.06);
        return m;
    }

    static double UnitValue(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        return def.Value * (1 + 0.6 * Math.Max(0, it.Rarity - def.Rarity)) * (1 + 0.15 * it.Affixes.Count);
    }

    /// <summary>What a thing costs to buy from this shop, or fetches sold to
    /// it (null: they will not buy it).</summary>
    public int? PriceOf(string shop, string uid, bool buying)
    {
        var def = Lore.Shops[shop];
        if (buying)
        {
            var it = World.Shops.GetValueOrDefault(shop)?.Stock.FirstOrDefault(x => x.Uid == uid);
            return it == null ? null : Math.Max(1, (int)Math.Ceiling(UnitValue(it) * def.Markup * PriceMod(shop)));
        }
        var mine = Ch.Pack.FirstOrDefault(x => x?.Uid == uid) ?? Inventory.Pouch(Ch).FirstOrDefault(x => x.Uid == uid);
        if (mine == null) return null;
        var kind = Items.Get(mine.Def).Kind;
        if (!def.BuysAll && !def.Buys.Contains(kind.Key())) return null;
        // Nothing the story still needs goes over a counter: sold there, a
        // strongbox or a ledger would vanish without anyone in the story
        // knowing. The story's own trades (Rav's fence, Pell's price for his
        // book) are made in conversation.
        if (StillNeeded(mine)) return null;
        return Math.Max(1, (int)Math.Floor(UnitValue(mine) * def.Pays / Math.Max(0.8, PriceMod(shop)))) * mine.Qty;
    }

    public void Buy(string shop, string uid)
    {
        if (!World.Shops.TryGetValue(shop, out var st)) return;
        int i = st.Stock.FindIndex(x => x.Uid == uid);
        if (i < 0) return;
        var it = st.Stock[i];
        int price = PriceOf(shop, uid, true)!.Value;
        if (Ch.Gold < price) { Warn($"That costs {price} gold"); return; }
        var one = it.Qty > 1 ? Json.Clone(it) : it;
        if (it.Qty > 1) { one.Uid = $"i{Ch.NextUid++}"; one.Qty = 1; }
        if (!Inventory.AddToPack(Ch, one)) { Warn("Your pack is full"); return; }
        Ch.Gold -= price;
        if (it.Qty > 1) it.Qty--; else st.Stock.RemoveAt(i);
        OnToast(new Toast(ToastKind.Loot, $"Bought {Inventory.Name(one)}", $"−{price} gold", Items.Get(one.Def).Icon, one.Rarity));
        OnTouch();
    }

    public void Sell(string shop, string uid)
    {
        var price = PriceOf(shop, uid, false);
        if (price == null) { Warn("They will not buy that"); return; }
        ItemInstance it;
        if (Inventory.FromPouch(uid) is { } mat)
        {
            // Out of the pouch, the whole of it: a stack on their counter.
            it = Inventory.Make(Ch, mat, Ch.Materials.GetValueOrDefault(mat));
            Ch.Materials.Remove(mat);
        }
        else
        {
            int i = Ch.Pack.FindIndex(x => x?.Uid == uid);
            it = Ch.Pack[i]!;
            Ch.Pack[i] = null;
        }
        Ch.Gold += price.Value;
        Ch.Stats.GoldEarned += price.Value;
        World.Shops.GetValueOrDefault(shop)?.Stock.Add(it);
        if (it.Def == "wolf_pelt" && shop == "brannoc")
            Apply($$"""[{ "add": { "beasts.pelts_sold": {{it.Qty}} } }, { "quest": { "id": "beasts", "entry": "pelts_sold" } }]""");
        OnToast(new Toast(ToastKind.Gold, $"Sold {Inventory.Name(it)}{(it.Qty > 1 ? $" ×{it.Qty}" : "")}", $"+{price} gold"));
        OnTouch();
    }

    /* ------------------------------------------------------ the storeroom -- */

    public void ToStash(string uid)
    {
        int i = Ch.Pack.FindIndex(x => x?.Uid == uid), j = World.Stash.IndexOf(null);
        if (i < 0) return;
        if (j < 0) { Warn("The storeroom is full"); return; }
        World.Stash[j] = Ch.Pack[i];
        Ch.Pack[i] = null;
        OnTouch();
    }

    public void FromStash(string uid)
    {
        int j = World.Stash.FindIndex(x => x?.Uid == uid);
        if (j < 0) return;
        if (!Inventory.AddToPack(Ch, World.Stash[j]!)) { Warn("Your pack is full"); return; }
        World.Stash[j] = null;
        OnTouch();
    }

    /* -------------------------------------------------------------- rest -- */

    /// <summary>A bed at the inn: free to someone Mother Rook is fond of.</summary>
    public int RestCost
    {
        get { var rook = World.Npc("rook"); return rook.Affection >= 30 || rook.Trust >= 40 ? 0 : 5; }
    }

    /// <summary>Wait for nightfall.</summary>
    public void Nightfall() => World.Time = TimeOfDay.Night;

    /// <summary>Sleep the night: the world moves on a day, the ember goes
    /// out, wounds close. What happened overnight, as lines to read.</summary>
    public List<string>? Sleep(Battle? b, Func<double> rng)
    {
        int cost = RestCost;
        if (Ch.Gold < cost) return null;
        Ch.Gold -= cost;
        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Day;
        Expedition = null;
        if (b != null) b.Player.Hp = b.MaxHp;
        var lines = new List<string>(report.Lines);
        // The talk of the town: who heard what, overnight.
        var short_ = new Dictionary<string, string> { ["holloway"] = "Holloway", ["harlan"] = "Harlan", ["pell"] = "Pell", ["keegan"] = "Keegan" };
        var byEvent = new List<(string Event, List<string> Who)>();
        foreach (var h in report.Heard)
        {
            if (Lore.Person(h.Npc) == null) continue;
            var entry = byEvent.FirstOrDefault(x => x.Event == h.Event);
            if (entry.Who == null) byEvent.Add(entry = (h.Event, new()));
            entry.Who.Add(short_.GetValueOrDefault(h.Npc) ?? Lore.NameOf(h.Npc));
        }
        foreach (var (id, who) in byEvent.Take(2))
        {
            var ev = World.History.FirstOrDefault(h => h.Id == id);
            if (ev == null) continue;
            var names = who.Count == 1 ? who[0] : $"{string.Join(", ", who.Take(who.Count - 1))} and {who[^1]}";
            lines.Add($"By breakfast, {names} had heard that you {ev.Text}.");
        }
        if (lines.Count == 0) lines.Add("A quiet night. Rook's bread is hot, and nobody died.");
        OnTouch();
        return lines;
    }

    /* --------------------------------------------------------------- map -- */

    /// <summary>Mark the ground around (x, z) as walked on a zone's map
    /// (its fog grid over extent metres, a character a cell). True if any
    /// was new.</summary>
    public bool Walk(string zone, double extent, double x, double z, double r = 30)
    {
        var zs = World.Zone(zone);
        var seen = zs.TryGetValue("seen", out var f) && f.Str is { Length: FogN * FogN } s ? s.ToCharArray() : new string('0', FogN * FogN).ToCharArray();
        double c = extent / FogN;
        bool changed = false;
        int i0 = (int)Math.Floor((x - r) / c + FogN / 2.0), i1 = (int)Math.Floor((x + r) / c + FogN / 2.0);
        int j0 = (int)Math.Floor((z - r) / c + FogN / 2.0), j1 = (int)Math.Floor((z + r) / c + FogN / 2.0);
        for (int j = Math.Max(0, j0); j <= Math.Min(FogN - 1, j1); j++)
            for (int i = Math.Max(0, i0); i <= Math.Min(FogN - 1, i1); i++)
            {
                double cx = (i + 0.5 - FogN / 2.0) * c, cz = (j + 0.5 - FogN / 2.0) * c;
                if (seen[j * FogN + i] == '0' && Math.Sqrt((cx - x) * (cx - x) + (cz - z) * (cz - z)) < r) { seen[j * FogN + i] = '1'; changed = true; }
            }
        if (changed) zs["seen"] = new string(seen);
        return changed;
    }
}

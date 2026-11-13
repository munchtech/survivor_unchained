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
/// <param name="Through">(M5 r2) Shown even while banners are held (IZoneHost.HoldBanners): the staging's own.</param>
public sealed record Announcement(string Title, string? Sub, string Kind, double Seconds, string? Kicker = null, bool Through = false);

/// <summary>A piece fell that grants a skill her calling can get no other way (Drops.GiftOf): the biggest drop in the game. Its own
/// event, beside the Legendary's sound and beam it borrows until bd-ui gives it a voice and a look.</summary>
public sealed record GiftDrop(ItemInstance Item, string Skill);

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
    /// <summary>A skill-granting great piece has fallen (see <see cref="GiftDrop"/>); raised once per piece, as it is rolled.</summary>
    public Action<GiftDrop> OnGift = _ => { };
    /// <summary>The first Legendary (or Storied) piece this world has ever seen taken, and where it lay:
    /// the experience director stages its moment on it (docs/design/LOOT_DESIGN.md §8.2).</summary>
    public Action<ItemInstance, double, double> FirstLegendaryTaken = (_, _, _) => { };
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
        // (M7a) A new survivor's first run (the Ford) has no point lit: each carried wick skill holds its first
        // (skill_lamps.json rules.points.lit; ARPG.md 5 row 5a: her first level's card offers it). Here, not in
        // Character.Create: the creation screen's figures and bare test characters burn every point as before.
        foreach (var (id, _) in SkillBook.Carried(ch).ToList()) WickBook.Arrived(ch, id);
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
        TakeRoadPick();
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
    /// <summary>The fight in play carries the world's tier, so its drops do too (Drops).</summary>
    public bool WorldTierOn;

    public Battle StartBattle(bool combat, CollisionWorld col, Func<double, double, double> heightAt, double x, double z, double facing, uint seed, bool arena = false, bool ember = false, bool? worldTier = null)
    {
        // The kit goes on with the place: the night's wherever the ember burns, where its coals work.
        FightNight = combat && (arena || ember);
        Kits.Wear(Ch, FightNight ? KitKind.Night : KitKind.Day);
        // (M3) A campaign fight: her calling's taught build is what she carries (taught_builds.json), its levels granted.
        bool campaign = combat && !arena && !ember;
        if (campaign)
            // (M7a) A skill granted as the fight starts holds its points like one taught mid-fight.
            foreach (var s in Content.TaughtBuilds.Grant(Ch, Ch.Level)) WickBook.Arrived(Ch, s.Skill);
        var kit = Character.Kit(Ch, FightNight);
        InArena = arena;
        var exp = combat && !arena ? Expedition : null;
        var b = new Battle(new BattleSetup
        {
            Seed = seed, Combat = combat, Collision = col, HeightAt = heightAt, Stats = kit.Stats,
            // The campaign (ARPG.md 3.1): story fights press their skills; the arena keeps every skill self-firing, and so
            // does a night the ember burns in (the prologue's: the survivors' ruleset, the arena's in all but name, until
            // the ARPG tutorial replaces it).
            Campaign = campaign,
            StartX = x, StartZ = z, StartFacing = facing,
            // (bd-keys) In the campaign her bar (Character.Bar): her keys in key order (the basic attack on the first), her
            // auto slots, her gear's auto skills; those that run themselves come in kindled; set B's stance once it opens.
            Weapons = campaign ? kit.Bar : kit.Weapons, Triggers = kit.Triggers, Ability = kit.Ability,
            Kindled = campaign ? kit.Autos : null, Stance = campaign ? SkillBook.StanceOf(Ch) : null, Calling = Ch.Archetype,
            ArtRank = kit.ArtRank, Facets = kit.Facets, DashSteps = kit.DashSteps,
            Lamps = kit.Lamps, ReflexRanks = kit.ReflexRanks, Level = Ch.Level,
            // Each skill's wick, as planned by day (Light my way where she planned none).
            // (M7a) By day a skill holding points lights only its burning lamps; a night takes the whole path.
            Wicks = combat ? WickBook.Paths(Ch, night: arena || ember) : null,
            // Story fights are short: the Flare starts at half (CLASSES.md §3.2). Nights and maps (arena runs) start at a fifth.
            FlareStart = combat && ember && !arena ? Battle.FlareFull / 2 : combat && arena ? Battle.FlareStartNight : 0,
            Hp = exp != null ? Math.Min(exp.Hp, kit.Stats.Get(Stat.MaxHealth)) : null,
        });
        // The world's tier (ARPG.md 7.3) goes on story fights and story nights; not on arena nights or maps (worldTier false: they climb
        // tiers with the atlas later). Left null it is every non-arena fight.
        WorldTierOn = combat && (worldTier ?? !arena);
        if (WorldTierOn)
        {
            var wt = Content.WorldTiers.Get(Content.WorldTiers.Of(World));
            b.WorldHealth = wt.Health; b.WorldDamage = wt.Damage; b.KitDamageMul = wt.Kit; b.KitEveryMul = wt.KitEvery; b.StoryStand = wt.Stand;
        }
        // (M6, TUTORIAL_COPY.md A12/A14) Taken at the Low Ford's dawn page, the Flare is not hers again until the
        // Waystation's lamp lights it for good; arena runs keep theirs.
        if (!arena && FlareOut) { b.Flare = null; b.FlareMeter = 0; }
        b.EmberOn = combat && (arena || ember);
        EmberLit = b.EmberOn && !arena;
        b.Night = arena || ember || World.Time == TimeOfDay.Night;
        GearWeapons = kit.Weapons.Select(w => w.Id).ToHashSet();
        b.Favours.UnionWith(Callings.Archetype(Ch.Archetype).Favours);
        b.Calling = Ch.Archetype;
        // (bd-keys) The campaign runs each carried skill in the form its place gives it (Character.Bar: a key pressed, an
        // auto slot kindled), set as it came in (BattleSetup.Kindled), no longer the taught build's over her choice.
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
        else if (combat && !campaign)
            foreach (var (id, rank) in kit.Learned) b.AddWeapon(id, rank);
        // (bd-sockets) The Unions she has joined go in before the kit's learned set is read (their halves leave the fight).
        if (campaign) UnionJoin.Apply(b, Ch);
        b.KitLearned = combat && campaign && !b.EmberOn ? kit.Learned.Select(w => w.Id).Where(id => b.Weapons.Any(x => x.Id == id)).ToHashSet() : null;
        campaignFight = campaign ? b : null;
        // (M6, TUTORIAL_COPY.md A3) A story fight with the ember out: the dead still spill their light, and it pays her
        // experience as it reaches her (Battle.DropXpStones). Arena runs pay at their end, as before.
        stoneFight = combat && !arena && !b.EmberOn ? b : null;
        if (stoneFight != null) b.PayXp = Learn;
        // (bd-sockets) The gems in her skills' sockets.
        if (combat) b.WearSupports(Supports.SourceFor(Ch));
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

    /// <summary>The fight in play is read by the night's rules (StartBattle: an ember arena or night), until its
    /// dawn (Douse): a gear change mid-fight is read in that context (RefreshKit, SU-039).</summary>
    public bool FightNight { get; private set; }

    /// <summary>The dawn: the ember goes out, and what it built with it; what the night taught is
    /// paid. The levels it came to.</summary>
    public int Douse(Battle b)
    {
        // (from the dawn on, the fight is read by day: a gear change after it too, RefreshKit)
        FightNight = false;
        var kit = Character.Kit(Ch);
        b.Douse(kit.Weapons);
        GearWeapons = kit.Weapons.Select(w => w.Id).ToHashSet();
        EmberLit = false;
        if (!InArena && b.Combat) { stoneFight = b; b.PayXp = Learn; }
        if (World.NightLessons <= 0) return 0;
        int levels = Character.GainXp(Ch, World.NightLessons);
        World.NightLessons = 0;
        if (levels > 0) RaiseRoad();
        return levels;
    }

    /// <summary>Leaving a zone: the wounds come along (an arena's are left in it).</summary>
    public void Capture(Battle? b)
    {
        // (M6 A3) Leaving: the experience stones still lying or on their way are hers now.
        b?.PayXpStones();
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
        // (M6 A3) With the ember out in a story fight, it comes to her as stones and is paid as each lands.
        if (stoneFight is { PayXp: not null, EmberOn: false } sf) { sf.DropXpStones(e.X, e.Z, xp); return; }
        Learn(xp);
    }

    /// <summary>The fight whose kills spill experience stones (a story fight with the ember out), else null.</summary>
    Battle? stoneFight;

    /// <summary>Experience reaching her (a kill's, or its stone's as it lands): a level teaches and is named, and the
    /// road's choice is raised when she reaches it (RaiseRoad).</summary>
    public void Learn(double xp)
    {
        int levels = Character.GainXp(Ch, xp);
        if (levels > 0)
        {
            Teach(campaignFight);
            Grew();
            RaiseRoad();
            OnTouch();
        }
    }

    /* ---------------------------------------------- the road (subclass) -- */

    /* Her road is chosen at LampBook.RoadLevel (BUILD_UNLOCKS: level 6), a story beat with weight. The game raises it
     * (RaiseRoad: the fact road.open, an announcement, OnRoadOpen); a story scene makes the choice by setting the fact
     * road.pick to a road's id (TakeRoadPick, after any Apply), and until that scene exists the lamp-post's menu offers it
     * (PostMenu.Option.Road). Afterwards she changes it at any lamp-post, free (WalkRoad). The fact road.walked holds the
     * road she walks, for the story's conditions. */

    /// <summary>World facts of the road's beat: raised, the scene's pick, and the road walked.</summary>
    public const string RoadOpenFact = "road.open", RoadPickFact = "road.pick", RoadWalkedFact = "road.walked";

    /// <summary>The road's choice was raised (the view may stage it; the story lead's scene will).</summary>
    public Action OnRoadOpen = () => { };

    /// <summary>The road's choice waits on her: her level has reached it and she walks none.</summary>
    public bool RoadDue => LampBook.RoadOpen(Ch) && LampBook.Roadless(Ch);

    /// <summary>Raise the road's choice once, when it is due: the fact road.open, the announcement, OnRoadOpen. True when raised now.</summary>
    public bool RaiseRoad()
    {
        if (!RoadDue || World.Fact(RoadOpenFact).Truthy) return false;
        World.Facts[RoadOpenFact] = true;
        OnAnnounce(new Announcement("Choose your road", "Two roads lie open to you. Take one at a lamp-post", "boon", 4.5, "Your road"));
        OnRoadOpen();
        return true;
    }

    /// <summary>A story scene's choice (the fact road.pick set to a road's id): walked as WalkRoad's first choice, and the fact cleared.</summary>
    void TakeRoadPick()
    {
        if (World.Fact(RoadPickFact).Str is not { Length: > 0 } pick) return;
        World.Facts.Remove(RoadPickFact);
        WalkRoad(pick, null);
    }

    /// <summary>Walk a road of her calling: her first choice (anywhere the beat is offered), or a change at a lamp-post or in a
    /// town by day (LampBook.LayoutsOpen, as the layouts; free). The layout in use is refunded to the road's free lamps
    /// (LampBook.ChooseRoad), and its own skill is learned if she does not know it. Null when walked; else why not.</summary>
    public string? WalkRoad(string road, string? zone, string? atPost = null)
    {
        if (!LampBook.RoadOpen(Ch)) return $"Your road opens at level {LampBook.RoadLevel}";
        if (Content.Lamps.Roads.GetValueOrDefault(road) is not { } r || r.Calling != Ch.Archetype) return "Not a road of your calling";
        if (LampBook.Walked(Ch)?.Id == road) return "You already walk this road";
        if (!LampBook.Roadless(Ch) && !LampBook.LayoutsOpen(World, zone, atPost)) return "Change your road at a lamp-post";
        if (!LampBook.ChooseRoad(Ch, road)) return "Not now";
        World.Facts[RoadWalkedFact] = road;
        string? taught = null;
        if (LampBook.RoadSkill(Ch, road) is { } id && !SkillBook.Knows(Ch, id))
        {
            if (!Ch.Discovered.Contains(id)) Ch.Discovered.Add(id);
            if (SkillBook.Learn(Ch, id)) { WickBook.Arrived(Ch, id); taught = id; }
        }
        OnToast(new Toast(ToastKind.Level, $"You walk {r.Name}", taught != null && Content.Weapons.All.TryGetValue(taught, out var wd) ? $"{r.Line} {wd.Name} is yours." : r.Line));
        OnTouch();
        return null;
    }

    /// <summary>The campaign fight running (its levels teach the taught build into it), else null.</summary>
    Battle? campaignFight;

    /// <summary>(M3) Levels reached in the campaign teach the taught build's slots of those levels (TaughtBuilds.Grant),
    /// each into the fight running in its taught form (a worn skill the build does not name gives up its key if the keys
    /// are full), with an Ev.Taught for the views and the tutorial. What was taught.</summary>
    public List<Content.TaughtSlot> Teach(Battle? b)
    {
        var got = Content.TaughtBuilds.Grant(Ch, Ch.Level);
        foreach (var s in got)
        {
            // (M7a) It comes in holding its points (its first waits for her too), while she lights them herself.
            WickBook.Arrived(Ch, s.Skill);
            if (b != null && WickBook.Paths(Ch) is { } paths && paths.TryGetValue(s.Skill, out var path)) b.WickPaths[s.Skill] = path;
            int slot = -1;
            if (b != null && b.Campaign && !b.Weapons.Exists(w => w.Id == s.Skill))
            {
                // (bd-keys) a kindled one comes into an auto slot (never full); a pressed one into a key, a worn key the
                // build does not name giving it up when the keys are full
                if (s.Cast == "kindle") b.Kindles.Add(s.Skill); else b.Kindles.Remove(s.Skill);
                if (!b.HasRoomFor(s.Skill) && Content.TaughtBuilds.Of(Ch.Archetype) is { } t
                    && b.Weapons.LastOrDefault(w => w.Slot < b.KeyCount && t.Slots.All(x => x.Skill != w.Id)) is { } spare)
                    b.RemoveWeapon(spare.Id);
                if (b.AddWeapon(s.Skill, WickBook.DayRank(Ch, s.Skill)) is { } w) { b.SetForm(s.Skill, s.Cast); slot = w.Slot; }
            }
            b?.Events.Emit(new Ev.Taught { Skill = s.Skill, Cast = s.Cast, Slot = slot, Level = Ch.Level });
        }
        // (bd-keys) The stance opens on its level (BUILD_UNLOCKS.md: the eighth), in the fight running too.
        if (b != null && b.Campaign) b.SetStance(SkillBook.StanceOf(Ch));
        return got;
    }

    /// <summary>(M7a) Light one point a carried skill holds (the level-up card's offer; ARPG.md 3.5 "one press lights it"):
    /// WickBook.Light, then the live weapon in the fight, if there is one, takes the skill's DayRank and its day path
    /// (Battle.LightHeld: ranked by RankWeapon, relit, an Ev.Wick for the lamp). The lamp lit, or null when nothing was held.
    /// Any time is allowed: the Battle has no "a foe is on her" test (the zone's Encounters.Fighting is the caller's).</summary>
    public string? LightHeld(string skill, Battle? b)
    {
        if (WickBook.Held(Ch, skill) <= 0) return null;
        var lamp = WickBook.Light(Ch, skill);
        b?.LightHeld(skill, WickBook.DayRank(Ch, skill), WickBook.DayPath(Ch, skill));
        return lamp;
    }

    /// <summary>(M4) What the calling last taught in a campaign fight, and at which level: the HUD's level card prints it.</summary>
    public (int Level, string Skill)? CallingTaught;

    /// <summary>The survivor has grown: their calling may teach them a skill
    /// they have seen burn (every third level). What it taught, or null.</summary>
    public string? Grew()
    {
        if (SkillBook.Calling(Ch) is not { } id) return null;
        var wd = Content.Weapons.All[id];
        if (campaignFight is { Campaign: true }) CallingTaught = (Ch.Level, id);
        else OnAnnounce(new Announcement(wd.Name, "Your calling teaches it to you. Put it on a key (K)", "boon", 3.8, "A new skill"));
        return id;
    }

    /// <summary>A pickup reached the survivor: gear, materials and quest
    /// things into the pack. False leaves it on the ground (a full pack).</summary>
    public bool PickedUp(Pickup p)
    {
        // A chart carries its map in its name until it is in the pack.
        if (p.Kind == PickupKind.Item && p.Ref != null && Maps.Charts.FromRef(p.Ref) is { } chart)
            return GiveChart(chart);
        // Gear rolled whole where it fell (Rpg/Loot.cs) is taken as it is.
        if (p.Payload is ItemInstance whole)
        {
            if (!Take(whole)) return false;
            if (!World.FirstLegendaryTaken && Rpg.Drops.TierOf(whole) is LootTier.Legendary or LootTier.Storied)
            {
                World.FirstLegendaryTaken = true;
                FirstLegendaryTaken(whole, p.X, p.Z);
            }
            return true;
        }
        if (p.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Quest && p.Ref != null)
        {
            // Gear on the ground was rolled when it fell; its light said how good it is. A ruler's
            // Mark fell at its grade the same way.
            int? rolled = p.Kind == PickupKind.Item && (Items.Find(p.Ref)?.Base != null || Crafting.MarkOf(p.Ref) != null) ? p.Tier : null;
            return GiveItem(p.Ref, Math.Max(1, MathX.RoundInt(p.Value)), rolled, p.Lean, dropped: true);
        }
        return true;
    }

    /// <summary>Something found in the field. False if there is no room.</summary>
    /// <param name="dropped">It fell in the world (its heat is rolled: docs/CRAFTING_DESIGN.md 5.1).</param>
    /// <summary>A Wayfinder's chart into the pack.</summary>
    public bool GiveChart(Maps.Chart chart)
    {
        var it = Inventory.Make(Ch, Maps.Charts.Item, 1, chart.Rarity);
        it.Chart = chart;
        it.Name = Maps.Charts.Title(chart);
        // A chart has heat as a piece has: the budget for working it at the Wayfinder's table.
        it.Heat = it.HeatFull = Crafting.ChartHeat(chart);
        if (!Inventory.AddToPack(Ch, it)) { OnToast(new Toast(ToastKind.Warning, "Your pack is full", it.Name)); return false; }
        OnToast(new Toast(ToastKind.Loot, it.Name, Items.Get(Maps.Charts.Item).Description, Items.Get(Maps.Charts.Item).Icon, it.Rarity));
        OnTouch();
        return true;
    }

    public bool GiveItem(string defId, int qty = 1, int? rarity = null, IReadOnlyCollection<string>? lean = null, bool dropped = false)
    {
        // Found in a Wayfinder's map, gear is made at the map's level (design 20.3).
        var it = Inventory.Make(Ch, defId, qty, rarity, lean: lean, dropped: dropped, level: dropped ? World.Map?.ItemLevel : null);
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
        var landed = Inventory.Deliver(Ch, World, it);
        OnToast(new Toast(ToastKind.Loot, Inventory.Name(it), landed switch
        {
            Inventory.Landed.Pack => "Yours again",
            Inventory.Landed.Shelf => "Your pack is full: Rook will keep it for you",
            _ => "Your pack and Rook's shelves are full: she is holding it by the door",
        }, def.Icon, it.Rarity));
        OnTouch();
    }

    // (SU-058) The corpse-and-nemesis death (Fell) is retired: a fight's death is its zone's (Zone.OnDeath: she rises at
    // a post, or the run ends). An old save's Corpse and Nemesis still load (WorldState) and are ignored.

    static string Esc(string s) => s.Replace("\\", "\\\\").Replace("\"", "\\\"");

    /// <summary>A story fight lost (the owner, 4 October): the night is gone, and she wakes in
    /// town the next morning on Chid's bench, carried home in the dark. Call it as she wakes; Chid's
    /// conversation tells the waking for the fight she lost (docs/WRITING_PASS.md §22). It costs
    /// the night, and nothing else: no gold, no wound, nothing carried off.</summary>
    public void CarriedHome(SurvivorUnchained.Arena.ArenaSpec spec) => Apply($$"""
        [{ "set": { "player.just_died": true, "player.carried_home": "{{Esc(spec.Id)}}" } }, { "add": { "player.deaths": 1 } }]
        """);

    /* -------------------------------------------------------------- gear -- */

    const string Draught = "health_draught", Moonpetal = "moonpetal_draught";

    /// <summary>The draughts the draught key can drink, of either kind (the HUD's count).</summary>
    public int Draughts => Inventory.Count(Ch, Draught) + Inventory.Count(Ch, Moonpetal);

    /// <summary>R: drink a draught: the one that fits the wound. The moonpetal (60%) only for a deep
    /// one, 55% of health or more gone, so a rare draught is not spent on a scratch (combat's rule).</summary>
    public void Quaff(Battle? b)
    {
        if (b == null || !b.Player.Alive) return;
        if (b.NoDraught) { Warn("You have no draught"); return; } // reaver.nothing_spared
        if (Draughts == 0) { Warn("No draughts left"); return; }
        if (b.Player.Hp >= b.MaxHp - 0.5) { Warn("You are unhurt"); return; }
        bool deep = 1 - b.Player.Hp / b.MaxHp >= 0.55, moon = Inventory.Count(Ch, Moonpetal) > 0, plain = Inventory.Count(Ch, Draught) > 0;
        string pick = (deep && moon) || !plain ? Moonpetal : Draught;
        Inventory.Take(Ch, pick, 1);
        b.HealPlayer(b.MaxHp * (Items.Get(pick).Consumable?.Heal ?? 0.4), "draught");
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
        if (Inventory.Find(Ch, uid) is not { Carried: true } loc) return;
        var def = Items.Get(loc.Item.Def);
        if (def.Kind != ItemKind.Consumable || def.Consumable is not { } c) { if (loc.InPack) PutOn(uid, Kits.On(Ch), null, b); return; }
        if (c.Heal is double heal && b != null)
        {
            if (b.NoDraught) { Warn("You have no draught"); return; } // reaver.nothing_spared
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
            if (!SkillBook.Carries(Ch, skill)) { Warn($"{wd.Name} is not a {Callings.Archetype(Ch.Archetype).Name}'s to carry"); return; }
            if (!SkillBook.Learn(Ch, skill)) { Warn($"The words mean nothing yet: {wd.Name} has to be seen burning in an arena first"); return; }
            OnAnnounce(new Announcement(wd.Name, SkillBook.Meets(Ch, skill) ? "Learned for the day. Carry it from your skills (K)" : $"Learned, but it asks {SkillBook.Need} {SkillBook.Attribute(skill)} of you", "boon", 3.6, "A new skill"));
            // (SU-045) carried now, it goes into the fight running at once
            RefreshKit(b);
        }
        foreach (var cure in c.Cure ?? new())
        {
            if (cure == "poisoned" && b != null) b.Player.PoisonT = 0;
            if (EnumKey<ConditionId>.TryParse(cure, out var cid)) Ch.Conditions.RemoveAll(x => x.Id == cid);
        }
        Inventory.Remove(Ch, uid, 1);
        OnToast(new Toast(ToastKind.World, $"{def.Name} used"));
        OnTouch();
    }

    /// <summary>A quest thing whose part in the story is not yet played.</summary>
    public bool StillNeeded(ItemInstance it) => Items.Get(it.Def) is { Kind: ItemKind.Quest } d && Rules.Test(d.Needed, Ctx);

    public void Drop(string uid)
    {
        if (Inventory.Find(Ch, uid) is not { Carried: true } loc) return;
        if (StillNeeded(loc.Item)) { Warn("You might need that"); return; }
        Inventory.Remove(Ch, uid);
        OnToast(new Toast(ToastKind.World, $"Left behind: {Inventory.Name(loc.Item)}"));
        OnTouch();
    }

    /// <summary>The sources Character.Kit gives that follow what she wears: a piece's numbers and rules, a set's
    /// bonuses, her traits, her attributes and her conditions. Its lamps' numbers (lamp:, lamps:, price:) stay as
    /// lit, and the battle's own (weapon:, evo:, boon:, its own lamp: rules) are never touched (SU-038).</summary>
    public static bool FromKit(string src) =>
        src.StartsWith("item:") || src.StartsWith("set:") || src.StartsWith("trait:") || src == "attributes" || src.StartsWith("cond:");

    /// <summary>The build changed (gear put on or off, a layout switched, a lamp lit or put out, a wick planned, a skill
    /// learned from a tome, an attribute point spent): the ONE live-build reconcile (CODEX_audit.md installments 6 and 7).
    /// A fresh read of the kit in the fight's own context (by night, the night's lamp rules) goes into the running fight
    /// at once: the gear's numbers and rules, the lamps' (replaced, not merged: Battle.ReplaceLamps; their reflexes, the
    /// Flare), the art in hand, the wicks, and the skills she fights with (the gear's; by day the learned ones she now
    /// carries, at their rank and in the campaign in their taught form; one no longer carried goes). The same build
    /// after any number of refreshes, and the rest of the fight left alone. The caged coals' draft gifts (rerolls,
    /// banishes, stands, roads, omens, start levels) stay as the ember was lit (StartBattle), by installment 6's ruling.</summary>
    public void RefreshKit(Battle? b)
    {
        OnTouch();
        if (b == null) return;
        var kit = Character.Kit(Ch, FightNight);
        b.Stats.RemoveWhere(FromKit);
        b.Stats.SetBase(kit.Stats.GetBase());
        b.Stats.AddAll(kit.Stats.List().Where(m => FromKit(m.Source)).ToList());
        b.Triggers = b.Triggers.Where(t => !FromKit(t.Source)).ToList();
        foreach (var (def, src) in kit.Triggers) if (FromKit(src)) b.AddTrigger(def, src);
        // The lamps (SU-042): their numbers, facets, reflexes and Flare, replaced; the art in hand as the kit reads it.
        b.SetArt(kit.Ability, kit.ArtRank, kit.Facets);
        b.ReplaceLamps(kit.Lamps, kit.ReflexRanks);
        // (M6, A12/A14) the Flare taken at the Low Ford's dawn stays out until the Waystation lights it
        if (!InArena && FlareOut) { b.Flare = null; b.FlareMeter = 0; }
        // The wicks as planned now (a plan changed, a layout switched): a skill whose path changed relights to it.
        if (b.Combat && WickBook.Paths(Ch, night: FightNight) is { } paths)
            foreach (var (id, path) in paths)
                if (!b.WickPaths.TryGetValue(id, out var was) || !was.SequenceEqual(path))
                {
                    b.WickPaths[id] = path;
                    foreach (var w in b.Weapons.Where(x => x.Id == id).ToList()) b.Relight(w, false);
                }
        var kitIds = kit.Weapons.Select(w => w.Id).ToHashSet();
        // By day, the learned skills she carries now (SU-045: a tome read, a point crossing a need, a layout's skills).
        bool learns = b.KitLearned != null;
        var learned = learns ? kit.Learned : new List<(string Id, int Rank)>();
        var learnedIds = learned.Select(w => w.Id).ToHashSet();
        var ours = GearWeapons.Concat(b.KitLearned ?? []).ToHashSet();
        // What a fresh battle keys (StartBattle): (bd-keys) her bar (Character.Bar) in the campaign, while the keys have
        // room (the keys a skill the kit did not give holds stay its; auto slots never run out); the gear's elsewhere.
        var want = new List<(string Id, int Rank)>();
        // (bd-sockets) The Unions live now: one no longer live leaves the fight (its halves come back through the bar); a live
        // one already in keeps its halves out of it.
        var live = b.Campaign && learns ? UnionJoin.Live(Ch) : new List<Content.UnionDef>();
        var heldHalves = new HashSet<string>();
        if (b.Campaign && learns)
        {
            foreach (var u in Content.Unions.All)
            {
                if (!b.Weapons.Any(x => x.Id == u.Into)) continue;
                if (!live.Contains(u)) b.RemoveWeapon(u.Into);
                else { heldHalves.Add(u.A); heldHalves.Add(u.B); }
            }
        }
        if (learns)
        {
            int room = b.KeyCount - b.Weapons.Where(w => !ours.Contains(w.Id) && w.Slot < b.KeyCount).Sum(w => Content.Weapons.SlotCost(w.Id));
            foreach (var s in kit.Bar)
            {
                if (!Content.Weapons.All.ContainsKey(s.Id) || want.Any(x => x.Id == s.Id) || heldHalves.Contains(s.Id)) continue;
                int cost = kit.Autos.Contains(s.Id) ? 0 : Content.Weapons.SlotCost(s.Id);
                if (cost > room) continue;
                room -= cost; want.Add(s);
            }
        }
        else want.AddRange(kit.Weapons);
        var wantIds = want.Select(s => s.Id).ToHashSet();
        foreach (var id in ours) if (!wantIds.Contains(id)) b.RemoveWeapon(id);
        GearWeapons = kitIds;
        if (b.Campaign && learns)
        {
            // Where each runs now (she moved one between a key and an auto slot): the autos first, so a key they free
            // is free for one moving the other way.
            foreach (var w in b.Weapons.Where(w => wantIds.Contains(w.Id)).OrderBy(w => kit.Autos.Contains(w.Id) ? 0 : 1).ToList())
                b.SetForm(w.Id, kit.Autos.Contains(w.Id) ? "kindle" : (w.Def.Press?.Kind ?? Content.PressKind.Press).ToString().ToLowerInvariant());
            b.Kindles.Clear();
            b.Kindles.UnionWith(kit.Autos);
        }
        // Keys in her bar's order: a skill new to the fight takes the lowest key free.
        foreach (var (id, rank) in want)
        {
            if (b.Weapons.Any(x => x.Id == id)) { if (learnedIds.Contains(id)) b.SetRank(id, rank); continue; }
            b.AddWeapon(id, rank);
        }
        // (bd-sockets) A Union newly live joins the halves she carries.
        if (b.Campaign && learns) UnionJoin.Apply(b, live);
        // (bd-keys) Her stance as the build has it now (a stance weapon taken up at a lamp-post).
        if (b.Campaign) b.SetStance(SkillBook.StanceOf(Ch));
        if (learns) b.KitLearned = learnedIds.Where(id => b.Weapons.Any(x => x.Id == id)).ToHashSet();
        // (M9) A campaign fight's carried skills at their rank with the gear worn now ("+1 to a skill" on or off).
        if (b.Campaign)
        {
            var carried = SkillBook.Carried(Ch).ToDictionary(c => c.Id, c => c.Rank);
            foreach (var w in b.Weapons.ToList())
                if (carried.TryGetValue(w.Id, out var r)) b.SetRank(w.Id, r);
            // (bd-sockets) A Union runs at the better of its halves' ranks.
            foreach (var u in Content.Unions.All)
                if (b.Weapons.Find(x => x.Id == u.Into) is { } uw && carried.TryGetValue(u.A, out var ra) && carried.TryGetValue(u.B, out var rb))
                {
                    b.SetRank(u.Into, Math.Max(ra, rb));
                    if (uw.Half != null) uw.Half.Rank = uw.Rank;
                }
        }
        // In a map (and only there) its Marks and skill numbers are worn again: replaced, not merged (SU-041).
        if (b.WearsMarks) b.Wear(kit.Marks, kit.SkillMods);
        b.GearIds.Clear(); b.GearIds.UnionWith(kit.GearIds);
        b.GearStatuses.Clear(); b.GearStatuses.UnionWith(kit.GearStatuses);
        b.Player.Hp = Math.Min(b.Player.Hp, b.MaxHp);
        if (b.Combat) b.WearSupports(Supports.SourceFor(Ch));
    }

    /// <summary>The Flare is out for the story (taken at the Low Ford's dawn, not yet lit at the Waystation).</summary>
    bool FlareOut => World.Fact(Zones.Prologue.FlareOutFact).Truthy && !World.Fact(Zones.Prologue.FlareLitFact).Truthy;

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

    /// <summary>A step of the dash's growth (Content/DashSteps.cs) taken: kept on her, and into the fight now if
    /// one runs (Ev.DashStep, for the view to announce). The design lead's route (a lamp-post Wick, a level-up)
    /// calls this. False if unknown or taken as often as it may be.</summary>
    public bool GrantDashStep(string id, Battle? b)
    {
        if (!Ch.GrantDashStep(id)) return false;
        b?.GrantDashStep(id);
        OnTouch();
        return true;
    }

    /// <summary>Carry another known art (somewhere safe).</summary>
    public void HoldArt(string id, Battle? b)
    {
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
            // Snib's jars, bought in his hearing (docs/CRAFTING_DESIGN.md 9): the talk goes on.
            case "slurry":
            {
                var q = Crafting.BuyJar(Craft);
                if (!q.Ok) { Warn(q.Blocked!); return true; }
                Make(q);
                return true;
            }
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
        if (Inventory.Find(Ch, uid) is not { Carried: true } at) return null;
        var mine = at.Item;
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
        // Out of wherever it is carried, the whole of it: a stack on their counter.
        var it = Inventory.Remove(Ch, uid)!;
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

    /// <summary>Wait for nightfall: a shortcut through what is left of the day (the clock would
    /// bring it anyway).</summary>
    public void Nightfall()
    {
        World.Time = TimeOfDay.Night;
        World.Clock = DayClock.NightAt;
    }

    /// <summary>Sleep the night: the world moves on a day, the ember goes
    /// out, wounds close. What happened overnight, as lines to read.</summary>
    public List<string>? Sleep(Battle? b, Func<double> rng)
    {
        int cost = RestCost;
        if (Ch.Gold < cost) return null;
        Ch.Gold -= cost;
        var report = Simulation.AdvanceDay(Ctx, rng);
        World.Time = TimeOfDay.Day;
        World.Clock = DayClock.DayAt;
        Expedition = null;
        if (b != null) b.Player.Hp = b.MaxHp;
        var lines = Overnight(report, atInn: true);
        if (lines.Count == 0) lines.Add("A quiet night. Rook's bread is hot, and nobody died.");
        OnTouch();
        return lines;
    }

    /// <summary>What the night brought, as lines: the world's own news, the talk of the town (who
    /// heard what), and, for a night spent at the inn, Wenna's flask filled; and the smith's morning.</summary>
    List<string> Overnight(DayReport report, bool atInn)
    {
        var lines = new List<string>(report.Lines);
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
        if (atInn && Flask() is { } flask) lines.Add(flask);
        Crafting.Morning(World);
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

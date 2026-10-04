using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.World;

/* The written world, as data (data/content, exported from the web game):
 * the journal's quests, the people of the Waystation and those met on the
 * road, the shops, the town's folk and what they mutter, what is on each
 * person's mind, and the looks a survivor can be given. */

public sealed class QuestDef
{
    public string Id = "", Name = "", Summary = "";
    public string? Giver;
    public Dictionary<string, string> Entries = new();
    /// <summary>How each ending reads.</summary>
    public Dictionary<string, string>? Outcomes;
    /// <summary>Shown as a breadcrumb, not a quest with an ending.</summary>
    public bool Mystery;
}

public sealed class Spot { public double X, Z, Facing; }

public sealed class Dye { public string? Cloth, Under; }

/// <summary>Who someone is in the flesh: a Quaternius person (the view's People).</summary>
public sealed class PersonSpec
{
    public Sex Sex;
    /// <summary>Whose body: null for the Quaternius base of their sex (and
    /// its clothes); "woman" for the woman survivor's own body (her hair and
    /// suit her own: Loadouts.HerBody), "anime" for donizaki's, bare.</summary>
    public string? Body;
    public string? HairColor, Hair, Skin;
    public List<string>? Outfit;
    public bool? Beard;
    /// <summary>A hero's own beard (Lore.Hero's beards: the male hero's), or none.</summary>
    public string? BeardStyle;
    public double? Figure, Head;
    public Dye? Dye;
    /// <summary>Her face (her body's own): its sliders, -1 to 1 about her own.</summary>
    public Dictionary<string, double>? Face;
    /// <summary>Her eyes' colour and the ring round their pupils (null: as painted).</summary>
    public string? Eyes, EyeRing;
    /// <summary>The paint on her face (Lore.Paints), or none.</summary>
    public string? Paint;
    /// <summary>The face she started from, whose painting of her skin her head wears (none: her own).</summary>
    public string? FaceShape;
}

public sealed class Held { public string? Right, Left, Forearm; }

public sealed class NpcDef
{
    public string Id = "", Name = "", Title = "", Model = "", Idle = "", Role = "";
    public List<string> Show = new();
    public string? Tint;
    public double? Scale;
    public Spot Spot = new();
    public List<string> Barks = new();
    public List<string>? NightBarks;
    /// <summary>Things said to the air only while the world is a certain way: the
    /// town noticing what the survivor settled, and lines that stop being true.</summary>
    public List<FolkLine>? Said;
    public PersonSpec? Person;
    public Held? Arms;
}

public sealed class Speaker { public string Name = "", Title = "", Glyph = ""; }
public sealed class Guard { public double X, Z, Facing; public string Line = ""; }

public sealed class ShopLine { public string Id = ""; public int? Rarity, Qty; public Cond? When; public double? Chance; }

public sealed class ShopDef
{
    public string Id = "", Name = "";
    /// <summary>Multiplier on item value when selling to the survivor.</summary>
    public double Markup = 1;
    /// <summary>What they will buy, by item kind ('all' for a fence).</summary>
    [JsonConverter(typeof(OneOrMany<string>))] public List<string> Buys = new();
    /// <summary>Fraction of value paid when buying from the survivor.</summary>
    public double Pays;
    public List<ShopLine> Lines = new();
    public int RestockDays;
    public bool BuysAll => Buys.Contains("all");
}

public sealed class FolkLook { public string Model = "", Tint = ""; public List<string> Show = new(); public string? Under; public double? Scale; }

public sealed class FolkLine
{
    public string Text = "";
    public Cond? When;
    /// <summary>Only after dark (true) or only by day (false).</summary>
    public bool? Night;
    /// <summary>Only for a survivor who has died and come back.</summary>
    public bool? Died;
    public bool? Child, Watch;
    /// <summary>A person's line said once in a playthrough, at the first chance
    /// once it holds (npcs.json "said": Brannoc's "Twelve, I made.").</summary>
    public bool? Once;
    /// <summary>What a once-only line does when said (Maeca, seeing the fang worn: her regard falls).</summary>
    public List<Change>? Effects;
}

public sealed class Concern { public string Text = ""; public Cond? When; public bool? Died; }

public sealed class LookChoice
{
    public string Id = "", Name = "", Color = "";
    /// <summary>An eye's second colour, the ring round its pupil ("" none).</summary>
    public string Ring = "";
}

/// <summary>One of a hero's own hairstyles (the heroine's: the view's heroine_hair_ID), and how it is worn.</summary>
public sealed class HairCut { public string Id = "", Name = "", Words = ""; }

/// <summary>
/// What a hero's own body offers to be shaped with in creation (looks.json's
/// heroes, by sex: the heroine's now, the male hero's when his body has them):
/// its own hairstyles, eyes (an iris to dye), paints for the face, faces to
/// start from and the face's sliders. A body without one is shaped as the
/// kit's people are (a Quaternius cut, a beard).
/// </summary>
public sealed class HeroLook
{
    public List<HairCut> Cuts = new();
    /// <summary>His beards (the male hero's: none, stubble, short, full...), as cuts are; hers none.</summary>
    public List<HairCut> Beards = new();
    public List<LookChoice> Eyes = new();
    public List<FacePaint> Paints = new();
    public List<FaceShape> Faces = new();
    public List<FaceSlider> Sliders = new();
}

/// <summary>Paint on a face (the view's art/people/paint/ID.png): how it reads,
/// and what it is made of (its sheen, and metal for leaf).</summary>
public sealed class FacePaint
{
    public string Id = "", Name = "", Words = "";
    public double Rough = 0.7, Metal;
}

/// <summary>One of her face's sliders (the view's shape keys ID+ and ID-): its
/// group, the words for its two ends, and how far it goes each way (within
/// -1 to 1: as far as it still looks like her).</summary>
public sealed class FaceSlider
{
    public string Id = "", Name = "", Group = "", Low = "", High = "";
    public double Min = -1, Max = 1;
}

/// <summary>A face to start from: her face's sliders (-1 to 1), set together;
/// and, for a face that has its own, a skin (Lore.Skins) and eyes (the hero's).</summary>
public sealed class FaceShape
{
    public string Id = "", Name = "", Words = "";
    public string? Skin, Eyes;
    public Dictionary<string, double> Shape = new();
}

public static class Lore
{
    sealed class NpcFile
    {
        public Dictionary<string, NpcDef> Npcs = new(), Outsiders = new();
        public Dictionary<string, Speaker> Speakers = new();
        public List<Guard> Guards = new();
    }

    sealed class FolkFile
    {
        public List<FolkLook> Looks = new(), Children = new();
        public FolkLook Watch = new();
        public List<FolkLine> Lines = new();
    }

    sealed class LooksFile
    {
        public List<LookChoice> Cloaks = new(), Skins = new(), Hairs = new();
        public Dictionary<string, List<string>> HairStyles = new();
        public Dictionary<string, HeroLook> Heroes = new();
    }

    static Dictionary<string, QuestDef>? quests;
    static NpcFile? npcs;
    static Dictionary<string, ShopDef>? shops;
    static FolkFile? folk;
    static LooksFile? looks;
    static Dictionary<string, List<Concern>>? concerns;

    public static Dictionary<string, QuestDef> Quests => quests ??= Json.Parse<Dictionary<string, QuestDef>>(Json.ReadContent("quests.json"));
    static NpcFile N => npcs ??= Json.Parse<NpcFile>(Json.ReadContent("npcs.json"));
    public static Dictionary<string, NpcDef> Npcs => N.Npcs;
    public static Dictionary<string, NpcDef> Outsiders => N.Outsiders;
    public static Dictionary<string, Speaker> Speakers => N.Speakers;
    public static List<Guard> Guards => N.Guards;
    public static Dictionary<string, ShopDef> Shops => shops ??= Json.Parse<Dictionary<string, ShopDef>>(Json.ReadContent("shops.json"));
    static FolkFile F => folk ??= Json.Parse<FolkFile>(Json.ReadContent("folk.json"));
    public static List<FolkLook> FolkLooks => F.Looks;
    public static List<FolkLook> ChildLooks => F.Children;
    public static FolkLook WatchLook => F.Watch;
    public static List<FolkLine> FolkLines => F.Lines;
    static LooksFile L => looks ??= Json.Parse<LooksFile>(Json.ReadContent("looks.json"));
    public static List<LookChoice> CloakDyes => L.Cloaks;
    public static List<LookChoice> Skins => L.Skins;
    public static List<LookChoice> Hairs => L.Hairs;
    public static List<string> HairStyles(Sex sex) => L.HairStyles[sex.Key()];
    /// <summary>What a hero's own body of that sex offers to be shaped with, or null.</summary>
    public static HeroLook? Hero(Sex sex) => L.Heroes.TryGetValue(sex.Key(), out var h) ? h : null;
    /// <summary>The heroine's: her own cuts (the first hers unless another is
    /// chosen), eyes, paints, faces to start from (the first her own) and sliders.</summary>
    public static HeroLook Her => Hero(Sex.Female)!;
    public static Dictionary<string, List<Concern>> Concerns => concerns ??= Json.Parse<Dictionary<string, List<Concern>>>(Json.ReadContent("concerns.json"));

    /// <summary>Anyone who can be spoken to, in town or on the road.</summary>
    public static NpcDef? Person(string id) => Npcs.TryGetValue(id, out var n) ? n : Outsiders.TryGetValue(id, out var o) ? o : null;

    /// <summary>A name for anyone who speaks.</summary>
    public static string NameOf(string id) => Person(id)?.Name ?? (Speakers.TryGetValue(id, out var s) ? s.Name : id);

    public static string EntryText(string quest, string entry) =>
        Quests.TryGetValue(quest, out var q) && q.Entries.TryGetValue(entry, out var t) ? t : "Journal updated";

    /// <summary>A person's clothes by kind (the view's part names): the
    /// peasant's shirt, vest and trousers; the ranger's leathers; or bare to
    /// the waist. A hood and a pauldron go on top.</summary>
    public static List<string> OutfitFor(Sex sex, string kind, bool hood = false, bool pauldron = false)
    {
        string S = sex == Sex.Male ? "Male" : "Female";
        var o = kind switch
        {
            "ranger" => new List<string> { $"{S}_Ranger_Arms", $"{S}_Ranger_Body", $"{S}_Ranger_Legs", sex == Sex.Male ? "Male_Ranger_Feet_Boots" : "Female_Ranger_Feet" },
            "bare" => new List<string> { $"{S}_Peasant_Legs", $"{S}_Peasant_Feet" },
            _ => new List<string> { $"{S}_Peasant_Arms", $"{S}_Peasant_Body", $"{S}_Peasant_Legs", $"{S}_Peasant_Feet" },
        };
        if (pauldron) o.Add(sex == Sex.Male ? "Male_Ranger_Acc_Pauldron" : "Female_Ranger_Acc_Pauldrons");
        if (hood) o.Add($"{S}_Ranger_Head_Hood");
        return o;
    }

    /// <summary>A Ctx with the written world's names for people, quests and journal lines.</summary>
    public static Ctx Context(WorldState world, CharacterData ch, System.Action<Notice>? notify = null) =>
        new(world, ch, notify)
        {
            NpcName = NameOf,
            QuestName = id => Quests.TryGetValue(id, out var q) ? q.Name : id,
            // "Quest: what you learned", which the notices read as a title and
            // a line: the quest's name is the title, however many colons the line has.
            EntryText = (quest, entry) => $"{(Quests.TryGetValue(quest, out var q) ? q.Name : quest)}: {EntryText(quest, entry)}",
        };

    /// <summary>What is on someone's mind: the first concern that holds.</summary>
    public static string? ConcernOf(string npc, Ctx ctx)
    {
        if (!Concerns.TryGetValue(npc, out var list)) return null;
        bool died = ctx.Ch.Stats.Deaths > 0;
        return list.FirstOrDefault(c => (c.Died != true || died) && Rules.Test(c.When, ctx))?.Text;
    }
}

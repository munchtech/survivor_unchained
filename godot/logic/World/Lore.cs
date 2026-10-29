using System;
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
    /// <summary>Her hair's highlights' colour ("#rrggbb"), or none.</summary>
    public string? HairHighlight;
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
    /// <summary>The pieces her equipment wears (Rpg.Wear.Of: visual slot -> piece id), or none: her calling's outfit whole.</summary>
    public Dictionary<string, string>? Worn;
    /// <summary>Visual slots left empty on her ("head": her show-helm toggle off).</summary>
    public List<string>? HideSlots;
    /// <summary>Dyes on the pieces she wears: piece id -> dye zone -> "#rrggbb" (Rpg.Wear.DyeOf).</summary>
    public Dictionary<string, Dictionary<string, string>>? WornDye;
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
    /// <summary>npcs.json "talkIdle": the stand a working idle gives way to while they talk or the survivor is close
    /// (NPC 18: the smith's hammering showed his back and raised arm as a talk opened), or null to keep their own.</summary>
    public string? TalkIdle;
    /// <summary>The stand they talk in: TalkIdle, else the plain Idle for a hammering idle (the old rule), else null (their own).</summary>
    public string? Stand => TalkIdle is { Length: > 0 } t ? (t == Idle ? null : t) : Idle == "1H_Melee_Attack_Chop" ? "Idle" : null;
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
    /// <summary>A hair colour's highlights when they are turned on and none is picked (looks.json's hairHighlights' id).</summary>
    public string Highlight = "";
    /// <summary>A highlight's share of the locks and its strength, against the others' (looks.json's hairHighlights:
    /// face 40, platinum 2 and honey 3).</summary>
    public float Share = 1f, Strength = 1f;
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
    /// <summary>(its sheen's strength and how much of her skin's light under it shows through, heroine_skin's paint_shine
    /// and paint_scatter; 0.5 each if not given: face 32, ash matte and dry, the gilt's leaf not lit from under)</summary>
    public double Shine = 0.5, Scatter = 0.5;
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
    /// <summary>How freckled the face starts (0 none to 1 heavy), from its portrait.</summary>
    public double Freckles;
    /// <summary>How far its upper lids rest down over its eyes (0 open to 1 shut), from its portrait: wide open, the
    /// whole iris showed with white above it, and every face stared.</summary>
    public double Lid;
    /// <summary>Its pupil (of the iris's radius; 0: 0.28) and how light its eyes' whites stand (0: as hers, 1),
    /// from its portrait: under one light, one white outshone a darker cheek.</summary>
    public double Pupil, Whites;
    /// <summary>Its iris's radius (of the eye's paint; 0: 0.117) and how much of the iris its upper lid covers at
    /// rest (0 to 1, its portrait's), where the lid's shadow on the eye is laid.</summary>
    public double Iris, Cover;
    /// <summary>How much fuller its lower lip is than its sculpt's (the lips_lower slider's key, added under the
    /// player's slider): the owner's lips B3-15 (14 October 2026), about 15% fuller, lower:upper about 1.5
    /// (tools/assets/heroine_lip_raise.py's LIPS_LOWER).</summary>
    public double Lips;
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
        public Dictionary<string, string>? Packages;
        public List<FolkLine> Lines = new();
    }

    sealed class LooksFile
    {
        public List<LookChoice> Cloaks = new(), Skins = new(), Hairs = new(), HairHighlights = new();
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
    static NpcFile N => npcs ??= LoadNpcs();
    static NpcFile LoadNpcs()
    {
        var f = Json.Parse<NpcFile>(Json.ReadContent("npcs.json"));
        // --folk-kit: the named people keep the kit bodies too.
        if (kitFolk)
            foreach (var d in f.Npcs.Values.Concat(f.Outsiders.Values))
                if (d.Person?.Body is { } b && b.StartsWith("npc:")) d.Person.Body = null;
        return f;
    }
    static bool kitFolk;
    /// <summary>--folk-kit (set once at game start by the game): today's kit people everywhere, for A/B.</summary>
    public static bool KitFolk { get => kitFolk; set { if (kitFolk != value) { kitFolk = value; npcs = null; } } }
    /// <summary>Marionette packages for the town's people ("man", "woman", "watch"), or null.</summary>
    public static Dictionary<string, string>? FolkPackages => F.Packages;
    /// <summary>The town's people are built from packages (and there are no children).</summary>
    public static bool PackageFolk => FolkPackages != null && !kitFolk;
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
    /// <summary>The colours her hair's highlights may take (a second colour on some of her locks: the owner, 22 Oct).</summary>
    public static List<LookChoice> HairHighlights => L.HairHighlights;
    /// <summary>The id a highlight choice of "auto" stands for (CharacterData.HairHighlight).</summary>
    public const string HighlightAuto = "auto";

    /// <summary>A hair colour's own highlights (an id of HairHighlights): its looks.json default, or, for a colour
    /// not among the hairs (a "#rrggbb", "" as it grew), by how light it is: copper on the dark, honey on the
    /// middling, platinum on the fair.</summary>
    public static string DefaultHighlight(string? hair)
    {
        var h = Hairs.FirstOrDefault(x => x.Id == hair || x.Color != "" && string.Equals(x.Color, hair, StringComparison.OrdinalIgnoreCase));
        if (h is { Highlight: not "" }) return h.Highlight;
        var hex = h?.Color is { Length: > 0 } c ? c : hair;
        if (hex is not { Length: 7 } || hex[0] != '#') return "honey";
        double Ch(int i) => Convert.ToInt32(hex.Substring(i, 2), 16) / 255.0;
        double lum = 0.2126 * Ch(1) + 0.7152 * Ch(3) + 0.0722 * Ch(5);
        return lum < 0.2 ? "copper" : lum < 0.5 ? "honey" : "platinum";
    }

    /// <summary>Whether character creation offers highlights and her hair shows them (face 40, 22 Oct): PARKED, off.
    /// The highlights failed their judge (j1: tiger stripes, crown crumbs, a half-head panel) and wait for a rebuild;
    /// until then the Look hides the row and a saved look's highlight loads but renders off (ShownHighlight). Set
    /// true to bring them back. (--hair-highlight still forces them on in pictures: ForceHighlights.)</summary>
    public const bool ShowHighlights = false;
    /// <summary>Highlights shown even while parked (the shot switch --hair-highlight, and tests).</summary>
    public static bool ForceHighlights;
    /// <summary>The highlight her hair renders with: HighlightColor while highlights are shown (ShowHighlights or
    /// ForceHighlights), else none.</summary>
    public static string? ShownHighlight(string? hair, string? choice) =>
        ShowHighlights || ForceHighlights ? HighlightColor(hair, choice) : null;

    /// <summary>Her hair's highlights' colour ("#rrggbb"), or null for none: a choice null or "" is off, "auto" (or
    /// "default") the hair's own (DefaultHighlight), else a HairHighlights id or a "#rrggbb" of its own.</summary>
    public static string? HighlightColor(string? hair, string? choice)
    {
        if (string.IsNullOrEmpty(choice) || choice == "off") return null;
        if (choice[0] == '#') return choice;
        var id = choice is HighlightAuto or "default" ? DefaultHighlight(hair) : choice;
        return HairHighlights.FirstOrDefault(x => x.Id == id)?.Color is { Length: > 0 } c ? c : null;
    }
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

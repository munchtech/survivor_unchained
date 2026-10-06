"""The scars pay fire, deeper the longer one stays (design 20.5): a shard a minute past thirty minutes beyond the
win, and once the stream is cured, scar-glass past the hour: the slurry's gamble earned by staying."""
from ed import sub
C = "logic/Rpg/Crafting.cs"
sub(C, [
    ("""    public int EmberFrom = 10, EmberPer = 8, MinutesPer = 2, StoryBonus = 2, Cap = 8, Miniboss = 2;""",
     """    public int EmberFrom = 10, EmberPer = 8, MinutesPer = 2, StoryBonus = 2, Cap = 8, Miniboss = 2;
    /// <summary>The scars' depth (design 20.5): past this many minutes beyond the win, a shard a minute; past
    /// GlassFrom, once the stream is cured, scar-glass, one and another each GlassEvery minutes more.</summary>
    public int DeepFrom = 30, GlassFrom = 60, GlassEvery = 60;
    public string Glass = "scar_glass";"""),
    ("""        IReadOnlyDictionary<Family, int> champions, IReadOnlyDictionary<Family, int>? minibosses = null)
    {
        var r = Rules.Night;
        var all = new Dictionary<string, int>();
        void Add(string m, int n) { if (n > 0) all[m] = all.GetValueOrDefault(m) + n; }
        Add(Shard, Math.Max(0, ember - r.EmberFrom) / Math.Max(1, r.EmberPer) + Math.Max(0, tier - 1)
            + (won ? (int)Math.Floor(Math.Max(0, minutesPast) / Math.Max(1, r.MinutesPer)) : 0) + (won && story ? r.StoryBonus : 0));""",
     """        IReadOnlyDictionary<Family, int> champions, IReadOnlyDictionary<Family, int>? minibosses = null, bool cured = false)
    {
        var r = Rules.Night;
        var all = new Dictionary<string, int>();
        void Add(string m, int n) { if (n > 0) all[m] = all.GetValueOrDefault(m) + n; }
        // Past the win the scar keeps paying: a shard every two minutes, then from its deep a shard a minute.
        double past = Math.Max(0, minutesPast);
        int deep = won ? (int)Math.Floor(Math.Min(past, r.DeepFrom) / Math.Max(1, r.MinutesPer)) + (int)Math.Floor(Math.Max(0, past - r.DeepFrom)) : 0;
        Add(Shard, Math.Max(0, ember - r.EmberFrom) / Math.Max(1, r.EmberPer) + Math.Max(0, tier - 1) + deep + (won && story ? r.StoryBonus : 0));
        // The slurry's heir: with the stream cured the jars are gone, but a scar stayed in past the hour
        // gives glass with the same gamble in it (earned by staying, not bought).
        if (won && cured && past >= r.GlassFrom) Add(r.Glass, 1 + (int)((past - r.GlassFrom) / Math.Max(1, r.GlassEvery)));"""),
    # Steeping takes a jar, or scar-glass where there is no jar.
    ("""        var q = Begin(Verb.Steep, crafter, "Steep in slurry");
        q.Takes[s.Jar] = 1;""",
     """        var q = Begin(Verb.Steep, crafter, "Steep in slurry");
        q.Takes[SteepWith(x.Ch)] = 1;"""),
    ("""        else if (Inventory.Count(x.Ch, s.Jar) < 1) q.Blocked = "You have no slurry.";""",
     """        else if (Inventory.Count(x.Ch, SteepWith(x.Ch)) < 1) q.Blocked = "You have no slurry.";"""),
    ("""            if (Inventory.Count(ch, Rules.Slurry.Jar) < 1 || Slurried(it) || q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;
            Inventory.Take(ch, Rules.Slurry.Jar, 1);""",
     """            string with = q.Takes.Keys.FirstOrDefault() ?? Rules.Slurry.Jar;
            if (Inventory.Count(ch, with) < 1 || Slurried(it) || q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;
            Inventory.Take(ch, with, 1);"""),
    ("""    public static bool Slurried(ItemInstance it) => it.Marks?.Contains(Rules.Slurry.Mark) == true;""",
     """    public static bool Slurried(ItemInstance it) => it.Marks?.Contains(Rules.Slurry.Mark) == true;

    /// <summary>What a steeping is done with: a jar of Snib's while one is carried, else the scars' glass.</summary>
    public static string SteepWith(CharacterData ch) =>
        Inventory.Count(ch, Rules.Slurry.Jar) > 0 || Inventory.Count(ch, Rules.Night.Glass) == 0 ? Rules.Slurry.Jar : Rules.Night.Glass;

    /// <summary>Something carried to steep with by hand (a jar, or scar-glass).</summary>
    public static bool CanSteep(CharacterData ch) => Inventory.Count(ch, Rules.Slurry.Jar) + Inventory.Count(ch, Rules.Night.Glass) > 0;"""),
])
sub("logic/Arena/Arena.cs", [
    ("""Math.Max(0, b.Time / 60 - spec.Minutes), won, fell, b.ChampionsByFamily, b.MinibossesByFamily);""",
     """Math.Max(0, b.Time / 60 - spec.Minutes), won, fell, b.ChampionsByFamily, b.MinibossesByFamily,
            cured: j.World.Fact("stream.clear").Truthy || j.World.Fact("beasts.outcome").Str == "cured");"""),
])
sub("src/Ui/Pack.cs", [
    ("""            if (!G.Journey.InArena && Inventory.Count(Ch, Crafting.Rules.Slurry.Jar) > 0 && Crafting.Steep(G.Journey.Craft, it) is { Ok: true })""",
     """            if (!G.Journey.InArena && Crafting.CanSteep(Ch) && Crafting.Steep(G.Journey.Craft, it) is { Ok: true })"""),
    ("""        if (G.Journey.InArena || Controls.Instance.UsingPad || Inventory.Count(Ch, Crafting.Rules.Slurry.Jar) == 0 || !Crafting.Steep(G.Journey.Craft, it).Ok) return;""",
     """        if (G.Journey.InArena || Controls.Instance.UsingPad || !Crafting.CanSteep(Ch) || !Crafting.Steep(G.Journey.Craft, it).Ok) return;"""),
])
sub("data/content/items.json", [
    ("""  "mark_hunt_bone": {""",
     """  "scar_glass": {
   "id": "scar_glass",
   "name": "Scar-Glass",
   "plural": "pieces of scar-glass",
   "kind": "material",
   "rarity": 3,
   "icon": "scar_glass",
   "value": 60,
   "stack": 10,
   "description": "What a deep scar leaves for one who stays past the hour, once the stream runs clean. Steep a piece in it, from the pack: a grade past what the forge can do, or something strong with a price, or only the veins, or a grade lost. It sets the piece for good."
  },
  "mark_hunt_bone": {"""),
])

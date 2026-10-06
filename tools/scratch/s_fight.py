PAIRS = [
('''    /// <summary>A named foe: a miniboss of its people, on the bar while it lives, carrying a small chest.</summary>
    Enemy? Foe(string def, double x, double z, double hpMul = 1, string? kicker = null);''',
'''    /// <summary>A named foe: a miniboss of its people, on the bar while it lives, carrying a small chest.
    /// `kicker`: over its name (the fight's own by default); `quiet`: not announced (a picket, one of three).</summary>
    Enemy? Foe(string def, double x, double z, double hpMul = 1, string? kicker = null, bool quiet = false);'''),
('''    /// <summary>The world told what happened (the story's effects, as a dialogue's are).</summary>
    void Apply(string effectsJson);''',
'''    /// <summary>The world told what happened (the story's effects, as a dialogue's are).</summary>
    void Apply(string effectsJson);
    /// <summary>A condition on the world, as dialogue tests it (a flag on someone, a thing she knows).</summary>
    bool Test(SurvivorUnchained.World.Cond cond);
    /// <summary>She knows it (a clue, a name).</summary>
    bool Knows(string key);
    /// <summary>Something that happened tonight, in this fight (the crates fired): marked, and asked after.</summary>
    void Mark(string key);
    bool Marked(string key);
    /// <summary>Done this many seconds on (a cart dragged, a cage closing).</summary>
    void After(double seconds, Action act);'''),
('''    /// <summary>The pull, and the sight after each stage (docs/WRITING_PASS.md §21).</summary>
    public abstract string Pull { get; }
    public abstract string[] Between { get; }''',
'''    /// <summary>The pull, and the sight after each stage (docs/WRITING_PASS.md §21, §23).</summary>
    public abstract string Pull { get; }
    public abstract string[] Between { get; }
    /// <summary>The sight after a stage, where it reads the world (who is in the cages); by default, Between's.</summary>
    public virtual string? BetweenSight(IStoryArena a, int stage) => stage < Between.Length ? Between[stage] : null;
    /// <summary>The words over its named foes' names (its people).</summary>
    public virtual string Kicker => "";'''),
('''        "hollow_by_night" => new HollowByNight(),''', '''        "hollow_by_night" => new HollowByNight(),
        "roost_raid" => new RaidOnTheRoost(),'''),
]

PAIRS = [
('''    static readonly string[] CageLines =''', '''    /// <summary>What each teamster does as his cage opens: by day here, or in a raid on the Roost by night.</summary>
    public static readonly string[] CageLines ='''),
('''        if (Enumerable.Range(0, cageNodes.Length).All(CageOpen))
            G.Apply($$"""
                [
                  { "set": { "caravan.survivors": "rescued" } }, { "quest": { "id": "caravan", "entry": "survivors_freed" } }, {{CaravanSettle}},
                  {{Hist("freed_teamsters", "freed the Coyle teamsters from the Kerchief cages", ["rescue", "caravan"], 2, """{ "affection": 10 }""", """{ "harlan": { "affection": 40, "trust": 30 }, "holloway": { "respect": 15 } }""")}}
                ]
                """);
    }''', '''        if (Enumerable.Range(0, cageNodes.Length).All(CageOpen)) G.Apply(TeamstersFreed);
    }

    /// <summary>The teamsters out of the Kerchief cages, every one: the world's own effects, whether she
    /// opened the cages by day or broke their locks in a raid by night (the Roost's cage yard). The cages
    /// stand open after, as by day.</summary>
    public static string TeamstersFreed => $$"""
        [
          { "zone": { "id": "verge", "key": "cage0", "value": true } }, { "zone": { "id": "verge", "key": "cage1", "value": true } }, { "zone": { "id": "verge", "key": "cage2", "value": true } },
          { "set": { "caravan.survivors": "rescued" } }, { "quest": { "id": "caravan", "entry": "survivors_freed" } }, {{CaravanSettle}},
          {{Hist("freed_teamsters", "freed the Coyle teamsters from the Kerchief cages", ["rescue", "caravan"], 2, """{ "affection": 10 }""", """{ "harlan": { "affection": 40, "trust": 30 }, "holloway": { "respect": 15 } }""")}}
        ]
        """;'''),
]

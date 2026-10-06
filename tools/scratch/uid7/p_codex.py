PAIRS = [
("x.Findable && x.Evolutions.Count > 0", "x.Findable && x.Evolutions.Length > 0"),
("int all = arts.Sum(x => x.Evolutions.Count) + Unions.All.Length;", "int all = arts.Sum(x => x.Evolutions.Length) + Unions.All.Length;"),
("string Way(Rpg.EvolutionDef e)", "string Way(Evolution e)"),
]

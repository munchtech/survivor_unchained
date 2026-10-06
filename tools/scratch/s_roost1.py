PAIRS = [
('''            A.Apply("""[{ "set": { "be.crates": "burned", "roost.crates_fired_tonight": true } }]""");''',
'''            A.Apply("""[{ "set": { "be.crates": "burned" } }]""");
            A.Mark("crates");'''),
('''        _ => a.Fact("roost.crates_fired_tonight")''', '''        _ => a.Marked("crates")'''),
]

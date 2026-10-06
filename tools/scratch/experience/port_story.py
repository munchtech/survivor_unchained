"""Port the story lead's spare outcomes and lost lines into StoryFights.Spec (run from godot/)."""
p = "logic/Play/StoryFights.cs"
s = open(p, encoding="utf-8").read()

start = s.index('            case "hollow":')
end = s.index('            case "dig":')
new = '''            case "hollow":
            {
                // Greymuzzle let go (docs/STORY_BIBLE.md, "The nights"), narrowly: only if she knelt
                // and promised and the stream already runs clean. Then it is her choice at his side
                // (the owner, 4 October): let go, he gets up and goes to his sick, beasts.outcome
                // stands, and Maeca hears of it, the one fight that raises her regard; finished, the
                // promise she knelt to make is broken with him. Otherwise he dies.
                bool spare = F(c, "promise.pack").Truthy && !F(c, "promise.broken").Truthy && StreamClean(c);
                string killed = $$"""{ "set": { "greymuzzle": "dead", "hollow.hostile": true } }, { "add": { "beasts.population": -30 } }, { "quest": { "id": "beasts", "entry": "alpha_dead" } }, { "give": "greymuzzle_fang" }, {{ZoneRuntime.Hist("killed_greymuzzle", "killed Greymuzzle, the Pack's old dog-wolf, in his own Hollow by night", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": -50, "respect": -20 }, "holloway": { "respect": 20 } }""")}}""";
                string broken = spare ? $$""", { "set": { "promise.broken": true } }, {{ZoneRuntime.Hist("broke_promise", "knelt to Greymuzzle and promised him a cure, and finished him on his own den floor", ["beasts", "wolves", "betrayal"], 2, null, """{ "maeca": { "trust": -30, "affection": -20 } }""")}}""" : "";
                var spec = Night("hollow_by_night", "The Hollow by Night", "pack", 311, "boss_pack", "Greymuzzle", "Who Kept the Cold Off",
                    $"[{killed}{broken}]",
                    """[{ "add": { "beasts.population": 10 } }, { "set": { "hollow.hostile": true } }, { "quest": { "id": "beasts", "entry": "hollow_lost" } }]""",
                    "The Hollow is quiet. The only breath in it is yours, and it does not show in the cold.",
                    "The last thing you know is the stream, very loud, and the Pack standing round you in a ring. None of them comes in.");
                if (spare)
                {
                    spec.OnSpare = $$"""[{ "set": { "greymuzzle": "spared" } }, {{ZoneRuntime.Hist("spared_greymuzzle", "brought Greymuzzle down in his own Hollow by night, and let him get up and go to his sick", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": 15, "respect": 20 } }""")}}]""";
                    spec.EndSpared = "Behind you, in the den's mouth, an old wolf is breathing. You leave him to it.";
                    spec.SpareVerb = "Let him go";
                }
                spec.Spare = spare;
                return spec;
            }
            case "roost":
            {
                // The Missing Caravan, by force. At his knee it is her choice (the owner, 4 October):
                // finished, his last words (C11) and the red hat in the mud; spared, he owes her,
                // strikes the camp before first light and takes his people off the Old Road (Act 2
                // brings him back), and the Coyle cargo is left in the empty Roost. The six crates go
                // with him only if he swore to keep them (be.crates = redcowl).
                var spec = Night("roost_raid", "Raid on the Roost", "kerchiefs", 523, "boss_kerchiefs", "Redcowl", "Of the Kerchiefs",
                    $$"""[{ "set": { "redcowl": "dead", "roost.cleared": true, "roost.hostile": true } }, { "quest": { "id": "caravan", "entry": "roost_raided" } }, { "if": { "fact": "redcowl.ashford_said", "eq": true }, "then": [{ "set": { "redcowl.last_words": "ashford" } }], "else": [{ "set": { "redcowl.last_words": "leg" } }] }, {{PackLed}}, {{ZoneRuntime.Hist("killed_redcowl", "took Redcowl's Roost by night and killed him in it", ["kerchief", "caravan"], 2, """{ "fear": 10 }""", """{ "holloway": { "respect": 25 }, "rav": { "affection": -20 } }""")}}]""",
                    """[{ "set": { "roost.hostile": true } }, { "quest": { "id": "caravan", "entry": "roost_repelled" } }]""",
                    "The red hat lies in the mud. By the fires, someone is telling the children to hush, and they do.",
                    "The last thing you know is the fire going small, and a big hand closing your eyes for you.");
                spec.OnSpare = $$"""[{ "set": { "redcowl": "spared", "roost.cleared": true } }, { "quest": { "id": "caravan", "entry": "roost_spared" } }, {{PackLed}}, {{ZoneRuntime.Hist("spared_redcowl", "brought Redcowl to his knee in his own camp by night, and let him get up", ["kerchief", "caravan"], 2, """{ "respect": 15 }""", """{ "rav": { "affection": 20, "trust": 10 }, "maeca": { "respect": 10 }, "holloway": { "respect": 10 } }""")}}]""";
                spec.EndSpared = "He walks back through his people, and does not limp until he is past the fires. Behind the carts, someone is waking the children and telling them to hush.";
                spec.SpareVerb = "Spare him";
                return spec;
            }
'''
s = s[:start] + new + s[end:]
for old, newl in [
    ('"When you come to, they have gone back down the hole, and taken their own dead with them."',
     '"The last thing you know is little hands, a great many of them, lifting you."'),
    ('"The dead carry you back up the stair and put you out, the way you would put out a cat."',
     '"The last thing you know is the stair going by beneath you, and the dead carrying you up it, in step."'),
]:
    assert old in s, old
    s = s.replace(old, newl, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")

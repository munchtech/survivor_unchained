from ed import sub
sub('logic/Rpg/Crafting.cs', [
('public Dictionary<string, int> Odds = new() { ["up"] = 25, ["slurry"] = 25, ["nothing"] = 30, ["down"] = 20 };',
 'public Dictionary<string, int> Odds = new() { ["up"] = 25, ["affix"] = 25, ["nothing"] = 30, ["down"] = 20 };'),
('if (pick is "up" or "down" && plain.Count == 0) pick = pick == "up" ? "slurry" : "nothing";',
 'if (pick is "up" or "down" && plain.Count == 0) pick = pick == "up" ? "affix" : "nothing";'),
('            case "slurry":\n            {\n                var pool = s.Affixes', '            case "affix":\n            {\n                var pool = s.Affixes'),
('if (a?.Kindled != null) { q.Blocked = Line(crafter, "bind.coal") ?? "That one is caged. It will not come out."; return q; }',
 'if (a?.Kindled != null) { q.Blocked = Line(crafter, "bind.caged") ?? "That one is caged. It will not come out."; return q; }'),
('    /// <summary>What a gamble came to, once done ("up", "slurry", "nothing", "down").</summary>',
 '    /// <summary>What a gamble came to, once done ("up", "affix", "nothing", "down").</summary>'),
])

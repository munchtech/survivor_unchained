PAIRS = [
('''    bool Act2 = false, string Choice = "spare", double Cap = 25)
{
    public string Key => $"{Fight}/{Calling}/{Policy}/t{Tier}/s{Seed}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") + (Act2 ? "/act2" : "") + $"/{Choice}";''',
'''    bool Act2 = false, string Choice = "spare", double Cap = 25, bool Crates = false)
{
    public string Key => $"{Fight}/{Calling}/{Policy}/t{Tier}/s{Seed}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") + (Act2 ? "/act2" : "") + $"/{Choice}" + (Crates ? "/crates" : "");'''),
('''            // Her choice at his side, by the run's own.
            var offer = zone.Interactables.FirstOrDefault(i => i.Id == (spec.Choice == "finish" ? "story:finish" : "story:let_go"))
                ?? zone.Interactables.FirstOrDefault(i => i.Id.StartsWith("story:"));
            offer?.Act();''',
'''            // Her choice at his side, by the run's own; and the crates, fired or left, by the run's own.
            var offer = zone.Interactables.FirstOrDefault(i => i.Id == (spec.Choice == "finish" ? "story:finish" : "story:let_go"))
                ?? zone.Interactables.FirstOrDefault(i => i.Id is "story:let_go" or "story:finish");
            offer?.Act();
            if (spec.Crates && zone.Interactables.FirstOrDefault(i => i.Id == "story:crates") is { } crates
                && Math.Abs(crates.X - b.Player.X) + Math.Abs(crates.Z - b.Player.Z) < 6) crates.Act();'''),
]

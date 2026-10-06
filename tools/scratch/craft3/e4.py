"""Marks: done at Vonnra's table, never tempered, made with their Mark, in data."""
from ed import sub
C = "logic/Rpg/Crafting.cs"
sub(C, [
    ("""        if (q.Verb == Verb.Bind && (q.Donor == null || Inventory.Find(ch, q.Donor) is not { InPack: true })) return false;""",
     """        if (q.Verb is Verb.Bind or Verb.Mark && (q.Donor == null || Inventory.Find(ch, q.Donor) is not { InPack: true })) return false;"""),
    ("""            case Verb.Set:
            {
                var s = Rules.Settings[q.Def!];""",
     """            case Verb.Mark:
            {
                var roll = new AffixRoll { Id = q.Affix!, Tier = q.Grade };
                if (q.Index >= 0) it.Affixes[q.Index] = roll; else it.Affixes.Add(roll);
                // The ruler's thing is used up: what it held is written into the piece.
                ch.Pack[Inventory.Find(ch, q.Donor!)!.Index] = null;
                (it.History ??= new()).Add(History(x, q.Crafter, "mark", "Marked by {who}, day {day}"));
                break;
            }
            case Verb.Set:
            {
                var s = Rules.Settings[q.Def!];"""),
    ("""        if (def?.Kindled != null || def?.Grants != null) { q.Blocked = "A coal or a worn skill has no grades."; return q; }""",
     """        if (def?.Kindled != null || def?.Grants != null) { q.Blocked = "A coal or a worn skill has no grades."; return q; }
        if (def?.Mark == true) { q.Blocked = "A mark is as fine as what it came from. A finer one comes from a harder map."; return q; }"""),
])
sub("logic/Rpg/Character.cs", [
    ("""        if (Crafting.Workable(def)) it.Heat = it.HeatFull = Crafting.HeatAtMaking(it.Rarity, dropped ? new Rng(seed ?? (uint)loose.Next(1_000_000_000)) : null);""",
     """        if (Crafting.Workable(def)) it.Heat = it.HeatFull = Crafting.HeatAtMaking(it.Rarity, dropped ? new Rng(seed ?? (uint)loose.Next(1_000_000_000)) : null);
        // A ruler's thing carries its Mark at the grade it fell at (its rarity, I to VI).
        if (affixes == null && Crafting.MarkOf(defId) is { } mark) it.Affixes.Add(new AffixRoll { Id = mark, Tier = Math.Clamp(it.Rarity, 0, 5) });"""),
])
J = "data/content/crafting.json"
sub(J, [
    (""" "bind": { "shardsPerGrade": 1, "goldPerGrade": 40, "heat": [5, 7], "crafter": "vonnra" },""",
     """ "bind": { "shardsPerGrade": 1, "goldPerGrade": 40, "heat": [5, 7], "crafter": "vonnra" },
 "_mark": "Marks (design 20.3): a map's ruler leaves its people's thing with its Mark, at a grade every three tiers (sometimes one finer); Vonnra inscribes it in a seam. Worn three at once, in the maps only.",
 "mark": { "crafter": "vonnra", "gold": 60, "goldPerGrade": 30, "shards": 2, "heat": [5, 7], "worn": 3, "chance": 0.5, "finer": 0.3, "tiersPerGrade": 3,
  "drops": { "pack": { "item": "mark_hunt_bone", "mark": "of_the_ravine" }, "lamplings": { "item": "mark_lamp_glass", "mark": "of_the_falling_star" },
   "dead": { "item": "mark_gate_nail", "mark": "of_the_open_gate" }, "kerchiefs": { "item": "mark_red_cord", "mark": "of_the_gyre" } } },"""),
    ("""   "verbs": ["bind"],""", """   "verbs": ["bind", "mark"],"""),
])

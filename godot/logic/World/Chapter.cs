using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.World;

/* The end of the chapter, read back from the world.
 *
 * Nothing here is stored: every line is worked out from the facts, the
 * journal, the people and the history, so two survivors who took different
 * roads close the same chapter on two different pages. */

public enum ThreadTone { Good, Grey, Bad, Open }
public sealed record Thread(string Id, string Name, string Verdict, ThreadTone Tone, string Outcome, List<string> Beats);
public sealed record Remembered(string Id, string Name, string Role, string Regard, string? Knows, double Warmth);
public sealed record OpenThread(string Id, string Name, string Line);
public sealed record ChapterSummary(string Epithet, List<Thread> Threads, List<OpenThread> Open, List<Remembered> People, List<string> Deeds, List<(string Label, string Value)> Stats);

public static class Chapter
{
    static List<string> Pick(WorldState w, string quest, string[] ids)
    {
        var q = Lore.Quests[quest];
        return (w.Quests.TryGetValue(quest, out var s) ? s.Entries : new())
            .Where(ids.Contains).Select(e => q.Entries.TryGetValue(e, out var t) ? t : "").Where(t => t != "").ToList();
    }

    static string? S(WorldState w, string k) => w.Fact(k).Str;

    static Thread Beasts(WorldState w)
    {
        var q = Lore.Quests["beasts"];
        var o = S(w, "beasts.outcome");
        var (verdict, tone) = o switch
        {
            null => ("Not yet settled", ThreadTone.Open),
            "cured" => ("Cured at the source", ThreadTone.Good),
            "allied" => ("Ran with the Pack", ThreadTone.Grey),
            "slaughtered" => (S(w, "greymuzzle") == "dead" ? "Put down, Greymuzzle and all" : "Put down", ThreadTone.Grey),
            "ignored" => ("Left to fester", ThreadTone.Bad),
            "exploited" => ("Settled, for a price", ThreadTone.Grey),
            _ => ("Settled", ThreadTone.Grey),
        };
        string outcome = o != null && q.Outcomes != null && q.Outcomes.TryGetValue(o, out var t) && t != "" ? t : "The wolves are still out there, and still sick.";
        return new Thread("beasts", q.Name, verdict, tone, outcome,
            Pick(w, "beasts", ["greymuzzle_met", "root_cause", "dig_sold", "pump_moved", "pump_broken", "pump_blown", "redcowl_charge", "alpha_dead", "bounty_claimed", "told_holloway", "pelts_sold", "pack_led"]));
    }

    static Thread Caravan(WorldState w)
    {
        var q = Lore.Quests["caravan"];
        string Out(string k) => q.Outcomes![k];
        var surv = S(w, "caravan.survivors");
        var cargo = S(w, "caravan.cargo");
        string verdict = "Not yet found", outcome = "Jory and the others are still somewhere in the Verge. The clock is running.";
        var tone = ThreadTone.Open;
        if (surv == "rescued" && cargo == "returned") { verdict = "Brought home"; tone = ThreadTone.Good; outcome = Out("returned"); }
        else if (surv == "rescued" && cargo is "sold" or "kept") { verdict = "Rescued, and robbed"; tone = ThreadTone.Grey; outcome = Out("kept"); }
        else if (surv == "rescued" && cargo == "with_kerchiefs") { verdict = "The teamsters freed"; tone = ThreadTone.Good; outcome = $"Jory is home. {Out("with_kerchiefs")}"; }
        else if (surv == "rescued" && cargo == "lost") { verdict = "The teamsters freed"; tone = ThreadTone.Good; outcome = "Jory is home. The cargo burned with the Roost."; }
        else if (surv == "rescued") { verdict = "The teamsters freed"; tone = ThreadTone.Good; outcome = "Jory is home. The cargo is another story."; }
        else if (surv == "dead" && cargo == "returned") { verdict = "The goods, not the men"; tone = ThreadTone.Grey; outcome = "Harlan has his strongbox back. He would give it all to have Jory."; }
        else if (surv == "dead" && cargo is "sold" or "kept") { verdict = "Too late, and robbed"; tone = ThreadTone.Bad; outcome = "The prisoners did not come home, and the cargo went where you took it."; }
        else if (surv == "dead") { verdict = "Too late"; tone = ThreadTone.Bad; outcome = "The prisoners in the Roost did not come home."; }
        else if (cargo == "returned") { verdict = "The goods, not the men"; tone = ThreadTone.Grey; outcome = Out("returned"); }
        var beats = Pick(w, "caravan", ["roost_found", "roost_told", "redcowl_met", "survivors_freed", "survivors_dead", "cargo_returned", "cargo_sold", "cargo_kept", "cargo_lost", "cargo_moved",
            "crates_redcowl", "crates_harlan", "crates_sunk", "jory_told", "pell_exposed", "pell_joined", "pell_given", "pell_hunted"]);
        if (S(w, "redcowl") == "tricked") beats.Add("You bluffed the Kerchiefs out of their own camp.");
        if (S(w, "redcowl") == "dead") beats.Add("Redcowl is dead.");
        if (S(w, "redcowl") == "spared") beats.Add("You had Redcowl on his knee, and let him get up. He took his people off the Old Road.");
        // Taken from his bed is not fled: the journal's own line says where Redcowl looked.
        if (S(w, "caravan.pell") == "fled" && S(w, "pell.fate") != "taken") beats.Add("Pell Varrow fled the Waystation in the night.");
        return new Thread("caravan", q.Name, verdict, tone, outcome, beats);
    }

    static string Epithet(CharacterData ch, WorldState w)
    {
        string? f(string k) => S(w, k);
        if (f("beasts.outcome") == "allied") return $"{ch.Name}, who runs with wolves";
        if (w.Fact("vonnra.accused").Truthy) return $"{ch.Name}, who said it to Vonnra's face";
        if (f("caravan.pell") == "ally") return $"{ch.Name}, in Pell Varrow's ledger";
        if (f("beasts.outcome") == "exploited") return $"{ch.Name}, who sold the cure";
        if (f("caravan.cargo") == "sold") return $"{ch.Name}, who sold the Coyle strongbox";
        if (f("caravan.cargo") == "kept") return $"{ch.Name}, who kept the Coyle strongbox";
        if (f("beasts.outcome") == "cured" && f("caravan.survivors") == "rescued") return $"{ch.Name}, who cleared the water and opened the cages";
        if (f("beasts.outcome") == "cured") return $"{ch.Name}, who cleared the water";
        if (f("caravan.survivors") == "rescued") return $"{ch.Name}, who opened the cages";
        if (f("beasts.outcome") == "slaughtered") return $"{ch.Name}, the wolf-killer";
        if (ch.Traits.Contains("risen_once")) return $"{ch.Name}, who would not stay dead";
        return $"{ch.Name}, late of the Low Ford road";
    }

    public static ChapterSummary Summary(CharacterData ch, WorldState w)
    {
        // The lamps are a thread only once the dead watchman's book (or
        // someone's word) has opened them: a save from before may not have it.
        bool Begun(string id) => id != "lamps" || (w.Quests.TryGetValue(id, out var q) && q.Status != QuestStatus.Unknown);
        var open = new[] { "vault", "below", "lamps" }.Where(Begun).Select(id =>
        {
            var def = Lore.Quests[id];
            string? last = w.Quests.TryGetValue(id, out var q) && q.Entries.Count > 0 ? q.Entries[^1] : null;
            return new OpenThread(id, def.Name, last != null && def.Entries.TryGetValue(last, out var t) ? t : def.Summary);
        }).ToList();
        var people = Lore.Npcs.Values
            .Select(d => (d, s: w.Npcs.TryGetValue(d.Id, out var s) ? s : null))
            .Where(x => x.s != null && x.s.Flag("met").Truthy)
            .Select(x =>
            {
                var s = x.s!;
                double weight = Math.Abs(s.Trust) + Math.Abs(s.Affection) + Math.Abs(s.Respect) + Math.Abs(s.Fear);
                var latest = Enumerable.Reverse(s.Memories).Select(m => w.History.Find(h => h.Id == m)).FirstOrDefault(h => h != null && h.Id != "fortune_read");
                return (weight, r: new Remembered(x.d.Id, x.d.Name, s.Alive ? x.d.Role : $"{x.d.Role}, dead", Rules.Attitude(s), latest?.Text, s.Trust + s.Affection));
            })
            .OrderByDescending(x => x.weight).Take(4).Select(x => x.r).ToList();
        var deeds = w.History.Where(h => h.Id != "fortune_read").TakeLast(5).Reverse().Select(h => h.Text).ToList();
        var inv = System.Globalization.CultureInfo.InvariantCulture;
        return new ChapterSummary(Epithet(ch, w), [Beasts(w), Caravan(w)], open, people, deeds,
        [
            ("Days", w.Day.ToString(inv)), ("Level", ch.Level.ToString(inv)), ("Slain", ch.Stats.Kills.ToString(inv)),
            ("Falls", ch.Stats.Deaths.ToString(inv)), ("Gold earned", ch.Stats.GoldEarned.ToString(inv)),
        ]);
    }
}

using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.World;

/* What to do next, for the corner of the screen.
 *
 * The journal says what happened; this says where to go. Each quest's next
 * step is worked out from the same facts the quest is written in, so it
 * follows whichever way the survivor went about it: found the pipe before
 * Wenna asked, freed the cages before hearing of the Roost. Steps name a
 * place and, where it matters, the person. Optional leads come after the
 * main step, and the clocks (the cages do not wait) are said out loud.
 *
 * The Verge, for the directions: the Old Road runs west to east through it;
 * the stream comes down from the Dig in the north-east, turns green at the
 * wood's heart and crosses the road; Wolf Hollow is north, the Roost in the
 * ravine to the south-east. */

public sealed record Step(string Text, bool Optional = false, bool Done = false);
public enum TrackTone { Main, Side, Tutorial }
public sealed record Tracked(string Id, string Title, TrackTone Tone, List<Step> Steps);

public static class Objectives
{
    static readonly string[] TrackedQuests = ["beasts", "caravan"];

    public static List<Tracked> Of(Ctx c)
    {
        var o = new List<Tracked>();
        foreach (var id in TrackedQuests)
        {
            if (!c.World.Quests.TryGetValue(id, out var q)) continue;
            // The caravan can settle at the cages while Harlan still has not
            // heard that Jory is alive: until he has, there is news to carry.
            bool news = id == "caravan" && q.Status == QuestStatus.Resolved && JoryUntold(c);
            if (q.Status != QuestStatus.Active && !news) continue;
            List<Step> steps = news ? [new Step("Tell Harlan Coyle that Jory is alive")] : id == "beasts" ? Beasts(c) : Caravan(c);
            if (steps.Count > 0) o.Add(new Tracked(id, Lore.Quests[id].Name, TrackTone.Main, steps.Take(3).ToList()));
        }
        // Just arrived, and nobody has told you anything yet.
        if (o.Count == 0 && c.World.Fact("prologue.done").Truthy && TrackedQuests.All(id => !c.World.Quests.ContainsKey(id)))
            o.Add(new Tracked("arrival", "The Waystation", TrackTone.Tutorial,
            [
                new("Mother Rook, outside the Last Lamp, hears all the talk"),
                new("Anyone marked ! has something to tell you", Optional: true),
            ]));
        return o;
    }

    sealed class H
    {
        readonly Ctx c;
        readonly string quest;
        public H(Ctx c, string quest) { this.c = c; this.quest = quest; }
        public bool Knows(string k) => Rules.Test(new Cond { Knows = k }, c);
        public bool Has(string item) => Rules.Test(new Cond { HasItem = item }, c);
        public bool Entry(string e) => Rules.Test(new Cond { Quest = new QuestCond { Id = quest, Entry = e } }, c);
        public bool Any(params string[] entries) => entries.Any(Entry);
        public Fact F(string key) => c.World.Fact(key);
    }

    /// <summary>Jory is home and his uncle has not yet been told (nor paid for him).</summary>
    static bool JoryUntold(Ctx c) => c.World.Fact("caravan.survivors").Str == "rescued" &&
        !Rules.Test(new Cond { NpcFlag = new NpcFlagCond { Npc = "harlan", Key = "once:jory", Eq = true } }, c);

    /* What the survivor can know about Pell's ledger (docs/WRITING_PASS.md
     * section 3): that "R." is someone in red, and which night it is about.
     * The tracker only sends them to show the book once it proves something. */
    static bool KnowsKerchiefs(H h) => h.Any("wreck", "ruts", "roost_found", "redcowl_met", "redcowl_wagons", "roost_raided") || h.Knows("hint.roost");
    static bool KnowsTheNight(H h) => h.Any("harlan_plea", "guard_says", "clerk_turned", "wreck", "redcowl_wagons", "ledger_read");

    static List<Step> Beasts(Ctx c)
    {
        var h = new H(c, "beasts");
        var pump = h.F("dig.pump").Str;
        var main = new List<Step>();
        if (pump is "broken" or "moved" or "blown") main.Add(new("The slurry has stopped. Give the stream a few days to run clear"));
        else if (h.Knows("root_cause")) main.Add(new("Stop the slurry at the Dig, up the stream in the north-east of the Verge"));
        else if (h.Knows("clue.analysis")) main.Add(new("Follow the stream up into the north-east of the Verge, to whoever is dumping the slurry"));
        else if (h.Has("stream_sample")) main.Add(new("Take the bottle of green water to Wenna"));
        else if (h.Entry("wenna_request") || h.Knows("clue.green_stream") || h.Knows("clue.pipe") || h.Knows("hint.stream")) main.Add(new("Fill a bottle at the green water in the Verge, and take it to Wenna"));
        else if (h.Knows("clue.sick_wolf")) main.Add(new("The wolves are sick. Ask Old Wenna, the herbalist, what could do that"));
        else main.Add(new("Find out what is wrong with the wolves: ask around town, or look in the Verge"));
        var opt = new List<Step>();
        bool early = !h.Knows("clue.sick_wolf") && !h.Knows("clue.green_stream") && !h.Knows("clue.pipe");
        if (early && !h.Entry("holloway_bounty")) opt.Add(new("Captain Holloway, on the square, is paying for wolves", Optional: true));
        if (early && !h.Entry("maeca_theory")) opt.Add(new("Maeca, the hunter by the east gate, thinks the wolves are running from something", Optional: true));
        if (h.Knows("hint.greymuzzle") && !h.Entry("greymuzzle_met") && h.F("greymuzzle").Str != "dead") opt.Add(new("Greymuzzle, the old alpha, keeps to Wolf Hollow, north of the Old Road", Optional: true));
        if (h.Entry("holloway_bounty") && !h.Entry("bounty_claimed") && !h.F("bounty.stopped").Truthy && (h.Has("wolf_pelt") || h.Has("greymuzzle_fang"))) opt.Add(new("Captain Holloway, on the square, pays for pelts", Optional: true));
        return main.Concat(opt).ToList();
    }

    static List<Step> Caravan(Ctx c)
    {
        var h = new H(c, "caravan");
        var survivors = h.F("caravan.survivors");
        var cargo = h.F("caravan.cargo");
        var main = new List<Step>();
        if (!survivors.Truthy)
        {
            double days = h.F("caravan.days").Number;
            string clock = days >= 3 ? " They will not last another night." : days >= 2 ? " They have a night or two left, no more." : "";
            if (h.Entry("roost_found")) main.Add(new($"Free the prisoners from the cages at Redcowl's Roost.{clock}"));
            else if (h.Entry("ruts") || h.Knows("hint.roost")) main.Add(new($"Find the Kerchief camp in the ravine, south-east in the Verge.{clock}"));
            else if (h.Entry("wreck")) main.Add(new($"Follow the wheel ruts from the wreck, off the road and into the trees.{clock}"));
            else main.Add(new($"Search the Old Road through the Verge for the Coyle wagons.{clock}"));
        }
        else if (JoryUntold(c))
            main.Add(new("Tell Harlan Coyle that Jory is alive"));
        // The box says whose it is wherever it is carried, whatever became of the teamsters.
        if (!cargo.Truthy && h.Has("coyle_strongbox")) main.Add(new("Take the Coyle strongbox to Harlan Coyle, at Coyle Trading in the Waystation, or keep it"));
        else if (!cargo.Truthy && survivors.Truthy && !h.F("caravan.box_taken").Truthy) main.Add(new("The Coyle strongbox is still in the Roost, with the rest of the cargo"));
        var opt = new List<Step>();
        if (!Rules.Test(new Cond { Met = "harlan" }, c)) opt.Add(new("Harlan Coyle, outside Coyle Trading, is offering a reward", Optional: true));
        if (h.Has("pell_ledger") && !h.Entry("pell_exposed") && !h.Entry("pell_joined"))
        {
            bool kerchiefs = KnowsKerchiefs(h);
            if (kerchiefs && KnowsTheNight(h)) opt.Add(new("Pell Varrow's ledger: show it to Harlan, or to Captain Holloway", Optional: true));
            else if (!h.Entry("ledger_read")) opt.Add(new("Someone who knows the dates could read Pell's ledger: Captain Holloway, or Harlan Coyle", Optional: true));
            else opt.Add(new("Find out who \"R.\" is. Kerchief arrows are red-fletched; Rav Cutwell, at the Flagon, knows the Kerchiefs", Optional: true));
        }
        else if (h.Entry("clerk_turned") && !h.Entry("pell_ledger")) opt.Add(new("Someone paid the toll clerk. Pell Varrow's warehouse may say who", Optional: true));
        else if (h.Entry("wreck") && !h.Entry("clerk_turned")) opt.Add(new("Who sent the wagons off the road? Try the east-gate guard, or the tavern", Optional: true));
        if (h.Entry("manifest") && !h.Entry("blasting_ember")) opt.Add(new("Ask Harlan about the crates marked \"B.E.\" in the manifest", Optional: true));
        return main.Concat(opt).ToList();
    }
}

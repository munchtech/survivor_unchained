using System.Collections.Generic;

namespace SurvivorUnchained.World;

/* How the powers of Thornhollow regard the survivor.
 *
 * The Verge asks these when it decides whether a wolf, a Kerchief or a
 * digger raises a hand (so a peace holds until it is broken on purpose),
 * and the journal reads the same answers back as a page: who is with you,
 * who is against you, and why. */

public enum StandingTone { Ally, Friend, Neutral, Wary, Hostile, Gone }
public sealed record StandingEntry(string Id, string Name, string Word, StandingTone Tone, string Why);

public static class Standings
{
    static Fact F(Ctx c, string k) => c.World.Fact(k);
    static bool Is(Ctx c, string k, string v) => F(c, k).Str == v;

    /// <summary>The Pack lets you pass.</summary>
    public static bool WolvesFriendly(Ctx c) => !F(c, "hollow.hostile").Truthy &&
        (F(c, "hollow.peace").Truthy || F(c, "pack.allied").Truthy || Is(c, "beasts.outcome", "cured") || c.Ch.Traits.Contains("wolf_friend"));

    /// <summary>The Kerchiefs let you pass: their colours, a bargain, Pell's word, Redcowl's pass.</summary>
    public static bool KerchiefsFriendly(Ctx c) => !F(c, "roost.hostile").Truthy &&
        (Rules.Test(new Cond { HasTag = "kerchief_colors" }, c) || Is(c, "redcowl", "bargained") || Is(c, "caravan.pell", "ally") ||
         (Rules.Test(new Cond { Knows = "pass.redcowl" }, c) && c.World.Npcs.TryGetValue("redcowl", out var r) && r.Flag("met").Truthy));

    /// <summary>The Dig's crew leaves you be, until you give them a reason.</summary>
    public static bool DiggersFriendly(Ctx c) => !F(c, "dig.hostile").Truthy;

    /// <summary>At their own den the Pack holds off for someone who knows how to come to it,
    /// as Maeca tells it: no wolf blood on you since you last slept, and none of
    /// their skins on your back. Their kin worn into the Hollow undoes any peace
    /// short of running with them.</summary>
    public static bool HollowCalm(Ctx c)
    {
        if (F(c, "hollow.hostile").Truthy) return false;
        if (Rules.Test(new Cond { HasTag = "wolf_pelts" }, c) && !F(c, "pack.allied").Truthy) return false;
        return WolvesFriendly(c) || (!F(c, "wolf.blood").Truthy &&
            Rules.Test(new Cond { Any = [new() { Knows = "beastlore" }, new() { Knows = "hint.greymuzzle" }, new() { HasTag = "wolf_fang" }] }, c));
    }

    /// <summary>Every power you have met, and where you stand with it.</summary>
    public static List<StandingEntry> Of(Ctx c)
    {
        var o = new List<StandingEntry>();
        var w = c.World;
        bool Q(string id, string entry) => w.Quests.TryGetValue(id, out var q) && q.Entries.Contains(entry);

        // The Watch: Holloway's regard, and the law.
        if (F(c, "player.wanted").Truthy) o.Add(new("watch", "The Watch", "Wanted", StandingTone.Hostile, "For selling stolen Coyle cargo. Holloway has your name."));
        else if (F(c, "holloway.lied_to").Truthy && !F(c, "holloway.lie_settled").Truthy) o.Add(new("watch", "The Watch", "Suspicious", StandingTone.Wary, "Holloway knows you lied to him about the wolves."));
        else if (w.Npcs.TryGetValue("holloway", out var h))
        {
            double v = h.Trust + h.Respect;
            o.Add(v >= 50 ? new("watch", "The Watch", "Trusted", StandingTone.Ally, "Holloway would stand a gate beside you.")
                : v >= 15 ? new("watch", "The Watch", "Friendly", StandingTone.Friend, "The captain nods when you pass. From him, that is a speech.")
                : v <= -30 ? new("watch", "The Watch", "Watchful", StandingTone.Wary, "The gate guards know your face, and not kindly.")
                : new("watch", "The Watch", "Watchful", StandingTone.Neutral, "Another armed stranger off the road."));
        }

        // The Coyle Company: Harlan, and his nephew.
        if (w.Quests.TryGetValue("caravan", out var cq) && cq.Status != QuestStatus.Unknown)
        {
            if (Is(c, "caravan.survivors", "rescued") && Is(c, "caravan.cargo", "returned")) o.Add(new("coyle", "The Coyle Company", "In your debt", StandingTone.Ally, "You brought Jory home, and every crate with him."));
            else if (Is(c, "caravan.cargo", "kept") || Is(c, "caravan.cargo", "sold"))
                o.Add(new("coyle", "The Coyle Company", "Cheated", StandingTone.Hostile, Is(c, "caravan.survivors", "rescued") ? "You brought Jory home. You kept his uncle's goods." : "The Coyle cargo went where you took it."));
            else if (Is(c, "caravan.survivors", "rescued")) o.Add(new("coyle", "The Coyle Company", "Grateful", StandingTone.Ally, "You brought Jory home."));
            else if (Is(c, "caravan.survivors", "dead")) o.Add(new("coyle", "The Coyle Company", "Grieving", StandingTone.Neutral, "The teamsters died in the Roost's cages."));
            else o.Add(new("coyle", "The Coyle Company", "Hoping", StandingTone.Friend, "Harlan is waiting on news of his nephew."));
        }

        // The Kerchiefs, once you know they are there.
        if (Q("caravan", "wreck") || Q("caravan", "roost_found") || F(c, "kerchief.raids").Number > 0 || (w.Npcs.TryGetValue("redcowl", out var rc) && rc.Flag("met").Truthy))
        {
            if (Is(c, "redcowl", "dead")) o.Add(new("kerchief", "The Kerchiefs", "Broken", StandingTone.Gone, "Redcowl is dead. What is left of them has scattered."));
            else if (Is(c, "redcowl", "spared")) o.Add(new("kerchief", "The Kerchiefs", "In your debt", StandingTone.Friend, "You let Redcowl get up. He has taken his people off the Old Road, and he pays his debts."));
            else if (F(c, "roost.hostile").Truthy) o.Add(new("kerchief", "The Kerchiefs", "At war", StandingTone.Hostile, "You broke the peace at the Roost. Every red rag in the Verge knows it."));
            else if (KerchiefsFriendly(c))
            {
                string why = Rules.Test(new Cond { HasTag = "kerchief_colors" }, c) ? "You wear their red. They take it as a promise."
                    : Is(c, "be.crates", "redcowl") ? "Redcowl keeps the Coyle crates from the Dig, on your word."
                    : Is(c, "redcowl", "bargained") ? "You struck a bargain with Redcowl. It holds while it pays."
                    : Is(c, "caravan.pell", "ally") ? "Pell's word goes a long way in the Roost."
                    : "Redcowl gave you a pass, and his people know your face.";
                o.Add(new("kerchief", "The Kerchiefs", "Tolerated", StandingTone.Neutral, why));
            }
            else o.Add(new("kerchief", "The Kerchiefs", "Hostile", StandingTone.Hostile, "Road bandits in red. They take what travels the Old Road."));
        }

        // The Pack.
        if (w.Quests.TryGetValue("beasts", out var bq) && bq.Status != QuestStatus.Unknown)
        {
            var outcome = F(c, "beasts.outcome").Str;
            if (outcome == "slaughtered" || Is(c, "greymuzzle", "dead"))
                o.Add(new("pack", "The Pack", "Gone", StandingTone.Gone, outcome == "slaughtered" ? "You killed them. The Verge is quiet." : "Greymuzzle is dead. The rest will not come near you."));
            else if (F(c, "pack.allied").Truthy || outcome == "allied") o.Add(new("pack", "The Pack", "Runs with you", StandingTone.Ally, "Greymuzzle's wolves follow where you lead."));
            else if (F(c, "hollow.hostile").Truthy) o.Add(new("pack", "The Pack", "Hunting you", StandingTone.Hostile, "You drew blood at the Hollow. They remember."));
            else if (outcome == "cured") o.Add(new("pack", "The Pack", "At peace", StandingTone.Friend, "The stream runs clear. The wolves have gone back to the deep wood."));
            else if (WolvesFriendly(c)) o.Add(new("pack", "The Pack", "Let you pass", StandingTone.Neutral, "Greymuzzle showed you the sick ones. The Pack holds off."));
            else o.Add(new("pack", "The Pack", "Starving", StandingTone.Hostile, "The wolves are sick, and they are hunting the road."));
        }

        // The Dig, once you know who is poisoning the stream.
        if (Q("beasts", "root_cause") || Q("beasts", "clue.pipe") || F(c, "dig.hostile").Truthy)
        {
            var pump = F(c, "dig.pump").Str;
            if (pump == "blown") o.Add(new("dig", "Grimtunnel's Dig", "Buried", StandingTone.Gone, "You blew their powder. There is not much Dig left."));
            else if (F(c, "dig.hostile").Truthy)
                o.Add(new("dig", "Grimtunnel's Dig", "Hostile", StandingTone.Hostile, pump == "broken" ? "You wrecked their pump. The crew wants a word." : "You gave the diggers a reason."));
            else if (pump == "moved")
            {
                bool paid = F(c, "dig.pell_cut").Truthy;
                o.Add(new("dig", "Grimtunnel's Dig", paid ? "Paid off" : "Working elsewhere", StandingTone.Neutral,
                    paid ? "Pell paid them to move the outflow. You were paid to tell him." : "The foreman moved the outflow. He did not enjoy it."));
            }
            else o.Add(new("dig", "Grimtunnel's Dig", "Indifferent", StandingTone.Neutral, "Diggers and their lamplings. They will not trouble you, if you do not trouble them."));
        }
        return o;
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.World;

/* The language the world is written in.
 *
 * Quests, dialogue, zone events, shops and the daily simulation never touch
 * state directly: they ask questions (Cond) and make changes (Change), both
 * as plain data. That is what lets one quest have six solutions without six
 * code paths - each solution is a different set of facts arriving at a
 * different outcome - and it is what the journal and the tests read to
 * explain why the world is the way it is.
 *
 * Every change also produces a Notice, so the interface can tell the player
 * what just happened ("Maeca will remember that.") without the content
 * having to say it twice.
 *
 * Both are written as the web game writes them (data/content, exported from
 * its TypeScript): an object whose one key says what kind it is ({ fact:
 * 'beasts.outcome', eq: 'cured' }, { give: 'antidote' }). */

/// <summary>A comparison: equal, not equal, at least, at most, above, below, set at all.</summary>
public class Cmp
{
    public Fact? Eq, Ne;
    public double? Gte, Lte, Gt, Lt;
    public bool? Exists;

    public bool Holds(Fact v)
    {
        if (Exists is { } ex) return ex ? !v.IsNull : v.IsNull;
        if (Eq is { } eq && v != eq) return false;
        if (Ne is { } ne && v == ne) return false;
        double n = v.Number;
        if (Gte is { } a && !(n >= a)) return false;
        if (Lte is { } b && !(n <= b)) return false;
        if (Gt is { } c && !(n > c)) return false;
        if (Lt is { } d && !(n < d)) return false;
        return true;
    }
}

public sealed class RelCond : Cmp { public string Npc = ""; public Axis Axis; }
public sealed class NpcFlagCond : Cmp { public string Npc = "", Key = ""; }
public sealed class NpcKnowsCond { public string Npc = "", Event = ""; }
public sealed class FactionCond : Cmp { public string Id = ""; }
public sealed class QuestCond { public string Id = ""; public QuestStatus? Status; public string? Entry; }
public sealed class ZoneCond : Cmp { public string Id = "", Key = ""; }

/// <summary>A question about the world and the survivor. Exactly one kind is set.</summary>
public sealed class Cond : Cmp
{
    [JsonPropertyName("fact")] public string? FactKey;
    public string? Knows, NotKnows, Bg, Archetype, HasItem, HasTag, Trait, Met, History;
    /// <summary>"male" or "female": who people take the survivor for.</summary>
    public string? Sex;
    public int? Qty;
    public RelCond? Rel;
    public NpcFlagCond? NpcFlag;
    public NpcKnowsCond? NpcKnows;
    public FactionCond? Faction;
    public QuestCond? Quest;
    /// <summary>Kills: everything the survivor has ever put down, day and night; how
    /// dangerous the town thinks they are, beside their level.</summary>
    public Cmp? Day, Level, Gold, Kills;
    [JsonConverter(typeof(OneOrMany<TimeOfDay>))] public List<TimeOfDay>? Time;
    public ZoneCond? Zone;
    public List<Cond>? All, Any;
    public Cond? Not;
}

public enum NoticeTone { Item, Gold, Rel, Journal, History, Learn, Faction, Trait, Warn, Info }
public sealed record Notice(string Text, NoticeTone Tone);

public sealed class RelChange : Feel { public string Npc = ""; }
public sealed class NpcFlagChange { public string Npc = "", Key = ""; public Fact Value; }
public sealed class FactionChange { public string Id = ""; public double? Standing, Strength; }
public sealed class QuestChange { public string Id = ""; public QuestStatus? Status; public string? Entry, Outcome; }
public sealed class TellChange { public string Npc = "", Event = ""; }
public sealed class ConditionChange { public ConditionId Id; public int Days; public string? Note; }
public sealed class ZoneChange { public string Id = "", Key = ""; public Fact Value; }
public sealed class LaterChange
{
    public int Days;
    public string Id = "";
    [JsonConverter(typeof(OneOrMany<Change>))] public List<Change> Effect = new();
}

/// <summary>A change to the world or the survivor. Exactly one kind is set.</summary>
public sealed class Change
{
    public Dictionary<string, Fact>? Set;
    public Dictionary<string, double>? Add;
    [JsonConverter(typeof(OneOrMany<string>))] public List<string>? Learn;
    public string? Text;
    public RelChange? Rel;
    public bool? Quiet;
    public NpcFlagChange? NpcFlag;
    public FactionChange? Faction;
    public string? Give, Take;
    public int? Qty, Rarity;
    public double? Gold;
    public QuestChange? Quest;
    public HistoryDef? History;
    public List<string>? Witnesses;
    public TellChange? Tell;
    public string? Trait;
    public ConditionChange? Condition;
    public string? Cure;
    public ZoneChange? Zone;
    public LaterChange? Later;
    public double? Xp;
    public string? Notice;
    public NoticeTone? Tone;
    [JsonPropertyName("if")] public Cond? If;
    [JsonPropertyName("then"), JsonConverter(typeof(OneOrMany<Change>))] public List<Change>? Then;
    [JsonPropertyName("else"), JsonConverter(typeof(OneOrMany<Change>))] public List<Change>? Else;
}

/// <summary>What the rules need: the world, the survivor, somewhere to say
/// what happened, and names for people, quests and journal lines.</summary>
public sealed class Ctx
{
    public WorldState World;
    public CharacterData Ch;
    public Action<Notice> Notify;
    public Func<string, string>? NpcName, QuestName;
    public Func<string, string, string>? EntryText;

    public Ctx(WorldState world, CharacterData ch, Action<Notice>? notify = null)
    {
        World = world;
        Ch = ch;
        Notify = notify ?? (_ => { });
    }
}

public static class Rules
{
    public static bool Test(Cond? c, Ctx ctx)
    {
        if (c == null) return true;
        var w = ctx.World;
        var ch = ctx.Ch;
        if (c.All != null) return c.All.All(x => Test(x, ctx));
        if (c.Any != null) return c.Any.Any(x => Test(x, ctx));
        if (c.Not != null) return !Test(c.Not, ctx);
        if (c.FactKey != null) return c.Holds(w.Fact(c.FactKey));
        if (c.Knows != null) return ch.Knowledge.Contains(c.Knows);
        if (c.NotKnows != null) return !ch.Knowledge.Contains(c.NotKnows);
        if (c.Bg != null) return ch.Background == c.Bg;
        if (c.Archetype != null) return ch.Archetype == c.Archetype;
        if (c.Sex != null) return (ch.Sex ?? Rpg.Sex.Male).Key() == c.Sex;
        if (c.HasItem != null) return Inventory.Count(ch, c.HasItem) >= (c.Qty ?? 1);
        if (c.HasTag != null) return Inventory.WorldTags(ch).Contains(c.HasTag);
        if (c.Trait != null) return ch.Traits.Contains(c.Trait);
        if (c.Rel != null) return c.Rel.Holds(Fact.Of(w.Npc(c.Rel.Npc)[c.Rel.Axis]));
        if (c.Met != null) return w.Npc(c.Met).Flag("met").Truthy;
        if (c.NpcFlag != null) return c.NpcFlag.Holds(w.Npc(c.NpcFlag.Npc).Flag(c.NpcFlag.Key));
        if (c.NpcKnows != null) return w.Npc(c.NpcKnows.Npc).Memories.Contains(c.NpcKnows.Event);
        if (c.Faction != null) return c.Faction.Holds(Fact.Of(w.Factions.TryGetValue(c.Faction.Id, out var f) ? f.Standing : 0));
        if (c.Quest != null)
        {
            w.Quests.TryGetValue(c.Quest.Id, out var q);
            if (c.Quest.Status is { } st && (q?.Status ?? QuestStatus.Unknown) != st) return false;
            if (c.Quest.Entry != null && !(q?.Entries.Contains(c.Quest.Entry) ?? false)) return false;
            return true;
        }
        if (c.Day != null) return c.Day.Holds(Fact.Of(w.Day));
        if (c.Time != null) return c.Time.Contains(w.Time);
        if (c.Level != null) return c.Level.Holds(Fact.Of(ch.Level));
        if (c.Gold != null) return c.Gold.Holds(Fact.Of(ch.Gold));
        if (c.Kills != null) return c.Kills.Holds(Fact.Of(ch.Stats.Kills));
        if (c.History != null) return w.History.Exists(h => h.Id == c.History);
        if (c.Zone != null) return c.Zone.Holds(w.Zones.TryGetValue(c.Zone.Id, out var z) && z.TryGetValue(c.Zone.Key, out var v) ? v : Fact.Null);
        return false;
    }

    static readonly Dictionary<Axis, (string Up, string Down)> AxisWords = new()
    {
        [Axis.Trust] = ("trusts you more", "trusts you less"),
        [Axis.Affection] = ("warms to you", "cools toward you"),
        [Axis.Respect] = ("respects you more", "thinks less of you"),
        [Axis.Fear] = ("is more afraid of you", "is less afraid of you"),
    };

    static readonly Axis[] Axes = [Axis.Trust, Axis.Affection, Axis.Respect, Axis.Fear];

    public static void Apply(IEnumerable<Change>? list, Ctx ctx)
    {
        if (list == null) return;
        foreach (var e in list) Apply(e, ctx);
    }

    public static void Apply(Change? e, Ctx ctx)
    {
        if (e == null) return;
        var w = ctx.World;
        var ch = ctx.Ch;
        if (e.If != null) { Apply(Test(e.If, ctx) ? e.Then : e.Else, ctx); return; }
        if (e.Set != null) { foreach (var (k, v) in e.Set) w.Facts[k] = v; return; }
        if (e.Add != null) { foreach (var (k, v) in e.Add) w.Facts[k] = Fact.Of(w.Fact(k).Number + v); return; }
        if (e.Learn != null)
        {
            bool fresh = false;
            foreach (var k in e.Learn) if (!ch.Knowledge.Contains(k)) { ch.Knowledge.Add(k); fresh = true; }
            if (fresh && e.Text != null) ctx.Notify(new Notice(e.Text, NoticeTone.Learn));
            return;
        }
        if (e.Rel != null)
        {
            var s = w.Npc(e.Rel.Npc);
            foreach (var axis in Axes)
            {
                var d = e.Rel.Of(axis) ?? 0;
                if (d == 0) continue;
                s[axis] = Math.Max(-100, Math.Min(100, s[axis] + d));
                if (e.Quiet != true && Math.Abs(d) >= 5)
                    ctx.Notify(new Notice($"{ctx.NpcName?.Invoke(e.Rel.Npc) ?? e.Rel.Npc} {(d > 0 ? AxisWords[axis].Up : AxisWords[axis].Down)}.", NoticeTone.Rel));
            }
            return;
        }
        if (e.NpcFlag != null) { w.Npc(e.NpcFlag.Npc).Flags[e.NpcFlag.Key] = e.NpcFlag.Value; return; }
        if (e.Faction != null)
        {
            if (!w.Factions.TryGetValue(e.Faction.Id, out var f)) w.Factions[e.Faction.Id] = f = new FactionState { Id = e.Faction.Id };
            if (e.Faction.Standing is { } st && st != 0) f.Standing = Math.Max(-100, Math.Min(100, f.Standing + st));
            if (e.Faction.Strength is { } sg && sg != 0) f.Strength = Math.Max(0, Math.Min(100, f.Strength + sg));
            return;
        }
        if (e.Give != null)
        {
            int qty = e.Qty ?? 1;
            var it = Inventory.Make(ch, e.Give, qty: qty, rarity: e.Rarity);
            var name = Items.Get(e.Give).Name;
            if (Inventory.AddToPack(ch, it)) ctx.Notify(new Notice(qty > 1 ? $"{name} ×{qty}" : name, NoticeTone.Item));
            else
            {
                int slot = w.Stash.IndexOf(null);
                if (slot >= 0) w.Stash[slot] = it;
                ctx.Notify(new Notice($"{name} was sent to the inn - your pack is full.", NoticeTone.Warn));
            }
            return;
        }
        if (e.Take != null) { Inventory.Take(ch, e.Take, e.Qty ?? 1); return; }
        if (e.Gold is { } gold)
        {
            ch.Gold = Math.Max(0, ch.Gold + gold);
            if (gold > 0) ch.Stats.GoldEarned += gold;
            ctx.Notify(new Notice($"{(gold > 0 ? "+" : "")}{gold} gold", NoticeTone.Gold));
            return;
        }
        if (e.Quest != null)
        {
            var qc = e.Quest;
            if (!w.Quests.TryGetValue(qc.Id, out var q)) w.Quests[qc.Id] = q = new QuestState { Id = qc.Id };
            // A settled quest stays settled: meeting someone late, or reading
            // an old notice, can add to its story but never reopens it.
            bool settled = q.Status is QuestStatus.Resolved or QuestStatus.Failed or QuestStatus.Abandoned;
            if (qc.Status is { } status && q.Status != status && !(settled && status == QuestStatus.Active))
            {
                var was = q.Status;
                q.Status = status;
                if (was == QuestStatus.Unknown && q.Status == QuestStatus.Active)
                {
                    q.StartedDay = w.Day;
                    ctx.Notify(new Notice($"New: {ctx.QuestName?.Invoke(q.Id) ?? q.Id}", NoticeTone.Journal));
                }
                if (q.Status == QuestStatus.Resolved) ctx.Notify(new Notice($"{ctx.QuestName?.Invoke(q.Id) ?? q.Id}: resolved", NoticeTone.Journal));
            }
            if (qc.Entry != null && !q.Entries.Contains(qc.Entry))
            {
                q.Entries.Add(qc.Entry);
                if (q.Status == QuestStatus.Unknown) { q.Status = QuestStatus.Active; q.StartedDay = w.Day; }
                ctx.Notify(new Notice(ctx.EntryText?.Invoke(q.Id, qc.Entry) ?? "Journal updated", NoticeTone.Journal));
            }
            if (qc.Outcome != null) q.Outcome = qc.Outcome;
            return;
        }
        if (e.History != null)
        {
            if (w.History.Exists(h => h.Id == e.History.Id)) return;
            var ev = new HistoryEvent
            {
                Id = e.History.Id, Text = e.History.Text, Tags = new(e.History.Tags), Spread = e.History.Spread,
                Sentiment = e.History.Sentiment, Reactions = e.History.Reactions, Day = w.Day,
            };
            w.History.Add(ev);
            foreach (var who in e.Witnesses ?? new()) Witness(w, who, ev, ctx);
            return;
        }
        if (e.Tell != null)
        {
            var ev = w.History.Find(h => h.Id == e.Tell.Event);
            if (ev != null) Witness(w, e.Tell.Npc, ev, ctx);
            return;
        }
        if (e.Trait != null)
        {
            if (!ch.Traits.Contains(e.Trait))
            {
                ch.Traits.Add(e.Trait);
                ctx.Notify(new Notice($"You have become: {Callings.Trait(e.Trait)?.Name ?? e.Trait}", NoticeTone.Trait));
            }
            return;
        }
        if (e.Condition != null)
        {
            var cur = ch.Conditions.Find(c => c.Id == e.Condition.Id);
            if (cur != null) cur.Days = Math.Max(cur.Days, e.Condition.Days);
            else ch.Conditions.Add(new Condition { Id = e.Condition.Id, Days = e.Condition.Days, Note = e.Condition.Note });
            return;
        }
        if (e.Cure != null) { ch.Conditions.RemoveAll(c => c.Id.Key() == e.Cure); return; }
        if (e.Zone != null) { w.Zone(e.Zone.Id)[e.Zone.Key] = e.Zone.Value; return; }
        if (e.Later != null) { w.Scheduled.Add(new ScheduledChange { Day = w.Day + e.Later.Days, Id = e.Later.Id, Effect = e.Later.Effect }); return; }
        if (e.Xp is { } xp) { ch.Xp += xp; return; }
        if (e.Notice != null) { ctx.Notify(new Notice(e.Notice, e.Tone ?? NoticeTone.Info)); return; }
    }

    /// <summary>Someone learns of an event and it changes how they feel about you.</summary>
    public static bool Witness(WorldState w, string who, HistoryEvent ev, Ctx? ctx = null)
    {
        var s = w.Npc(who);
        if (s.Memories.Contains(ev.Id) || !s.Alive) return false;
        s.Memories.Add(ev.Id);
        Feel? personal = null;
        ev.Reactions?.TryGetValue(who, out personal);
        var r = personal ?? ev.Sentiment;
        if (r != null)
        {
            foreach (var axis in Axes)
            {
                var d = r.Of(axis) ?? 0;
                if (d != 0) s[axis] = Math.Max(-100, Math.Min(100, s[axis] + d));
            }
            if (ctx != null && personal != null) ctx.Notify(new Notice($"{ctx.NpcName?.Invoke(who) ?? who} will remember that.", NoticeTone.Rel));
        }
        return true;
    }

    /// <summary>A short read of how someone regards you, for the interface.</summary>
    public static string Attitude(NpcState s)
    {
        // Each axis says something once it is past a murmur; the two loudest speak.
        var said = new List<(double Loud, string Words)>();
        void Say(double v, (double At, string Words)[] words)
        {
            foreach (var (at, wd) in words)
                if (at > 0 ? v >= at : v <= at) { said.Add((Math.Abs(v), wd)); return; }
        }
        Say(s.Fear, [(40, "afraid of you"), (20, "uneasy around you")]);
        Say(s.Trust, [(40, "trusts you"), (15, "starting to trust you"), (-40, "distrusts you"), (-15, "wary of you")]);
        Say(s.Affection, [(40, "fond of you"), (15, "likes you"), (-40, "dislikes you"), (-15, "cool toward you")]);
        Say(s.Respect, [(40, "respects you"), (15, "thinks you capable"), (-40, "holds you in contempt"), (-15, "thinks little of you")]);
        if (said.Count == 0) return s.Flag("met").Truthy ? "unsure of you" : "a stranger";
        return string.Join(", ", said.OrderByDescending(x => x.Loud).Take(2).Select(x => x.Words));
    }
}

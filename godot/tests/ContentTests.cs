using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The content is data; these read all of it and check that every
/// reference points at something real. A typo in a quest entry id is a
/// silent bug in play; here it is a red line.</summary>
public class ContentTests
{
    static readonly HashSet<string> Actions = ["trade", "rest", "stash", "sell", "craft", "leave", "fortune", "bounty", "sellpelts", "reforge", "travel_verge"];

    static void WalkChanges(IEnumerable<Change>? list, Action<Change> fn)
    {
        if (list == null) return;
        foreach (var e in list)
        {
            fn(e);
            if (e.If != null) { WalkChanges(e.Then, fn); WalkChanges(e.Else, fn); }
            if (e.Later != null) WalkChanges(e.Later.Effect, fn);
        }
    }

    static void WalkConds(Cond? c, Action<Cond> fn)
    {
        if (c == null) return;
        fn(c);
        foreach (var x in c.All ?? new()) WalkConds(x, fn);
        foreach (var x in c.Any ?? new()) WalkConds(x, fn);
        WalkConds(c.Not, fn);
    }

    static Action<Change> CheckChange(string where, List<string> problems) => e =>
    {
        if (e.Give != null && Items.Find(e.Give) == null) problems.Add($"{where}: gives unknown item {e.Give}");
        if (e.Take != null && Items.Find(e.Take) == null) problems.Add($"{where}: takes unknown item {e.Take}");
        if (e.Trait != null && Callings.Trait(e.Trait) == null) problems.Add($"{where}: unknown trait {e.Trait}");
        if (e.Quest != null)
        {
            if (!Lore.Quests.TryGetValue(e.Quest.Id, out var q)) problems.Add($"{where}: unknown quest {e.Quest.Id}");
            else
            {
                if (e.Quest.Entry != null && !q.Entries.ContainsKey(e.Quest.Entry)) problems.Add($"{where}: quest {e.Quest.Id} has no entry {e.Quest.Entry}");
                if (e.Quest.Outcome != null && q.Outcomes != null && !q.Outcomes.ContainsKey(e.Quest.Outcome)) problems.Add($"{where}: quest {e.Quest.Id} has no outcome {e.Quest.Outcome}");
            }
        }
    };

    static Action<Cond> CheckCond(string where, List<string> problems) => c =>
    {
        if (c.HasItem != null && Items.Find(c.HasItem) == null) problems.Add($"{where}: checks unknown item {c.HasItem}");
        if (c.Trait != null && Callings.Trait(c.Trait) == null) problems.Add($"{where}: checks unknown trait {c.Trait}");
        if (c.Quest != null && !Lore.Quests.ContainsKey(c.Quest.Id)) problems.Add($"{where}: checks unknown quest {c.Quest.Id}");
        if (c.Quest?.Entry != null && !(Lore.Quests.TryGetValue(c.Quest.Id, out var q) && q.Entries.ContainsKey(c.Quest.Entry)))
            problems.Add($"{where}: checks unknown entry {c.Quest.Id}.{c.Quest.Entry}");
    };

    [Fact]
    public void Every_conversation_is_well_formed()
    {
        var problems = new List<string>();
        foreach (var (id, convo) in Dialogue.All)
        {
            if (Lore.Person(id) == null && !Lore.Speakers.ContainsKey(id)) problems.Add($"{id}: speaker has no definition");
            foreach (var e in convo.Entry)
            {
                if (!convo.Nodes.ContainsKey(e.Node)) problems.Add($"{id}: entry points at missing node {e.Node}");
                WalkConds(e.When, CheckCond($"{id} entry", problems));
            }
            foreach (var m in convo.Marker ?? new()) WalkConds(m.When, CheckCond($"{id} marker", problems));
            foreach (var (nid, n) in convo.Nodes)
            {
                string where = $"{id}.{nid}";
                if (n.Id != nid) problems.Add($"{where}: id mismatch ({n.Id})");
                if (n.Next != null && !convo.Nodes.ContainsKey(n.Next)) problems.Add($"{where}: next points at missing node {n.Next}");
                if (n.Next == null && (n.Choices?.Count ?? 0) == 0) problems.Add($"{where}: a dead end with no choices");
                WalkChanges(n.Effects, CheckChange(where, problems));
                foreach (var v in n.Text) WalkConds(v.When, CheckCond(where, problems));
                foreach (var c in n.Choices ?? new())
                {
                    if (c.Goto != null && !convo.Nodes.ContainsKey(c.Goto)) problems.Add($"{where}: choice goes to missing node {c.Goto}");
                    if (c.Action != null && !Actions.Contains(c.Action)) problems.Add($"{where}: unknown action {c.Action}");
                    WalkChanges(c.Effects, CheckChange(where, problems));
                    WalkConds(c.When, CheckCond(where, problems));
                    WalkConds(c.Show, CheckCond(where, problems));
                }
            }
        }
        Assert.Empty(problems);
        Assert.True(Dialogue.All.Count >= 18, $"{Dialogue.All.Count} conversations");
    }

    [Fact]
    public void Rules_shops_and_creatures_reference_real_things()
    {
        var p = new List<string>();
        foreach (var r in Simulation.DailyRules) WalkChanges(r.Effect, CheckChange($"rule {r.Id}", p));
        foreach (var s in Lore.Shops.Values) foreach (var l in s.Lines) if (Items.Find(l.Id) == null) p.Add($"shop {s.Id}: unknown item {l.Id}");
        foreach (var e in Enemies.All.Values) if (e.Raise != null && !Enemies.All.ContainsKey(e.Raise.Into)) p.Add($"enemy {e.Id}: raises unknown {e.Raise.Into}");
        foreach (var it in Items.All.Values) if (it.Weapon != null && !Weapons.All.ContainsKey(it.Weapon.Id)) p.Add($"item {it.Id}: unknown weapon {it.Weapon.Id}");
        foreach (var a in Callings.Archetypes.Values)
        {
            foreach (var w in a.Weapons) if (Items.Find(w) == null) p.Add($"calling {a.Id}: unknown weapon item {w}");
            foreach (var ab in a.Abilities) if (!Abilities.All.Values.Any(x => x.Id == ab)) p.Add($"calling {a.Id}: unknown ability {ab}");
        }
        foreach (var b in Callings.Backgrounds.Values) foreach (var i in b.Items) if (Items.Find(i) == null) p.Add($"background {b.Id}: unknown item {i}");
        Assert.Empty(p);
    }

    [Fact]
    public void Every_item_has_an_icon_a_value_and_words()
    {
        foreach (var it in Items.All.Values)
        {
            Assert.False(string.IsNullOrEmpty(it.Icon), it.Id);
            Assert.True(it.Description.Length > 8, it.Id);
            Assert.True(it.Value >= 0, it.Id);
        }
        Assert.True(Items.All.Count >= 50);
    }

    [Fact]
    public void Every_trigger_in_items_and_traits_is_read()
    {
        // Rules carried as data survive the trip: every item and trait trigger has effects.
        foreach (var it in Items.All.Values) foreach (var t in it.Triggers ?? new()) Assert.NotEmpty(t.Effects);
        foreach (var tr in Callings.Traits.Values) foreach (var t in tr.Triggers ?? new()) Assert.NotEmpty(t.Effects);
    }
}

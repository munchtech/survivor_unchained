using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.World;

/* Conversations.
 *
 * A conversation is a small graph. Where it starts depends on who you are to
 * the person and what they know about you: the same innkeeper greets a
 * stranger, a friend, a thief and someone she heard died last week in four
 * different ways, chosen by conditions, first that holds.
 *
 * Choices are shown when their condition holds. Some are shown DISABLED
 * with a reason instead ("Requires: Beastlore") - the game telling you there
 * was another way, which is half of what makes a background feel like it
 * matters. Text can vary by condition and quote the world back ({name},
 * {day}, {gold}, {fact:key}). The conversations are data
 * (data/content/dialogue.json). */

/// <summary>One way a line can read. The first variant whose condition holds
/// is used; Add variants are instead all collected, in order, and joined.</summary>
public sealed class Variant
{
    public Cond? When;
    public string Text = "";
    public bool Add;
}

/// <summary>Text written either as a plain string or as variants.</summary>
public sealed class TextConverter : JsonConverter<List<Variant>>
{
    public override List<Variant> Read(ref Utf8JsonReader r, Type t, JsonSerializerOptions o)
    {
        if (r.TokenType == JsonTokenType.String) return new List<Variant> { new() { Text = r.GetString()! } };
        return JsonSerializer.Deserialize<List<Variant>>(ref r, o) ?? new();
    }

    public override void Write(Utf8JsonWriter w, List<Variant> v, JsonSerializerOptions o)
    {
        if (v.Count == 1 && v[0].When == null && !v[0].Add) w.WriteStringValue(v[0].Text);
        else JsonSerializer.Serialize(w, v, o);
    }
}

public sealed class DChoice
{
    [JsonConverter(typeof(TextConverter))] public List<Variant> Text = new();
    /// <summary>Offered at all only while this holds.</summary>
    public Cond? Show;
    public Cond? When;
    /// <summary>Show the choice greyed out, with this reason, when When fails.</summary>
    public string? Locked;
    public string? Badge;
    public List<Change>? Effects;
    public string? Goto;
    /// <summary>Can only be picked once in this person's lifetime.</summary>
    public string? Once;
    /// <summary>Special actions the game handles: services and trades
    /// ('trade', 'rest', 'stash', 'sell', 'fortune', 'travel_verge'...).</summary>
    public string? Action;
    public bool End;
}

public sealed class DNode
{
    public string Id = "";
    /// <summary>Who speaks: the conversation's owner by default, 'player', 'narrator'.</summary>
    public string? Speaker;
    [JsonConverter(typeof(TextConverter))] public List<Variant> Text = new();
    public List<DChoice>? Choices;
    public List<Change>? Effects;
    /// <summary>No choices: continue to this node on click.</summary>
    public string? Next;
}

public sealed class Entry { public Cond? When; public string Node = ""; }
public sealed class Marker { public Cond? When; public string Mark = "!"; }

public sealed class Conversation
{
    public string Npc = "";
    public List<Entry> Entry = new();
    public Dictionary<string, DNode> Nodes = new();
    /// <summary>The mark over their head: '!' something new to say, '?' waiting on you.</summary>
    public List<Marker>? Marker;
}

public sealed record PresentedChoice(int Index, string Text, bool Enabled, string? Locked, string? Badge, bool Ends, string? Action);
public sealed record Presented(DNode Node, string Speaker, string Text, List<PresentedChoice> Choices);

public static class Dialogue
{
    static Dictionary<string, Conversation>? all;
    public static Dictionary<string, Conversation> All => all ??= Json.Parse<Dictionary<string, Conversation>>(Json.ReadContent("dialogue.json"));
    public static Conversation? Find(string id) => All.TryGetValue(id, out var c) ? c : null;

    public static string PickText(List<Variant> t, Ctx ctx)
    {
        if (t.Exists(v => v.Add)) return string.Join("  ·  ", t.Where(v => v.Add && Rules.Test(v.When, ctx)).Select(v => v.Text));
        foreach (var v in t) if (Rules.Test(v.When, ctx)) return v.Text;
        return t.Count > 0 ? t[^1].Text : "";
    }

    static readonly Regex FactRef = new(@"\{fact:([\w.]+)\}", RegexOptions.Compiled);

    /// <summary>Fill {name}, {day}, {gold}, {fact:key} from the world.</summary>
    public static string Template(string s, Ctx ctx) =>
        FactRef.Replace(s.Replace("{name}", ctx.Ch.Name).Replace("{day}", ctx.World.Day.ToString())
            .Replace("{gold}", ctx.Ch.Gold.ToString(System.Globalization.CultureInfo.InvariantCulture)),
            m => ctx.World.Fact(m.Groups[1].Value).ToString());

    /// <summary>The marker a conversation shows right now, if any.</summary>
    public static string? MarkerOf(Conversation convo, Ctx ctx)
    {
        foreach (var m in convo.Marker ?? new()) if (Rules.Test(m.When, ctx)) return m.Mark;
        return null;
    }
}

public sealed class DialogueRunner
{
    public DNode? Node { get; private set; }
    public readonly Conversation Convo;
    readonly Ctx ctx;
    readonly string seenKey;

    public DialogueRunner(Conversation convo, Ctx ctx)
    {
        Convo = convo;
        this.ctx = ctx;
        seenKey = convo.Npc;
    }

    public Presented? Start()
    {
        var s = ctx.World.Npc(Convo.Npc);
        var entry = Convo.Entry.Find(e => Rules.Test(e.When, ctx));
        if (entry == null) return null;
        var p = Enter(entry.Node);
        s.Flags["met"] = true;
        return p;
    }

    Presented? Enter(string id)
    {
        if (!Convo.Nodes.TryGetValue(id, out var n)) return null;
        Node = n;
        Rules.Apply(n.Effects, ctx);
        var s = ctx.World.Npc(seenKey);
        if (!s.Seen.Contains(id)) s.Seen.Add(id);
        return Present();
    }

    public Presented? Present()
    {
        var n = Node;
        if (n == null) return null;
        var s = ctx.World.Npc(seenKey);
        var choices = new List<PresentedChoice>();
        var list = n.Choices ?? new();
        for (int index = 0; index < list.Count; index++)
        {
            var c = list[index];
            if (c.Once != null && s.Flag($"once:{c.Once}").Truthy) continue;
            if (c.Show != null && !Rules.Test(c.Show, ctx)) continue;
            bool ok = Rules.Test(c.When, ctx);
            if (!ok && c.Locked == null) continue;
            choices.Add(new PresentedChoice(index, Dialogue.Template(Dialogue.PickText(c.Text, ctx), ctx), ok, ok ? null : c.Locked, c.Badge,
                c.End || (c.Goto == null && c.Action == null), c.Action));
        }
        return new Presented(n, n.Speaker ?? Convo.Npc, Dialogue.Template(Dialogue.PickText(n.Text, ctx), ctx), choices);
    }

    /// <summary>Pick a choice by its index in the node: the next view (null
    /// when the conversation ends), and any action the game must perform.</summary>
    public (Presented? Next, string? Action) Choose(int index)
    {
        var n = Node;
        var c = n?.Choices is { } cs && index >= 0 && index < cs.Count ? cs[index] : null;
        if (n == null || c == null || !Rules.Test(c.When, ctx)) return (Present(), null);
        var s = ctx.World.Npc(seenKey);
        if (c.Once != null) s.Flags[$"once:{c.Once}"] = true;
        Rules.Apply(c.Effects, ctx);
        if (c.End || (c.Goto == null && c.Action == null)) { Node = null; return (null, c.Action); }
        if (c.Action != null && c.Goto == null) return (Present(), c.Action);
        return (Enter(c.Goto!), c.Action);
    }

    /// <summary>Nodes with no choices continue on click.</summary>
    public Presented? Advance()
    {
        var n = Node;
        if (n == null) return null;
        if (n.Next != null) return Enter(n.Next);
        Node = null;
        return null;
    }
}

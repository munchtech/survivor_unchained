using System;
using System.Collections.Generic;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Cinema;

/// <summary>A line a cinematic says: its recording's id, the words as written
/// (what the take was made from) and as shown, and who says it (null: the narrator).</summary>
public sealed record CineLine(string Id, string VoId, string Raw, string Text, string? Speaker, string? SpeakerId);

/// <summary>
/// A cinematic's lines, read from the conversation that holds them
/// (dialogue.json; docs/cinematics/README.md section 5): "conversation.node",
/// the variant the survivor gets, and how long it runs: its take, or a
/// slow reading pace when there is no take yet.
/// </summary>
public static class CineLines
{
    public static CineLine Find(string id, Ctx ctx)
    {
        int dot = id.IndexOf('.');
        if (dot < 0) throw new FormatException($"a line id is conversation.node, not {id}");
        string conv = id[..dot], node = id[(dot + 1)..];
        var c = Dialogue.Find(conv) ?? throw new KeyNotFoundException($"no conversation {conv}");
        if (!c.Nodes.TryGetValue(node, out var n)) throw new KeyNotFoundException($"no node {node} in {conv}");
        int i = Math.Max(0, Dialogue.PickIndex(n.Text, ctx));
        string raw = n.Text.Count > 0 ? n.Text[i].Text : "";
        string who = n.Speaker ?? c.Npc;
        string? name = who == "narrator" ? null : Lore.NameOf(who);
        return new CineLine(id, VoiceLines.Dialogue(conv, node, i), raw, Dialogue.Template(raw, ctx), name, who);
    }

    /// <summary>How long a line runs, for the cut: its take's voice when there is
    /// one made from these words (Read, without the room's tail, which plays on
    /// over what follows; the whole file for a take made before Read was
    /// measured), else a slow narrator's pace (about 2.6 words a second).</summary>
    public static double Seconds(CineLine l)
    {
        if (l.Raw == "") return 0;
        if (VoiceLines.Take(l.VoId, l.Raw) is { } take) return take.Read > 0 ? take.Read : take.Sec;
        return Reading(l.Text);
    }

    public static double Reading(string text)
    {
        int words = text.Split((char[])[' ', '/'], StringSplitOptions.RemoveEmptyEntries).Length;
        return Math.Max(1.2, 0.5 + words / 2.6);
    }

    /// <summary>The survivor a cinematic is played for, from the character.</summary>
    public static CineContext Context(CharacterData ch, IEnumerable<string>? facts = null)
    {
        var c = new CineContext
        {
            Calling = ch.Archetype,
            Background = ch.Background,
            Sex = ch.Sex == Sex.Male ? "male" : "female",
            Hair = ch.HairStyle ?? "long",
        };
        foreach (var f in facts ?? []) c.Facts.Add(f);
        return c;
    }
}

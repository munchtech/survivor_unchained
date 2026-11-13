using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/* (bd-ui2, Godot-free: tests link this file) The road page as data: her calling's roads side by side, which one she
 * walks, whether a change is open (level gate), what each teaches, its Strike and Stand, its three leaning skills. */
public static class RoadPageModel
{
    public sealed record FlareLine(string Id, string Name, string Text, string Icon);
    public sealed record RoadPanel(string Id, string Name, string Line, bool Walked, string? RoadSkill, FlareLine? Strike, FlareLine? Stand, string[] Leaning);
    public sealed record Page(List<RoadPanel> Roads, bool Open, int OpensAt, string Gate);

    public const string Foot = "Changing your road at a lamp-post puts out every lamp (refunded).";

    public static Page Of(CharacterData ch)
    {
        var walked = LampBook.Walked(ch)?.Id;
        var roads = Lamps.RoadsOf(ch.Archetype).Select(r => new RoadPanel(r.Id, r.Name, r.Line, r.Id == walked,
            LampBook.RoadSkill(ch, r.Id), Flare(r.Strike), Flare(r.Stand), r.Skills.ToArray())).ToList();
        bool open = LampBook.RoadOpen(ch);
        return new Page(roads, open, LampBook.RoadLevel, $"Opens at level {LampBook.RoadLevel}");
    }

    static FlareLine? Flare(string id) => Lamps.Flare(id) is { } f ? new FlareLine(f.Id, f.Name, f.Text, f.Icon) : null;
}

using System.Linq;
using Godot;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>The Wayfinder's table by the east gate: today's maps, three of
/// them, each a place, a people, a tier and the oaths it is sworn under.
/// Choose one and set out (Maps/MapOffers.cs).</summary>
public partial class MapTableScreen : Overlay
{
    public override string Kind => "maps";

    public MapTableScreen(Game g) : base(g) { }

    protected override void Build()
    {
        var w = G.Journey.World;
        int best = (int)System.Math.Max(1, w.Fact("map.best").Number);
        var offers = MapOffers.Today(w.Day, best, (int)w.Fact("map.drawn").Number);
        var v = Frame("The Wayfinder's Table", new Vector2(1180, 700), "Esc", $"Maps to places the road forgets. You have taken tier {best}. A map's spoils lean toward what answers it.");
        var row = Style.H(16);
        foreach (var o in offers)
        {
            var people = MapOffers.People(o.People);
            var card = Style.V(8,
                Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, 13, Style.Gold),
                Style.Label(o.Spec.Name, Style.Display, 26, Style.GoldHi, true),
                Style.Label($"Held by {people.Name}{(o.Spec.Night ? ", by night" : "")}", Style.TextItalic, 16, Style.Ink, true),
                Style.Label($"Ruled by {people.BossName}", Style.Text, 15, Style.InkDim, true),
                Style.Label($"Their bane: {string.Join(", ", people.Lean.Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a))} gear", Style.TextItalic, 13, new Color("#b8a8d8"), true),
                Style.Rule());
            if (o.Spec.Oaths.Count == 0) card.AddChild(Style.Label("Sworn under no oath.", Style.TextItalic, 15, Style.InkDim, true));
            foreach (var id in o.Spec.Oaths)
            {
                var oath = MapOffers.Oath(id);
                card.AddChild(Style.V(1,
                    Style.Label(oath.Name, Style.UiBold, 15, Style.Ink, true),
                    Style.Label($"Asks: {oath.Asks}", Style.Text, 14, new Color("#d08a6a"), true),
                    Style.Label($"Gives: {oath.Gives}", Style.Text, 14, new Color("#9ac48a"), true),
                    Style.Label($"Answered by {oath.Answer}", Style.TextItalic, 13, new Color("#b8a8d8"), true)));
            }
            card.AddChild(Style.Gap(6));
            var pick = o;
            card.AddChild(Style.Button("Set out", () => G.SetOut(pick), true));
            var panel = Style.Panel(Style.Plate(16), card);
            panel.CustomMinimumSize = new Vector2(360, 480);
            row.AddChild(panel);
        }
        v.AddChild(row);
    }
}

using System.Linq;
using Godot;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>The Wayfinder's table by the east gate: today's maps, three of
/// them, each an ember arena (a place, a people, a tier and the oaths it is
/// sworn under), and the story's fights that were lost, to be taken again
/// (Maps/MapOffers.cs, Arena/Arena.cs).</summary>
public partial class MapTableScreen : Overlay
{
    public override string Kind => "maps";

    public MapTableScreen(Game g) : base(g) { }

    protected override void Build()
    {
        var w = G.Journey.World;
        int won = (int)w.Fact("arena.best").Number;
        var offers = MapOffers.Today(w.Day, System.Math.Max(1, won), (int)w.Fact("map.drawn").Number);
        var v = Frame("The Wayfinder's Table", new Vector2(1180, w.Rematches.Count > 0 ? 820 : 700), "Esc",
            $"Maps to places the road forgets: each an ember arena, half an hour and what rules it at the end. {(won > 0 ? $"You have won tier {won}." : "You have won none yet.")} Spoils lean toward what answers the map.", fit: true);
        if (w.Rematches.Count > 0)
        {
            var again = Style.V(6, Style.SubLabel("Fights to take again"));
            foreach (var r in w.Rematches)
            {
                var spec = r;
                var line = Style.H(12,
                    Style.V(0, Style.Label(r.Name, Style.UiBold, 17, Style.GoldHi), Style.Label(r.Sub != "" ? r.Sub : $"Tier {r.Tier}", Style.TextItalic, 14, Style.InkDim)),
                    new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill },
                    Style.Button("Take it again", () => G.Rematch(spec), false, true));
                again.AddChild(line);
            }
            v.AddChild(Style.Panel(Style.Plate(12), again));
        }
        var row = Style.H(16);
        foreach (var o in offers)
        {
            var people = MapOffers.People(o.People);
            var card = Style.V(8,
                Style.H(8, Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, Style.Caption, Style.Gold), Style.Gems(System.Math.Min(o.Spec.Tier - 1, 5), 6)),
                Style.Label(o.Spec.Name, Style.Display, 26, Style.GoldHi, true),
                Style.Label($"Held by {people.Name}", Style.TextItalic, Style.Body, Style.Ink, true),
                Style.Label($"Ruled by {people.BossName}", Style.Text, Style.Small, Style.InkDim, true),
                Style.Label($"Their bane: {string.Join(", ", people.Lean.Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a))} gear", Style.TextItalic, Style.Caption, new Color("#b8a8d8"), true),
                Style.Rule());
            if (o.Spec.Oaths.Count == 0) card.AddChild(Style.Label("Sworn under no oath.", Style.TextItalic, Style.Small, Style.InkDim, true));
            foreach (var id in o.Spec.Oaths)
            {
                var oath = MapOffers.Oath(id);
                card.AddChild(Style.V(1,
                    Style.Label(oath.Name, Style.UiBold, Style.Small, Style.Ink, true),
                    Style.Label($"Asks: {oath.Asks}", Style.Text, Style.Caption, new Color("#e09a7a"), true),
                    Style.Label($"Gives: {oath.Gives}", Style.Text, Style.Caption, new Color("#a8d498"), true),
                    Style.Label($"Answered by {oath.Answer}", Style.TextItalic, Style.Caption, new Color("#c0b0e0"), true)));
            }
            card.AddChild(Style.Gap(6));
            var pick = o;
            card.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
            card.AddChild(Style.Label("Half an hour; the ember from nothing", Style.TextItalic, Style.Caption, Style.InkDim, true));
            card.AddChild(Nav.Id(Style.Button("Enter the arena", () => G.SetOut(pick), true), $"enter:{o.Spec.Name}"));
            var panel = Style.Panel(Style.Plate(16), card);
            panel.CustomMinimumSize = new Vector2(360, 480);
            row.AddChild(panel);
        }
        v.AddChild(row);
        if (Controls.Instance.UsingPad) v.AddChild(Footer((Act.Left, "Choose a map"), (Act.Confirm, "Enter the arena"), (Act.Cancel, "Close")));
    }
}

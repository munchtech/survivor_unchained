using System;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A still-room (docs/CRAFTING_DESIGN.md 7.2): what the herbalist brews from what the survivor
/// brings, her flask, and the way to her bench. A panel at the right with the world in view, not
/// a page: brewing is an errand on the way out of town, not a sheet to plan at (the owner: full
/// pages are often not the best choice), and she stands there at her table beside the survivor.
/// Mouse: press Brew. Pad: the stick between the presses and A.
/// </summary>
public partial class StillRoom : Overlay
{
    public override string Kind => "still";
    readonly string crafter;
    const float PanelW = 760;

    public StillRoom(Game g, string crafter) : base(g)
    {
        this.crafter = crafter;
        Nav.Prefer = "brew:0";
        g.Journey.CraftSaid = null;
    }

    /// <summary>The survivor and the herbalist stand in view to the left of the panel.</summary>
    public override float CameraShift => -200;

    CharacterData Ch => G.Journey.Ch;
    CraftCtx X => G.Journey.Craft;

    protected override void Build()
    {
        var def = Crafting.Crafter(crafter);
        var who = Lore.Person(crafter);
        string? sub = who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}  ·  {Rules.Attitude(G.Journey.World.Npc(crafter)).ToLowerInvariant()}" : null;
        var area = SidePanel(def?.Place ?? "The still-room", sub, true, PanelW);
        var v = Style.V(Style.Gap3);
        v.Size = area.Size;
        area.AddChild(v);

        v.AddChild(Said());

        v.AddChild(new Section("Brew", "cheaper than the shop's, from what you bring her"));
        int k = 0;
        foreach (var r in Crafting.Brews(crafter).Where(Known)) v.AddChild(BrewRow(r, k++));

        var f = Crafting.Rules.Flask;
        if (f.Crafter == crafter)
        {
            v.AddChild(new Section("Her flask", Crafting.HasFlask(Ch) ? "yours" : "the end of brewing"));
            v.AddChild(Flask(f));
        }
        if (Crafting.Does(crafter, Verb.WorkIn))
        {
            v.AddChild(new Section("Tinctures", "worked into what you wear, at her bench"));
            v.AddChild(Bench());
        }

        var room = new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
        v.AddChild(room);
        v.AddChild(Purse());
        SideFooter(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Brew, or buy"), (Act.Cancel, "Close"))
            : MouseFooter("Brewed here, a draught is cheaper than at the shop", "never stronger"));
    }

    /// <summary>What she says: over the last brew, or a greeting (the story lead's words, in data).</summary>
    Control Said()
    {
        var said = G.Journey.CraftSaid ?? new Said(null, Crafting.Line(crafter, "greet", G.Journey.World.Day), null);
        var box = Style.V(Style.Gap1);
        if (said.Before != null) box.AddChild(Style.Label(said.Before, Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
        if (said.Line != null) box.AddChild(Style.Label($"“{said.Line}”", Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
        if (said.After != null) box.AddChild(Style.Label(said.After, Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
        return Style.Panel(Style.Slab(14), box);
    }

    /// <summary>A brew shows once what it takes has been in the survivor's hands (discovery by touch,
    /// design 8): the moonpetal draught is not offered to someone who has never picked the flower.</summary>
    bool Known(BrewRule r) =>
        r.Takes.Keys.All(m => Inventory.Count(Ch, m) > 0) || Inventory.Count(Ch, r.Draught) > 0
        || (r.Moment != null && G.Journey.World.Npc(r.Crafter).Flag($"said.{r.Moment}").Truthy)
        || r.Takes.Keys.All(m => Items.Find(m)?.Rarity == 0);

    Control BrewRow(BrewRule r, int k)
    {
        var d = Items.Get(r.Draught);
        var one = Crafting.Brew(X, r.Draught);
        var slab = Style.Panel(Style.Slab(12));
        var h = Style.H(Style.Gap3);
        h.AddChild(Style.Panel(Style.Box(new Color(0.03f, 0.03f, 0.04f), Style.RarityOf(d.Rarity) with { A = 0.4f }, 1, 4, 4), ItemPhotos.Icon(d.Icon, 64, Style.RarityOf(d.Rarity))));
        var words = Style.V(2);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        int carry = Inventory.Count(Ch, r.Draught);
        var head = Style.H(Style.Gap2, Style.Label(d.Name, Style.UiBold, Style.Body, Style.GoldHi));
        if (carry > 0) head.AddChild(Style.Label($"you carry {carry}", Style.TextItalic, Style.Caption, Style.InkDim));
        words.AddChild(head);
        words.AddChild(Style.Label(d.Description, Style.UiBold, Style.Small, new Color("#9ad8ff"), true));
        words.AddChild(Style.Label(Cost(one), Style.Ui, Style.Caption, one.Ok ? Style.Ink : Style.InkDim, true));
        if (!one.Ok) words.AddChild(Style.Label(one.Blocked!, Style.TextItalic, Style.Caption, Style.Bad, true));
        h.AddChild(words);
        var presses = Style.V(Style.Gap1);
        presses.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        presses.AddChild(Press(Style.Button("Brew", null, one.Ok, true), one, $"brew:{k}"));
        // As many as she can make of what is in hand, to five: one press for a repeat (no chores, C24).
        int n = Crafting.CanBrew(X, r.Draught, 5);
        if (n >= 2)
        {
            var many = Crafting.Brew(X, r.Draught, n);
            presses.AddChild(Press(Style.Button($"Brew {n}", null, false, true), many, $"brew:{k}:many"));
        }
        h.AddChild(presses);
        slab.AddChild(h);
        return slab;
    }

    Control Flask(FlaskRules f)
    {
        var d = Items.Get(f.Item);
        var slab = Style.Panel(Style.Slab(12));
        var h = Style.H(Style.Gap3);
        h.AddChild(Style.Panel(Style.Box(new Color(0.03f, 0.03f, 0.04f), Style.Line with { A = 0.4f }, 1, 4, 4), ItemPhotos.Icon(d.Icon, 64, Style.InkDim)));
        var words = Style.V(3);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (Crafting.HasFlask(Ch))
        {
            words.AddChild(Style.Label(d.Name, Style.UiBold, Style.Body, Style.GoldHi));
            words.AddChild(Style.Label(d.Description, Style.UiBold, Style.Small, new Color("#9ad8ff"), true));
            int root = Inventory.Count(Ch, f.Material) / Math.Max(1, f.Per);
            words.AddChild(Style.Label(root == 0 ? $"You carry no {Items.Get(f.Material).Plural ?? f.Material}: it will stay dry."
                : $"Your {Items.Get(f.Material).Plural ?? f.Material} fills {Items.Several(f.Draught, root)}.", Style.TextItalic, Style.Caption, root == 0 ? Style.Bad : Style.InkDim, true));
            h.AddChild(words);
            slab.AddChild(h);
            return slab;
        }
        var q = Crafting.BuyFlask(X);
        if (Crafting.Line(crafter, "flask.sale") is { } sale)
            words.AddChild(Style.Label($"“{sale}”", Style.TextItalic, Style.Small, Style.Ink, true));
        words.AddChild(Style.Label(d.Description, Style.UiBold, Style.Small, new Color("#9ad8ff"), true));
        words.AddChild(Style.Label(Cost(q), Style.Ui, Style.Caption, q.Ok ? Style.Ink : Style.InkDim, true));
        if (!q.Ok) words.AddChild(Style.Label(q.Blocked!, Style.TextItalic, Style.Caption, Style.Bad, true));
        h.AddChild(words);
        var b = Press(Style.Button("Buy it", null, q.Ok, true), q, "flask");
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        h.AddChild(b);
        slab.AddChild(h);
        return slab;
    }

    /// <summary>Her bench (the forge's page in her place), or what she says while the Verge is still sick.</summary>
    Control Bench()
    {
        if (Crafting.Closed(crafter, G.Journey.Ctx, Verb.WorkIn) is { } shut)
            return Style.Panel(Style.Slab(12), Style.Label($"“{shut}”", Style.TextItalic, Style.Small, Style.InkDim, true));
        var slab = Style.Panel(Style.Slab(12));
        var h = Style.H(Style.Gap3);
        var into = Crafting.Rules.Materials.Where(m => m.Value.Crafter == crafter)
            .Select(m => $"{Items.Get(m.Key).Plural ?? m.Key} for {string.Join(" or ", m.Value.Into.Select(a => Items.Affix(a)?.Name ?? a))}");
        var words = Style.Label(Style.Cap1(string.Join("; ", into)) + ".", Style.Ui, Style.Small, Style.Ink, true);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        h.AddChild(words);
        var b = Style.Button("Her bench", () => { Sound.Sfx.Page(); G.Open($"forge:{crafter}"); }, false, true);
        b.SetMeta("nav_id", "bench");
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        h.AddChild(b);
        slab.AddChild(h);
        return slab;
    }

    /// <summary>The purse and what she works with, from the pouch.</summary>
    Control Purse()
    {
        var mats = Crafting.Brews(crafter).SelectMany(r => r.Takes.Keys).Concat(new[] { Crafting.Rules.Flask.Material }).Distinct()
            .Select(m => Inventory.Count(Ch, m) is int n && n > 0 ? Items.Several(m, n) : null).Where(s => s != null).ToList();
        var row = Style.H(18,
            Style.H(4, Glyphs.Icon("coin", 18, Style.GoldHi), Style.Label($"{Math.Floor(Ch.Gold)} gold", Style.UiBold, Style.Body, Style.GoldHi)),
            Style.Label(mats.Count == 0 ? "nothing for her in your pouch" : $"in your pouch: {string.Join(", ", mats)}", Style.Ui, Style.Small, Style.InkDim));
        row.Alignment = BoxContainer.AlignmentMode.Center;
        return row;
    }

    static string Cost(Quote q)
    {
        var parts = q.Takes.Select(kv => Items.Several(kv.Key, kv.Value)).ToList();
        if (q.Gold > 0) parts.Add($"{q.Gold} gold");
        return parts.Count == 0 ? "" : "Takes " + string.Join("  ·  ", parts);
    }

    Button Press(Button b, Quote q, string navId)
    {
        b.Disabled = !q.Ok;
        b.SetMeta("nav_id", navId);
        b.Pressed += () =>
        {
            if (!q.Ok) { Sound.Sfx.Deny(); return; }
            (q.Verb == Verb.Buy ? (Action)(() => Sound.Sfx.Loot(true)) : Sound.Sfx.Discovery)();
            if (G.Journey.Make(q)) Refresh();
        };
        return b;
    }
}

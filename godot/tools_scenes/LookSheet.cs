using System.Linq;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Tools;

/// <summary>Contact sheet of LookThumbs for her: every look per slot, the second row of each locked. OUT=png path, SIZE=px (96).</summary>
public partial class LookSheet : Control
{
    int frames;
    public override void _Ready()
    {
        int size = OS.GetEnvironment("SIZE") is { Length: > 0 } s ? int.Parse(s) : 96;
        var ch = Character.Create(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Sex = Sex.Female, Ability = "shield_bash", WeaponItem = Callings.Archetype("warden").Weapons[0] });
        LookThumbs.Her = ch;
        SetAnchorsPreset(LayoutPreset.FullRect);
        var bg = new ColorRect { Color = new Color("#1a1512"), AnchorRight = 1, AnchorBottom = 1 };
        AddChild(bg);
        var v = new VBoxContainer { Position = new Vector2(10, 10) };
        v.AddThemeConstantOverride("separation", 8);
        AddChild(v);
        foreach (var slot in Wardrobe.LookSlots)
        {
            foreach (bool locked in new[] { false, true })
            {
                var row = new HBoxContainer();
                row.AddThemeConstantOverride("separation", 6);
                foreach (var d in Wardrobe.All(ch, slot).Take(12)) row.AddChild(LookThumbs.For(d.Id, slot, size, locked));
                v.AddChild(row);
            }
        }
    }

    public override void _Process(double delta)
    {
        if (++frames < 400) return;
        GetViewport().GetTexture().GetImage().SavePng(OS.GetEnvironment("OUT"));
        GetTree().Quit();
    }
}

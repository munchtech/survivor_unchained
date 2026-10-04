using System;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The way in: the title at a fire on the Low Ford road, a stranger sitting
 * by it; making a survivor, who stands up beside the same fire and changes
 * as they are chosen; and from there one continuous shot into the game. */
public partial class Game
{
    PersonView? figure;
    string figureKey = "";
    CreationDraft? draft;
    static readonly Vector2 Fire = new(-10.5f, 90.5f);

    public void ShowTitle()
    {
        Mode = "title";
        inTransit = false;
        hudMode = null;
        hud.Draft(null);
        hud.Dialogue(null);
        hud.ShowPlay(false);
        var s = Stage("lowford");
        air.Set(Atmospheres.Night);
        s.View.SetNight(true);
        Seat(Stranger());
        PoseTitle(true);
        screens.Show(new TitleScreen(this));
        hud.Fade(0, 1.6);
    }

    /// <summary>The stranger at the title's fire: a hooded ranger, unarmed.</summary>
    static PersonSpec Stranger()
    {
        var a = Callings.Archetype("stalker");
        var ch = Character.Create(new CreationChoice { Name = "?", Archetype = "stalker", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = "hunting_bow", Ability = a.Abilities[0], Model = "rogue_hooded", Sex = Sex.Female });
        return Loadouts.Of(ch).Person;
    }

    void RemoveFigure()
    {
        figure?.QueueFree();
        figure = null;
        figureKey = "";
    }

    /// <summary>Someone on the log beside the fire, facing into it.</summary>
    void Seat(PersonSpec spec)
    {
        RemoveFigure();
        figure = new PersonView(spec, null, 0.8);
        scene!.AddChild(figure);
        float sx = Fire.X + 2.05f, sz = Fire.Y - 0.1f;
        figure.Place(sx + 0.12, scene.HeightAt(sx, sz) + 0.08, sz, -Math.PI / 2 - 0.12, true);
        figure.Loop("Sit_Chair_Idle", 0);
    }

    /// <summary>The survivor being made, standing by the fire as they are chosen.</summary>
    public void DressFigure(CreationDraft d)
    {
        if (d.LookKey == figureKey && figure != null) return;
        var was = figureKey.Split('|');
        bool changedBody = was.Length < 9 || was[0] != d.Archetype || was[1] != d.Model || was[8] != d.Sex.ToString();
        RemoveFigure();
        figureKey = d.LookKey;
        var ch = Character.Create(d.Choice() is var c && c.Name == "" ? WithName(c) : c);
        var lo = Loadouts.Of(ch);
        figure = new PersonView(lo.Person, new Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8);
        scene!.AddChild(figure);
        float x = Fire.X + 1.4f, z = Fire.Y + 1.0f;
        figure.Place(x, scene.HeightAt(x, z), z, Math.PI * 0.08, true);
        figure.Loop(lo.Arms.Idle, 0);
        if (changedBody) figure.Flourish(d.Archetype switch { "arcanist" => "Spell_Simple_Enter", "reaver" => "Sword_Regular_A", "warden" => "Sword_Block", _ => "Pistol_Shoot" });
    }

    static CreationChoice WithName(CreationChoice c) { c.Name = "Nameless"; return c; }

    /// <summary>Framings over the fire: the title's wide one, creation's portrait.</summary>
    void PoseTitle(bool snap = false)
    {
        float y = (float)scene!.HeightAt(Fire.X, Fire.Y);
        Pose(new Vector3(Fire.X + 7.5f, y + 3.2f, Fire.Y + 7.8f), new Vector3(Fire.X + 0.4f, y + 0.9f, Fire.Y - 0.4f), snap);
    }

    void PoseCreate()
    {
        float y = (float)scene!.HeightAt(Fire.X, Fire.Y);
        // The figure on the right third, the fire glowing at the left edge.
        Pose(new Vector3(Fire.X + 1.05f, y + 1.75f, Fire.Y + 7.0f), new Vector3(Fire.X + 0.95f, y + 1.0f, Fire.Y + 0.9f));
    }

    public void NewJourney()
    {
        Mode = "create";
        draft = new CreationDraft();
        // --new --sex female: creation opens on a woman (pictures of her).
        if (Args.Get("sex") == "female") draft.Sex = Sex.Female;
        if (Args.Get("archetype") is string arch)
        {
            var a = SurvivorUnchained.Rpg.Callings.Archetype(arch);
            draft.Archetype = arch; draft.WeaponItem = a.Weapons[0]; draft.Ability = a.Abilities[0]; draft.Palette = a.Palettes[0].Id; draft.Model = a.Model;
        }
        DressFigure(draft);
        PoseCreate();
        screens.Show(new CreateScreen(this, draft));
    }

    public void CancelCreation()
    {
        Mode = "title";
        draft = null;
        Seat(Stranger());
        PoseTitle();
        screens.Show(new TitleScreen(this));
    }

    /// <summary>From the portrait into the game, by the same fire.</summary>
    public void BeginJourney(CreationChoice c)
    {
        if (Mode != "create") return;
        Begin(c);
        draft = null;
        screens.Close();
        EnterZone("lowford", null, new Arrival(Fire.X + 1.4, Fire.Y + 1.0, Math.PI * 0.08));
        Save("new");
    }

    public void Continue(int slot)
    {
        var d = saves.Read(slot);
        if (d == null) { Toast(new Toast(ToastKind.Warning, "That journey could not be read.")); return; }
        screens.Close();
        hud.Fade(1, 0.5, d.Character.Name, $"Day {d.World.Day}");
        Wait(0.55, () =>
        {
            Journey = Journey.From(d, slot);
            Hook();
            // A journey kept on one of the old map runs comes back to the Wayfinder's table.
            if (d.Location.Zone == "map") EnterZone("waystation", null, Play.Zones.Waystation.AtTable);
            else EnterZone(d.Location.Zone, null, new Arrival(d.Location.X, d.Location.Z, d.Location.Facing));
            hud.Fade(0, 1.2);
        });
    }

    public void QuitToTitle()
    {
        Save("quit");
        screens.Close();
        hudMode = null;
        hud.Fade(1, 0.6);
        Wait(0.65, ShowTitle);
    }

    public void QuitGame()
    {
        if (Mode == "play") Save("quit");
        hud.Fade(1, 0.4);
        Wait(0.45, () => GetTree().Quit());
    }

    /// <summary>The autopilot at the title: through the notice, and a new journey.</summary>
    void AutoFront()
    {
        if (!Settings.Current.Mature) { Settings.Current.Mature = true; screens.Current?.Refresh(); return; }
        if (Mode == "title") NewJourney();
        else if (Mode == "create" && draft != null) { draft.Name = "Wren"; BeginJourney(draft.Choice()); }
    }
}

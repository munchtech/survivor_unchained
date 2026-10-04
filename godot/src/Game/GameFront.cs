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

    /// <summary>The survivor being made, standing by the fire as they are chosen.
    /// Her hair, skin, eyes, face and paint change on her where she stands (a
    /// face's slider moves as it is dragged); anything else builds the figure again.</summary>
    public void DressFigure(CreationDraft d)
    {
        if (d.LookKey == figureKey && figure != null) return;
        var ch = Character.Create(d.Choice() is var c && c.Name == "" ? WithName(c) : c);
        var lo = Loadouts.Of(ch);
        if (figure != null && d.BodyKey == figureBody && figure.Person.Body == "heroine")
        {
            figureKey = d.LookKey;
            People.HerRestyle(figure.Person, People.LookOf(lo.Person));
            return;
        }
        var was = figureBody.Split('|');
        bool changedBody = was.Length < 7 || was[0] != d.Archetype || was[1] != d.Model || was[6] != d.Sex.ToString();
        RemoveFigure();
        figureKey = d.LookKey;
        figureBody = d.BodyKey;
        figure = new PersonView(lo.Person, new Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8);
        scene!.AddChild(figure);
        float x = Fire.X + 1.4f, z = Fire.Y + 1.0f;
        figure.Place(x, scene.HeightAt(x, z), z, FigureHeading + figTurnNow, true);
        figure.Loop(lo.Arms.Idle, 0);
        if (changedBody) figure.Flourish(d.Archetype switch { "arcanist" => "Spell_Simple_Enter", "reaver" => "Sword_Regular_A", "warden" => "Sword_Block", _ => "Pistol_Shoot" });
    }

    string figureBody = "";
    const double FigureHeading = Math.PI * 0.08;
    // The figure turned (radians from how she stands) and brought near (0 all
    // of her, 0.55 head and shoulders, 1 her face): asked, and as it is now.
    float figTurn, figTurnNow, figZoom;
    CameraAttributesPractical? portrait;

    /// <summary>How near the figure is asked to be framed (0 all of her, 1 her face).</summary>
    public float FigureZoom => figZoom;

    /// <summary>Turned by so much and brought nearer or further (a drag, the wheel, the right stick).</summary>
    public void Turntable(float turn, float zoom)
    {
        figTurn += turn;
        figZoom = Mathf.Clamp(figZoom + zoom, 0, 1);
    }

    /// <summary>Framed for a step or a part of the look: so near, turned so far.</summary>
    public void FrameFigure(float zoom, float turn = 0)
    {
        figZoom = Mathf.Clamp(zoom, 0, 1);
        figTurn = turn;
    }

    /// <summary>Each frame of creation: the figure turned toward where she is asked to
    /// face, and the camera framing her as near as asked, her face held in the middle of
    /// the space between the column and the plate (a close portrait: a longer lens, the
    /// fire and the trees behind her softened).</summary>
    void UpdateCreate(double dt)
    {
        if (figure == null || scene == null || draft == null) return;
        figTurnNow = Mathf.Lerp(figTurnNow, figTurn, 1 - Mathf.Exp(-9f * (float)dt));
        figure.Rotation = new Vector3(0, (float)FigureHeading + figTurnNow, 0);
        float y = (float)scene.HeightAt(Fire.X, Fire.Y);
        Vector3 fullPos = new(Fire.X + 1.05f, y + 1.75f, Fire.Y + 7.0f), fullLook = new(Fire.X + 0.95f, y + 1.0f, Fire.Y + 0.9f);
        var eyes = People.EyesOf(figure.Person);
        var dir = new Vector3(fullPos.X - eyes.X, 0, fullPos.Z - eyes.Z).Normalized();
        // Head and shoulders, then her face: the look a little under the eyes, the lens longer.
        Vector3 bustLook = eyes + new Vector3(0, -0.26f, 0), faceLook = eyes + new Vector3(0, -0.035f, 0);
        Vector3 bustPos = bustLook + dir * 2.0f + new Vector3(0, 0.1f, 0), facePos = faceLook + dir * 0.95f + new Vector3(0, 0.015f, 0);
        float z = figZoom;
        Vector3 pos, look;
        float fov;
        if (z <= 0.55f)
        {
            float t = Smooth(z / 0.55f);
            pos = fullPos.Lerp(bustPos, t); look = fullLook.Lerp(bustLook, t); fov = Mathf.Lerp(34, 26, t);
        }
        else
        {
            float t = Smooth((z - 0.55f) / 0.45f);
            pos = bustPos.Lerp(facePos, t); look = bustLook.Lerp(faceLook, t); fov = Mathf.Lerp(26, 19, t);
        }
        Pose(pos, look, false, fov, Mathf.Lerp(1, 0.08f, Mathf.Clamp(z * 1.6f, 0, 1)));
        // A close portrait: what is behind her softened, the more the nearer.
        if (z > 0.05f)
        {
            portrait ??= new CameraAttributesPractical { DofBlurFarEnabled = true, DofBlurFarTransition = 2.5f };
            float dist = pos.DistanceTo(look);
            portrait.DofBlurFarDistance = dist + 0.5f + (1 - z) * 4;
            portrait.DofBlurAmount = 0.06f * z;
            camera.Attributes = portrait;
        }
        else if (camera.Attributes == portrait && portrait != null) camera.Attributes = null;

        static float Smooth(float t) { t = Mathf.Clamp(t, 0, 1); return t * t * (3 - 2 * t); }
    }

    /// <summary>Creation is over (begun or left): the camera as it was.</summary>
    void EndCreate()
    {
        figTurn = figTurnNow = figZoom = 0;
        figureBody = "";
        if (camera.Attributes == portrait) camera.Attributes = null;
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
        EndCreate();
        Seat(Stranger());
        PoseTitle();
        screens.Show(new TitleScreen(this));
    }

    /// <summary>From the portrait into the game, by the same fire.</summary>
    public void BeginJourney(CreationChoice c)
    {
        if (Mode != "create") return;
        EndCreate();
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
        else if (Mode == "create" && draft != null) { draft.Name = "Ashe"; BeginJourney(draft.Choice()); }
    }
}

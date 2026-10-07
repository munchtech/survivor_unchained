using System;
using System.Globalization;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// A crowd kind's role as a contact sheet, for judging the dead's and the
/// beasts' motion as the crowd draws it (tools_scenes/crowd_sheet.gd runs
/// it): the kind baked as the game bakes it (Vat.cs), then one body per cell
/// in a row, each a step further into the role, under a plain studio light.
/// VISUAL=its key (EnemyDef.Visual); ROLE=move|idle|attack|windup|cast|die|die2|die3|rise|hit, or several
/// comma-separated, taken in turn cell by cell;
/// N=cells; STEP=seconds between them; START=seconds; YAW=degrees each is
/// turned (90: seen from its side); YAWSTEP=degrees more for each cell; CELL=cell width in metres;
/// LIFT=the camera's elevation in degrees (the game's is 64); SIZE=metres the picture spans top to
/// bottom; LOOKY=the height it looks at; OUT=png.
/// </summary>
public partial class CrowdSheet : Node
{
    int wait = 8;
    SubViewport vp = null!;

    static string Env(string k, string d) => OS.GetEnvironment(k) is { Length: > 0 } v ? v : d;
    static float Num(string k, float d) => float.Parse(Env(k, d.ToString(CultureInfo.InvariantCulture)), CultureInfo.InvariantCulture);

    public override void _Ready()
    {
        // Drawn in a viewport of its own, whatever the project's window is.
        vp = new SubViewport { Size = new Vector2I((int)Num("W", 1800), (int)Num("H", 400)), RenderTargetUpdateMode = SubViewport.UpdateMode.Always,
            Msaa3D = Viewport.Msaa.Msaa4X, OwnWorld3D = true };
        AddChild(vp);
        var root = new Node3D();
        vp.AddChild(root);
        var asset = Vat.Of(Visuals.Of(Env("VISUAL", "wolf")), root);
        var crowd = new VatCrowd(asset);
        root.AddChild(crowd);
        int n = (int)Num("N", 8);
        float step = Num("STEP", 0.1f), start = Num("START", 0), yaw = Mathf.DegToRad(Num("YAW", 90)), yawStep = Mathf.DegToRad(Num("YAWSTEP", 0));
        float h = Math.Max(asset.Height, 0.6f), cell = Num("CELL", h * 1.1f);
        // Several roles (comma-separated) are taken in turn, cell by cell.
        var roles = Env("ROLE", "idle").Split(",");
        crowd.Begin();
        for (int i = 0; i < n; i++)
        {
            var at = new Transform3D(new Basis(Vector3.Up, yaw + i * yawStep), new Vector3((i - (n - 1) / 2f) * cell, 0, 0));
            crowd.Push(i, at, roles[i % roles.Length], start + i * step, 0, 0, 0, 0, Colors.White, 0);
        }
        crowd.End();
        // The floor, checked, so a foot that slides shows.
        var floor = new MeshInstance3D { Mesh = new PlaneMesh { Size = new Vector2(n * cell + 4, 8) } };
        floor.MaterialOverride = new StandardMaterial3D { AlbedoColor = new Color(0.55f, 0.55f, 0.57f), Roughness = 0.9f };
        root.AddChild(floor);
        var e = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Color, BackgroundColor = new Color(0.3f, 0.31f, 0.34f),
            AmbientLightSource = Godot.Environment.AmbientSource.Color, AmbientLightColor = new Color(0.7f, 0.7f, 0.75f), AmbientLightEnergy = 0.6f,
            TonemapMode = Godot.Environment.ToneMapper.Agx,
        };
        root.AddChild(new WorldEnvironment { Environment = e });
        root.AddChild(new DirectionalLight3D { RotationDegrees = new Vector3(-40, 30, 0), LightEnergy = 1.6f, ShadowEnabled = true });
        root.AddChild(new DirectionalLight3D { RotationDegrees = new Vector3(-15, -150, 0), LightEnergy = 0.7f });
        // Orthographic, from the front and a little above: every cell the same size.
        float w = n * cell, lift = Num("LIFT", 12);
        var cam = new Camera3D { Projection = Camera3D.ProjectionType.Orthogonal, Size = Num("SIZE", Math.Max(w * vp.Size.Y / vp.Size.X, h * 1.3f)), Current = true };
        root.AddChild(cam);
        var look = new Vector3(0, Num("LOOKY", h * 0.5f), 0);
        cam.GlobalPosition = look + new Vector3(0, Mathf.Sin(Mathf.DegToRad(lift)), Mathf.Cos(Mathf.DegToRad(lift))) * 20;
        cam.LookAt(look);
    }

    public override void _Process(double delta)
    {
        if (wait-- > 0) return;
        vp.GetTexture().GetImage().SavePng(Env("OUT", "user://crowd_sheet.png"));
        GD.Print("CROWDSHEET ", Env("OUT", ""));
        GetTree().Quit();
    }
}

using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Tools;

/// <summary>
/// Her looks side by side, for choosing them (tools_scenes/face_sheet.gd runs
/// it): the heroine built as the game builds her, then each look in a list
/// put on her where she stands (People.HerRestyle, as creation does) and
/// photographed in a plain studio light, a picture each.
/// SHEET=a JSON file: [{"name", "face": {slider: v}, "hair", "hairColor",
/// "eyes", "eyeRing", "paint", "skin"}, ...]; OUT=a folder; CAM=face, head or
/// body; YAW=degrees she is turned; CLIP=the clip she holds (its first frame).
/// </summary>
public partial class FaceSheet : Node3D
{
    People.Person? her;
    Camera3D? cam;
    MeshInstance3D? marker;
    readonly List<Godot.Collections.Dictionary> looks = new();
    int at = -1, wait;
    string outDir = "";

    public override void _Ready()
    {
        var sheet = Json.ParseString(FileAccess.GetFileAsString(OS.GetEnvironment("SHEET"))).AsGodotArray();
        foreach (var v in sheet) looks.Add(v.AsGodotDictionary());
        outDir = OS.GetEnvironment("OUT");
        DirAccess.MakeDirRecursiveAbsolute(outDir);
        var spec = new PersonSpec
        {
            Sex = SurvivorUnchained.Rpg.Sex.Female, Body = SurvivorUnchained.Play.Loadouts.HerBody,
            Outfit = new List<string> { "her:" + (OS.GetEnvironment("OUTFIT") is { Length: > 0 } o ? o : "warden") },
        };
        her = People.Build(spec);
        AddChild(her.Root);
        her.Root.RotationDegrees = new Vector3(0, OS.GetEnvironment("YAW") is { Length: > 0 } y ? float.Parse(y) : 0, 0);
        // Still: no blinking, eyes ahead; held in the first frame of a clip.
        foreach (var life in her.Skeleton.GetChildren().OfType<HerFaceLife>()) life.ProcessMode = ProcessModeEnum.Disabled;
        var clip = OS.GetEnvironment("CLIP") is { Length: > 0 } c ? c : "Idle_Loop";
        her.Anim.Play(People.Clip(her, clip));
        her.Anim.Seek(0.4, true);
        her.Anim.Pause();
        // REST=1: her skeleton as it was bound (no clip, nor her carriage).
        if (OS.GetEnvironment("REST") == "1")
        {
            her.Anim.Stop();
            her.Skeleton.ResetBonePoses();
            if (her.Pose != null) her.Pose.Active = false;
        }
        Studio();
    }

    void Studio()
    {
        var env = new WorldEnvironment();
        var e = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Color, BackgroundColor = new Color(0.16f, 0.15f, 0.15f),
            AmbientLightColor = new Color(0.6f, 0.6f, 0.65f), AmbientLightEnergy = 0.5f, TonemapMode = Godot.Environment.ToneMapper.Agx,
        };
        var sky = new Sky { SkyMaterial = new ProceduralSkyMaterial { GroundBottomColor = new Color(0.18f, 0.16f, 0.14f), GroundHorizonColor = new Color(0.45f, 0.42f, 0.4f) } };
        e.Sky = sky;
        e.ReflectedLightSource = Godot.Environment.ReflectionSource.Sky;
        env.Environment = e;
        AddChild(env);
        // (LIGHTS=kbfa: which lights shine, key, back, fill and the ambient sky; all by default)
        var on = OS.GetEnvironment("LIGHTS") is { Length: > 0 } l ? l : "kbfa";
        if (!on.Contains('a')) { e.AmbientLightEnergy = 0; e.ReflectedLightSource = Godot.Environment.ReflectionSource.Disabled; e.AmbientLightSource = Godot.Environment.AmbientSource.Disabled; }
        if (on.Contains('k')) AddChild(new DirectionalLight3D { RotationDegrees = new Vector3(-30, 35, 0), LightEnergy = 1.5f, ShadowEnabled = OS.GetEnvironment("NOSHADOW") != "1" });
        if (on.Contains('b')) AddChild(new DirectionalLight3D { RotationDegrees = new Vector3(-15, -150, 0), LightEnergy = 0.9f });
        if (on.Contains('f')) AddChild(new DirectionalLight3D { RotationDegrees = new Vector3(-10, -40, 0), LightEnergy = 0.35f, LightColor = new Color(1, 0.9f, 0.8f) });
        cam = new Camera3D { Fov = 22, Current = true };
        AddChild(cam);
    }

    public override void _Process(double delta)
    {
        if (her == null || cam == null) return;
        // Frame her face (between her eyes, as she stands now).
        var eyes = People.HerEyes(her);
        string view = OS.GetEnvironment("CAM") is { Length: > 0 } cv ? cv : "face";
        var (lift, dist) = view switch { "body" => (-0.85f, 5.6f), "head" => (-0.12f, 1.5f), _ => (-0.025f, 0.85f) };
        var look = eyes + new Vector3(0, lift, 0);
        cam.GlobalPosition = look + new Vector3(0, 0.0f, dist);
        cam.LookAt(look);
        if (OS.HasEnvironment("FSDEBUG") && marker == null)
        {
            marker = new MeshInstance3D { Mesh = new SphereMesh { Radius = 0.006f, Height = 0.012f }, MaterialOverride = new StandardMaterial3D { AlbedoColor = Colors.Red, ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded } };
            AddChild(marker);
        }
        if (marker != null) marker.GlobalPosition = eyes;
        if (OS.HasEnvironment("FSDEBUG"))
        {
            int hb = her.Skeleton.FindBone("Head");
            var em = her.Meshes.First(m => m.Name == "HeroineEyes");
            GD.Print($"FACESHEET eyes {eyes} headpose {her.Skeleton.GlobalTransform * her.Skeleton.GetBoneGlobalPose(hb).Origin} headrest {her.Skeleton.GetBoneGlobalRest(hb).Origin} skel {her.Skeleton.GlobalTransform} eyesmesh {em.GlobalTransform * em.GetAabb().GetCenter()}");
        }
        if (wait-- > 0) return;
        if (at >= 0)
        {
            var name = (string)looks[at]["name"];
            GetViewport().GetTexture().GetImage().SavePng($"{outDir}/{name}.png");
        }
        at++;
        if (at >= looks.Count) { GetTree().Quit(); return; }
        Put(looks[at]);
        wait = 6;
    }

    void Put(Godot.Collections.Dictionary d)
    {
        static Color? C(Godot.Collections.Dictionary d, string k) => d.ContainsKey(k) && (string)d[k] != "" ? new Color((string)d[k]) : null;
        var face = d.ContainsKey("face") ? d["face"].AsGodotDictionary().ToDictionary(kv => (string)kv.Key, kv => (float)kv.Value) : new Dictionary<string, float>();
        var look = new People.Look("female", new[] { "her:warden" }, d.ContainsKey("hair") ? (string)d["hair"] : "long", false,
            C(d, "hairColor"), C(d, "skin"), null, null, 1, face, C(d, "eyes"), C(d, "eyeRing"), d.ContainsKey("paint") ? (string)d["paint"] : null);
        People.HerRestyle(her!, look);
        // PLAIN=1: her skin a plain glossy grey, to judge her shape and its
        // normals without her paint.
        if (OS.HasEnvironment("FSDEBUG"))
            foreach (var mi in her!.Meshes)
                if (mi.Mesh is ArrayMesh am)
                {
                    var on = Enumerable.Range(0, am.GetBlendShapeCount()).Where(k => Mathf.Abs(mi.GetBlendShapeValue(k)) > 1e-4)
                        .Select(k => $"{am.GetBlendShapeName(k)}={mi.GetBlendShapeValue(k):F2}");
                    GD.Print($"FACESHEET mesh {mi.Name} shapes {am.GetBlendShapeCount()} mode {am.BlendShapeMode} on: {string.Join(" ", on)}");
                }
        // (HIDE=name,name: those of her meshes hidden)
        if (OS.GetEnvironment("HIDE") is { Length: > 0 } hide)
            foreach (var mi in her!.Meshes)
                if (hide.Split(',').Contains(mi.Name.ToString())) mi.Visible = false;
        // (PLAIN=2: her surface's normals as colours, unlit, to find a crease in them)
        if (OS.GetEnvironment("PLAIN") is "1" or "2")
        {
            Material plain = OS.GetEnvironment("PLAIN") == "1"
                ? new StandardMaterial3D { AlbedoColor = new Color(0.62f, 0.6f, 0.58f), Roughness = 0.35f }
                : new ShaderMaterial { Shader = new Shader { Code = "shader_type spatial; render_mode unshaded; void fragment() { ALBEDO = (INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz * 0.5 + 0.5; }" } };
            foreach (var mi in her!.Meshes.Where(m => !her.Hair.Contains(m)))
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    mi.SetSurfaceOverrideMaterial(s, plain);
        }
    }
}

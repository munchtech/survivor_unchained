using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// Creation's portraits (tools/assets/creation_portraits.py runs it through
/// tools_scenes/portraits.gd): the heroine built as the game builds her, each
/// look put on her where she stands (People.HerRestyle, as creation does) and
/// photographed square by a firelit portrait light: a warm key from the
/// fire's side, a cool fill, moonlight rimming her hair from behind.
/// JOBS=a JSON file: [{"name", "view": "bust"|"head"|"face", "yaw", "back", "chin", "seek", "outfit", "hair",
/// "hairColor", "face": {slider: v}, "eyes", "eyeRing", "paint", "skin"}, ...];
/// OUT=a folder; SIZE=pixels (square). A picture a job, saved when her hair
/// has settled and the frame has gathered (the hair is cut by hashed alpha,
/// which the TAA smooths over frames).
/// </summary>
public partial class Portraits : Node3D
{
    People.Person? her;
    string outfit = "";
    SubViewport? vp;
    Camera3D? cam;
    readonly List<Godot.Collections.Dictionary> jobs = new();
    int at = -1, wait;
    /// <summary>The moment of her idle she is held at, unless a job says otherwise.</summary>
    static readonly double Seek = OS.GetEnvironment("SEEK") is { Length: > 0 } sk ? double.Parse(sk, System.Globalization.CultureInfo.InvariantCulture) : 0.4;
    string outDir = "";

    public override void _Ready()
    {
        var list = Json.ParseString(FileAccess.GetFileAsString(OS.GetEnvironment("JOBS"))).AsGodotArray();
        foreach (var v in list) jobs.Add(v.AsGodotDictionary());
        outDir = OS.GetEnvironment("OUT");
        DirAccess.MakeDirRecursiveAbsolute(outDir);
        int size = OS.GetEnvironment("SIZE") is { Length: > 0 } s ? int.Parse(s) : 768;
        vp = new SubViewport
        {
            Size = new Vector2I(size, size), UseTaa = true, Msaa3D = Viewport.Msaa.Msaa4X, RenderTargetUpdateMode = SubViewport.UpdateMode.Always,
            ScreenSpaceAA = Viewport.ScreenSpaceAAEnum.Disabled,
        };
        AddChild(vp);
        cam = new Camera3D { Current = true };
        vp.AddChild(cam);
        Studio();
    }

    void Dress(string fit)
    {
        if (her != null) { her.Root.QueueFree(); her = null; }
        outfit = fit;
        her = People.Build(new SurvivorUnchained.World.PersonSpec
        {
            Sex = SurvivorUnchained.Rpg.Sex.Female, Body = SurvivorUnchained.Play.Loadouts.HerBody, Outfit = new List<string> { "her:" + fit },
        });
        AddChild(her.Root);
        // Still: no blinking, eyes ahead; held in a frame of her idle.
        foreach (var life in her.Skeleton.GetChildren().OfType<HerFaceLife>()) life.ProcessMode = ProcessModeEnum.Disabled;
        her.Anim.Play(People.Clip(her, "Idle_Loop"));
        Hold(0.4);
    }

    /// <summary>Held at a moment of her idle (one where she looks up and ahead).</summary>
    void Hold(double t)
    {
        if (her == null) return;
        her.Anim.Play(People.Clip(her, "Idle_Loop"));
        her.Anim.Seek(t, true);
        her.Anim.Pause();
    }

    /// <summary>Her chin lifted so many degrees (her idle carries her head a little low for a portrait).</summary>
    void Chin(float degrees)
    {
        if (her == null || degrees == 0) return;
        foreach (var (bone, share) in new[] { ("Neck", 0.4f), ("Head", 0.6f) })
        {
            int b = her.Skeleton.FindBone(bone);
            if (b < 0) continue;
            her.Skeleton.SetBonePoseRotation(b, her.Skeleton.GetBonePoseRotation(b) * new Quaternion(Vector3.Right, -Mathf.DegToRad(degrees * share)));
        }
    }

    void Studio()
    {
        var e = new Godot.Environment
        {
            BackgroundMode = Godot.Environment.BGMode.Color, BackgroundColor = new Color(0.085f, 0.066f, 0.058f),
            AmbientLightSource = Godot.Environment.AmbientSource.Color, AmbientLightColor = new Color(0.55f, 0.5f, 0.52f), AmbientLightEnergy = 0.2f,
            TonemapMode = Godot.Environment.ToneMapper.Agx, TonemapExposure = 1.0f,
            ReflectedLightSource = Godot.Environment.ReflectionSource.Sky,
            Sky = new Sky { SkyMaterial = new ProceduralSkyMaterial { SkyTopColor = new Color(0.18f, 0.2f, 0.28f), SkyHorizonColor = new Color(0.32f, 0.26f, 0.22f), GroundBottomColor = new Color(0.08f, 0.06f, 0.05f), GroundHorizonColor = new Color(0.3f, 0.22f, 0.16f) } },
        };
        AddChild(new WorldEnvironment { Environment = e });
    }

    /// <summary>The lights, set about her face for a view: the key warm from the
    /// camera's right and above (the fire), a cool fill from its left, and the
    /// moon behind her drawing an edge round her hair.</summary>
    readonly List<Light3D> lights = new();

    void Light(Vector3 eyes, Vector3 toCam)
    {
        if (lights.Count == 0)
        {
            lights.Add(new DirectionalLight3D { LightColor = new Color(1f, 0.8f, 0.62f), LightEnergy = 2.1f, ShadowEnabled = true, DirectionalShadowMode = DirectionalLight3D.ShadowMode.Orthogonal, ShadowBlur = 1.5f });
            lights.Add(new DirectionalLight3D { LightColor = new Color(0.62f, 0.7f, 0.92f), LightEnergy = 0.3f });
            lights.Add(new DirectionalLight3D { LightColor = new Color(0.78f, 0.86f, 1f), LightEnergy = 2.6f, LightSpecular = 0.7f });
            foreach (var l in lights) AddChild(l);
            // LIGHTS=k,f,r: each light's energy scaled (to judge them one at a time).
            if (OS.GetEnvironment("LIGHTS") is { Length: > 0 } ls)
                foreach (var (l, k) in lights.Zip(ls.Split(',').Select(x => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture))))
                    l.LightEnergy *= k;
        }
        // (short lighting: the key on the side of her face turned from the camera, which models it;
        // the fill on the side toward it; the rim behind the other shoulder)
        var side = Vector3.Up.Cross(toCam).Normalized();
        var from = new[] { toCam * 1.0f + side * 1.5f + Vector3.Up * 1.2f, toCam * 1.6f - side * 1.3f + Vector3.Up * 0.1f, -toCam * 1.6f - side * 0.5f + Vector3.Up * 1.1f };
        for (int i = 0; i < lights.Count; i++)
        {
            lights[i].GlobalPosition = eyes + from[i];
            lights[i].LookAt(eyes, Vector3.Up);
        }
    }

    public override void _Process(double delta)
    {
        if (vp == null || cam == null) return;
        // Aimed at her face as she stands now, until the last frames gather the picture.
        if (at >= 0 && at < jobs.Count && wait > 12) Frame(jobs[at]);
        if (wait-- > 0) return;
        if (at >= 0)
        {
            var name = (string)jobs[at]["name"];
            vp.GetTexture().GetImage().SavePng($"{outDir}/{name}.png");
            GD.Print($"PORTRAIT {name}");
        }
        at++;
        if (at >= jobs.Count) { GetTree().Quit(); return; }
        var job = jobs[at];
        // (one of her callings' own outfits, always: another name would build her bare)
        string fit = job.ContainsKey("outfit") && (string)job["outfit"] is "warden" or "reaver" or "arcanist" or "ranger" ? (string)job["outfit"] : "ranger";
        bool fresh = her == null || fit != outfit;
        if (fresh) Dress(fit);
        Put(job);
        Hold(job.ContainsKey("seek") ? (double)job["seek"] : Seek);
        Chin(job.ContainsKey("chin") ? (float)job["chin"] : 0);
        // (a new body needs its first frames to stand, her hair to fall still)
        wait = fresh ? 70 : 45;
    }

    void Frame(Godot.Collections.Dictionary job)
    {
        if (her == null || cam == null) return;
        her.Root.RotationDegrees = new Vector3(0, job.ContainsKey("yaw") ? (float)job["yaw"] : 0, 0);
        var eyes = People.HerEyes(her);
        string view = job.ContainsKey("view") ? (string)job["view"] : "face";
        // (the look a little under her eyes; how tall a slice of her the frame holds)
        var (lift, tall, dist) = view switch { "bust" => (-0.12f, 0.62f, 1.6f), "head" => (-0.06f, 0.4f, 1.5f), "eyes" => (0f, 0.12f, 1.3f), _ => (-0.03f, 0.26f, 1.3f) };
        // (a cut that hangs behind her, seen in profile: the frame moved back to hold it)
        float back = job.ContainsKey("back") ? (float)job["back"] : 0;
        var look = eyes + new Vector3(0, lift, 0) - her.Root.GlobalBasis.Z.Normalized() * back;
        var toCam = Vector3.Back;
        cam.GlobalPosition = look + toCam * dist;
        cam.LookAt(look);
        cam.Fov = Mathf.RadToDeg(2 * Mathf.Atan(tall / 2 / dist));
        Light(eyes, toCam);
    }

    void Put(Godot.Collections.Dictionary d)
    {
        static Color? C(Godot.Collections.Dictionary d, string k) => d.ContainsKey(k) && (string)d[k] != "" ? new Color((string)d[k]) : null;
        var face = d.ContainsKey("face") ? d["face"].AsGodotDictionary().ToDictionary(kv => (string)kv.Key, kv => (float)kv.Value) : new Dictionary<string, float>();
        var look = new People.Look("female", new[] { "her:" + outfit }, d.ContainsKey("hair") ? (string)d["hair"] : "long", false,
            C(d, "hairColor"), C(d, "skin"), null, null, 1, face, C(d, "eyes"), C(d, "eyeRing"), d.ContainsKey("paint") ? (string)d["paint"] : null);
        People.HerRestyle(her!, look);
    }
}

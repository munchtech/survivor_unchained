using System;
using System.Linq;
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
        // (the title and the Look hold the grade's whole toe: her irises and dark hair keep their colour (Atmospheres.Front))
        air.Set(Atmospheres.Front);
        s.View.SetNight(true);
        Seat(Stranger());
        PoseTitle(true);
        screens.Show(new TitleScreen(this));
        hud.Fade(0, 1.6);
    }

    /// <summary>The stranger at the title's fire: a ranger, bare-headed (her face and hair are the point; Loadout gives her no hood), unarmed.</summary>
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
        // (on the log (Camp's seat log, seed 1): her root brought `on` metres along her facing
        // and lowered `down`, so sit_log's glutes rest on the log's crown and her thighs on its
        // fire side (measured on the stalker's outfit: thighs 2 mm off, glutes 5 mm, cloth at
        // most 4 mm in), her boot soles on the ground (1 mm) and her feet clear of the log)
        double heading = -Math.PI / 2 - 0.12, on = 0.61, down = 0.18;
        figure.Place(sx + 0.12 + on * Math.Sin(heading), scene.HeightAt(sx, sz) + 0.08 - down, sz + on * Math.Cos(heading), heading, true);
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
        // (her chin: HerPose.ChinUp. 12 was set for the guard idle, whose head hung 17.8 deg face-down; the town idle
        // she loops here carries it level (+0.5 deg) on its own, and 12 would tip her face 11.5 deg up past the lens)
        if (figure.Person.Pose is HerPose hp) hp.ChinUp = 0f;
        scene!.AddChild(figure);
        // (where the camera looks: she stands in the middle of the screen, between creation's two
        // panels, the fire behind her at her right hand, in view between her and the choices)
        float x = Fire.X + 0.95f, z = Fire.Y + 1.0f;
        figure.Place(x, scene.HeightAt(x, z), z, FigureHeading + figTurnNow, true);
        figure.Loop(guardIdle = lo.Arms.Idle, 0);
        onLook = false;
        if (changedBody) figure.Flourish(d.Archetype switch { "arcanist" => "Spell_Simple_Enter", "reaver" => "Sword_Regular_A", "warden" => "Sword_Block", _ => "Pistol_Shoot" });
    }

    string figureBody = "";
    const double FigureHeading = Math.PI * 0.08;
    // The figure turned (radians from how she stands) and brought near (0 all
    // of her, 0.55 head and shoulders, 1 her face): asked, and as it is now.
    float figTurn, figTurnNow, figZoom;
    CameraAttributesPractical? portrait;
    // (--look-dof: the portrait's depth of field, off since 10 October 2026: blended
    // hair took the backdrop's depth and blurred, and the focus edge moved every frame)
    static readonly bool LookDof = Args.Has("look-dof");
    SpotLight3D? keyLight, bodyKey;

    /// <summary>How near the figure is asked to be framed (0 all of her, 1 her face).</summary>
    public float FigureZoom => figZoom;

    /// <summary>Turned by so much and brought nearer or further (a drag, the wheel, the right stick).</summary>
    public void Turntable(float turn, float zoom)
    {
        figTurn += turn;
        figZoom = Mathf.Clamp(figZoom + zoom, 0, 1);
    }

    /// <summary>The figure's weapon and shield shown or put away (away on creation's look screen).</summary>
    public void FigureArms(bool shown)
    {
        if (figure == null) return;
        // (the Look shows her town idle, sheathed: the guard idle's forward lean sank her head between her shoulders;
        // a flourish still playing finishes first, then the loop takes over, her pieces already away and out of sight)
        bool look = !shown && figure.Person.Own is { } own && own.Has($"idle_{figure.Person.Calling}_town");
        if (look != onLook)
        {
            onLook = look;
            figure.Sheathe(look);
            figure.Loop(look ? figure.Person.Own!.Prefix + $"idle_{figure.Person.Calling}_town" : guardIdle, 0.3);
            // (her arms nearer her body on the Look, eased with the crossfade: HerPose.LookArms. Measured on the town
            // idle, Body 5, 24 October 2026: upper arms 10.7 and 13.3 deg from her chest's line (were 20.8 and 43.6),
            // every skin gap 24 mm or more. Her left hand stays on her hip as the idle shaped it (roll 0): rolled out 8
            // it hung 6 cm off her hip against open ground at turn 40, and judge 10 preferred it back on the hip.
            // LookRollL/FanL/CurlL/ThumbL stay as try flags.)
            if (figure.Person.Pose is HerPose hp)
            {
                hp.LookOn = look;
                if (look) { hp.LookArmsDownR = 10f; hp.LookSwivelL = 31f; hp.LookRollL = 0f; hp.LookFanL = 0f; hp.LookCurlL = 0f; hp.LookThumbL = 0f; }
            }
        }
        figure.ShowHeld(shown);
    }

    string guardIdle = "";
    bool onLook;
    /// <summary>--look-pan M: the Look's framing pan (metres) tried at another value.</summary>
    static readonly float LookPan = Args.Has("look-pan") ? Args.Num("look-pan", 0.04f) : 0.04f;

    /// <summary>Framed for a step or a part of the look: so near, turned so far.</summary>
    public void FrameFigure(float zoom, float turn = 0)
    {
        // --fig-zoom Z, --fig-turn DEG: creation's figure framed and turned so, whatever the screen asks (pictures of her
        // whole stance on the look, its pieces put away).
        figZoom = Mathf.Clamp(Args.Has("fig-zoom") ? Args.Num("fig-zoom", 0f) : zoom, 0, 1);
        figTurn = Args.Has("fig-turn") ? Mathf.DegToRad((float)Args.Num("fig-turn", 0f)) : turn;
    }

    /// <summary>Each frame of creation: the figure turned toward where she is asked to
    /// face, and the camera framing her as near as asked, her face held in the middle of
    /// the space between the column and the plate (a close portrait: a longer lens, the
    /// fire and the trees behind her softened).</summary>
    void UpdateCreate(double dt)
    {
        if (figure == null || scene == null || draft == null) return;
        // --spin DEG: the turntable turned DEG a second, as a player holding the turn key (pictures of her hair turning).
        if (Args.Has("spin")) figTurn += Mathf.DegToRad((float)Args.Num("spin", 90)) * (float)dt;
        // --hairdump DIR: her hair and body as drawn, every 0.25 s from 2 s in, for posed_clip.py (HairDump).
        if (Args.Has("hairdump")) HairDump.Tick(figure, dt);
        figTurnNow = Mathf.Lerp(figTurnNow, figTurn, 1 - Mathf.Exp(-9f * (float)dt));
        figure.Rotation = new Vector3(0, (float)FigureHeading + figTurnNow, 0);
        float y = (float)scene.HeightAt(Fire.X, Fire.Y);
        Vector3 fullPos = new(Fire.X + 1.05f, y + 1.75f, Fire.Y + 7.0f), fullLook = new(Fire.X + 0.95f, y + 1.0f, Fire.Y + 0.9f);
        var eyes = People.EyesOf(figure.Person);
        var dir = new Vector3(fullPos.X - eyes.X, 0, fullPos.Z - eyes.Z).Normalized();
        // Head and shoulders, then her face: the look a little under the eyes, the lens longer.
        Vector3 bustLook = eyes + new Vector3(0, -0.16f, 0), faceLook = eyes + new Vector3(0, -0.05f, 0);
        // On the Look, the bust framing panned so she stands LookPan metres right of its middle (about 38 px at the
        // 0.45 framing): her town idle's right forearm ran under creation's left panel. Faded with her turn (none
        // with her back to the camera) and with the Look's ease (HerPose.LookWeight); her face framing keeps none.
        if (figure.Person.Pose is HerPose lp && lp.LookWeight > 0)
            bustLook -= (-dir).Cross(Vector3.Up).Normalized() * LookPan * lp.LookWeight * Mathf.Max(0, Mathf.Cos(figTurnNow));
        Vector3 bustPos = bustLook + dir * 1.75f + new Vector3(0, 0.08f, 0), facePos = faceLook + dir * 1.3f + new Vector3(0, 0.02f, 0);
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
            pos = bustPos.Lerp(facePos, t); look = bustLook.Lerp(faceLook, t); fov = Mathf.Lerp(26, 20, t);
        }
        Pose(pos, look, false, fov, Mathf.Lerp(1, 0.08f, Mathf.Clamp(z * 1.6f, 0, 1)));
        PortraitLight(dt, eyes, dir, z, y);
        // A close portrait: what is behind her softened, the more the nearer.
        if (z > 0.05f && LookDof)
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

    SpotLight3D? fillLight, edgeLight, rimLight, bounceLight, lookBodyRim;
    static float LookBodyRim => Args.Num("look-body-rim", 2.5f);   // (Body 20 light judge, max: ADOPT at the Look: her body no longer muddy and darker than her face; --look-body-rim 0 = before)
    // --key-aim Y: the key's aim over her eyes (metres; -0.05 as before face 34), --key-falloff E (see the key).
    // --key-body S: the key's share on its broad cone (bodyKey; 1: all of it, as before face 34).
    // (Face 34: the key's own cone 4.5 degrees (about 18 cm at her), its edge falloff 1.5, aimed 2 cm under her eyes, a quarter
    // of its light on the broad cone: her chest down the frame 77-79 to 69-63 Oklab L, her face within 2 of before (forehead
    // 84.0 to 83.2, cheeks 75.8/73.4 to 74.3/71.4); at 7 degrees it still lit her chest at her face's level (72-75).)
    // --key-face-gain G: the key's own cone's light against its share (with a quarter on the broad cone her shade cheek fell 3 L).
    static readonly float KeyFaceGain = Args.Num("key-face-gain", 1.2f);
    static readonly float KeyCone = Args.Num("key-cone", 4.5f);
    static readonly float KeyAim = Args.Num("key-aim", -0.02f), KeyFalloff = Args.Num("key-falloff", 1.5f), KeyBody = Args.Num("key-body", 0.25f);
    static readonly Color BodyWarm = Args.Get("key-body-colour") is string bwc && bwc.Split(',') is { Length: 3 } bw
        ? new Color(float.Parse(bw[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(bw[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(bw[2], System.Globalization.CultureInfo.InvariantCulture))
        : new Color(1f, 0.9f, 0.82f);
    float bounce = -1;
    float ambientBase = -1;
    Vector2 bounceAt = new(1.3f, 1.0f);
    Vector2? keyAt;
    // (Body 5, judge 10: the broad cone from high over the lens, 0.55 m aside and 3.0 m up, a "butterfly" light that gives
    // her yoke and collarbones form; the face's own cone stays where it was and her face reads unchanged. --body-key-at
    // SIDE,UP tries another; --body-key-at off puts it back on the face key's position)
    static readonly Vector2? BodyKeyAt = Args.Get("body-key-at") is string bk
        ? (bk.Split(',') is [var bx, var by] ? new Vector2(float.Parse(bx, System.Globalization.CultureInfo.InvariantCulture), float.Parse(by, System.Globalization.CultureInfo.InvariantCulture)) : null)
        : new Vector2(0.55f, 3.0f);
    static readonly bool LookReflOff = Args.Get("look-refl") == "off";
    float[]? rig;
    OmniLight3D? herFire, fireSrc;
    uint fireMask;

    /// <summary>
    /// Her light as she is made: a portrait's three points, coming up as the camera comes near,
    /// so a face is judged by the light faces are judged in. The whole figure keeps the fire's
    /// light as the scene has it; at head and shoulders and nearer:
    ///   - the key, soft and frontal, a little above her eyes and to the side away from the fire;
    ///   - a gentle fill from the fire's side, cooler, so the far side of her face never falls to black;
    ///   - the fire's orange off her face, kept only as a warm edge along her cheek and hair on its side;
    ///   - a faint cool rim from behind on the other side, to lift her off the dark trees.
    /// The rig lights only the figure (layer 2): the camp keeps its own light.
    /// </summary>
    void PortraitLight(double dt, Vector3 eyes, Vector3 dir, float z, float ground)
    {
        static float Smooth(float t) { t = Mathf.Clamp(t, 0, 1); return t * t * (3 - 2 * t); }
        // How much of the portrait's light: none for her whole figure, all of it from head and shoulders in.
        float p = Smooth((z - 0.15f) / 0.45f);
        // (her head's tones fitted under this rig, as much as it lights her: People.HerLookRig)
        if (figure?.Person is { } herRig) People.HerLookRig(herRig, p);
        float k = 1 - Mathf.Exp(-4f * (float)dt);
        var camLeft = dir.Cross(Vector3.Up).Normalized();
        SpotLight3D Spot(Color c, float angle, bool shadow, float specular)
        {
            var l = new SpotLight3D
            {
                LightColor = c, SpotAngle = angle, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = shadow,
                LightSize = shadow ? 0.6f : 0, ShadowBlur = 1.5f, LightSpecular = specular, LightCullMask = 2, LightEnergy = 0,
            };
            scene!.AddChild(l);
            return l;
        }
        void Aim(Light3D l, Vector3 at, Vector3 target, float energy)
        {
            l.GlobalPosition = at;
            l.LookAt(target);
            l.LightEnergy = Mathf.Lerp(l.LightEnergy, energy, k);
        }
        // (--rig-white: every light of the rig white, a face's colours judged
        // as a studio's light shows them, not only in the fire's warmth)
        bool white = Args.Has("rig-white");
        if (keyLight == null)
        {
            // (a smaller source than the others: at 0.6 m its soft shadow washed out the shade under her jaw (jaw 0.06
            // lighter than the portraits'), and its highlight on a polished pauldron was a broad patch blown to white;
            // its sheen 0.3, not 0.45, for the same patch, her skin's sheen as it was to the eye)
            var keyC = new Color(1f, 0.93f, 0.86f);
            // (--key-colour R,G,B: its colour, for judging it (pictures))
            if (Args.Get("key-colour") is string kcs && kcs.Split(',') is { Length: 3 } kp)
                keyC = new Color(float.Parse(kp[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(kp[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(kp[2], System.Globalization.CultureInfo.InvariantCulture));
            keyLight = Spot(white ? Colors.White : keyC, KeyCone, true, 0.3f);
            keyLight.LightSize = 0.3f;
            // (--key-spec X: its highlight's strength, for judging it (pictures))
            if (Args.Get("key-spec") is string kss) keyLight.LightSpecular = float.Parse(kss, System.Globalization.CultureInfo.InvariantCulture);
            // (--key-cone ANGLE: its cone's half angle, for judging it (pictures))
            // (--key-falloff E: its cone's edge falloff (Godot's spot_angle_attenuation), for judging it (pictures))
            keyLight.SpotAngleAttenuation = KeyFalloff;
            // --key-shadow off | SIZE: the key's shadow off, or its light size (softness), for judging what it casts (pictures).
            if (Args.Get("key-shadow") is string ks)
            {
                if (ks == "off") { keyLight.ShadowEnabled = false; keyLight.LightSize = 0; }
                else if (float.TryParse(ks, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var sz)) keyLight.LightSize = sz;
            }
            // The key's body share (face 34): the same lamp, its old broad cone, at KeyBody of the key's light, the rest in
            // the key's own narrow cone on her face. Under one broad key her neck and chest took as much light as her face,
            // high on the tone curve's shoulder, where their relief (the neck's turn, collarbones, the notch) flattened to a
            // featureless peach plane.
            // (Warmer than the key (--key-body-colour R,G,B): lit by it alone, at L 63-69 her chest's chroma fell 7.2-9.3 to 5.6-5.9, grey
            // beside her face's 8.6, the cool rim and the neutral fill showing there once the key no longer drowned them.)
            var bodyC = white ? Colors.White : keyLight.LightColor * BodyWarm;
            bodyKey = Spot(bodyC, 20, keyLight.ShadowEnabled, keyLight.LightSpecular);
            bodyKey.LightSize = keyLight.LightSize;
        }
        // The fill is near white: cool, it turned the shade under her jaw grey; warm (1/0.95/0.9), with a strong warm
        // bounce, it gave every face a fake tan (cheek chroma 25-43% over its portrait, judge j1). A faint warm bounce
        // from below (her chest and collar giving back the key) and a rim whose sheen is half its light (at full, a
        // lilac sheen along her collar). (--rig-old: the rig before, for pictures.)
        bool old = Args.Has("rig-old");
        // (--fill-colour R,G,B: the fill's colour for judging it (pictures))
        var fillC = old ? new Color(0.88f, 0.92f, 1f) : new Color(1f, 0.98f, 0.96f);
        if (Args.Get("fill-colour") is string fcs && fcs.Split(',') is { Length: 3 } fp)
            fillC = new Color(float.Parse(fp[0], System.Globalization.CultureInfo.InvariantCulture),
                float.Parse(fp[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(fp[2], System.Globalization.CultureInfo.InvariantCulture));
        fillLight ??= Spot(white ? Colors.White : fillC, 26, false, 0.1f);
        edgeLight ??= Spot(white ? Colors.White : new Color(1f, 0.56f, 0.26f), 24, false, 0.35f);
        if (rimLight == null)
        {
            // The rim casts her shadow: without one it lit the far side of her neck under her jaw through her jaw and
            // head, a cool grey-lilac band there on the fair faces (the owner, 10 October 2026; skin r13 B1b). Soft
            // (Spot's 0.6 m at 2.2 m from her), so her jaw's shadow on her neck has no hard edge. (--rim-shadow off |
            // SIZE: none, as r12, or another light size, for judging it (pictures).)
            // (--rim-colour R,G,B: its colour, for judging it (pictures))
            var rimC = new Color(0.72f, 0.82f, 1f);
            if (Args.Get("rim-colour") is string rcs && rcs.Split(',') is { Length: 3 } rp)
                rimC = new Color(float.Parse(rp[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(rp[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(rp[2], System.Globalization.CultureInfo.InvariantCulture));
            rimLight = Spot(white ? Colors.White : rimC, 24, true, old ? 0.5f : 0.25f);
            if (Args.Get("rim-shadow") is string rsh)
            {
                if (rsh == "off") { rimLight.ShadowEnabled = false; rimLight.LightSize = 0; }
                else if (float.TryParse(rsh, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var rsz)) rimLight.LightSize = rsz;
            }
        }
        // (--bounce E: a warm light from below, as her chest and collar give back the key, for judging it (pictures);
        // --ssao off | RADIUS,INTENSITY: the world's ambient occlusion at the Look, likewise)
        if (bounce < 0)
        {
            bounce = old ? 0 : 0.045f;
            if (Args.Get("bounce") is string bs && bs.Split(',') is { } bp)
            {
                float F(int i, float d) => i < bp.Length ? float.Parse(bp[i], System.Globalization.CultureInfo.InvariantCulture) : d;
                bounce = F(0, 0); bounceAt = new Vector2(F(1, 1.3f), F(2, 1.0f));
            }
            if (Args.Get("ssao") is string so)
            {
                if (so == "off") air.Env.SsaoEnabled = false;
                else if (so.Split(',') is [var sr, var si])
                {
                    air.Env.SsaoRadius = float.Parse(sr, System.Globalization.CultureInfo.InvariantCulture);
                    air.Env.SsaoIntensity = float.Parse(si, System.Globalization.CultureInfo.InvariantCulture);
                }
            }
        }
        if (bounce > 0) bounceLight ??= Spot(white ? Colors.White : new Color(1f, 0.74f, 0.58f), 30, false, 0f);
        // --rig K,F,E,R: the four lights' strengths at the face, for judging them (pictures).
        if (rig == null)
        {
            rig = new[] { 1.3f, 0.22f, 0.8f, 0.55f };
            if (Args.Get("rig") is string rs)
                foreach (var (v, i) in rs.Split(',').Select((v, i) => (v, i)))
                    if (i < 4 && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f)) rig[i] = f;
        }
        // The key high and near the lens, as the portraits are lit: their catchlights sit at 11 to 1 o'clock and
        // their jaws fall into shade (from 28 degrees to the side and 22 up, ours sat at 10 to 11 and the jaw lit).
        // (--key-at SIDE,UP: its offsets for judging it (pictures))
        if (keyAt == null)
        {
            keyAt = new Vector2(0.55f, 1.25f);
            if (Args.Get("key-at") is string ka && ka.Split(',') is [var kx, var ky])
                keyAt = new Vector2(float.Parse(kx, System.Globalization.CultureInfo.InvariantCulture), float.Parse(ky, System.Globalization.CultureInfo.InvariantCulture));
        }
        // (the whole figure's 0.15 on the broad cone, as before)
        var keyPos = eyes + dir * 1.9f - camLeft * keyAt.Value.X + Vector3.Up * keyAt.Value.Y;
        Aim(keyLight, keyPos, eyes + Vector3.Up * KeyAim, rig[0] * p * (1 - KeyBody) * KeyFaceGain);
        // (--body-key-at SIDE,UP: the broad cone alone from elsewhere, the face's own cone left where it is: a steeper,
        // wider body light rakes her collarbones, which the key's lens-near angle lit flat (pictures, Body 5))
        var bodyPos = BodyKeyAt is { } bka ? eyes + dir * 1.9f - camLeft * bka.X + Vector3.Up * bka.Y : keyPos;
        if (bodyKey != null) Aim(bodyKey, bodyPos, eyes + Vector3.Down * 0.05f, 0.15f + rig[0] * p * KeyBody);
        Aim(fillLight, eyes + dir * 1.8f + camLeft * 1.1f, eyes + Vector3.Down * 0.08f, rig[1] * p);
        // (1.3 m over her eyes: at 0.35 it grazed her jaw's silhouette, a warm line along it and orange under Sunborn's
        // jaw, judge j6; --edge-up U: another height, for judging it (pictures))
        float edgeUp = Args.Get("edge-up") is string eu ? float.Parse(eu, System.Globalization.CultureInfo.InvariantCulture) : 1.3f;
        Aim(edgeLight, eyes - dir * 1.3f + camLeft * 1.4f + Vector3.Up * edgeUp, eyes + Vector3.Down * 0.1f, rig[2] * p);
        Aim(rimLight, eyes - dir * 1.6f - camLeft * 1.0f + Vector3.Up * 1.1f, eyes + Vector3.Down * 0.12f, rig[3] * p);
        if (bounceLight != null) Aim(bounceLight, eyes + dir * bounceAt.X + Vector3.Down * bounceAt.Y, eyes + Vector3.Down * 0.14f, bounce * p);
        // --look-body-rim E (Body 20 light test, 27 Oct): a soft rim on her skin from behind, on the rim's side, at her upper
        // arms' height, so her arms' outline and broad planes read (0: off, as before 27 Oct). --look-body-rim-side S (m to her
        // left of the lens's line; negative: the other side), --look-body-rim-up U (m from her eyes).
        if (LookBodyRim > 0)
        {
            lookBodyRim ??= Spot(white ? Colors.White : new Color(1f, 0.93f, 0.84f), 30, false, 0.2f);
            lookBodyRim.LightCullMask = 2 | SurvivorUnchained.View.PlayerView.HerLayer;
            Aim(lookBodyRim, eyes - dir * 1.6f - camLeft * Args.Num("look-body-rim-side", 1.6f) + Vector3.Up * Args.Num("look-body-rim-up", 0.3f), eyes + Vector3.Down * 0.45f,
                LookBodyRim * Mathf.Clamp(p / 0.74f, 0, 1));   // (as judged at zoom 0.45 (p 0.74) and closer; it fades with the rig toward her whole figure)
        }
        // The sky's own light (the moon) off her from head and shoulders in: the
        // portrait's lights are hers there. Left on, it was a fourth light, cold
        // and flat across her face, and its reflection a white blob as big as her
        // pupil on the lower edge of each iris.
        air.Key.LightCullMask = p > 0.5f ? air.Key.LightCullMask & ~(2u | Brush.MaskLayer) : air.Key.LightCullMask | 2u;
        // Embers and smoke kept out of the space between the lens and her (an ember drifting there was a soft
        // orange disc over her neck), from head and shoulders in.
        Campfire.ClearNear(p > 0.01f ? p * (camera.GlobalPosition.DistanceTo(eyes) + 0.05f) : 0);
        // (--look-refl off: the sky's reflections off at the Look, to find what blows her armour's highlights (pictures))
        if (LookReflOff) air.Env.ReflectedLightSource = p > 0.5f ? Godot.Environment.ReflectionSource.Disabled : Godot.Environment.ReflectionSource.Sky;
        // (--look-ambient X: the sky's ambient light times X at the Look, for judging what greys the shade under her jaw (pictures))
        if (Args.Get("look-ambient") is string la)
        {
            if (ambientBase < 0) ambientBase = air.Env.AmbientLightEnergy;
            air.Env.AmbientLightEnergy = ambientBase * Mathf.Lerp(1f, float.Parse(la, System.Globalization.CultureInfo.InvariantCulture), p);
        }

        // The fire lights her through a stand-in that fades as the portrait comes up; the fire
        // itself no longer reaches her (layer 2), so the camp around her stays as it is.
        if (fireSrc == null && scene!.View.LightNear(new Vector3(Fire.X, ground, Fire.Y), 4) is { } src)
        {
            fireSrc = src;
            fireMask = src.LightCullMask;
            src.LightCullMask = fireMask & ~(2u | Brush.MaskLayer);
            herFire = new OmniLight3D
            {
                LightColor = src.LightColor, OmniRange = src.OmniRange, OmniAttenuation = src.OmniAttenuation,
                ShadowEnabled = src.ShadowEnabled, LightSpecular = src.LightSpecular, LightCullMask = 2,
            };
            scene.AddChild(herFire);
        }
        if (herFire != null && fireSrc != null && IsInstanceValid(fireSrc))
        {
            herFire.GlobalPosition = fireSrc.GlobalPosition;
            herFire.LightColor = fireSrc.LightColor;
            herFire.LightEnergy = fireSrc.LightEnergy * (1 - p);
        }
    }

    /// <summary>Creation is over (begun or left): the camera and the fire as they were.</summary>
    void EndCreate()
    {
        figTurn = figTurnNow = figZoom = 0;
        figureBody = "";
        foreach (var l in new Light3D?[] { keyLight, bodyKey, fillLight, edgeLight, rimLight, bounceLight, lookBodyRim, herFire }) l?.QueueFree();
        keyLight = bodyKey = fillLight = edgeLight = rimLight = bounceLight = lookBodyRim = null;
        air.Key.LightCullMask |= 2u;                       // (the sky's light on her again)
        if (figure?.Person is { } herRig) People.HerLookRig(herRig, 0);
        Campfire.ClearNear(0);
        herFire = null;
        if (fireSrc != null && IsInstanceValid(fireSrc)) fireSrc.LightCullMask = fireMask;
        fireSrc = null;
        if (camera.Attributes == portrait) camera.Attributes = null;
        LookView(false);
    }

    /// <summary>The Look's own smoothing on or off (Graphics.AtLook).</summary>
    void LookView(bool on)
    {
        if (Graphics.AtLook == on) return;
        Graphics.AtLook = on;
        Graphics.Apply(Settings.Current, air, GetViewport(), scene);
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
        LookView(true);
        draft = new CreationDraft();
        // --new --sex female: creation opens on a woman (pictures of her).
        if (Args.Get("sex") == "female") draft.Sex = Sex.Female;
        else if (Args.Get("sex") == "male") draft.SetSex(Sex.Male);
        if (Args.Get("archetype") is string arch)
        {
            var a = SurvivorUnchained.Rpg.Callings.Archetype(arch);
            draft.Archetype = arch; draft.WeaponItem = a.Weapons[0]; draft.Ability = a.Abilities[0]; draft.Palette = a.Palettes[0].Id; draft.Model = a.Model;
        }
        // --step N --part N (pictures of a screen, 0 or 1, and of its group: the calling's 0 calling, 1 arms,
        // 2 origin; the look's 0 her face, 1 her hair).
        if (Args.Get("step") is string st && int.TryParse(st, out var sn)) draft.Step = Math.Clamp(sn, 0, 1);
        if (Args.Get("part") is string pt && int.TryParse(pt, out var pn)) draft.Section = pn;
        // --face slider=v,slider=v (pictures of a face shaped so), --hair ID
        if (Args.Get("face") is string fc)
            foreach (var kv in fc.Split(',', StringSplitOptions.RemoveEmptyEntries))
                if (kv.Split('=') is [var k, var v] && double.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var x))
                    draft.Face[k] = x;
        if (Args.Get("hair") is string hs) draft.HairStyle = hs;
        // --hair-colour ID: pictures of her with that hair (and brows) colour.
        if (Args.Get("hair-colour") is string hc) draft.Hair = hc;
        // --hair-highlight HEX|default: her hair's highlights (Game.HighlightArg).
        if (Game.HighlightArg() is string hl) draft.HairHighlight = Args.Get("hair-highlight") is "default" or "auto" ? Lore.HighlightAuto : hl;
        // --preset ID: one of her faces to start from (its sliders and painting); --skin ID, --eyes ID
        if (Args.Get("preset") is string ps && Loadouts.HeroKit(draft.Sex)?.Faces.FirstOrDefault(f => f.Id == ps) is { } pf)
        {
            draft.FaceShape = pf.Id;
            foreach (var kv in pf.Shape) draft.Face.TryAdd(kv.Key, kv.Value);
            // (its own skin, as the Look's Choose gives it when none is picked: without it Sunborn shot on Fair)
            if (pf.Skin is { } fs && SurvivorUnchained.World.Lore.Skins.Any(s => s.Id == fs)) draft.Skin = fs;
        }
        if (Args.Get("skin") is string sk) draft.Skin = sk;
        if (Args.Get("eyes") is string ey) draft.Eyes = ey;
        // --paint ID: the paint on her face (Lore.Hero's paints: none, kohl, woad...).
        if (Args.Get("paint") is string pa) draft.Paint = pa;
        DressFigure(draft);
        PoseCreate();
        // --look-time day|dawn|dusk: the Look in that light, not the fire's night (pictures of her hair by day).
        if (Args.Get("look-time") is string lt && lt != "night" && scene != null)
        {
            air.Set(Atmospheres.ByName(lt));
            scene.SetNight(false);
        }
        var create = new CreateScreen(this, draft);
        screens.Show(create);
        create.FrameForStep();
        // --turn DEGREES: the figure turned so far on the turntable (pictures of her from the side).
        if (Args.Get("turn") is string tn && double.TryParse(tn, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var deg))
            Turntable(Mathf.DegToRad((float)deg), 0);
        // --zoom Z: framed so near (0 all of her, 0.55 head and shoulders, 1 her face), in the portrait's light from
        // head and shoulders in (pictures of her skin at the bust).
        if (Args.Has("zoom")) figZoom = Mathf.Clamp(Args.Num("zoom", figZoom), 0, 1);
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
        if (Mode != "create" || beginning) return;
        // The storybook first, when there is one (GameStory).
        if (OpensOnStory) { BeginWithStory(c); return; }
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

    /// <summary>--load FILE: a journey read from a save file as it stands (pictures of a later day:
    /// the journal written, people met), and never saved over (Save keeps out of it).</summary>
    void LoadFile(string path)
    {
        var d = Saves.Parse(System.IO.File.ReadAllText(path));
        if (d == null) return;
        Journey = Journey.From(d, 0);
        Hook();
        EnterZone(d.Location.Zone == "map" ? "waystation" : d.Location.Zone, null, new Arrival(d.Location.X, d.Location.Z, d.Location.Facing));
        hud.Fade(0, 0.5);
    }

    public void QuitToTitle()
    {
        Save("quit");
        screens.Close();
        hudMode = null;
        // (notices held over a fall or a chest are not carried into the next journey)
        hud.HoldToasts = false;
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

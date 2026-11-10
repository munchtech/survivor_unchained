using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.World;

/* A zone as data: what tools/godot/export_zone.mjs writes from the web game's
 * build of it into data/zones/<id>/zone.json and heights.bin. The view builds
 * the place from the rest of the files; this is what the game's logic reads:
 * the ground's heights, the colliders (with the ids the runtime refers to),
 * where the survivor starts, the lights and fires the runtime lights and puts
 * out, the named places and paths, and what the map is drawn from. */

public readonly record struct XZ(double X, double Z);

public sealed class Start
{
    public double X, Z, Facing;
}

public sealed class LightDef
{
    public double X, Y, Z;
    public string Color = "#ffffff";
    public double Intensity, Distance, Flicker;
    public bool On;
    /// <summary>Metres: the radius of a small bright glow drawn at the light while it is on (a board lamp's lantern
    /// flame, Maps/ArenaBoard.cs); 0 for none.</summary>
    public double Core;
    /// <summary>The landmark nodes that glow with it (shown while it is on).</summary>
    public List<string> Glow = new();
}

public sealed class FireDef
{
    public double X, Y, Z, Size;
    /// <summary>The light it burns with (an index into the lights): a fire
    /// burns while its light is on.</summary>
    public int Light;
    /// <summary>In a ring of stones (a campfire); without, a fire where it caught (a deadfall).</summary>
    public bool Ring = true;
}

public sealed class Point3
{
    public double X, Y, Z;
}

public sealed class ColliderDef
{
    public int Id;
    public ColliderKind Kind;
    public double X, Z, R, Hw, Hd, Rot;
    public string? Tag;
    public bool Soft, PlayerOnly;
}

public sealed class ZoneMapDef
{
    /// <summary>[kind, x, z, scale] per tree and rock, for the map.</summary>
    public List<JsonElement> Flora = new();
    public JsonElement? Extent;
    public List<JsonElement> Buildings = new();
}

public sealed class WaterMaskDef
{
    /// <summary>n by n cells over the zone, a byte each, 1 where there is water.</summary>
    public int N;
    public string Bits = "";
}

/// <summary>The light, air and colour of a moment of the day (the web game's
/// render/atmosphere.ts): colours as sRGB hex.</summary>
public sealed record SkySettings(string Top, string Horizon, string Bottom, string Glow, double GlowPower, double Stars, double Moon);

public sealed record GradeSettings(double[] Lift, double[] Gamma, double[] Gain, string ShadowTint, string HighlightTint,
    double TintStrength, double Saturation, double Vibrance, double Contrast)
{
    /// <summary>How much of the shadow tint's darkening is held off in the toe (0 to 1): the tint stays a colour there,
    /// so dark values (an iris, dark hair, unlit ground) keep their detail instead of falling to black.</summary>
    public double Toe { get; init; }
    /// <summary>The moon's colour over what it lights (0: none; play's own grades, E1 round 3): a weakly coloured pixel
    /// (moonlit grass, stone, a slate shade) gives up MoonDrop of its own chroma and takes MoonSat of lightness in the
    /// moon's hue (Oklab degrees); one coloured past MoonLo..MoonHi (C/L: a fire, her ember's pool, skin by it) keeps its
    /// own. Faded out over lightness MoonTop - MoonWidth..MoonTop (Oklab L), so at dawn it cools the shade only. After the
    /// warm-hue hold and the toe's: they kept the khaki of olive grass and the brown of the shade under a blue moon.</summary>
    public double Moon { get; init; }
    public double MoonHue { get; init; } = 250;
    public double MoonSat { get; init; } = 0.06;
    public double MoonDrop { get; init; } = 0.75;
    public double MoonLo { get; init; } = 0.06;
    public double MoonHi { get; init; } = 0.16;
    public double MoonTop { get; init; } = 0.9;
    public double MoonWidth { get; init; } = 0.2;
    /// <summary>Skin's hues spared the moon's step, this share of it (0: none, as before; the Look's 1): skin in shade is
    /// weakly coloured (C/L under MoonHi) and mid-dark, so the step gave it the moon's silver-blue, a blue-grey patch on the
    /// far side of her neck under her jaw at the Look (P1 R1 round 33, gate judge 2 S4: Oklab h 46 C .045 before the grade,
    /// h -15 C .020 after; on A and B alike). The band: Atmosphere.MoonSkinHue on the input, C 0.012 up.</summary>
    public double MoonSkin { get; init; }
    /// <summary>The paint grade (art style round 2, approved 20 Oct; 0: off), after the moon's step, in Oklab: PaintVib
    /// raises the chroma of what is dull and not dark (skin hues held), PaintHi that of the lit brights, PaintLift lifts the
    /// darkest values, and PaintShadowK of PaintShadow's hue and chroma (sRGB hex; "" none) is laid on what is dark and
    /// weakly coloured: painted shadows coloured blue to violet, not slate. --grade-try overrides any of them for pictures.</summary>
    public double PaintVib { get; init; }
    public double PaintHi { get; init; }
    public string PaintShadow { get; init; } = "";
    public double PaintShadowK { get; init; }
    public double PaintLift { get; init; }
    /// <summary>How much of skin's hues (Oklab h 15-90, C over 0.012) the painted shadow spares (0: none; Face 44, skin A0). Laid on
    /// her shaded skin, the blue lerp passed through red and violet on the way: deep skin's shade side went from h 40-55 to
    /// 20-43, brick-red and purple patches with hard edges where her shade crossed its L and C thresholds.</summary>
    public double PaintShadowSkin { get; init; }
    /// <summary>The vibrance's share in the darks (Oklab L 0.44 and under; all of it from L 0.52): G1 r2's 0.2.</summary>
    public double PaintVibDark { get; init; } = 0.2;
    /// <summary>(L1 W2) The tone curve on Oklab L, last in the grade: (in, out) pairs from 0 to 1, flattened, through which a
    /// monotone cubic runs (null: none). Lightness only: a darkened pixel keeps its chroma's share of its L (C x L'/L), a
    /// lightened one its chroma, so the curve's contrast never raises the surfaces' chroma (the per-channel Contrast did:
    /// by day x1.6 took midC 0.065 to 0.090). From a rig's "grade_curve".</summary>
    public double[]? Curve { get; init; }
    /// <summary>(L1 W2) The warm-source term (0: none): what a warm light lit (Oklab hue WarmHue +-WarmWidth, chroma over
    /// 0.10-0.18 of its L: her ember's pool, a lamp's, a fire's) keeps WarmKeep of the chroma and hue the renderer gave it,
    /// past the grade's mute, moon step and vibrance; the light's own color, not a vibrance raise on the surfaces.</summary>
    public double WarmKeep { get; init; }
    public double WarmHue { get; init; } = 58;
    public double WarmWidth { get; init; } = 32;
    /// <summary>(L1 lead 7, S1 daycast) The scene's color (0: none; 1: the day rigs, rigs.json "scene_color"): the drawn color
    /// keeps the hue and the chroma's share of its L (Oklab; the linear channel ratios) of what was lit, the light times the
    /// surface as it reached the tone mapper; AgX and the grade give its lightness only. Last in the grade, after the tone
    /// curve. Why: AgX's per-channel sigmoid pulls a color's channels together (the neutral 0.18 card's lit side under the
    /// #f3d9a0 sun: the scene's R/B 2.26 drawn 1.72), and the day grade's chroma terms (saturation and vibrance, PaintVib 0.75,
    /// PaintHi 0.7, the per-channel contrast) pushed it back past the light's own (R/B 2.95, red near its ceiling on the 0.5
    /// card), so the color chain's per-channel division of the boards drew every warm surface pink-mauve (bible rules 3-4:
    /// the color is the light's and the surface's, never a grade push the chain must divide out).</summary>
    public double SceneColor { get; init; }
    /// <summary>(L1 lead 7, S2) Under SceneColor, the Moon step after it (1) rather than before (0, where SceneColor overrides it).
    /// Why: the boards and the picked night targets paint what the moon lights moon-blue whatever its albedo (MB4's night grass
    /// teal, MB3's setts and plaster blue, the targets' cold 73-86% of the chroma, shade h 251-263), which no light gives a warm
    /// or olive albedo (under scene_color alone the Deep Shaw's moonlit ground read C 0.03, grey, and the shade h 313, gray 24%);
    /// and LB DAWN's shade is lilac on every surface. The step re-hues only the weakly colored and the dark (MoonLo..MoonHi,
    /// MoonTop), so what her ember, a lamp or a fire lights keeps the scene's own color.</summary>
    public double SceneMoon { get; init; }
}

public sealed record AtmospherePreset(
    SkySettings Sky, string KeyColor, double KeyIntensity, double KeyElevation, double KeyAzimuth, double ShadowStrength,
    string HemiSky, string HemiGround, double HemiIntensity, double EnvIntensity, string FogColor, double FogDensity,
    double Exposure, string Rim, double RimStrength, GradeSettings Grade)
{
    /// <summary>The volumetric fog's density: the air the lamps' halos and the key's shafts are seen in.</summary>
    public double Haze { get; init; } = 0.0012;
    /// <summary>How thick the mist lies on a river (0: none, as the cinematics' presets have it; 1: thick).</summary>
    public double Mist { get; init; }
    /// <summary>The mist's colour (sRGB hex): the key's light in the air, as the eye sees it.</summary>
    public string MistColor { get; init; } = "#000000";
    /// <summary>Her carried light's strength against its base (play's night lights her pool more, in a darker world).</summary>
    public double Ember { get; init; } = 1;
    /// <summary>(H2 R1) Her carried light's colour under this air (sRGB hex; "": her own #ffa868), and its reach against
    /// its base (1: as built). The arena's night: a paler gold, so her pool lights the brown litter amber, not rust.</summary>
    public string EmberColor { get; init; } = "";
    public double EmberReach { get; init; } = 1;
    /// <summary>(L1 W2) How the moon gives way to her light within its reach under the cel model (cel.gdshaderinc cel_give): the
    /// share of the moon's key, fill and rim given up at the pool's heart, the share of the sky's light, and where the giving
    /// starts to fade and where it is gone (metres from her light; S2b-N2). Null: none (the rig's rigs.json "ember_give").</summary>
    public double[]? EmberGive { get; init; }
    /// <summary>(L1 lead 9, NIGHT2) How the moon gives way to the zone's fires and lamps (the nearest few lit warm lights,
    /// ZoneView.CelFires; cel.gdshaderinc cel_fires_at), as to her light (bible rule 3, T01/T05/T06: each lamp and the camp
    /// fire throws its own warm pool, the moon giving way inside it): the share of the moon's key, fill and rim given up at a
    /// source's foot, the share of the sky's light, and where the giving starts to fade and where it is gone (shares of the
    /// source's own range, on the ground). Null: none (the rig's rigs.json "fire_give").</summary>
    public double[]? FireGive { get; init; }
    /// <summary>(L1 lead 9, B1) Her pool as light, a ramp in metres from her light's foot (cel.gdshaderinc cel_pool_paint;
    /// Atmosphere.PoolRamp): [how much of the canopy's dapple stays in it at its edge and at its core (target 09: the leaf shapes
    /// cut its edge, its core whole), then stops of r (m, rising), level (over her light's
    /// energy; the last 0), color (sRGB 0-255, its largest channel taken as 1)], linear between stops; the moon gives way along
    /// it (ember_give x and y at the core's level). FROM targets 09 and 12 (judge 1, verdict section 3): a gold core falling off
    /// from 0.5 m through orange and dusk into the moon's ground by 3.25 m, no plateau, no ring. Null: her light as Godot
    /// falls it.</summary>
    public double[]? EmberPool { get; init; }
    /// <summary>(L1 lead 12, R4 round 4; rigs.json "ember_smooth") Her pool's ramp runs smooth through its stops (a monotone
    /// cubic, flat at her feet and at its end; Atmosphere.PoolRamp) instead of straight between them: a field with no kink
    /// and no edge. (Retired with it: lead 11's ember_break and ember_brush, a shaped end that drew a disc.)</summary>
    public bool EmberSmooth { get; init; }
    /// <summary>(L1 lead 12, R4 round 4; rigs.json "ember_shade") The canopy's leaf shade across her fire: [the share of her
    /// fire a leaf's shade takes, the canopy's opening over her fire (m from her light's foot: no leaf shade inside this),
    /// where the shade is whole (m), how much of the moon's give-way a leaf's shade undoes (1: the moon whole under a leaf)]
    /// (cel_pool_shade). Null: her light uncut and the moon's shade as it was.</summary>
    public double[]? EmberShade { get; init; }
    /// <summary>(L1 lead 17, P; rigs.json "ember_floor") Her fire on the floor as a table of TONES (Oklab L, C, hue in degrees,
    /// as the frame shows them): [the floor's own lit tone and its shade's away from her fire (L, C, h x 2), what the floor
    /// shows under one unit of her light (linear r, g, b), then stops of (r m, the moon's return 0..1, the lit gap's tone,
    /// the leaf shade's tone) x n, r rising; the last stop is where the floor is its own again (its tones are not read)].
    /// Atmosphere.FloorTurn builds cel_floor_turn from it. Null: the floor takes ember_pool as before.</summary>
    public double[]? EmberFloor { get; init; }
    /// <summary>(L1 lead 20, MASS; rigs.json "ember_floor_lift") [the floor's reference albedo luminance]: inside her fire the
    /// floor's own dark patches are lifted toward it before the tone table's turn (cel.gdshaderinc cel_floor_lift), so the
    /// pool never cuts to black on a dark material. Null: no lift, the floor as before.</summary>
    public double[]? EmberFloorLift { get; init; }
    /// <summary>(L1 lead 19, HER2; rigs.json "hero_pool") The hero figure in her lit pool, so a 40 px figure is the first thing
    /// the eye lands on: [the pool light's foot dx, dz (m from her: the fire sits BESIDE her, so her shade side faces the
    /// camera), the anchor's level and color (sRGB 0-255: the one dark warm tone her shade side takes), the side edge (the
    /// anchor's hard step in n.xz away from the foot), the under edge (n.y under it is anchor), the hero ink's width (px)
    /// and strength]. PlayerView places her light by it; Atmosphere sets cel_hero / cel_hero_tone (cel.gdshaderinc CEL_HERO).
    /// Null: the light over her at (0, 0.4) and no anchor, as before.</summary>
    public double[]? HeroPool { get; init; }
    /// <summary>(L1 lead 12, S3, rule R5; rigs.json "moon_top") The moon's top step on what stands: [level (scene light; the
    /// screen level is tuned at the frame), R, G, B (sRGB 0-255), the top band's edge in n.m, how far m leans up from the key
    /// (0 the key's way, 1 straight up), the rim's width (screen px), the key's share on a standing form's unlit side]
    /// (cel_s3, cel_s3_shape; a shader takes it by CEL_S3). Null: none.</summary>
    public double[]? MoonTop { get; init; }
    /// <summary>(L1 lead 12; rigs.json "foe_fire") Her fire on the foes from the ground's ramp: [the bright band's level, the
    /// second band's share, the bright band's edge in n.l toward her, the second's] (crowd_fire). Null: the crowd's smooth lamp.</summary>
    public double[]? FoeFire { get; init; }
    /// <summary>(L1 lead 12; rigs.json "foe_moon") The foes' moon read and their own shadow: [the luminance their paint is pulled to, how
    /// far (0-1), then each foe's hard shadow inside her fire: its level (scene light; 0: none), R, G, B (sRGB 0-255), the
    /// fire's residue in it (a share of the ground's ramp)] (crowd_moon, crowd_shade). Read only with FoeFire.</summary>
    public double[]? FoeMoon { get; init; }
    /// <summary>(L1 lead 8, S2b) The pool's outer step's color (sRGB hex). Retired by lead 9 (B1: the ramp's stops carry the colors); read, unused.</summary>
    public string EmberEdge { get; init; } = "";
    /// <summary>The moon's rim on the crowd in play, in shade as in its light (0: none, as the cinematics' presets have it).</summary>
    public double CrowdRim { get; init; }
    /// <summary>Her lamp and the sky's fill on the crowd in its own paint (vat.gdshaderinc crowd_ember/crowd_fill; 0: none, by day
    /// and in the cinematics' presets). Rendering 4: by night the bodies round her read as a black starburst.</summary>
    public double CrowdFill { get; init; }
    /// <summary>A river's light, the sky in it, and how far its ripples bend it (1: as built; the water shader's water_air).</summary>
    public double RiverLight { get; init; } = 1;
    public double RiverSky { get; init; } = 1;
    public double RiverBend { get; init; } = 1;
    /// <summary>(Low Ford r3) How far the river's moon glint is the water look's moonlight (moon_*: rougher, sparse, a soft column, tinted; the water shader's water_air.w); 0 as built.</summary>
    public double RiverMoon { get; init; } = 0;
    /// <summary>(Low Ford r3) How far a warm lamp's or fire's light on our own grass turns toward ochre, its lime taken out (grass_own.gdshader's flora_lamp); 0 as built.</summary>
    public double GrassLampOchre { get; init; } = 0;
    /// <summary>(Low Ford lf5p) Our broadleaf bushes' and alders' leaves by night pulled this share toward their own grey (kit.gdshader's flora_night.x); 0 as built.</summary>
    public double BushNightSat { get; init; } = 0;
    /// <summary>(Low Ford lf5p) How far the meadow ground in her ember's pool turns from green to straw, so her warm light reads ochre on it, not chartreuse (terrain.gdshader's flora_night.y; her own lighting untouched); 0 as built.</summary>
    public double GroundEmberOchre { get; init; } = 0;
    /// <summary>Hoar frost on the ground's exposed tops in play (0: none; 1: a night's full frost; look bible 1f),
    /// and how much of it the sun has thawed where it falls (0: none; 1: all of it, leaving it in the shade).</summary>
    public double Frost { get; init; }
    public double FrostThaw { get; init; }
    /// <summary>The sun's elevation the thaw is baked for, when not the key's (below 0: the key's): a sun climbing
    /// over minutes (Atmospheres.Morning) keeps its dawn's thaw while the frost burns off, not a bake a degree.</summary>
    public double ThawElevation { get; init; } = -1;
    /// <summary>(L1 B1a) The painted-cel shading model (shaders/cel.gdshaderinc) under this air: CelOn 0 lights as before,
    /// 1 the cel model; CelShadow the key's cast-shadow hardness (0 the PCF penumbra, 1 a narrow step); CelFill the key's
    /// fill in the shadow band (0..0.25, of the key's luminance); CelRim the stepped rim's strength and CelRimWidth its
    /// width in 1 - n.v; CelFillColor and CelRimColor their hues ("": the sky's, HemiSky, and the moon's or sun's rim, Rim).</summary>
    public double CelOn { get; init; } = 1;
    public double CelShadow { get; init; } = 0.85;
    public double CelFill { get; init; } = 0.06;
    public double CelRim { get; init; } = 0.35;
    public double CelRimWidth { get; init; } = 0.25;
    public string CelFillColor { get; init; } = "";
    public string CelRimColor { get; init; } = "";
    /// <summary>(L1 B4) The lighting rig this air is lit by under the cel model (godot/data/look/rigs.json; logic/Look/Rigs.cs;
    /// "": none, the preset's own light). The rig's numbers replace the preset's key, fill, rim, ink, hardness, grade,
    /// exposure, ember and dapple under cel; --cel off lights by the preset as it is.</summary>
    public string Rig { get; init; } = "";
    /// <summary>(L1 B4) The ink rig color (linear rgb, B5's InkPass.SetRig; null: the night's).</summary>
    public double[]? CelInk { get; init; }
    /// <summary>(L1 B4) The moon through the canopy (bible rule 9; cel.gdshaderinc cel_dapple): how much of the sky the crowns
    /// close where the canopy stands (0: none), how dark a leaf's shadow is, and the crowns' height (m).</summary>
    public double DappleCover { get; init; }
    public double DappleStrength { get; init; } = 1;
    public double DappleHeight { get; init; } = 9;
    /// <summary>(S2b-N3) The leaf tile's size (m; 0: CanopyCookie.Tile, 32): larger, the moon's patches and the leaves' shade
    /// grow together, the big painted shapes of target 09's clearing.</summary>
    public double DappleSize { get; init; }
    /// <summary>(S2b-N3) The canopy's cover floor (0-1): at least this much of the sky closed everywhere, the clearings too.</summary>
    public double DappleFloor { get; init; }
    /// <summary>(L1 B4) This air is already its rig's light (Rigs.Lit's output); Source is the preset it came from.</summary>
    /// <summary>(L1 lead 11, R3) The key's shadow is a level and the dapple the same shade (LightRig.OneShade; cel_oneshade.x).</summary>
    public bool ShadowLevel { get; init; }
    /// <summary>(L1 lead 11) The dapple's edge width (screen px; 0 or 1: hard) and the leaf cookie's shapes: clusters a tile (0: 420),
    /// leaf length [shortest, longest] m (null: 0.8-2.4), leaves a cluster [fewest, most] (null: 3-5). CanopyCookie.Shape.</summary>
    public double DappleEdge { get; init; }
    public double DappleClusters { get; init; }
    public double[]? DappleLeaf { get; init; }
    public double[]? DappleLeaves { get; init; }
    /// <summary>(L1 lead 12, F4) Leaf masses: each cluster a lobed mass this wide [narrowest, widest] m with small leaves round
    /// its rim (DappleLeaf their length, DappleLeaves the lobes a mass). Null: the fans of big leaves. CanopyCookie.Shape.</summary>
    public double[]? DappleMass { get; init; }
    public bool IsLit { get; init; }
    public AtmospherePreset? Source { get; init; }
    /// <summary>(L1 B4) A blend's light under cel: the blend of its two presets' rigs (Atmospheres.Blend sets it).</summary>
    public AtmospherePreset? CelTwin { get; init; }
}

public sealed class ZoneMeta
{
    public string Id = "";
    /// <summary>The ground: a square this many metres across, heights on a
    /// res by res grid, paint on a splatRes by splatRes image.</summary>
    public double Size;
    public int Res, SplatRes;
    /// <summary>How much of the ground is strewn with leaves (the terrain shader).</summary>
    public double Leaves;
    /// <summary>The colour the blight's veins glow (sRGB hex).</summary>
    public string BlightGlow = "#8cff5a";
    /// <summary>How far from the centre the survivor may go, each way.</summary>
    public double Bound;
    /// <summary>(M5) What the zone's ground has, by name (e.g. "lowford.pockets"); the ground lead adds one when it lands.
    /// Content that needs one (Encounters.Beat.Needs, LampPosts moved) is off until the zone holds it.</summary>
    public List<string> Features = new();
    public Start Start = new();
    /// <summary>The zone's air by day (the runtime changes it with the hour).</summary>
    public AtmospherePreset Atmosphere = null!;
    public List<LightDef> Lights = new();
    public List<FireDef> Fires = new();
    public List<Point3> Chimneys = new();
    /// <summary>Lights moths gather round after dark (indices into the lights).</summary>
    public List<int> Moths = new();
    /// <summary>Landmark nodes that only show after dark (light spilled from
    /// a doorway).</summary>
    public List<string> NightNodes = new();
    /// <summary>Landmark nodes the zone starts with hidden (the runtime
    /// shows them).</summary>
    public List<string> HiddenNodes = new();
    public List<ColliderDef> Colliders = new();
    /// <summary>A table arena made a board (Maps/ArenaBoard.cs: the fold, its chokepoints, the lamp, the lanes), or
    /// null; in play only (never written out).</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public SurvivorUnchained.Maps.ArenaBoard? Board;
    /// <summary>What the zone's runtime reaches into, zone by zone (the
    /// Verge's brambles and fires, Lowford's pylons, the Waystation's doors).</summary>
    public JsonElement Refs;
    /// <summary>The zone module's named places (a table of points, or a number).</summary>
    public Dictionary<string, JsonElement> Places = new();
    /// <summary>The zone module's paths: [x, z] points.</summary>
    public Dictionary<string, double[][]> Paths = new();
    public ZoneMapDef? Map;
    public WaterMaskDef? WaterMask;
    public int LandmarkMeshes;

    public static ZoneMeta Load(string id)
    {
        var z = Json.Parse<ZoneMeta>(DataFiles.Text($"zones/{id}/zone.json"));
        AddPropColliders(z, id);
        return z;
    }

    /// <summary>Box colliders for the placed props in zones/{id}/props_own.json: each "place" entry with
    /// "col": [cx, cz, hw, hd] (metres, in the preset's own frame, before its rotation and scale).</summary>
    public static void AddPropColliders(ZoneMeta z, string id)
    {
        string text;
        try { text = DataFiles.Text($"zones/{id}/props_own.json"); }
        catch { return; }
        if (string.IsNullOrWhiteSpace(text)) return;  // a zone with no props_own.json (the verge) reads as empty
        using var doc = JsonDocument.Parse(text);
        MoveFloraColliders(z, doc.RootElement);
        int nextId = 0;
        foreach (var c in z.Colliders) nextId = Math.Max(nextId, c.Id + 1);
        // "solid": [x, z, r] circles where the web game left none (H4 item 10: the cliff rocks along the hill's foot
        // east of the Kerchiefs' camp and west of the wallow, 8-20 m masses she could walk into, hidden at the play
        // camera; each rock's footprint and the strip north of it that it hides from the south-looking camera).
        if (doc.RootElement.TryGetProperty("solid", out var solid) && solid.ValueKind == JsonValueKind.Array)
            foreach (var e in solid.EnumerateArray())
                if (e.ValueKind == JsonValueKind.Array && e.GetArrayLength() >= 3)
                {
                    double r = e[2].GetDouble();
                    z.Colliders.Add(new ColliderDef { Id = nextId++, Kind = ColliderKind.Circle, X = e[0].GetDouble(), Z = e[1].GetDouble(), R = r, Hw = r, Hd = r, Tag = "solid" });
                }
        if (!doc.RootElement.TryGetProperty("place", out var place) || place.ValueKind != JsonValueKind.Array) return;
        foreach (var e in place.EnumerateArray())
        {
            var c = PropCollider(e);
            if (c == null) continue;
            c.Id = nextId++;
            z.Colliders.Add(c);
        }
    }

    /// <summary>props_own.json "flora_move" ([x, z, dx, dz] a flora copy at x, z within 0.5 m shifted, [x, z] dropped:
    /// OwnProps on the drawn side) applied to the tree's own collider too, so what blocks her is where the tree is
    /// drawn (H4 item 10: the day stretch's camp and hollow are cleared this way; the E7b moves had left their trunks'
    /// colliders standing in the open).</summary>
    public static void MoveFloraColliders(ZoneMeta z, JsonElement root)
    {
        if (!root.TryGetProperty("flora_move", out var mv) || mv.ValueKind != JsonValueKind.Array) return;
        foreach (var m in mv.EnumerateArray())
        {
            if (m.ValueKind != JsonValueKind.Array || m.GetArrayLength() < 2) continue;
            double x = m[0].GetDouble(), zz = m[1].GetDouble();
            var c = z.Colliders.FirstOrDefault(k => k.Kind == ColliderKind.Circle && k.Tag == null && Math.Abs(k.X - x) < 0.5 && Math.Abs(k.Z - zz) < 0.5);
            if (c == null) continue;
            if (m.GetArrayLength() >= 4) { c.X += m[2].GetDouble(); c.Z += m[3].GetDouble(); }
            else z.Colliders.Remove(c);
        }
    }

    /// <summary>One "place" entry as a box collider (Id left 0), or null without a "col". Godot's
    /// Basis(Up, rot) sends local x to world (cos, -sin) and local z to (sin, cos); the box's own x axis
    /// runs along (cos Rot, sin Rot), so its Rot is -rot.</summary>
    public static ColliderDef? PropCollider(JsonElement e)
    {
        if (e.ValueKind != JsonValueKind.Object || !e.TryGetProperty("col", out var col)
            || col.ValueKind != JsonValueKind.Array || col.GetArrayLength() < 4) return null;
        double cx = col[0].GetDouble(), cz = col[1].GetDouble(), hw = col[2].GetDouble(), hd = col[3].GetDouble();
        double x = e.TryGetProperty("x", out var px) ? px.GetDouble() : 0;
        double zz = e.TryGetProperty("z", out var pz) ? pz.GetDouble() : 0;
        double rot = e.TryGetProperty("rot", out var pr) ? pr.GetDouble() : 0;
        double s = e.TryGetProperty("scale", out var ps) ? ps.GetDouble() : 1;
        double cos = Math.Cos(rot), sin = Math.Sin(rot);
        hw *= s; hd *= s;
        return new ColliderDef
        {
            Kind = ColliderKind.Box,
            X = x + (cx * cos + cz * sin) * s,
            Z = zz + (-cx * sin + cz * cos) * s,
            Hw = hw, Hd = hd, Rot = -rot,
            R = Math.Sqrt(hw * hw + hd * hd),
            Tag = "prop",
        };
    }

    /// <summary>A named place: Places[table][name] as a point.</summary>
    public XZ Place(string table, string name)
    {
        var p = Places[table].GetProperty(name);
        return new XZ(p.GetProperty("x").GetDouble(), p.GetProperty("z").GetDouble());
    }

    /// <summary>The colliders, in the world the fight is in, each with the id
    /// the web game gave it (the runtime removes some by id: a bramble wall
    /// burned away).</summary>
    public CollisionWorld Collision()
    {
        var w = new CollisionWorld(Size) { Bound = Bound };
        foreach (var c in Colliders)
            w.Restore(new Collider
            {
                Id = c.Id, Kind = c.Kind, X = c.X, Z = c.Z, R = c.R, Hw = c.Hw, Hd = c.Hd, Rot = c.Rot,
                Tag = c.Tag, Soft = c.Soft, PlayerOnly = c.PlayerOnly,
            });
        return w;
    }

    /// <summary>Is there water here, on the map's mask.</summary>
    public bool WaterAt(double x, double z)
    {
        if (WaterMask == null) return false;
        mask ??= Convert.FromBase64String(WaterMask.Bits);
        int n = WaterMask.N;
        int i = (int)Math.Floor((x + Size / 2) / Size * n), j = (int)Math.Floor((z + Size / 2) / Size * n);
        return i >= 0 && j >= 0 && i < n && j < n && mask[j * n + i] != 0;
    }

    byte[]? mask;
}

/// <summary>The ground's heights (the web game's Terrain.heightAt): res by
/// res samples over a square size metres across, centred on the origin, row
/// by row from -z, each row from -x.</summary>
public sealed class Heightfield
{
    public readonly double Size, Half, Step;
    public readonly int Res;
    public readonly float[] Heights;

    public Heightfield(double size, int res, float[] heights)
    {
        if (heights.Length != res * res) throw new ArgumentException($"{heights.Length} heights for a {res}² grid");
        Size = size; Res = res; Heights = heights;
        Half = size / 2;
        Step = size / (res - 1);
    }

    public static Heightfield Load(ZoneMeta z)
    {
        var b = DataFiles.Bytes($"zones/{z.Id}/heights.bin");
        var h = new float[b.Length / 4];
        Buffer.BlockCopy(b, 0, h, 0, b.Length);
        return new Heightfield(z.Size, z.Res, h);
    }

    /// <summary>Bilinear height at a point (clamped to the edge).</summary>
    public double HeightAt(double x, double z)
    {
        double fx = Math.Clamp((x + Half) / Step, 0, Res - 1.0001), fz = Math.Clamp((z + Half) / Step, 0, Res - 1.0001);
        int i = (int)fx, j = (int)fz;
        double tx = fx - i, tz = fz - j;
        double a = Heights[j * Res + i], b = Heights[j * Res + i + 1], c = Heights[(j + 1) * Res + i], d = Heights[(j + 1) * Res + i + 1];
        return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz;
    }
}

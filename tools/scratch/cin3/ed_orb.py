p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a79b6d8c81e14dc63\godot\src\Actors\BossViews.cs'
t = open(p, encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, a[:70]
    t = t.replace(a, b)


rep('''public partial class OrbView : Node3D, IOrb
{
    readonly MeshInstance3D ball;
    readonly OmniLight3D light;

    public OrbView(string color, double size)
    {
        var c = new Color(color).SrgbToLinear();
        ball = new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = (float)size, Height = (float)size * 2, RadialSegments = 16, Rings = 8 },
            MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(c.R * 3, c.G * 3, c.B * 3) },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };''', '''/// <summary>The Warden's heart: a stone the size of a fist, cut in a few broad faces, with a cold
/// light in it. Its faces catch the light unevenly as it turns, so it reads as a thing and not a
/// glare; the light inside rises and falls with Light.</summary>
public partial class OrbView : Node3D, IOrb
{
    readonly MeshInstance3D ball;
    readonly OmniLight3D light;
    readonly StandardMaterial3D stone;

    public OrbView(string color, double size)
    {
        var c = new Color(color);
        stone = new StandardMaterial3D
        {
            AlbedoColor = c.Darkened(0.55f), Metallic = 0.35f, Roughness = 0.12f,
            EmissionEnabled = true, Emission = c, EmissionEnergyMultiplier = 1.2f,
            RimEnabled = true, Rim = 0.6f, RimTint = 0.8f,
        };
        ball = new MeshInstance3D { Mesh = Facets((float)size), MaterialOverride = stone, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };''')
rep('''    public double Light { set => light.LightEnergy = (float)(value / Math.PI); }''', '''    public double Light
    {
        set
        {
            light.LightEnergy = (float)(value / Math.PI);
            stone.EmissionEnergyMultiplier = 0.5f + (float)value * 0.6f;
        }
    }

    /// <summary>A rough-cut stone: a squashed, uneven sphere of a few flat faces.</summary>
    static Mesh Facets(float size)
    {
        var src = new SphereMesh { Radius = size, Height = size * 1.7f, RadialSegments = 7, Rings = 4 };
        var st = new SurfaceTool();
        st.CreateFrom(src, 0);
        st.Deindex();
        var arrays = st.Commit().SurfaceGetArrays(0);
        var verts = (Vector3[])arrays[(int)Mesh.ArrayType.Vertex];
        // Each corner pushed in or out a little, the same for the same corner, so the faces are uneven.
        for (int i = 0; i < verts.Length; i++)
        {
            var v = verts[i];
            float n = Mathf.Sin(v.X * 53.1f + v.Y * 17.3f) * Mathf.Cos(v.Z * 41.7f - v.Y * 9.1f);
            verts[i] = v * (1 + n * 0.14f);
        }
        var flat = new SurfaceTool();
        flat.Begin(Mesh.PrimitiveType.Triangles);
        foreach (var v in verts) flat.AddVertex(v);
        flat.GenerateNormals();
        return flat.Commit();
    }''')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')

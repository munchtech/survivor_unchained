import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('src/Fx/Palette.cs', [
("""    public static readonly Color HostileRim = K("#ff5a2a", 2.2f), HostileDanger = K("#ff2a1a", 2.4f);""",
 """    public static readonly Color HostileRim = K("#ff5a2a", 2.2f), HostileDanger = K("#ff2a1a", 2.4f);

    /// <summary>The telegraph language (docs/bosses/MECHANICS.md section 2): amber a blow is
    /// coming here, violet this ground stays bad, pale blue stand here, grey this will be
    /// solid. Each has its own edge as well (filled, hatched, dashed, hard), so colour is
    /// never the only sign.</summary>
    public static readonly Color TeleBlow = K("#ff9a1a", 2.6f), TeleGround = K("#a050ff", 2.2f), TeleSafe = K("#8ad0ff", 2.2f), TeleWall = K("#c8c8d0", 1.6f);
    public static Color Telegraph(TelegraphKind k) => k switch
    {
        TelegraphKind.Ground => TeleGround, TelegraphKind.Safe => TeleSafe, TelegraphKind.Wall => TeleWall, _ => TeleBlow,
    };"""),
])

F = 'src/Fx/BattleFx.cs'
edit(F, [
("""    static Texture2D? ringTex, discTex, laneTex;""",
 """    static Texture2D? ringTex, discTex, laneTex, hatchTex, dashTex, wallTex;
    static readonly Dictionary<int, Texture2D> coneTex = new();"""),
("""        ringTex ??= GroundTexture(0);
        discTex ??= GroundTexture(1);
        laneTex ??= GroundTexture(2);""",
 """        ringTex ??= GroundTexture(0);
        discTex ??= GroundTexture(1);
        laneTex ??= GroundTexture(2);
        hatchTex ??= GroundTexture(3);
        dashTex ??= GroundTexture(4);
        wallTex ??= GroundTexture(5);"""),
# Textures: hatched ground, a dashed ring, a hard wall's edge; cones by their arc.
("""                else { float e = Mathf.Abs(u); a = (Mathf.Clamp(1 - Mathf.Abs(e - 0.88f) / 0.1f, 0, 1) + 0.22f) * Mathf.Clamp((1 - Mathf.Abs(v)) / 0.05f, 0, 1); }""",
 """                else if (kind == 2) { float e = Mathf.Abs(u); a = (Mathf.Clamp(1 - Mathf.Abs(e - 0.88f) / 0.1f, 0, 1) + 0.22f) * Mathf.Clamp((1 - Mathf.Abs(v)) / 0.05f, 0, 1); }
                // This ground stays bad: hatched, with its edge.
                else if (kind == 3) a = r < 0.97f ? (Mathf.PosMod((u + v) * 7f, 1f) < 0.3f ? 0.55f : 0.12f) + Mathf.Clamp(1 - Mathf.Abs(r - 0.92f) / 0.05f, 0, 1) : 0;
                // Stand here: a dashed ring.
                else if (kind == 4) a = Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.06f, 0, 1) * (Mathf.PosMod(Mathf.Atan2(v, u) / Mathf.Tau * 24f, 1f) < 0.55f ? 1 : 0) + (r < 0.9f ? 0.1f : 0);
                // This will be solid: a hard, thick edge.
                else a = (r < 0.97f ? 0.2f : 0) + Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.09f, 0, 1);"""),
("""    /* ------------------------------------------------------------- events -- */""",
 """    /// <summary>A cone pointing along the texture's v, apex at the centre, `arc` degrees wide.</summary>
    static Texture2D ConeTexture(int arc)
    {
        if (coneTex.TryGetValue(arc, out var t)) return t;
        const int N = 128;
        float half = arc * Mathf.Pi / 360f;
        var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v), ang = Mathf.Abs(Mathf.Atan2(u, v));
                float a = 0;
                if (r < 0.97f && ang <= half)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.07f, 0, 1), Mathf.Clamp(1 - (half - ang) * r / 0.05f, 0, 1));
                    a = 0.18f + 0.82f * edge;
                }
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return coneTex[arc] = ImageTexture.CreateFromImage(img);
    }

    /// <summary>A cone on the ground from (x, z), pointing at `angle` (radians, in the plane), `radius` long.</summary>
    void ConeMark(double x, double z, float radius, double angle, double arc, Color color, float life, int? key = null)
    {
        if (key is int k && keyed.TryGetValue(k, out var old)) { old.Active = false; old.Decal.Visible = false; }
        var m = Ground(x, z, radius, ConeTexture((int)Math.Round(arc * 180 / Math.PI / 5) * 5), color, life);
        m.Decal.Rotation = new Vector3(0, (float)Math.Atan2(Math.Cos(angle), Math.Sin(angle)), 0);
        if (key is int k2) keyed[k2] = m;
    }

    /* ------------------------------------------------------------- events -- */"""),
# Telegraphs drawn in the language: a cone as a cone, a band as a band, each kind its edge.
("""                case Ev.Telegraph e:
                {
                    var col = e.Hostile ? Palette.HostileDanger : Palette.Of(School.Holy).Glow;
                    if (e.Shape == TelegraphShape.Line) Lane(e.X, e.Z, e.X1 ?? e.X, e.Z1 ?? e.Z, (float)(e.Width ?? 1), col, (float)e.Duration, e.Id);
                    else if (e.Shape == TelegraphShape.Ring) Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, false, e.Id);
                    else Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, true, e.Id);
                    break;
                }""",
 """                case Ev.Telegraph e:
                {
                    var col = e.Hostile ? Palette.Telegraph(e.Kind) : Palette.Of(School.Holy).Glow;
                    if (e.Shape == TelegraphShape.Line) Lane(e.X, e.Z, e.X1 ?? e.X, e.Z1 ?? e.Z, (float)(e.Width ?? 1), col, (float)e.Duration, e.Id);
                    else if (e.Shape == TelegraphShape.Cone) ConeMark(e.X, e.Z, (float)e.Radius, e.Angle ?? 0, e.Arc ?? Math.PI / 2, col, (float)e.Duration, e.Id);
                    else if (e.Shape == TelegraphShape.Ring)
                    {
                        Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, false, e.Id);
                        if (e.Inner > 0.5) Ring(e.X, e.Z, (float)e.Inner, col, (float)e.Duration, false, e.Id + 500000);
                    }
                    else if (e.Hostile && e.Kind != TelegraphKind.Blow)
                    {
                        if (keyed.TryGetValue(e.Id, out var old)) { old.Active = false; old.Decal.Visible = false; if (old.Fill != null) old.Fill.Visible = false; }
                        var tex = e.Kind == TelegraphKind.Ground ? hatchTex! : e.Kind == TelegraphKind.Safe ? dashTex! : wallTex!;
                        keyed[e.Id] = Ground(e.X, e.Z, (float)e.Radius, tex, col, (float)e.Duration);
                    }
                    else Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, true, e.Id);
                    // A boss's move, named over it for a moment.
                    if (e.Label is { Length: > 0 } label)
                        Hits.Text(V(e.X, Y(e.X, e.Z) + 2.2, e.Z), label, col with { A = 1 }, 40);
                    break;
                }
                case Ev.Break br:
                {
                    // A phase broken past its mark: the surplus as one big number.
                    var at = V(br.X, Y(br.X, br.Z) + 2.6, br.Z);
                    Hits.Text(at, $"BREAK {Math.Round(br.Amount):N0}", new Color(2.4f, 1.9f, 0.6f), 76);
                    Flash(at, new Color("#ffd46a"), 8, 0.5f, 9);
                    Cam?.AddTrauma(0.35f);
                    break;
                }"""),
])
print('ok')

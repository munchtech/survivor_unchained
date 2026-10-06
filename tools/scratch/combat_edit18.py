W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'src\Fx\BattleFx.cs', [
('''    static readonly Dictionary<int, Texture2D> coneTex = new();''',
'''    static readonly Dictionary<int, Texture2D> coneTex = new(), bandTex = new();'''),
('''    /// <summary>A cone on the ground from (x, z), pointing at `angle` (radians, in the plane), `radius` long.</summary>''',
'''    /// <summary>A band: the ground between two circles filled, edged at both, and the
    /// inside left clear (the inside is where to stand; two rings with a wash over the
    /// whole disc said the opposite).</summary>
    static Texture2D BandTexture(int innerPct)
    {
        if (bandTex.TryGetValue(innerPct, out var t)) return t;
        const int N = 192;
        float inner = innerPct / 100f * 0.97f, outer = 0.97f;
        var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v), a = 0;
                if (r >= inner && r <= outer)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - (r - inner) / 0.035f, 0, 1), Mathf.Clamp(1 - (outer - r) / 0.035f, 0, 1));
                    a = 0.3f + 0.7f * edge;
                }
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return bandTex[innerPct] = ImageTexture.CreateFromImage(img);
    }

    void BandMark(double x, double z, double inner, float outer, Color color, float life, int? key = null)
    {
        if (key is int k && keyed.TryGetValue(k, out var old)) { old.Active = false; old.Decal.Visible = false; if (old.Fill != null) old.Fill.Visible = false; }
        int pct = (int)Math.Round(Math.Clamp(inner / Math.Max(0.01, outer), 0, 0.95) * 20) * 5;
        var m = Ground(x, z, outer, BandTexture(pct), color, life);
        if (key is int k2) keyed[k2] = m;
    }

    /// <summary>A cone on the ground from (x, z), pointing at `angle` (radians, in the plane), `radius` long.</summary>'''),
('''                    else if (e.Shape == TelegraphShape.Ring)
                    {
                        Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, false, e.Id);
                        if (e.Inner > 0.5) Ring(e.X, e.Z, (float)e.Inner, col, (float)e.Duration, false, e.Id + 500000);
                    }''',
'''                    else if (e.Shape == TelegraphShape.Ring) BandMark(e.X, e.Z, e.Inner, (float)e.Radius, col, (float)e.Duration, e.Id);'''),
])
print("ok")

import re
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\godot\src\Actors\Vat.cs"
s = open(p, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:80], s.count(old))
    s = s.replace(old, new)

# Pace for a charge (a gallop of its own).
rep('''    public float Pace;

    public Clip For(string role) =>''', '''    public float Pace;
    /// <summary>How fast its charge (its own gallop, the role "charge")
    /// carries it at its natural rate, as Pace; 0 when it has none.</summary>
    public float ChargePace;

    public Clip For(string role) =>''')

# A beast's pace comes from its definition; a person's from its clips.
rep('''        if (beast == null) asset.Pace = Pace(spec);''', '''        if (beast == null) asset.Pace = Pace(spec);
        else { asset.Pace = (float)(beast.Pace * spec.Scale); asset.ChargePace = (float)(beast.ChargePace * spec.Scale); }''')

# Surfaces carry a normal map.
rep('''        /// <summary>Fur and hair cards: cut where the texture's alpha falls below this (-1: solid).</summary>
        public float Cut = -1;''', '''        /// <summary>Fur and hair cards: cut where the texture's alpha falls below this (-1: solid).</summary>
        public float Cut = -1;
        /// <summary>A normal map (tangent space), drawn with vat_normal.gdshader.</summary>
        public Texture2D? Normal;''')

# Roles may loop by their own say.
rep('''    public sealed record Role(string Name, string Clip, double From, double Length, Func<double, Moves>? Over = null, bool Hold = false, bool Seam = false, double Rate = 1);''',
    '''    public sealed record Role(string Name, string Clip, double From, double Length, Func<double, Moves>? Over = null, bool Hold = false, bool Seam = false, double Rate = 1, bool? Loop = null)
    {
        /// <summary>Whether it loops: its own say, or the crowd's rule for its name.</summary>
        public bool Loops => Loop ?? Vat.Loops(Name);
    }''')
rep('''    static bool Loops(string role) => role is "move" or "idle" or "burrow" or "cast";''',
    '''    static bool Loops(string role) => role is "move" or "idle" or "burrow" or "cast" or "charge";''')
rep('''                var off = Loops(r.Name) && !r.Hold ?''', '''                var off = r.Loops && !r.Hold ?''')
rep('''        var list = new List<(string Role, double Duration)>();
        foreach (var r in roles) list.Add((r.Name, r.Length));''', '''        var list = new List<(string Role, double Duration, bool Loop)>();
        foreach (var r in roles) list.Add((r.Name, r.Length, r.Loops));''')
rep('''    static VatAsset Write(string key, List<Surf> surfs, int total, List<(string Role, double Duration)> roles, double fps, Sampler sample)''',
    '''    static VatAsset Write(string key, List<Surf> surfs, int total, List<(string Role, double Duration, bool Loop)> roles, double fps, Sampler sample)''')
rep('''        foreach (var (role, dur) in roles)
        {
            int frames = Math.Min(MaxFrames, Math.Max(2, (int)Math.Round(dur * fps) + 1));
            clips[role] = new VatAsset.Clip(frameCount, frames, (frames - 1) / Math.Max(1e-3, dur), dur, Loops(role));''',
    '''        foreach (var (role, dur, loop) in roles)
        {
            int frames = Math.Min(MaxFrames, Math.Max(2, (int)Math.Round(dur * fps) + 1));
            clips[role] = new VatAsset.Clip(frameCount, frames, (frames - 1) / Math.Max(1e-3, dur), dur, loop);''')
rep('''        foreach (var (role, dur) in roles)
        {
            var c = clips[role];''', '''        foreach (var (role, dur, _) in roles)
        {
            var c = clips[role];''')

# The normal map read off the model's material.
rep('''            s.Tex = bm.AlbedoTexture;
            s.Albedo = bm.AlbedoColor;''', '''            s.Tex = bm.AlbedoTexture;
            if (bm.NormalEnabled && bm.NormalTexture != null) s.Normal = bm.NormalTexture;
            s.Albedo = bm.AlbedoColor;''')

# Built with the normal-mapped variant where it has one.
rep('''        cutShader ??= GD.Load<Shader>("res://shaders/vat_cut.gdshader");
        var mesh = new ArrayMesh();''', '''        cutShader ??= GD.Load<Shader>("res://shaders/vat_cut.gdshader");
        normalShader ??= GD.Load<Shader>("res://shaders/vat_normal.gdshader");
        var mesh = new ArrayMesh();''')
rep('''            var m = new ShaderMaterial { Shader = s.Cut >= 0 ? cutShader : shader };''',
    '''            // Only a surface with a normal map pays for reading it (a variant
            // of the shader, so every other kind's is unchanged).
            var m = new ShaderMaterial { Shader = s.Cut >= 0 ? cutShader : s.Normal != null ? normalShader : shader };
            if (s.Normal != null && s.Cut < 0) m.SetShaderParameter("normal_tex", s.Normal);''')
rep('''    static Shader? shader, cutShader;''', '''    static Shader? shader, cutShader, normalShader;''')

# Cache: version, and the normal map kept by its file like the paint.
rep('''    const int Version = 13;''', '''    const int Version = 14;''')
rep('''            // A texture by its file, or (one inside a model's file) by its pixels.
            var tp = s.Tex?.ResourcePath ?? "";
            if (s.Tex == null) f.Store8(0);
            else if (tp != "" && !tp.Contains("::")) { f.Store8(1); f.StorePascalString(tp); }
            else
            {
                var img = s.Tex.GetImage();
                if (img == null || img.IsEmpty()) { f.Close(); DirAccess.RemoveAbsolute(CachePath(b.Key)); return; }
                f.Store8(2);
                f.Store32((uint)img.GetWidth()); f.Store32((uint)img.GetHeight()); f.Store32((uint)img.GetFormat()); f.Store8((byte)(img.HasMipmaps() ? 1 : 0));
                Blob(img.GetData());
            }''', '''            if (!Tex(s.Tex)) { f.Close(); DirAccess.RemoveAbsolute(CachePath(b.Key)); return; }''')
rep('''            f.StoreFloat(s.DyeLum);
            f.StoreFloat(s.Cut);
        }
    }''', '''            f.StoreFloat(s.DyeLum);
            f.StoreFloat(s.Cut);
            if (!Tex(s.Normal)) { f.Close(); DirAccess.RemoveAbsolute(CachePath(b.Key)); return; }
        }

        // A texture by its file, or (one inside a model's file) by its pixels.
        bool Tex(Texture2D? t)
        {
            var tp = t?.ResourcePath ?? "";
            if (t == null) f.Store8(0);
            else if (tp != "" && !tp.Contains("::")) { f.Store8(1); f.StorePascalString(tp); }
            else
            {
                var img = t.GetImage();
                if (img == null || img.IsEmpty()) return false;
                f.Store8(2);
                f.Store32((uint)img.GetWidth()); f.Store32((uint)img.GetHeight()); f.Store32((uint)img.GetFormat()); f.Store8((byte)(img.HasMipmaps() ? 1 : 0));
                Blob(img.GetData());
            }
            return true;
        }
    }''')
rep('''            var v = Of<Vector3>(Blob()); var nn = Of<Vector3>(Blob()); var uv = Of<Vector2>(Blob()); var col = Blob(); var idx = Of<int>(Blob());
            Texture2D? tex = null;
            switch (f.Get8())
            {
                case 1: tex = GD.Load<Texture2D>(f.GetPascalString()); break;
                case 2:
                {
                    int w = (int)f.Get32(), h = (int)f.Get32();
                    var fmt = (Image.Format)f.Get32();
                    bool mips = f.Get8() == 1;
                    tex = ImageTexture.CreateFromImage(Image.CreateFromData(w, h, mips, fmt, Blob()));
                    break;
                }
            }''', '''            var v = Of<Vector3>(Blob()); var nn = Of<Vector3>(Blob()); var uv = Of<Vector2>(Blob()); var col = Blob(); var idx = Of<int>(Blob());
            var tex = Tex();''')
rep('''            s.DyeLum = f.GetFloat();
            s.Cut = f.GetFloat();
            surfs.Add(s);''', '''            s.DyeLum = f.GetFloat();
            s.Cut = f.GetFloat();
            s.Normal = Tex();
            surfs.Add(s);''')
rep('''        if (f.GetError() != Error.Ok && f.GetError() != Error.FileEof) return null;
        return new Baked''', '''        if (f.GetError() != Error.Ok && f.GetError() != Error.FileEof) return null;
        return new Baked''')
# The reader's texture helper, beside Blob.
rep('''        byte[] Blob() => f.GetBuffer(f.Get32());''', '''        byte[] Blob() => f.GetBuffer(f.Get32());
        Texture2D? Tex()
        {
            switch (f.Get8())
            {
                case 1: return GD.Load<Texture2D>(f.GetPascalString());
                case 2:
                {
                    int w = (int)f.Get32(), h = (int)f.Get32();
                    var fmt = (Image.Format)f.Get32();
                    bool mips = f.Get8() == 1;
                    return ImageTexture.CreateFromImage(Image.CreateFromData(w, h, mips, fmt, Blob()));
                }
                default: return null;
            }
        }''')
open(p, "w", encoding="utf-8").write(s)
print("ok")

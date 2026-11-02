using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Godot;

namespace SurvivorUnchained.View;

/* The Long Cut's baked art (docs/design/SKILL_VFX_STUDY.md §6.1): the crack strip (art/fx/longcut/crack_{albedo,normal,
 * emis,height}.png, 4096x512: U along the 24 m line from her end, V across a 2.4 m band; albedo alpha its coverage, emis
 * the hot core), packed off the main thread into the two textures flare_world samples (flare_crack_a: paint + coverage;
 * flare_crack_b: normal xy, core, height), and the crack's centre along it (for where the dust jets and chunks rise);
 * the rock chunks (chunks.glb, 12 meshes). Missing files get stand-ins: a procedural crack on the same line FlareFx's
 * SeamOffset draws, and dark rock boxes. (Read as raw PNGs from the project folder: a shipped build packs them first.) */
public partial class FlareFx
{
    const string LcArtDir = "res://art/fx/longcut/";
    /// <summary>The seam's lights cast shadows (the fuse front's and the spend light at her); false: the unshadowed path.</summary>
    const bool LcShadows = true;

    sealed class LcArt
    {
        public required Image A, B;
        /// <summary>The crack's centre across the band (m) in 256 steps along the line.</summary>
        public required float[] Off;
        public bool Baked;
    }

    static Task<LcArt>? lcArtTask;
    static LcArt? lcArt;
    static bool lcArtSet;
    static Mesh[]? lcChunkMeshes;

    /// <summary>Starts reading the strip (once a game, off the main thread).</summary>
    static void LcArtStart()
    {
        if (lcArtTask != null) return;
        string dir = ProjectSettings.GlobalizePath(LcArtDir);
        lcArtTask = Task.Run(() => LcArtBuild(dir));
    }

    /// <summary>Hands the packed strip to the shaders once it is read (each frame until then; a frame's upload).</summary>
    static void LcArtPoll()
    {
        if (lcArtSet || lcArtTask is not { IsCompleted: true } task) return;
        lcArtSet = true;
        if (task.IsFaulted) { GD.PrintErr($"longcut art: {task.Exception?.GetBaseException().Message}"); return; }
        lcArt = task.Result;
        RenderingServer.GlobalShaderParameterSet("flare_crack_a", ImageTexture.CreateFromImage(lcArt.A));
        RenderingServer.GlobalShaderParameterSet("flare_crack_b", ImageTexture.CreateFromImage(lcArt.B));
        if (Args.Has("shot")) GD.Print($"longcut art: strip {(lcArt.Baked ? "baked" : "stand-in")} {lcArt.A.GetWidth()}x{lcArt.A.GetHeight()}");
    }

    static Image? LcLoad(string dir, string name)
    {
        var p = System.IO.Path.Combine(dir, name);
        if (!System.IO.File.Exists(p)) return null;
        var im = Image.LoadFromFile(p);
        if (im == null || im.IsEmpty()) return null;
        if (im.IsCompressed()) im.Decompress();
        im.Convert(Image.Format.Rgba8);
        return im;
    }

    static LcArt LcArtBuild(string dir)
    {
        var alb = LcLoad(dir, "crack_albedo.png");
        var nrm = LcLoad(dir, "crack_normal.png");
        var emi = LcLoad(dir, "crack_emis.png");
        var hgt = LcLoad(dir, "crack_height.png");
        LcArt art = alb != null && nrm != null && emi != null && hgt != null ? LcPack(alb, nrm, emi, hgt) : LcStandIn();
        // The main split's own centre (crack.json centre_m, 256 steps), so the jets and chunks rise from it, not from
        // the light's centroid that the side branches pull off it (r3c).
        try
        {
            var jp = System.IO.Path.Combine(dir, "crack.json");
            if (art.Baked && System.IO.File.Exists(jp))
            {
                using var doc = System.Text.Json.JsonDocument.Parse(System.IO.File.ReadAllText(jp));
                if (doc.RootElement.TryGetProperty("centre_m", out var c) && c.GetArrayLength() == 256)
                {
                    int k = 0;
                    foreach (var v in c.EnumerateArray()) art.Off[k++] = v.GetSingle();
                }
            }
        }
        catch (Exception ex) { GD.PrintErr($"longcut art: crack.json {ex.Message}"); }
        art.A.GenerateMipmaps();
        art.B.GenerateMipmaps();
        return art;
    }

    static LcArt LcPack(Image alb, Image nrm, Image emi, Image hgt)
    {
        int w = alb.GetWidth(), h = alb.GetHeight();
        foreach (var im in new[] { nrm, emi, hgt })
            if (im.GetWidth() != w || im.GetHeight() != h) im.Resize(w, h, Image.Interpolation.Bilinear);
        byte[] n = nrm.GetData(), e = emi.GetData(), g = hgt.GetData();
        var b = new byte[w * h * 4];
        var off = new float[256];
        var sw = new double[256];
        var sv = new double[256];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                int i = (y * w + x) * 4;
                b[i] = n[i]; b[i + 1] = n[i + 1];
                // (the core: the brightest of its channels, whether it is painted grey or gold)
                byte c = Math.Max(e[i], Math.Max(e[i + 1], e[i + 2]));
                b[i + 2] = c; b[i + 3] = g[i];
                double wt = (double)c * c;
                int k = x * 256 / w;
                sw[k] += wt; sv[k] += wt * (y + 0.5) / h;
            }
        float last = 0;
        for (int k = 0; k < 256; k++) off[k] = last = sw[k] > 1 ? (float)((sv[k] / sw[k] - 0.5) * 2.4) : last;
        return new LcArt { A = alb, B = Image.CreateFromData(w, h, false, Image.Format.Rgba8, b), Off = off, Baked = true };
    }

    static float LcHash(float x) { float s = Mathf.Sin(x * 91.7f + 17.3f) * 43758.5453f; return s - Mathf.Floor(s); }

    /// <summary>A stand-in strip until the baked one lands: SeamOffset's broken line, a crack 0.1-0.3 m wide with dark
    /// broken lips, a core deep in it, its normal from its depth.</summary>
    static LcArt LcStandIn()
    {
        const int W = 2048, H = 256;
        const float Len = 24, Band = 2.4f;
        var a = new byte[W * H * 4];
        var hgt = new float[W * H];
        var core = new float[W * H];
        var off = new float[256];
        for (int x = 0; x < W; x++)
        {
            float u = (x + 0.5f) / W, along = u * Len;
            float c = SeamOffset(along);
            float taper = Mathf.SmoothStep(0.25f, 1.4f, along) * Mathf.Lerp(1f, 0.45f, u) * (1 - Mathf.SmoothStep(Len - 1.2f, Len - 0.1f, along));
            float n1 = LcHash(Mathf.Floor(along / 0.7f)), n2 = LcHash(Mathf.Floor(along / 0.7f) + 1);
            float wob = Mathf.Lerp(n1, n2, along / 0.7f - Mathf.Floor(along / 0.7f));
            float pinch = LcHash(Mathf.Floor(along / 1.9f) + 40) > 0.8f ? 0.35f : 1;
            float hw = (0.07f + 0.14f * wob) * taper * pinch;
            float lip = hw + (0.1f + 0.16f * LcHash(Mathf.Floor(along / 0.31f) + 7)) * taper;
            if (x * 256 / W != (x + 1) * 256 / W || x == W - 1) off[x * 256 / W] = c;
            for (int y = 0; y < H; y++)
            {
                float across = ((y + 0.5f) / H - 0.5f) * Band;
                float d = Mathf.Abs(across - c) + (LcHash(x * 0.37f + y * 1.71f) - 0.5f) * 0.012f;
                int i = y * W + x;
                float inside = hw > 1e-4f ? 1 - Mathf.SmoothStep(hw * 0.85f, hw * 1.1f, d) : 0;
                float lipk = 1 - Mathf.SmoothStep(lip - 0.03f, lip + 0.03f, d);
                float cov = Mathf.Max(inside, lipk * 0.85f);
                // the edge texels empty (the strip clamps)
                if (y < 2 || y >= H - 2 || x < 2 || x >= W - 2) cov = 0;
                var col = new Color(0.035f, 0.028f, 0.022f).Lerp(new Color(0.1f, 0.078f, 0.058f), 1 - inside);
                a[i * 4] = (byte)(Mathf.Pow(col.R, 1 / 2.2f) * 255); a[i * 4 + 1] = (byte)(Mathf.Pow(col.G, 1 / 2.2f) * 255);
                a[i * 4 + 2] = (byte)(Mathf.Pow(col.B, 1 / 2.2f) * 255); a[i * 4 + 3] = (byte)(Mathf.Clamp(cov, 0, 1) * 255);
                hgt[i] = inside > 0 ? Mathf.Lerp(1f, Mathf.SmoothStep(0, hw, d) * 0.5f, inside) : 1 - 0.1f * lipk;
                core[i] = hw > 1e-4f ? (1 - Mathf.SmoothStep(0, hw * 0.5f, d)) * Mathf.Clamp(taper * 1.5f, 0, 1) : 0;
            }
        }
        var b = new byte[W * H * 4];
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
            {
                int i = y * W + x;
                // (slopes in metres: U steps 24/2048 m, V 2.4/256 m; the depth is 0.4 m at the bottom)
                float dx = (hgt[y * W + Math.Min(W - 1, x + 1)] - hgt[y * W + Math.Max(0, x - 1)]) * 0.4f / (2 * Len / W);
                float dy = (hgt[Math.Min(H - 1, y + 1) * W + x] - hgt[Math.Max(0, y - 1) * W + x]) * 0.4f / (2 * Band / H);
                var nv = new Vector3(-dx, -dy, 1).Normalized();
                b[i * 4] = (byte)((nv.X * 0.5f + 0.5f) * 255); b[i * 4 + 1] = (byte)((nv.Y * 0.5f + 0.5f) * 255);
                b[i * 4 + 2] = (byte)(Mathf.Clamp(core[i], 0, 1) * 255); b[i * 4 + 3] = (byte)(Mathf.Clamp(hgt[i], 0, 1) * 255);
            }
        return new LcArt
        {
            A = Image.CreateFromData(W, H, false, Image.Format.Rgba8, a), B = Image.CreateFromData(W, H, false, Image.Format.Rgba8, b), Off = off,
        };
    }

    /// <summary>The crack's centre across the line (m) this far along a line this long: the strip's own, scaled to it.</summary>
    float CrackOff(float along)
    {
        if (lcArt == null) return SeamOffset(along);
        float k = Mathf.Clamp(along / Math.Max(1, lcLen), 0, 1) * 255;
        int i = (int)k;
        return Mathf.Lerp(lcArt.Off[i], lcArt.Off[Math.Min(255, i + 1)], k - i);
    }

    /// <summary>The chunks' meshes: chunks.glb's, or rough dark boxes standing in.</summary>
    static Mesh[] ChunkMeshes()
    {
        if (lcChunkMeshes != null) return lcChunkMeshes;
        var list = new List<Mesh>();
        const string path = LcArtDir + "chunks.glb";
        if (ResourceLoader.Exists(path) && GD.Load<PackedScene>(path) is { } ps)
        {
            var root = ps.Instantiate();
            foreach (var n in root.FindChildren("*", "MeshInstance3D", true, false))
                if (((MeshInstance3D)n).Mesh is { } m) list.Add(m);
            root.Free();
        }
        if (list.Count == 0)
        {
            var mat = new StandardMaterial3D { AlbedoColor = new Color(0.09f, 0.075f, 0.06f), Roughness = 0.95f };
            for (int i = 0; i < 4; i++)
                list.Add(new BoxMesh { Size = new Vector3(0.22f + 0.1f * i, 0.12f + 0.04f * i, 0.18f + 0.05f * (3 - i)), Material = mat });
        }
        GD.Print($"longcut art: {list.Count} chunk meshes ({(ResourceLoader.Exists(path) ? "chunks.glb" : "stand-in")})");
        return lcChunkMeshes = list.ToArray();
    }
}

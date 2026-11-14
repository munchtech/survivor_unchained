using System;
using System.Globalization;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The ink line (L1 painted cel, B5): a compute pass on the current game camera's Compositor at PostTransparent, on the
/// linear HDR frame after the MSAA resolve and the transparent pass, before TAA (Godot 4.5.1 runs TAA after the
/// PostTransparent effects, so the line is jittered with the frame and antialiased by TAA like any edge), the tonemap
/// and the grade LUT. Its darkening is taken from the frame as it stood before the transparent pass (InkSnap, at
/// PreTransparent, copies it): out = max(post - pre x (1 - ink), post x ink), so the effects (spells, sparks, smoke, the
/// Flare) carry no line of what stands behind them (bible rule 8), while opaque pixels and her blended hair over its own
/// solid core keep theirs (--ink-mask off: today's multiply over everything). From the resolved depth: silhouettes on the near side and creases (InkShaders). The ink class
/// rides each lit material's roughness (cel_tag: n = round(r x 31) x 4 + class, roughness = n/127; Godot stores the
/// normal_roughness alpha as r x 127/255, 1 - that on a dynamic instance): 0 full, 1 silhouette only, 2 none, 3 full.
/// out = colour x mix(1, RigInk x k, a): the surface's own tone deepened, tinted by the light rig, never black.
/// Args: --ink off, --ink-px close,play (2.5,1.5 px at 1080p), --ink-depth a,b (the drop threshold max(a m, b x z)),
/// --ink-crease deg (45), --ink-fade near,far (30,60 m), --ink-dark k (0.25), --ink-rig r,g,b, --ink-dbg edges|class|code|lines (edges: as drawn; lines: before the effects' mask),
/// --ink-time (the pass's GPU ms), --ink-test S (rows of tagged spheres for the encoding, the static row set at S s).
/// </summary>
public partial class InkPass : CompositorEffect, InkRelease.IRids
{
    /// <summary>The rig's ink colours (the lead wires RigInk to the presets).</summary>
    public static readonly Color Night = new(0.42f, 0.45f, 0.85f), Day = new(0.85f, 0.6f, 0.5f);
    /// <summary>The light rig's ink, before the darkness k (--ink-rig pins it; then SetRig is ignored).</summary>
    public static Color RigInk { get; private set; } = Night;
    static bool rigPinned;
    public static void SetRig(Color c) { if (!rigPinned) RigInk = c; }

    public static bool On => Args.Get("ink") is not ("off" or "0");   // (read live: the look viewer's replays vary it)
    public static readonly bool Mask = Args.Get("ink-mask") is not ("off" or "0");
    public static float RClose = 2.5f, RPlay = 1.5f, ThA = 0.05f, ThB = 0.025f, CreaseDeg = 45, FadeNear = 30, FadeFar = 60, Dark = 0.25f,
        LumCut = 2.0f, ZClose = 3f, ZPlay = 16f, CreaseW = 0.5f, SilThin = 0.6f;
    public static int Dbg;
    public static readonly bool Time = Args.Has("ink-time");

    static InkPass()
    {
        float[]? V(string k, int n)
        {
            if (Args.Get(k) is not string s) return null;
            var p = s.Split(',');
            if (p.Length != n) { GD.PushWarning($"--{k}: want {n} numbers, got '{s}'"); return null; }
            var o = new float[n];
            for (int i = 0; i < n; i++)
                if (!float.TryParse(p[i], NumberStyles.Float, CultureInfo.InvariantCulture, out o[i])) { GD.PushWarning($"--{k}: bad '{s}'"); return null; }
            return o;
        }
        if (V("ink-px", 2) is [var rc, var rp]) { RClose = rc; RPlay = rp; }
        if (V("ink-depth", 2) is [var a, var b]) { ThA = a; ThB = b; }
        if (V("ink-crease", 1) is [var cd]) CreaseDeg = cd;
        if (V("ink-fade", 2) is [var fn, var ff]) { FadeNear = fn; FadeFar = Mathf.Max(ff, fn + 0.01f); }
        if (V("ink-dark", 1) is [var k]) Dark = k;
        if (V("ink-rig", 3) is [var r, var g, var bb]) { RigInk = new Color(r, g, bb); rigPinned = true; }
        Dbg = Args.Get("ink-dbg") switch { "edges" => 1, "class" => 2, "code" => 3, "lines" => 4, null => 0, var x => int.TryParse(x, out var d) ? d : 0 };
    }

    public double GpuMs = -1;
    /// <summary>(--ink-test) a request for the normal_roughness buffer's bytes, filled on the render thread.</summary>
    public volatile bool DumpReq;
    public volatile byte[]? Dump;
    public Vector2I DumpSize;
    /// <summary>The fog as the camera sees it (main thread, each frame): mode (0 none, 1 exponential, 2 depth), density,
    /// begin, end; curve, the volumetric fog's density and length.</summary>
    public Vector4 Fog, Fog2;

    RenderingDevice? rd;
    Rid shader, pipe, sampler, ubo;
    bool failed;

    public InkPass()
    {
        EffectCallbackType = EffectCallbackTypeEnum.PostTransparent;
        AccessResolvedColor = true;
        AccessResolvedDepth = true;
        NeedsNormalRoughness = true;
    }

    void Init()
    {
        rd = RenderingServer.GetRenderingDevice();
        var spirv = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = InkShaders.Line });
        if (!string.IsNullOrEmpty(spirv.CompileErrorCompute)) { GD.PushError($"ink shader: {spirv.CompileErrorCompute}"); failed = true; return; }
        shader = rd.ShaderCreateFromSpirV(spirv, "ink_line");
        pipe = rd.ComputePipelineCreate(shader);
        sampler = rd.SamplerCreate(new RDSamplerState
        {
            MinFilter = RenderingDevice.SamplerFilter.Nearest, MagFilter = RenderingDevice.SamplerFilter.Nearest,
            RepeatU = RenderingDevice.SamplerRepeatMode.ClampToEdge, RepeatV = RenderingDevice.SamplerRepeatMode.ClampToEdge,
        });
        ubo = rd.UniformBufferCreate(128);
        InkRelease.Track(this);
    }

    /// <summary>(render thread, from <see cref="InkRelease.Release"/>) frees the device RIDs; the next live frame remakes them.</summary>
    public void FreeRids(RenderingDevice dev)
    {
        foreach (var r in new[] { shader, sampler, ubo })
            if (r.IsValid) dev.FreeRid(r);
        shader = pipe = sampler = ubo = default;
        rd = null;
    }

    static RDUniform U(RenderingDevice.UniformType t, int binding, params Rid[] ids)
    {
        var u = new RDUniform { UniformType = t, Binding = binding };
        foreach (var id in ids) u.AddId(id);
        return u;
    }

    public override void _RenderCallback(int effectCallbackType, RenderData renderData)
    {
        if (!InkRelease.Live || failed || effectCallbackType != (int)EffectCallbackTypeEnum.PostTransparent) return;
        if (rd == null) { Init(); if (failed) return; }
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf || renderData.GetRenderSceneData() is not RenderSceneDataRD data) return;
        var size = buf.GetInternalSize();
        if (size.X <= 0 || size.Y <= 0) return;
        if (Time)
        {
            ulong t0 = 0, t1 = 0;
            for (uint i = 0, n = rd!.GetCapturedTimestampsCount(); i < n; i++)
            {
                var nm = rd.GetCapturedTimestampName(i);
                if (nm == "ink0") t0 = rd.GetCapturedTimestampGpuTime(i);
                else if (nm == "ink1") t1 = rd.GetCapturedTimestampGpuTime(i);
            }
            if (t1 > t0 && t0 > 0) GpuMs = (t1 - t0) / 1e6;
            rd.CaptureTimestamp("ink0");
        }
        var proj = data.GetCamProjection();
        // (the projection comes depth-corrected, reverse Z 0-1; NDC y taken as 2v - 1, Vulkan's, so an unflipped one is turned over)
        var flipY = Projection.Identity; if (proj.Y.Y > 0) flipY.Y = new Vector4(0, -1, 0, 0);
        var inv = proj.Inverse() * flipY;
        var m = new float[32];
        Vector4[] cols = { inv.X, inv.Y, inv.Z, inv.W };
        for (int c = 0; c < 4; c++) { m[c * 4] = cols[c].X; m[c * 4 + 1] = cols[c].Y; m[c * 4 + 2] = cols[c].Z; m[c * 4 + 3] = cols[c].W; }
        var rig = RigInk;
        m[16] = rig.R; m[17] = rig.G; m[18] = rig.B; m[19] = Dark;
        m[20] = Fog.X; m[21] = Fog.Y; m[22] = Fog.Z; m[23] = Fog.W;
        m[24] = Fog2.X; m[25] = Fog2.Y; m[26] = Fog2.Z; m[27] = Fog2.W;
        // (the pre-transparent copy, when InkSnap made it this frame at this size)
        bool hasPre = Mask && InkSnap.Fresh && buf.HasTexture(InkSnap.Ctx, InkSnap.Name) && InkSnap.Size == size;
        InkSnap.Fresh = false;
        m[28] = hasPre ? 1 : 0;
        rd!.BufferUpdate(ubo, 0, (uint)(m.Length * 4), MemoryMarshal.AsBytes(m.AsSpan()).ToArray());
        float scale = size.Y / 1080f;
        bool hasN = buf.HasTexture("forward_clustered", "normal_roughness");
        var push = new float[]
        {
            size.X, size.Y, RClose * scale, RPlay * scale,
            ThA, ThB, Mathf.Cos(Mathf.DegToRad(CreaseDeg)), hasN ? 1 : 0,
            FadeNear, FadeFar, Dbg, LumCut,
            ZClose, ZPlay, CreaseW, SilThin,
        };
        var pb = MemoryMarshal.AsBytes(push.AsSpan()).ToArray();
        for (uint v = 0, nv = buf.GetViewCount(); v < nv; v++)
        {
            Rid colour = buf.GetColorLayer(v), depth = buf.GetDepthLayer(v);
            Rid nr = hasN ? buf.GetTextureSlice("forward_clustered", "normal_roughness", v, 0, 1, 1) : depth;
            Rid pre = hasPre ? buf.GetTextureSlice(InkSnap.Ctx, InkSnap.Name, v, 0, 1, 1) : depth;
            var set = UniformSetCacheRD.GetCache(shader, 0, new Godot.Collections.Array<RDUniform>
            {
                U(RenderingDevice.UniformType.Image, 0, colour),
                U(RenderingDevice.UniformType.SamplerWithTexture, 1, sampler, depth),
                U(RenderingDevice.UniformType.SamplerWithTexture, 2, sampler, nr),
                U(RenderingDevice.UniformType.UniformBuffer, 3, ubo),
                U(RenderingDevice.UniformType.SamplerWithTexture, 4, sampler, pre),
            });
            long l = rd.ComputeListBegin();
            rd.ComputeListBindComputePipeline(l, pipe);
            rd.ComputeListBindUniformSet(l, set, 0);
            rd.ComputeListSetPushConstant(l, pb, (uint)pb.Length);
            rd.ComputeListDispatch(l, (uint)((size.X + 15) / 16), (uint)((size.Y + 15) / 16), 1);
            rd.ComputeListEnd();
        }
        if (Time) rd.CaptureTimestamp("ink1");
        if (DumpReq && hasN)
        {
            DumpReq = false; DumpSize = size;
            // (the buffer has no copy-from bit: a probe pass writes its alpha bytes to a storage buffer, read back once)
            var ps = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = InkShaders.Probe });
            var psh = rd.ShaderCreateFromSpirV(ps, "ink_probe");
            var ppipe = rd.ComputePipelineCreate(psh);
            uint bytes = (uint)(size.X * size.Y * 4);
            var sb = rd.StorageBufferCreate(bytes);
            var pset = rd.UniformSetCreate(new Godot.Collections.Array<RDUniform>
            {
                U(RenderingDevice.UniformType.SamplerWithTexture, 0, sampler, buf.GetTextureSlice("forward_clustered", "normal_roughness", 0, 0, 1, 1)),
                U(RenderingDevice.UniformType.StorageBuffer, 1, sb),
            }, psh, 0);
            var pp = MemoryMarshal.AsBytes(new float[] { size.X, size.Y, 0, 0 }.AsSpan()).ToArray();
            long l = rd.ComputeListBegin();
            rd.ComputeListBindComputePipeline(l, ppipe);
            rd.ComputeListBindUniformSet(l, pset, 0);
            rd.ComputeListSetPushConstant(l, pp, (uint)pp.Length);
            rd.ComputeListDispatch(l, (uint)((size.X + 15) / 16), (uint)((size.Y + 15) / 16), 1);
            rd.ComputeListEnd();
            var raw = rd.BufferGetData(sb);
            var outb = new byte[size.X * size.Y * 4];
            for (int i = 0; i < size.X * size.Y; i++) outb[i * 4 + 3] = raw[i * 4];
            Dump = outb;
            rd.FreeRid(sb); rd.FreeRid(psh);
        }
    }

}

/// <summary>The ink's copy of the frame before the transparent pass (PreTransparent, the resolved colour into the scene
/// buffers' ink/pre, one layer per view): InkPass takes its darkening from it, so effects drawn after carry no line.</summary>
public partial class InkSnap : CompositorEffect, InkRelease.IRids
{
    public static readonly StringName Ctx = "ink", Name = "pre";
    /// <summary>Set on the render thread when the copy is made; InkPass consumes it the same frame.</summary>
    public static volatile bool Fresh;
    public static Vector2I Size;
    public double GpuMs = -1;

    const string Copy = """
        #version 450
        layout(local_size_x = 16, local_size_y = 16, local_size_z = 1) in;
        layout(set = 0, binding = 0, rgba16f) uniform restrict readonly image2D src;
        layout(set = 0, binding = 1, rgba16f) uniform restrict writeonly image2D dst;
        void main() {
            ivec2 p = ivec2(gl_GlobalInvocationID.xy);
            if (any(greaterThanEqual(p, imageSize(src)))) return;
            imageStore(dst, p, imageLoad(src, p));
        }
        """;

    RenderingDevice? rd;
    Rid shader, pipe;
    bool failed;

    public InkSnap()
    {
        EffectCallbackType = EffectCallbackTypeEnum.PreTransparent;
        AccessResolvedColor = true;
    }

    public override void _RenderCallback(int effectCallbackType, RenderData renderData)
    {
        if (!InkRelease.Live || failed || effectCallbackType != (int)EffectCallbackTypeEnum.PreTransparent) return;
        if (rd == null)
        {
            rd = RenderingServer.GetRenderingDevice();
            var spirv = rd.ShaderCompileSpirVFromSource(new RDShaderSource { Language = RenderingDevice.ShaderLanguage.Glsl, SourceCompute = Copy });
            if (!string.IsNullOrEmpty(spirv.CompileErrorCompute)) { GD.PushError($"ink snap shader: {spirv.CompileErrorCompute}"); failed = true; return; }
            shader = rd.ShaderCreateFromSpirV(spirv, "ink_snap");
            pipe = rd.ComputePipelineCreate(shader);
            InkRelease.Track(this);
        }
        if (renderData.GetRenderSceneBuffers() is not RenderSceneBuffersRD buf) return;
        var size = buf.GetInternalSize();
        if (size.X <= 0 || size.Y <= 0) return;
        if (InkPass.Time)
        {
            ulong t0 = 0, t1 = 0;
            for (uint i = 0, n = rd.GetCapturedTimestampsCount(); i < n; i++)
            {
                var nm = rd.GetCapturedTimestampName(i);
                if (nm == "snap0") t0 = rd.GetCapturedTimestampGpuTime(i);
                else if (nm == "snap1") t1 = rd.GetCapturedTimestampGpuTime(i);
            }
            if (t1 > t0 && t0 > 0) GpuMs = (t1 - t0) / 1e6;
            rd.CaptureTimestamp("snap0");
        }
        uint nv = buf.GetViewCount();
        // (unique, kept: the buffers free and remake it on a resize)
        if (!buf.HasTexture(Ctx, Name))
            buf.CreateTexture(Ctx, Name, RenderingDevice.DataFormat.R16G16B16A16Sfloat,
                (uint)(RenderingDevice.TextureUsageBits.StorageBit | RenderingDevice.TextureUsageBits.SamplingBit),
                RenderingDevice.TextureSamples.Samples1, size, nv, 1, true, false);
        for (uint v = 0; v < nv; v++)
        {
            var set = UniformSetCacheRD.GetCache(shader, 0, new Godot.Collections.Array<RDUniform>
            {
                new RDUniform { UniformType = RenderingDevice.UniformType.Image, Binding = 0, }.With(buf.GetColorLayer(v)),
                new RDUniform { UniformType = RenderingDevice.UniformType.Image, Binding = 1, }.With(buf.GetTextureSlice(Ctx, Name, v, 0, 1, 1)),
            });
            long l = rd.ComputeListBegin();
            rd.ComputeListBindComputePipeline(l, pipe);
            rd.ComputeListBindUniformSet(l, set, 0);
            rd.ComputeListDispatch(l, (uint)((size.X + 15) / 16), (uint)((size.Y + 15) / 16), 1);
            rd.ComputeListEnd();
        }
        if (InkPass.Time) rd.CaptureTimestamp("snap1");
        Size = size;
        Fresh = true;
    }

    public void FreeRids(RenderingDevice dev)
    {
        if (shader.IsValid) dev.FreeRid(shader);
        shader = pipe = default;
        rd = null;
    }
}

/// <summary>(L1 lead 8) The ink effects free their device RIDs as the Ink node leaves the tree (FX2's pattern, as FxWorldDepth):
/// their predelete came only during the C# shutdown, after the render server's teardown began, and hung the quit.</summary>
public static class InkRelease
{
    public static volatile bool Live;
    public interface IRids { void FreeRids(RenderingDevice rd); }
    static readonly System.Collections.Generic.List<IRids> owners = new();
    public static void Track(IRids o) { lock (owners) if (!owners.Contains(o)) owners.Add(o); }

    public static void Release()
    {
        Live = false;
        RenderingServer.CallOnRenderThread(Callable.From(ReleaseNow));
    }

    static void ReleaseNow()
    {
        var rd = RenderingServer.GetRenderingDevice();
        if (rd == null) return;
        IRids[] all;
        lock (owners) { all = owners.ToArray(); owners.Clear(); }
        foreach (var o in all) o.FreeRids(rd);
        // (QUIT, lead 21: QuitPath releases at the quit request, then the Ink node again as it leaves the tree: one line)
        if (all.Length == 0 && said) return;
        said = true;
        GD.Print($"ink: released {all.Length} effect(s)");
    }
    static bool said;
}

static class RDUniformX
{
    public static RDUniform With(this RDUniform u, Rid id) { u.AddId(id); return u; }
}

/// <summary>Keeps the ink pass first on whichever camera the game draws through (play, close-up, Look, cinematics),
/// beside the compositors already there (BattleFx's MarkPass inserts itself first; Brush swaps its own in on a camera
/// change): checked before every frame draws, after their own updates. Feeds the camera's fog. Made by Game unless --ink off.</summary>
public partial class Ink : Node
{
    readonly InkPass effect = new();
    readonly InkSnap snap = new();
    readonly Compositor own;
    double gpuSum, snapSum, vpSum; int gpuN; ulong frames;

    public Ink()
    {
        Name = "Ink";
        own = new Compositor { CompositorEffects = InkPass.Mask ? new Godot.Collections.Array<CompositorEffect> { snap, effect } : new Godot.Collections.Array<CompositorEffect> { effect } };
    }

    public override void _Ready()
    {
        // The ink class rides the roughness: the screen-space roughness limiter (specular AA, on by default) would widen
        // a curved surface's roughness and scramble its code. (project.godot: rendering/anti_aliasing/screen_space_roughness_limiter/enabled=false)
        RenderingServer.ScreenSpaceRoughnessLimiterSetActive(false, 0.25f, 0.18f);
        RenderingServer.FramePreDraw += Sync;
        InkRelease.Live = true;
        if (InkPass.Time) RenderingServer.ViewportSetMeasureRenderTime(GetViewport().GetViewportRid(), true);
        if (Args.Get("ink-test") is string t) testAt = float.TryParse(t, NumberStyles.Float, CultureInfo.InvariantCulture, out var s) && s > 0 ? s : 4;
    }

    public override void _ExitTree() { RenderingServer.FramePreDraw -= Sync; InkRelease.Release(); }

    void Sync()
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null) return;
        var comp = cam.Compositor;
        if (comp == null) cam.Compositor = own;
        else
        {
            var fx = comp.CompositorEffects;
            int i = fx.IndexOf(effect), j = InkPass.Mask ? fx.IndexOf(snap) : 0;
            if (i != 0 || (InkPass.Mask && j != 1))
            {
                var d = fx.Duplicate();
                d.Remove(effect); d.Remove(snap);
                d.Insert(0, effect);
                if (InkPass.Mask) d.Insert(1, snap);
                comp.CompositorEffects = d;
            }
        }
        var env = cam.Environment ?? cam.GetWorld3D()?.Environment;
        if (env != null && env.FogEnabled)
            effect.Fog = env.FogMode == Godot.Environment.FogModeEnum.Depth
                ? new Vector4(2, env.FogDensity, env.FogDepthBegin, env.FogDepthEnd)
                : new Vector4(1, env.FogDensity, 0, 0);
        else effect.Fog = Vector4.Zero;
        effect.Fog2 = new Vector4(env?.FogDepthCurve ?? 1, env is { VolumetricFogEnabled: true } ? env.VolumetricFogDensity : 0, env?.VolumetricFogLength ?? 0, 0);
        if (testAt > 0) Test(cam);
        if (InkPass.Time && ++frames > 60 && effect.GpuMs >= 0)
        {
            gpuSum += effect.GpuMs; snapSum += Math.Max(snap.GpuMs, 0); gpuN++;
            vpSum += RenderingServer.ViewportGetMeasuredRenderTimeGpu(GetViewport().GetViewportRid());
            if (gpuN == 120)
            {
                GD.Print($"INK gpu {gpuSum / gpuN:0.000} ms, snap {snapSum / gpuN:0.000} ms, viewport {vpSum / gpuN:0.000} ms (mean of {gpuN} frames, {GetViewport().GetVisibleRect().Size}, mask {(InkPass.Mask ? "on" : "off")})");
                gpuSum = 0; snapSum = 0; vpSum = 0; gpuN = 0;
            }
        }
    }

    // --ink-test S: two rows of four spheres coded class 0-3 (roughness (16 x 4 + class)/127): the upper row follows the
    // camera (moved every frame: a dynamic instance), the lower one is set in the world once at S seconds (static).
    float testAt;
    int frame, shown;
    bool dumped;
    Node3D? dynRow, statRow;
    void Test(Camera3D cam)
    {
        if (dynRow == null)
        {
            dynRow = Row(true); statRow = Row(false);
            AddChild(dynRow); AddChild(statRow);
            statRow.Visible = false;
        }
        var basis = cam.GlobalTransform.Basis;
        var at = cam.GlobalTransform * new Vector3(0, 0.55f, -4.5f);
        // (a hair's turn each frame: an unchanged transform is not "moved", so the row would read static)
        dynRow.GlobalTransform = new Transform3D(basis.Rotated(basis.Z.Normalized(), (frame++ & 1) * 1e-3f), at);
        if (statRow!.Visible && ++shown == 30) effect.DumpReq = true;
        if (effect.Dump is { } bytes && !dumped)
        {
            dumped = true;
            var sz = effect.DumpSize; var vs = GetViewport().GetVisibleRect().Size;
            foreach (var row in new[] { dynRow, statRow })
                for (int c = 0; c < 4; c++)
                {
                    var sp = cam.UnprojectPosition(((Node3D)row.GetChild(c)).GlobalPosition);
                    int x = (int)(sp.X * sz.X / vs.X), y = (int)(sp.Y * sz.Y / vs.Y);
                    if (x < 0 || y < 0 || x >= sz.X || y >= sz.Y) { GD.Print($"INK test {row.Name} c{c}: off screen"); continue; }
                    int b = bytes[(y * sz.X + x) * 4 + 3], n = b <= 127 ? b : 255 - b;
                    GD.Print($"INK test {row.Name} class {c} (code {16 * 4 + c}): byte {b} -> n {n}, {(b > 127 ? "dynamic" : "static")}, class {n & 3} at ({x},{y})");
                }
            var hist = new int[8];
            for (int i = 3; i < bytes.Length; i += 4) { int b = bytes[i], n = b <= 127 ? b : 255 - b; hist[(n & 3) + (b > 127 ? 4 : 0)]++; }
            GD.Print($"INK test frame classes static 0-3: {hist[0]} {hist[1]} {hist[2]} {hist[3]}, dynamic 0-3: {hist[4]} {hist[5]} {hist[6]} {hist[7]}");
        }
        if (!statRow.Visible && Engine.GetProcessFrames() / 60.0 >= testAt)
        {
            statRow.GlobalTransform = new Transform3D(basis, cam.GlobalTransform * new Vector3(0, 0.25f, -4.5f));
            statRow.Visible = true;
        }
    }

    static Node3D Row(bool dyn)
    {
        var row = new Node3D { Name = dyn ? "InkTestDyn" : "InkTestStatic" };
        var sh = new Shader { Code = "shader_type spatial;\nuniform float code;\nvoid fragment() { ALBEDO = vec3(0.5); ROUGHNESS = code / 127.0; }\n" };
        for (int c = 0; c < 4; c++)
        {
            var mat = new ShaderMaterial { Shader = sh };
            mat.SetShaderParameter("code", 16 * 4 + c);
            row.AddChild(new MeshInstance3D { Mesh = new SphereMesh { Radius = 0.11f, Height = 0.22f }, MaterialOverride = mat, Position = new Vector3(-0.45f + 0.3f * c, 0, 0) });
        }
        return row;
    }
}

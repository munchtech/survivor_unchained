using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using Godot;
using SurvivorUnchained.View;
using SurvivorUnchained.Viewer;

namespace SurvivorUnchained.Play;

/// <summary>
/// The live look viewer (docs/tools/LOOK_VIEWER.md): --look-viewer DROP keeps the game open on a Marionette package
/// and shows each edit of it in a few seconds, and answers capture requests with the same frames Marionette's
/// tools/npc/game_frame.py takes, without booting the game per shot. Dev builds only (Args).
///
/// Every refresh is a deterministic replay, not a live swap: the shot's switches set (Args.Override, exactly as
/// game_frame.py passes them), the package's caches forgotten (NpcPackage.Forget, NpcDye), the renderer's TIME put back
/// to 0 on a draw lined up with the TAA jitter's cycle (time_rollover_secs made tiny for that one draw; MotionClock with
/// it), then the main scene loaded afresh and run at the fixed 60 fps to the camera's seconds, where Shots takes its
/// frame as it would (Shots.ViewerFile: no quit). game_frame.gd's per-frame terms (--gf-off, --gf-light,
/// --gf-light-only, --gf-global), its given spot offset (and the Waystation's table shade), --gf-solo and --gf-mods are
/// done here, and its dump written beside the frame. Between replays the tree is paused and nothing is drawn
/// (RenderingServer.RenderLoopEnabled off), so an idle viewer costs no GPU; the godot turn (tools/turn.py) is held only
/// for a burst of replays.
/// </summary>
public partial class LookViewer : Node
{
    static LookViewer? one;

    /// <summary>From Game._Ready: the one viewer, on the root (it outlives every replayed scene).</summary>
    public static void Install(Game host)
    {
        if (one != null || Args.Get("look-viewer") is not string drop || drop == "1") return;
        one = new LookViewer(drop) { Name = "LookViewer", ProcessMode = ProcessModeEnum.Always, ProcessPriority = 1 << 30 };
        host.GetTree().Root.CallDeferred(Node.MethodName.AddChild, one);
    }

    /// <summary>A replay's draw lined up with the TAA jitter's cycle (16 draws, Godot's TAA_JITTER_COUNT): the reset
    /// draw comes after a multiple of 16, so each draw of the replay has the jitter game_frame's run had.</summary>
    const int JitterCycle = 16;
    const string RollKey = "rendering/limits/time/time_rollover_secs";

    readonly string drop, liveDir, liveJson, reqDir, statusFile, outLive, root;
    readonly IReadOnlyList<string> launch;
    readonly Stopwatch clock = Stopwatch.StartNew();
    readonly ChangeWatch watch;
    readonly int changeAt;
    readonly bool turns;
    readonly string turnPy, turnWho;
    double nextPoll, nextStatus, nextSlow, nextStop;
    string gameCommit = "", headNow = "", shadersAtStart = "", shadersNow = "";
    int dirtyAtStart;
    System.Threading.Tasks.Task? slow;

    sealed class Job
    {
        public string Kind = "live";            // live | request | f9
        public string? Request;                 // requests/ID.json's ID
        public LookSettings S = null!;
        public string PkgDir = "", Name = "";
        public string? Overlay;
        public string Out = "";
        public int Cam;
        public double QueuedAt, ChangedAt = double.NaN, TurnAt = double.NaN;
        public string Fingerprint = "";
        public List<PackageFingerprint.Entry> Files = new();
        public List<string> Done = new();
    }

    readonly Queue<Job> jobs = new();
    Job? job;
    enum St { Booting, Idle, Turn, Align, Change, Run, Failed }
    St st = St.Booting;
    string lastError = "", lastFrame = "";
    double lastFrameAt;
    Process? turnProc;
    string turnOut = "";
    bool turnHeld;

    // replay state
    int frameInRun, drawIdx;
    bool resetArmed, rollRestore;
    double rollWas = 3600;
    double runStart, sceneT;
    long resetDrawn;
    // game_frame.gd's per-frame terms
    HashSet<string> off = new();
    List<string> pats = new(), only = new();
    Dictionary<string, double[]> globals = new();
    Vector3 shift;
    bool spotDone, soloDone;
    readonly List<(Node3D N, Vector3 At)> moved = new();
    int hookFrames;
    string? pendingTaken;
    double pendingShotT;
    long pendingDrawn;

    LookViewer(string drop)
    {
        this.drop = drop.Replace('\\', '/').TrimEnd('/');
        liveDir = $"{this.drop}/live";
        liveJson = $"{this.drop}/live.json";
        reqDir = $"{this.drop}/requests";
        statusFile = $"{this.drop}/status.json";
        outLive = $"{this.drop}/live_out";
        root = ProjectSettings.GlobalizePath("res://").TrimEnd('/', '\\');
        root = Path.GetDirectoryName(root)!.Replace('\\', '/');
        launch = OS.GetCmdlineUserArgs();
        watch = new ChangeWatch(new DiskStats(), new[] { liveDir, liveJson });
        changeAt = (int)Args.Num("look-change-at", 1);
        turns = Args.Get("look-turn") != "off";
        turnPy = Args.Get("look-turn-py") is string tp && tp != "1" ? tp : "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py";
        turnWho = $"look-viewer: replays (pid {OS.GetProcessId()})";
    }

    sealed class DiskStats : IFileStats
    {
        public IEnumerable<FileStat> List(string r)
        {
            if (File.Exists(r)) { var fi = new FileInfo(r); return new[] { new FileStat(r, fi.Length, fi.LastWriteTimeUtc.Ticks) }; }
            if (!Directory.Exists(r)) return Array.Empty<FileStat>();
            try
            {
                return new DirectoryInfo(r).EnumerateFiles("*", SearchOption.AllDirectories)
                    .Select(fi => new FileStat(fi.FullName.Replace('\\', '/'), fi.Length, fi.LastWriteTimeUtc.Ticks)).ToList();
            }
            catch (IOException) { return Array.Empty<FileStat>(); }
        }
    }

    double Now => clock.Elapsed.TotalSeconds;

    public override void _Ready()
    {
        foreach (var d in new[] { drop, liveDir, reqDir, outLive }) Directory.CreateDirectory(d);
        if (File.Exists($"{drop}/stop")) File.Delete($"{drop}/stop");   // (a stop left by a viewer that was ended)
        AudioServer.SetBusMute(0, true);
        gameCommit = Git("rev-parse", "HEAD");
        dirtyAtStart = Git("status", "--porcelain", "--", "godot").Split('\n', StringSplitOptions.RemoveEmptyEntries).Length;
        headNow = gameCommit;
        shadersAtStart = shadersNow = ShaderPrint();
        rollWas = (double)ProjectSettings.GetSetting(RollKey, 3600.0);
        RenderingServer.FramePreDraw += PreDraw;
        RenderingServer.FramePostDraw += PostDraw;
        Shots.ViewerTaken += Taken;
        GD.Print($"look viewer: watching {drop} (game {gameCommit[..Math.Min(10, gameCommit.Length)]}, shaders {shadersAtStart}, turns {(turns ? "on" : "off")})");
        Hold();
        st = St.Idle;
        WriteStatus();
        beat = new System.Threading.Timer(_ => Beat(), null, 1000, 1000);
    }

    public override void _ExitTree()
    {
        RenderingServer.FramePreDraw -= PreDraw;
        RenderingServer.FramePostDraw -= PostDraw;
        Shots.ViewerTaken -= Taken;
        beat?.Dispose(); beat = null;
        GiveTurn(wait: true);
        st = St.Failed; lastError = "viewer closed";
        WriteStatus("stopped");
    }

    public override void _Notification(int what)
    {
        if (what == NotificationWMCloseRequest) GiveTurn(wait: true);
    }

    // ---- input: the replay's game gets none (a touch would reset the close-up's idle); F9 captures live, F5 replays it

    public override void _Input(InputEvent e)
    {
        if (e is InputEventKey { Pressed: true, Echo: false } k)
        {
            if (k.Keycode == Key.F9) { WriteF9(); GetViewport().SetInputAsHandled(); return; }
            if (k.Keycode == Key.F5) { watch.Again(); GetViewport().SetInputAsHandled(); return; }
        }
        if (st is St.Align or St.Change or St.Run) GetViewport().SetInputAsHandled();
    }

    void WriteF9()
    {
        var id = "f9_" + DateTime.Now.ToString("yyyyMMdd_HHmmss");
        var body = Json.Stringify(new Godot.Collections.Dictionary { ["package"] = "live", ["out"] = $"{drop}/captures", ["id"] = id });
        // (live.json's settings: merged by the request reader, which takes live.json's when the request names "live")
        File.WriteAllText($"{reqDir}/{id}.json", body);
        GD.Print($"look viewer: F9: capture of live asked ({reqDir}/{id}.json)");
    }

    // ---- the loop

    public override void _Process(double delta)
    {
        double now = Now;
        if (now >= nextStatus) { nextStatus = now + 1; WriteStatus(); }
        if (now >= nextStop) { nextStop = now + 0.25; if (StopAsked()) return; }
        if (now >= nextSlow && (slow == null || slow.IsCompleted))
        {
            nextSlow = now + 10;
            slow = System.Threading.Tasks.Task.Run(() => { headNow = Git("rev-parse", "HEAD"); shadersNow = ShaderPrint(); });
        }
        switch (st)
        {
            case St.Idle:
            case St.Failed:
                if (now >= nextPoll) { nextPoll = now + 0.1; Poll(now); }
                if (jobs.Count > 0) NextJob();
                else if (turnHeld) GiveTurn(wait: false);
                break;
            case St.Turn:
                TurnStep();
                break;
            case St.Align:
                // (the reset draw: the next one, when the draws so far end a jitter cycle)
                if ((long)Engine.GetFramesDrawn() % JitterCycle == JitterCycle - 1)
                {
                    resetArmed = true; frameInRun = 0; drawIdx = -1; resetDrawn = Engine.GetFramesDrawn();
                    st = St.Change;
                    if (changeAt == 0) ChangeScene();
                }
                break;
            case St.Change:
                frameInRun++;
                if (frameInRun >= changeAt) ChangeScene();
                break;
            case St.Run:
                frameInRun++;
                sceneT += delta;
                Late(delta);
                if (pendingTaken != null) Captured();
                else if (now - runStart > 120) Fail($"no frame within 120 s of the replay ({job!.S.CamList[job.Cam]})");
                break;
        }
    }

    /// <summary>look.py stop, in any state (a replay too): the turn given back and the game quit by its own path.</summary>
    bool StopAsked()
    {
        if (st == St.Booting || !File.Exists($"{drop}/stop")) return false;
        {
            File.Delete($"{drop}/stop");
            GD.Print("look viewer: stop asked");
            GiveTurn(wait: true);
            WriteStatus("stopped");
            RenderingServer.RenderLoopEnabled = true;
            GetTree().Paused = false;
            QuitPath.Request(GetTree(), 0, "look viewer stop");
            st = St.Booting;
            return true;
        }
    }

    void Poll(double now)
    {
        // requests first (someone waits on them), then the live package
        if (Directory.Exists(reqDir))
        {
            var files = new DirectoryInfo(reqDir).EnumerateFiles("*.json").Select(fi => new FileStat(fi.FullName, fi.Length, fi.LastWriteTimeUtc.Ticks)).ToList();
            foreach (var id in RequestQueue.Pending(files, DateTime.UtcNow.Ticks))
            {
                if (jobs.Any(j => j.Request == id) || job?.Request == id) continue;
                try { jobs.Enqueue(RequestJob(id, now)); }
                catch (Exception e) when (e is LookError or IOException) { Answer(id, false, e.Message, null); }
            }
        }
        if (job == null && jobs.Count == 0 && watch.Poll(now))
        {
            watch.Taken();
            if (!File.Exists($"{liveDir}/manifest.json")) { lastError = $"no live package ({liveDir}/manifest.json)"; return; }
            try { var j = LiveJob(now); j.ChangedAt = watch.ChangedAt; jobs.Enqueue(j); }
            catch (Exception e) when (e is LookError or IOException) { lastError = "live: " + e.Message; st = St.Failed; GD.PushWarning("look viewer: live: " + e.Message); }
        }
    }

    LookSettings LiveSettings() => File.Exists(liveJson) ? LookSettings.Parse(File.ReadAllText(liveJson), "live") : LookSettings.Parse("{\"id\": \"live\"}");

    Job LiveJob(double now)
    {
        var s = LiveSettings();
        return Prepare(new Job { Kind = "live", S = s, PkgDir = liveDir, Out = outLive, QueuedAt = now });
    }

    Job RequestJob(string id, double now)
    {
        var text = File.ReadAllText($"{reqDir}/{id}.json");
        var r = LookSettings.Parse(text, id);
        if (r.Package is null) throw new LookError("package: a package folder, or \"live\"");
        LookSettings s = r;
        string dir;
        if (r.Package == "live")
        {
            // (live's settings, with what the request sets over them)
            var baseJson = File.Exists(liveJson) ? File.ReadAllText(liveJson) : "{}";
            s = LookSettings.Parse(Merge(baseJson, text), id);
            dir = liveDir;
        }
        else dir = r.Package.Replace('\\', '/');
        var j = new Job { Kind = id.StartsWith("f9_") ? "f9" : "request", Request = id, S = s, PkgDir = dir, Out = (s.Out ?? $"{drop}/out").Replace('\\', '/'), QueuedAt = now };
        return Prepare(j);
    }

    static string Merge(string baseJson, string over)
    {
        var a = Json.ParseString(baseJson).AsGodotDictionary();
        foreach (var kv in Json.ParseString(over).AsGodotDictionary()) a[kv.Key] = kv.Value;
        a.Remove("id"); if (Json.ParseString(over).AsGodotDictionary().TryGetValue("id", out var id)) a["id"] = id;
        return Json.Stringify(a);
    }

    Job Prepare(Job j)
    {
        var (w, h) = j.S.SizeWH;
        var vs = DrawnSize();
        if (vs.X != w || vs.Y != h) throw new LookError($"size {j.S.Size}: this viewer draws {vs.X}x{vs.Y} (look.py start --size)");
        string? manName = null;
        if (Directory.Exists(j.PkgDir) && File.Exists($"{j.PkgDir}/manifest.json"))
        {
            var d = j.PkgDir;
            var fp = PackageFingerprint.Compute(rel => File.Exists($"{d}/{rel}") ? File.ReadAllBytes($"{d}/{rel}") : null);
            if (fp.Missing.Count > 0) throw new LookError($"package {d}: missing {string.Join(", ", fp.Missing)}");
            j.Fingerprint = fp.Hash; j.Files = fp.Files;
            var m = Json.ParseString(File.ReadAllText($"{d}/manifest.json"));
            if (m.VariantType == Variant.Type.Dictionary && m.AsGodotDictionary().TryGetValue("name", out var mn) && mn.VariantType == Variant.Type.String) manName = (string)mn;
            j.Name = LookSettings.NameFor(j.S.Name, d, manName);
            j.Overlay = Path.GetFullPath(d).Replace('\\', '/');
        }
        else if (Godot.FileAccess.FileExists($"{NpcPackage.Dir(j.PkgDir)}/manifest.json"))
        {
            j.Name = j.S.Name ?? j.PkgDir; j.Overlay = null; j.Fingerprint = "game package";
        }
        else throw new LookError($"no package folder (manifest.json) or game package {j.PkgDir}");
        return j;
    }

    void NextJob()
    {
        job = jobs.Dequeue();
        job.Cam = 0;
        if (!turns || turnHeld) { job.TurnAt = Now; BeginCam(); return; }
        st = St.Turn;
        StartTurn();
    }

    // ---- the godot turn (tools/turn.py), taken for a burst and given back while idle

    void StartTurn()
    {
        turnOut = "";
        var psi = new ProcessStartInfo("python") { UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true, CreateNoWindow = true, WorkingDirectory = root };
        foreach (var a in new[] { turnPy, "take", "godot", turnWho, "--wait", "1", "--root", root }) psi.ArgumentList.Add(a);
        turnProc = Process.Start(psi);
    }

    void TurnStep()
    {
        if (turnProc == null || !turnProc.HasExited) return;
        turnOut = (turnProc.StandardOutput.ReadToEnd() + turnProc.StandardError.ReadToEnd()).Trim();
        int code = turnProc.ExitCode;
        turnProc.Dispose(); turnProc = null;
        if (code == 0) { turnHeld = true; job!.TurnAt = Now; BeginCam(); return; }
        if (code == 1) { StartTurn(); return; }   // (busy: asking again keeps the place in the queue)
        Fail($"no godot turn (turn.py exit {code}): {turnOut}");
    }

    void GiveTurn(bool wait)
    {
        if (!turnHeld) return;
        turnHeld = false;
        try
        {
            var psi = new ProcessStartInfo("python") { UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = root };
            foreach (var a in new[] { turnPy, "give", "godot", turnWho }) psi.ArgumentList.Add(a);
            var p = Process.Start(psi);
            if (wait) p?.WaitForExit(15000);
        }
        catch (Exception e) { GD.PushWarning($"look viewer: turn give failed ({e.Message})"); }
    }

    // ---- a replay

    void BeginCam()
    {
        var j = job!;
        var cam = j.S.CamList[j.Cam];
        var args = new List<string> { "--look-viewer", drop };
        // (the launch's own --look-* switches kept: they are the viewer's, not the shot's)
        for (int i = 0; i < launch.Count; i++)
            if (launch[i].StartsWith("--look-") && launch[i] != "--look-viewer")
            {
                args.Add(launch[i]);
                if (i + 1 < launch.Count && !launch[i + 1].StartsWith("--")) args.Add(launch[++i]);
            }
        args.AddRange(j.S.GameArgs(cam, j.Name, j.Overlay, j.S.Tag(cam)));
        Args.Override(args);
        NpcPackage.Forget(j.Name);
        NpcDye.Restart();
        var (terms, lp, _) = j.S.OffTerms();
        off = terms.ToHashSet(); pats = lp; only = j.S.LightOnly.Select(x => x.ToLowerInvariant()).ToList(); globals = j.S.Global;
        shift = Vector3.Zero; spotDone = false; soloDone = false; moved.Clear(); hookFrames = 0; hookT = 0; sceneT = 0;
        pendingTaken = null;
        Shots.ViewerFile = $"{j.Out}/{j.S.Id}/{cam}.png";
        Directory.CreateDirectory($"{j.Out}/{j.S.Id}");
        if (File.Exists(Shots.ViewerFile)) File.Delete(Shots.ViewerFile);
        GD.Print($"look viewer: replay {j.Kind} {j.Request ?? ""} {j.Name} {cam}: {string.Join(' ', args)}");
        RenderingServer.RenderLoopEnabled = true;
        Engine.MaxFps = 0;
        runStart = Now;
        st = St.Align;
    }

    void ChangeScene()
    {
        GetTree().Paused = false;
        var main = (string)ProjectSettings.GetSetting("application/run/main_scene");
        var e = GetTree().ChangeSceneToFile(main);
        if (e != Error.Ok) { Fail($"the main scene did not load ({e})"); return; }
        st = St.Run;
        frameInRun = 0;
    }

    void PreDraw()
    {
        if (resetArmed)
        {
            // TIME: this draw wraps it at a tiny rollover (begin_frame: time = fmod(time + step, rollover)), so the
            // replay's draws carry the TIME a fresh run's do; the rollover goes back after the draw.
            resetArmed = false;
            ProjectSettings.SetSetting(RollKey, 1e-6);
            rollRestore = true;
            MotionClock.Restart();
            drawIdx = 0;
            return;
        }
        if (drawIdx >= 0) drawIdx++;
        if (st != St.Run) return;
        hookFrames++;
        Terms();
    }

    void PostDraw()
    {
        if (rollRestore) { rollRestore = false; ProjectSettings.SetSetting(RollKey, rollWas); }
        foreach (var (n, at) in moved) if (IsInstanceValid(n)) n.GlobalPosition = at;
        moved.Clear();
    }

    void Taken(string file, double shotT, long drawn)
    {
        if (st != St.Run) return;
        pendingTaken = file; pendingShotT = shotT; pendingDrawn = drawn;
    }

    void Captured()
    {
        var j = job!;
        var cam = j.S.CamList[j.Cam];
        double now = Now;
        var file = pendingTaken!;
        pendingTaken = null;
        var dir = $"{j.Out}/{j.S.Id}";
        WriteDump($"{dir}/{cam}_dump.json");
        var rec = new Godot.Collections.Dictionary
        {
            ["frame"] = file, ["cam"] = cam, ["kind"] = j.Kind, ["request"] = j.Request ?? "", ["settings"] = ToVariant(j.S.Record()),
            ["package"] = new Godot.Collections.Dictionary
            {
                ["dir"] = j.PkgDir, ["name"] = j.Name, ["overlay"] = j.Overlay ?? "", ["fingerprint"] = j.Fingerprint,
                ["files"] = new Godot.Collections.Array(j.Files.Select(f => (Variant)new Godot.Collections.Dictionary { ["file"] = f.File, ["size"] = f.Size, ["sha256"] = f.Sha256 })),
            },
            ["game_commit"] = gameCommit, ["game_head_now"] = headNow, ["game_dirty_at_start"] = dirtyAtStart,
            ["shader_fingerprint"] = shadersAtStart, ["shader_fingerprint_now"] = shadersNow,
            ["args"] = new Godot.Collections.Array(Argv(j, cam).Select(a => (Variant)a)),
            ["timings"] = new Godot.Collections.Dictionary
            {
                ["turn_wait_s"] = Math.Round(j.TurnAt - j.QueuedAt, 3), ["replay_s"] = Math.Round(now - runStart, 3),
                ["since_queued_s"] = Math.Round(now - j.QueuedAt, 3),
                ["change_to_frame_s"] = double.IsNaN(j.ChangedAt) ? -1 : Math.Round(now - j.ChangedAt, 3),
            },
            ["alignment"] = new Godot.Collections.Dictionary
            {
                ["reset_after_drawn"] = resetDrawn, ["change_at"] = changeAt, ["draws_since_reset"] = drawIdx, ["shots_clock_s"] = Math.Round(pendingShotT, 4),
                ["capture_drawn_since_reset"] = pendingDrawn - resetDrawn - 1,
            },
        };
        File.WriteAllText($"{dir}/{cam}.json", Json.Stringify(rec, " "));
        lastFrame = file; lastFrameAt = Time.GetUnixTimeFromSystem();
        GD.Print($"look viewer: {file} in {now - runStart:0.00} s (drawn since reset {pendingDrawn - resetDrawn - 1}, shots clock {pendingShotT:0.000})"
            + (double.IsNaN(j.ChangedAt) ? "" : $"; change to frame {now - j.ChangedAt:0.00} s"));
        j.Done.Add(file);
        j.Cam++;
        if (j.Cam < j.S.CamList.Count) { BeginCam(); return; }
        if (j.Request != null) Answer(j.Request, true, "", j);
        job = null;
        Hold();
        st = St.Idle;
        WriteStatus();
    }

    static IEnumerable<string> Argv(Job j, string cam) => j.S.GameArgs(cam, j.Name, j.Overlay, j.S.Tag(cam));

    void Fail(string why)
    {
        GD.PushWarning("look viewer: FAILED: " + why);
        lastError = why;
        if (job?.Request is string id) Answer(id, false, why, job);
        job = null;
        Shots.ViewerFile = null;
        Hold();
        st = St.Failed;
        WriteStatus();
    }

    void Answer(string id, bool ok, string why, Job? j)
    {
        var d = new Godot.Collections.Dictionary
        {
            ["id"] = id, ["ok"] = ok, ["error"] = why, ["at"] = Time.GetUnixTimeFromSystem(),
            ["frames"] = new Godot.Collections.Array((j?.Done ?? new()).Select(f => (Variant)f)),
            ["out"] = j == null ? "" : $"{j.Out}/{j.S.Id}", ["fingerprint"] = j?.Fingerprint ?? "", ["game_commit"] = gameCommit,
        };
        File.WriteAllText($"{reqDir}/{id}.{(ok ? "done" : "failed")}.json", Json.Stringify(d, " "));
    }

    /// <summary>Held: the tree paused and nothing drawn (the window keeps the last frame); the loop idles slowly.</summary>
    void Hold()
    {
        Shots.ViewerFile = null;
        GetTree().Paused = true;
        RenderingServer.RenderLoopEnabled = false;
        Engine.MaxFps = 20;
    }

    // ---- game_frame.gd's per-frame work: Late (after the game's own nodes, process priority 1 << 30) and _pre_draw

    void Late(double dt)
    {
        // (last on the root: its _Input comes first, so the replay's game gets no input)
        if (GetIndex() != GetParent().GetChildCount() - 1) GetParent().MoveChild(this, GetParent().GetChildCount() - 1);
        var npc = GetTree().Root.FindChild("ShotNpc", true, false) as Node3D;
        if (npc == null) return;
        var s = job!.S;
        if (s.Mods != "" || s.Solo)
        {
            var mods = s.Mods.ToLowerInvariant().Split(',', StringSplitOptions.RemoveEmptyEntries).ToHashSet();
            foreach (var sk in npc.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>())
                foreach (var m in sk.GetChildren().OfType<SkeletonModifier3D>())
                    if (m.Active && (mods.Contains("all") || mods.Contains(ModName(m).ToLowerInvariant()))) { m.Active = false; GD.Print($"game_frame: ShotNpc layer {ModName(m)} off"); }
            if (s.Solo && !soloDone)
            {
                soloDone = true;
                int n = 0;
                foreach (var sk in GetTree().Root.FindChildren("*", "Skeleton3D", true, false).OfType<Skeleton3D>())
                    if (!npc.IsAncestorOf(sk)) { sk.Visible = false; n++; }
                GD.Print($"game_frame: solo: {n} other figure(s) hidden");
            }
        }
        hookT += dt;
        if (s.SpotOffset() is { } o && !spotDone && hookT >= 1.0)
        {
            spotDone = true;
            shift = new Vector3((float)o.Dx, 0, (float)o.Dz);
            GD.Print($"game_frame: spot offset given {shift}");
        }
        if (shift != Vector3.Zero) ApplyShift(npc);
    }
    double hookT;

    static string ModName(Node m) => m.GetScript().AsGodotObject() is Script sc && sc.ResourcePath != "" ? sc.ResourcePath.GetFile().GetBaseName() : m.GetClass();

    void ApplyShift(Node3D npc)
    {
        moved.Clear();
        var near = npc.GlobalPosition;
        moved.Add((npc, npc.GlobalPosition));
        npc.GlobalPosition += shift;
        if (GetViewport().GetCamera3D() is { } cam) { moved.Add((cam, cam.GlobalPosition)); cam.GlobalPosition += shift; }
        foreach (var l in GetTree().Root.FindChildren("*", "Light3D", true, false).OfType<Light3D>())
        {
            if (l is DirectionalLight3D) continue;
            var p = ((string)l.GetPath()).ToLowerInvariant();
            if (p.Contains("/lights/light") || p.Contains("fires/") || p.Contains("posthead")) continue;
            if (l.GlobalPosition.DistanceTo(near) < 8f) { moved.Add((l, l.GlobalPosition)); l.GlobalPosition += shift; }
        }
    }

    List<Godot.Environment> Envs()
    {
        var o = new List<Godot.Environment>();
        foreach (var we in GetTree().Root.FindChildren("*", "WorldEnvironment", true, false).OfType<WorldEnvironment>())
            if (we.Environment != null && !o.Contains(we.Environment)) o.Add(we.Environment);
        if (GetViewport().GetCamera3D() is { Environment: { } ce } && !o.Contains(ce)) o.Add(ce);
        return o;
    }

    void Terms()
    {
        if (off.Count == 0 && pats.Count == 0 && only.Count == 0 && globals.Count == 0) return;
        foreach (var env in Envs())
        {
            if (off.Contains("glow")) env.GlowEnabled = false;
            if (off.Contains("grade")) env.AdjustmentEnabled = false;
            if (off.Contains("lut")) env.AdjustmentColorCorrection = null;
            if (off.Contains("tonemap")) env.TonemapMode = Godot.Environment.ToneMapper.Linear;
            if (off.Contains("exposure")) env.TonemapExposure = 1f;
            if (off.Contains("fog")) env.FogEnabled = false;
            if (off.Contains("volfog")) env.VolumetricFogEnabled = false;
            if (off.Contains("ssao")) env.SsaoEnabled = false;
            if (off.Contains("ssil")) env.SsilEnabled = false;
            if (off.Contains("ssr")) env.SsrEnabled = false;
            if (off.Contains("sdfgi")) env.SdfgiEnabled = false;
            if (off.Contains("ambient")) env.AmbientLightSource = Godot.Environment.AmbientSource.Disabled;
            if (off.Contains("reflection")) env.ReflectedLightSource = Godot.Environment.ReflectionSource.Disabled;
        }
        var vp = GetViewport();
        if (off.Contains("taa")) vp.UseTaa = false;
        if (off.Contains("msaa")) vp.Msaa3D = Viewport.Msaa.Disabled;
        foreach (var l in GetTree().Root.FindChildren("*", "Light3D", true, false).OfType<Light3D>())
        {
            var p = ((string)l.GetPath()).ToLowerInvariant();
            bool h = off.Contains("lights") || pats.Any(p.Contains);
            if (only.Count > 0) h = h || !only.Any(p.Contains);
            if (h && l.Visible) l.Visible = false;
            if (off.Contains("shadows") || (off.Contains("keyshadow") && l is DirectionalLight3D)) l.ShadowEnabled = false;
        }
        foreach (var (n, v) in globals)
            RenderingServer.GlobalShaderParameterSet(n, v.Length switch
            {
                1 => (float)v[0], 2 => new Vector2((float)v[0], (float)v[1]), 3 => new Vector3((float)v[0], (float)v[1], (float)v[2]),
                _ => new Vector4((float)v[0], (float)v[1], (float)v[2], (float)v[3]),
            });
    }

    // ---- game_frame.gd's dump (same keys as _dump), written at the capture

    static Godot.Collections.Array C(Color c) => new() { Snap(c.R), Snap(c.G), Snap(c.B), Snap(c.A) };
    static double Snap(float x) => Math.Round(x / 0.0001) * 0.0001;
    static Godot.Collections.Array V(Vector3 v) => new() { v.X, v.Y, v.Z };

    void WriteDump(string path)
    {
        var d = new Godot.Collections.Dictionary
        {
            ["frame"] = drawIdx, ["time_s"] = Math.Round(drawIdx / 60.0, 2), ["off"] = new Godot.Collections.Array(off.Select(x => (Variant)x)),
            ["globals_set"] = new Godot.Collections.Array(globals.Keys.Select(x => (Variant)x)),
        };
        var envs = new Godot.Collections.Array();
        foreach (var env in Envs())
            envs.Add(new Godot.Collections.Dictionary
            {
                ["background"] = (int)env.BackgroundMode, ["tonemap"] = (int)env.TonemapMode, ["exposure"] = env.TonemapExposure, ["white"] = env.TonemapWhite,
                ["glow"] = env.GlowEnabled, ["glow_intensity"] = env.GlowIntensity, ["glow_strength"] = env.GlowStrength, ["glow_bloom"] = env.GlowBloom,
                ["glow_blend"] = (int)env.GlowBlendMode, ["glow_hdr_threshold"] = env.GlowHdrThreshold, ["glow_hdr_scale"] = env.GlowHdrScale,
                ["glow_levels"] = new Godot.Collections.Array(Enumerable.Range(0, 7).Select(i => (Variant)env.GetGlowLevel(i))),
                ["adjust"] = env.AdjustmentEnabled, ["brightness"] = env.AdjustmentBrightness, ["contrast"] = env.AdjustmentContrast, ["saturation"] = env.AdjustmentSaturation,
                ["lut"] = env.AdjustmentColorCorrection != null,
                ["ambient_source"] = (int)env.AmbientLightSource, ["ambient_color"] = C(env.AmbientLightColor), ["ambient_energy"] = env.AmbientLightEnergy,
                ["ambient_sky"] = env.AmbientLightSkyContribution, ["reflection_source"] = (int)env.ReflectedLightSource,
                ["fog"] = env.FogEnabled, ["fog_mode"] = (int)env.FogMode, ["fog_density"] = env.FogDensity, ["fog_color"] = C(env.FogLightColor), ["fog_energy"] = env.FogLightEnergy,
                ["fog_sky_affect"] = env.FogSkyAffect, ["fog_sun_scatter"] = env.FogSunScatter, ["fog_height"] = env.FogHeight, ["fog_height_density"] = env.FogHeightDensity,
                ["fog_depth_begin"] = env.FogDepthBegin, ["fog_depth_end"] = env.FogDepthEnd, ["fog_aerial"] = env.FogAerialPerspective,
                ["volfog"] = env.VolumetricFogEnabled, ["volfog_density"] = env.VolumetricFogDensity, ["volfog_albedo"] = C(env.VolumetricFogAlbedo),
                ["volfog_emission"] = C(env.VolumetricFogEmission), ["volfog_gi"] = env.VolumetricFogGIInject, ["volfog_ambient"] = env.VolumetricFogAmbientInject,
                ["volfog_length"] = env.VolumetricFogLength, ["volfog_aniso"] = env.VolumetricFogAnisotropy,
                ["ssao"] = env.SsaoEnabled, ["ssil"] = env.SsilEnabled, ["ssr"] = env.SsrEnabled, ["sdfgi"] = env.SdfgiEnabled,
            });
        d["envs"] = envs;
        var lights = new Godot.Collections.Array();
        foreach (var l in GetTree().Root.FindChildren("*", "Light3D", true, false).OfType<Light3D>())
        {
            var e = new Godot.Collections.Dictionary
            {
                ["path"] = (string)l.GetPath(), ["class"] = l.GetClass(), ["visible"] = l.IsVisibleInTree(), ["energy"] = l.LightEnergy,
                ["indirect"] = l.LightIndirectEnergy, ["volfog"] = l.LightVolumetricFogEnergy, ["color"] = C(l.LightColor), ["specular"] = l.LightSpecular,
                ["cull_mask"] = l.LightCullMask, ["layers"] = l.Layers, ["shadow"] = l.ShadowEnabled, ["negative"] = l.LightNegative,
                ["bake"] = (int)l.LightBakeMode, ["pos"] = V(l.GlobalPosition), ["dir"] = V(-l.GlobalBasis.Z), ["angular"] = 0.0,
            };
            if (l is DirectionalLight3D dl) { e["angular"] = dl.LightAngularDistance; e["sky_mode"] = (int)dl.SkyMode; }
            if (l is OmniLight3D ol) { e["range"] = ol.OmniRange; e["atten"] = ol.OmniAttenuation; }
            if (l is SpotLight3D sl) { e["range"] = sl.SpotRange; e["atten"] = sl.SpotAttenuation; e["angle"] = sl.SpotAngle; }
            lights.Add(e);
        }
        d["lights"] = lights;
        if (GetViewport().GetCamera3D() is { } cam)
            d["camera"] = new Godot.Collections.Dictionary
            {
                ["path"] = (string)cam.GetPath(), ["pos"] = V(cam.GlobalPosition), ["fwd"] = V(-cam.GlobalBasis.Z), ["fov"] = cam.Fov, ["near"] = cam.Near, ["far"] = cam.Far,
                ["attributes"] = cam.Attributes != null,
            };
        File.WriteAllText(path, Json.Stringify(d, " "));
    }

    static Variant ToVariant(object? o) => o switch
    {
        null => default,
        string s => s, bool b => b, double d => d, int i => i,
        IEnumerable<string> l => new Godot.Collections.Array(l.Select(x => (Variant)x)),
        Dictionary<string, double[]> g => Dict(g.Select(kv => (kv.Key, (Variant)new Godot.Collections.Array(kv.Value.Select(x => (Variant)x))))),
        Dictionary<string, object?> m => Dict(m.Select(kv => (kv.Key, ToVariant(kv.Value)))),
        _ => o.ToString() ?? "",
    };

    static Godot.Collections.Dictionary Dict(IEnumerable<(string K, Variant V)> kvs)
    {
        var d = new Godot.Collections.Dictionary();
        foreach (var (k, v) in kvs) d[k] = v;
        return d;
    }

    // ---- status.json: the heartbeat Marionette reads to fail loudly when the viewer is stale

    void WriteStatus(string? state = null)
    {
        var why = new Godot.Collections.Array();
        if (headNow != "" && gameCommit != "" && headNow != gameCommit) why.Add($"the game checkout moved to {headNow[..Math.Min(10, headNow.Length)]} since the viewer started at {gameCommit[..Math.Min(10, gameCommit.Length)]} (restart it: look.py stop, start)");
        if (shadersNow != shadersAtStart) why.Add("godot/shaders changed since the viewer started (shaders are read once: restart it)");
        var showing = job ?? null;
        var d = new Godot.Collections.Dictionary
        {
            ["state"] = state ?? st switch { St.Idle => "idle", St.Turn => "waiting-turn", St.Align or St.Change or St.Run => "replaying", St.Failed => "failed", _ => "booting" },
            ["pid"] = OS.GetProcessId(), ["main_at"] = Math.Round(Time.GetUnixTimeFromSystem(), 3), ["drop"] = drop, ["game_root"] = root,
            ["game_commit"] = gameCommit, ["game_head_now"] = headNow, ["game_dirty_at_start"] = dirtyAtStart,
            ["shader_fingerprint"] = shadersAtStart, ["shader_fingerprint_now"] = shadersNow, ["stale"] = why.Count > 0, ["stale_why"] = why,
            ["turn"] = turnHeld ? "held" : st == St.Turn ? "waiting" : "free", ["turn_name"] = turnWho,
            ["size"] = $"{DrawnSize().X}x{DrawnSize().Y}",
            ["replaying"] = job == null ? new Godot.Collections.Dictionary() : new Godot.Collections.Dictionary
            {
                ["kind"] = job.Kind, ["request"] = job.Request ?? "", ["package"] = job.PkgDir, ["name"] = job.Name, ["fingerprint"] = job.Fingerprint,
                ["cam"] = job.Cam < job.S.CamList.Count ? job.S.CamList[job.Cam] : "",
            },
            ["shown"] = new Godot.Collections.Dictionary { ["frame"] = lastFrame, ["at"] = lastFrameAt },
            ["queue"] = new Godot.Collections.Array(jobs.Select(j => (Variant)(j.Request ?? j.Kind))),
            ["last_error"] = lastError,
        };
        statusBody = Json.Stringify(d, " ");
        Beat();
    }

    /// <summary>The frames Shots saves are the viewport's texture: its size, not the (content-scaled) visible rect.</summary>
    Vector2I DrawnSize() => GetViewport().GetTexture()?.GetSize() is { } t ? new Vector2I((int)t.X, (int)t.Y) : DisplayServer.WindowGetSize();

    // The heartbeat is written from a timer thread, so a replay's scene load (the main thread busy for many seconds)
    // never reads as a dead viewer; main_at says when the main thread last wrote its state (look.py: hung when old).
    string? statusBody;
    readonly object statusLock = new();
    System.Threading.Timer? beat;

    void Beat()
    {
        var b = statusBody;
        if (b == null || b.Length < 2) return;
        lock (statusLock)
        {
            try
            {
                var now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0;
                File.WriteAllText(statusFile + ".tmp", "{\n \"heartbeat\": " + now.ToString("0.000", System.Globalization.CultureInfo.InvariantCulture) + "," + b[1..]);
                File.Move(statusFile + ".tmp", statusFile, true);
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }
    }

    string Git(params string[] a)
    {
        try
        {
            var psi = new ProcessStartInfo("git") { UseShellExecute = false, RedirectStandardOutput = true, CreateNoWindow = true };
            psi.ArgumentList.Add("-C"); psi.ArgumentList.Add(root);
            foreach (var x in a) psi.ArgumentList.Add(x);
            using var p = Process.Start(psi)!;
            var o = p.StandardOutput.ReadToEnd();
            p.WaitForExit(10000);
            return o.Trim();
        }
        catch (Exception) { return ""; }
    }

    string ShaderPrint()
    {
        var dir = $"{root}/godot/shaders";
        if (!Directory.Exists(dir)) return "";
        try
        {
            return PackageFingerprint.Tree(Directory.EnumerateFiles(dir, "*", SearchOption.AllDirectories)
                .Where(f => !f.EndsWith(".uid") && !f.EndsWith(".import"))
                .Select(f => (Path.GetRelativePath(dir, f), File.ReadAllBytes(f))));
        }
        catch (IOException) { return "?"; }
    }
}

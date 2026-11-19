using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using Godot;
using SurvivorUnchained.Core;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/// <summary>The in-game bug report: F8 (or "Report a bug" in the pause menu) freezes the last 30 s of clip, takes the
/// screenshot, and opens a small box; Send writes report.json, shot.png, clip.avi, godot.log and the save beside the
/// game (BugReports/) or in user://. Dev switches for proof runs: --bug-tester, --bug-dir, --bug-auto-at,
/// --bug-auto-zone with --bug-auto-after, --bug-box-shot.</summary>
public partial class BugReporter : CanvasLayer
{
    public static BugReporter? Instance { get; private set; }
    const string Prefs = "user://bugreport.json";

    readonly Game g;
    Control? box;
    LineEdit? nameEdit, titleEdit;
    TextEdit? descEdit;
    Button? sendBtn;
    Image? shot;
    (List<byte[]> Jpegs, double Fps)? clip;
    bool prevPaused, resumeClip, askName;
    string tester = "";
    readonly ConcurrentQueue<string> done = new();
    string toast = "";
    double toastLeft;
    Label? toastLabel;
    readonly List<Thread> threads = new();
    // the pause menu's snapshot: the world as it was before the menu opened
    Image? snapShot;
    (List<byte[]> Jpegs, double Fps)? snapClip;
    // proof runs
    string? autoZone;
    double autoAfter = -1, autoAt = -1, zoneSince, clock;
    string? lastZone;
    bool autoDone;
    string? boxShotPath;
    double boxShotAt = -1;

    public BugReporter(Game game)
    {
        g = game;
        Layer = 100;
        ProcessMode = ProcessModeEnum.Always;
        Instance = this;
    }

    public override void _Ready()
    {
        toastLabel = Style.Label("", Style.UiBold, 18, Kit.Ink, false, HorizontalAlignment.Center, true);
        toastLabel.SetAnchorsPreset(Control.LayoutPreset.CenterTop);
        toastLabel.GrowHorizontal = Control.GrowDirection.Both;
        toastLabel.Position = new Vector2(0, 24);
        toastLabel.MouseFilter = Control.MouseFilterEnum.Ignore;
        toastLabel.Visible = false;
        AddChild(toastLabel);
        tester = Args.Get("bug-tester") ?? ReadPrefs();
        autoZone = Args.Get("bug-auto-zone");
        autoAfter = autoZone != null ? Args.Num("bug-auto-after", 5) : -1;
        autoAt = Args.Has("bug-auto-at") ? Args.Num("bug-auto-at", 5) : -1;
        boxShotPath = Args.Get("bug-box-shot");
        if (boxShotPath != null) boxShotAt = 3;
    }

    public override void _ExitTree()
    {
        foreach (var t in threads) t.Join();
    }

    static string ReadPrefs()
    {
        try
        {
            using var f = Godot.FileAccess.Open(Prefs, Godot.FileAccess.ModeFlags.Read);
            if (f == null) return "";
            using var d = JsonDocument.Parse(f.GetAsText());
            return d.RootElement.TryGetProperty("tester", out var t) ? t.GetString() ?? "" : "";
        }
        catch { return ""; }
    }

    static void WritePrefs(string name)
    {
        try
        {
            using var f = Godot.FileAccess.Open(Prefs, Godot.FileAccess.ModeFlags.Write);
            f?.StoreString(JsonSerializer.Serialize(new { tester = name }));
        }
        catch { }
    }

    public bool IsOpen => box != null;

    string ZoneId => g.Zone?.Id ?? g.Mode;

    public override void _Input(InputEvent e)
    {
        if (e is not InputEventKey { Pressed: true, Echo: false } k) return;
        if (k.Keycode == Key.F8 && box == null)
        {
            OpenFresh();
            GetViewport().SetInputAsHandled();
        }
        else if (k.Keycode == Key.Escape && box != null)
        {
            Cancel();
            GetViewport().SetInputAsHandled();
        }
    }

    /// <summary>The pause menu opened: keep the world's last frame and the clip as they were before it.</summary>
    public void SnapshotNow()
    {
        if (box != null) return;
        try
        {
            snapShot = GetViewport().GetTexture().GetImage();
            var rec = ClipRecorder.Instance;
            if (rec != null && rec.Enabled) { snapClip = rec.Freeze(); rec.Resume(); }
            else snapClip = null;
        }
        catch (Exception ex) { GD.PrintErr($"bugreport: snapshot failed: {ex.Message}"); }
    }

    void OpenFresh()
    {
        shot = GetViewport().GetTexture().GetImage();
        var rec = ClipRecorder.Instance;
        clip = rec != null && rec.Enabled ? rec.Freeze() : null;
        resumeClip = rec != null;
        Open();
    }

    /// <summary>From the pause menu's "Report a bug": the snapshot taken when it opened.</summary>
    public void OpenFromPause()
    {
        if (box != null) return;
        if (snapShot == null) { OpenFresh(); return; }
        shot = snapShot; clip = snapClip; resumeClip = false;
        Open();
    }

    void Open()
    {
        prevPaused = GetTree().Paused;
        GetTree().Paused = true;
        askName = tester.Trim().Length == 0;
        Build();
    }

    void Close()
    {
        box?.QueueFree();
        box = null;
        GetTree().Paused = prevPaused;
        if (resumeClip) ClipRecorder.Instance?.Resume();
        resumeClip = false;
        snapShot = null; snapClip = null;
    }

    void Cancel() { if (box != null) Close(); }

    static LineEdit Field(string placeholder, int size)
    {
        var edit = new LineEdit { PlaceholderText = placeholder, MaxLength = 120, CustomMinimumSize = new Vector2(440, 36), SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
        Style.Font(edit, Style.UiBold, size, Kit.Ink, false);
        edit.AddThemeColorOverride("font_placeholder_color", Kit.Faint);
        edit.AddThemeColorOverride("caret_color", Style.EmberHi);
        StyleBoxFlat Ruled(Color c) => new() { BgColor = Colors.Transparent, BorderColor = c, BorderWidthBottom = 1, ContentMarginLeft = 10, ContentMarginRight = 2, ContentMarginTop = 4, ContentMarginBottom = 6 };
        edit.AddThemeStyleboxOverride("normal", Ruled(Kit.Edge));
        edit.AddThemeStyleboxOverride("focus", Ruled(Style.Ember));
        return edit;
    }

    void Build()
    {
        var root = new Control { MouseFilter = Control.MouseFilterEnum.Stop };
        root.SetAnchorsPreset(Control.LayoutPreset.FullRect);
        root.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.55f), MouseFilter = Control.MouseFilterEnum.Ignore, AnchorRight = 1, AnchorBottom = 1 });
        var center = new CenterContainer { AnchorRight = 1, AnchorBottom = 1, MouseFilter = Control.MouseFilterEnum.Ignore };
        root.AddChild(center);
        var panel = Style.Panel(Kit.Window(28, 24, 22));
        panel.CustomMinimumSize = new Vector2(500, 0);
        center.AddChild(panel);
        var col = Style.V(Style.Gap3);
        panel.AddChild(col);
        col.AddChild(new Title("Report a bug", 30, false));
        col.AddChild(Kit.RuleH());

        if (askName)
        {
            col.AddChild(Style.Label("Your name", Style.UiBold, 14, Kit.HeadInk, false, HorizontalAlignment.Left, false));
            nameEdit = Field("Your name", 18);
            nameEdit.MaxLength = 24;
            col.AddChild(nameEdit);
        }
        else nameEdit = null;

        col.AddChild(Style.Label("What went wrong", Style.UiBold, 14, Kit.HeadInk, false, HorizontalAlignment.Left, false));
        titleEdit = Field("In a few words", 18);
        col.AddChild(titleEdit);

        col.AddChild(Style.Label("More (optional)", Style.UiBold, 14, Kit.HeadInk, false, HorizontalAlignment.Left, false));
        descEdit = new TextEdit { CustomMinimumSize = new Vector2(440, 110), WrapMode = TextEdit.LineWrappingMode.Boundary, PlaceholderText = "What you did, what you saw, what you expected" };
        Style.Font(descEdit, Style.UiBold, 16, Kit.Ink, false);
        descEdit.AddThemeColorOverride("font_placeholder_color", Kit.Faint);
        descEdit.AddThemeColorOverride("caret_color", Style.EmberHi);
        StyleBoxFlat Boxed(Color c) => new() { BgColor = new Color(0, 0, 0, 0.25f), BorderColor = c, BorderWidthBottom = 1, BorderWidthTop = 1, BorderWidthLeft = 1, BorderWidthRight = 1, ContentMarginLeft = 8, ContentMarginRight = 8, ContentMarginTop = 6, ContentMarginBottom = 6 };
        descEdit.AddThemeStyleboxOverride("normal", Boxed(Kit.Edge));
        descEdit.AddThemeStyleboxOverride("focus", Boxed(Style.Ember));
        col.AddChild(descEdit);

        bool withClip = clip is { Jpegs.Count: > 0 };
        col.AddChild(Style.Label(withClip ? "The screenshot and the last 30 seconds are attached." : "Screenshot only: the clip is off.", Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Left, false));
        col.AddChild(Kit.RuleH());

        sendBtn = Kit.Keyed(Act.Confirm, "Send", () => Send(false), Style.EmberHi);
        var cancel = Kit.Keyed(Act.Cancel, "Cancel", Cancel);
        var folder = Kit.Word("Open reports folder", OpenFolder, Kit.Ink2, 15);
        var row = Style.H(Style.Gap5, sendBtn, cancel, folder);
        col.AddChild(row);

        void Refresh()
        {
            bool ok = Valid();
            sendBtn!.Disabled = !ok;
            sendBtn.Modulate = Colors.White with { A = ok ? 1f : 0.4f };
        }
        titleEdit.TextChanged += _ => Refresh();
        if (nameEdit != null) nameEdit.TextChanged += _ => Refresh();
        titleEdit.TextSubmitted += _ => { if (Valid()) Send(false); };
        if (nameEdit != null) nameEdit.TextSubmitted += _ => titleEdit.GrabFocus();
        Refresh();

        AddChild(root);
        box = root;
        Control first = nameEdit != null && nameEdit.Text.Length == 0 ? nameEdit : titleEdit;
        first.CallDeferred(Control.MethodName.GrabFocus);
    }

    bool Valid() => titleEdit != null && titleEdit.Text.Trim().Length > 0 && (nameEdit == null || nameEdit.Text.Trim().Length > 0);

    /// <summary>The folder the reports go in: beside the executable in an export if it can be written, else user://BugReports.</summary>
    public static string ReportsDir()
    {
        if (Args.Get("bug-dir") is { Length: > 0 } dev) return Path.GetFullPath(dev);
        if (OS.HasFeature("template"))
        {
            try
            {
                string dir = Path.Combine(Path.GetDirectoryName(OS.GetExecutablePath()) ?? ".", "BugReports");
                Directory.CreateDirectory(dir);
                string probe = Path.Combine(dir, ".probe" + System.Environment.ProcessId);
                File.WriteAllText(probe, "x");
                File.Delete(probe);
                return dir;
            }
            catch { }
        }
        return ProjectSettings.GlobalizePath("user://BugReports");
    }

    public static void OpenFolder()
    {
        try
        {
            string dir = ReportsDir();
            Directory.CreateDirectory(dir);
            OS.ShellOpen(dir);
        }
        catch (Exception ex) { GD.PrintErr($"bugreport: could not open the folder: {ex.Message}"); }
    }

    void Send(bool sync)
    {
        if (!Valid()) return;
        string title = titleEdit!.Text.Trim(), desc = descEdit!.Text.Trim();
        if (nameEdit != null) { tester = nameEdit.Text.Trim(); WritePrefs(tester); }
        var img = shot; var cl = clip;
        var r = Gather(title, desc, cl);
        string root = ReportsDir();
        Close();
        void Work()
        {
            try { done.Enqueue(Write(root, r, img, cl)); }
            catch (Exception ex) { GD.PrintErr($"bugreport: failed: {ex}"); done.Enqueue("failed: " + ex.Message); }
        }
        if (sync) Work();
        else { var t = new Thread(Work) { IsBackground = false, Name = "bugreport" }; threads.Add(t); t.Start(); }
    }

    static string? ReadBuild(string key)
    {
        try
        {
            if (!Godot.FileAccess.FileExists("res://data/build.json")) return null;
            using var f = Godot.FileAccess.Open("res://data/build.json", Godot.FileAccess.ModeFlags.Read);
            using var d = JsonDocument.Parse(f.GetAsText());
            return d.RootElement.TryGetProperty(key, out var v) ? v.GetString() : null;
        }
        catch { return null; }
    }

    BugReport Gather(string title, string desc, (List<byte[]> Jpegs, double Fps)? cl)
    {
        var now = DateTimeOffset.Now;
        var rec = ClipRecorder.Instance;
        var (avg, p99, max) = BugReports.FrameStats(rec?.FrameMs() ?? new List<double>());
        var j = (Journey?)g.Journey;
        var p = g.Battle?.Player;
        var mem = OS.GetMemoryInfo();
        long ram = mem.TryGetValue("physical", out var ph) ? (long)ph : 0;
        var scr = DisplayServer.ScreenGetSize();
        var win = DisplayServer.WindowGetSize();
        int frames = cl?.Jpegs.Count ?? 0;
        double fps = cl?.Fps ?? 0;
        return new BugReport
        {
            Title = title, Description = desc, Tester = tester,
            Build = (string)ProjectSettings.GetSetting("application/config/version", "0"),
            Sha = ReadBuild("sha") ?? "dev",
            Flavor = Core.Demo.On ? "demo" : "full",
            TimeLocal = now.ToString("yyyy-MM-dd'T'HH:mm:ss.fffzzz", CultureInfo.InvariantCulture),
            TimeUtc = now.UtcDateTime.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture),
            Zone = ZoneId, ZoneName = g.Zone?.Name ?? ZoneId,
            Seed = j?.World.Map is { } m ? m.Seed : null,
            Mode = g.Mode,
            Level = j?.Ch.Level,
            X = p?.X, Z = p?.Z,
            DenClears = null,
            Os = $"{OS.GetName()} {OS.GetVersion()}",
            Cpu = $"{OS.GetProcessorName()} ({OS.GetProcessorCount()} threads)",
            Gpu = RenderingServer.GetVideoAdapterName(),
            GpuDriver = $"{RenderingServer.GetVideoAdapterVendor()} {RenderingServer.GetVideoAdapterApiVersion()}",
            Ram = ram > 0 ? $"{ram / (1024.0 * 1024 * 1024):0.0} GB" : null,
            Screen = $"screen {scr.X}x{scr.Y}, window {win.X}x{win.Y}",
            Renderer = (string)ProjectSettings.GetSetting("rendering/renderer/rendering_method", ""),
            FrameMsAvg = avg, FrameMsP99 = p99, FrameMsMax = max,
            ClipFrames = frames, ClipFps = fps, ClipSeconds = fps > 0 ? frames / fps : 0,
        };
    }

    static string Write(string root, BugReport r, Image? img, (List<byte[]> Jpegs, double Fps)? cl)
    {
        Directory.CreateDirectory(root);
        var existing = Directory.GetDirectories(root).Select(d => Path.GetFileName(d) ?? "");
        r.Number = BugReports.NextNumber(existing);
        string name = BugReports.FolderName(r.Tester ?? "", r.Number, DateTime.Now, r.Zone ?? "title");
        string dir = Path.Combine(root, name);
        Directory.CreateDirectory(dir);
        r.Files.Clear();
        if (img != null) { img.SavePng(Path.Combine(dir, "shot.png")); r.Files.Add("shot.png"); }
        if (cl is { Jpegs.Count: > 0 } c)
        {
            MjpegAvi.WriteFile(Path.Combine(dir, "clip.avi"), ClipRecorder.Width, ClipRecorder.Height, c.Fps, c.Jpegs);
            r.Files.Add("clip.avi");
        }
        try
        {
            string log = ProjectSettings.GlobalizePath("user://logs/godot.log");
            if (File.Exists(log))
            {
                using var src = new FileStream(log, FileMode.Open, System.IO.FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
                using var dst = File.Create(Path.Combine(dir, "godot.log"));
                src.CopyTo(dst);
                r.Files.Add("godot.log");
            }
        }
        catch (Exception ex) { GD.PrintErr($"bugreport: log copy failed: {ex.Message}"); }
        try
        {
            string saves = ProjectSettings.GlobalizePath("user://saves");
            if (Directory.Exists(saves))
            {
                string to = Path.Combine(dir, "save");
                Directory.CreateDirectory(to);
                foreach (var f in Directory.GetFiles(saves))
                {
                    File.Copy(f, Path.Combine(to, Path.GetFileName(f)), true);
                    r.Files.Add("save/" + Path.GetFileName(f));
                }
            }
        }
        catch (Exception ex) { GD.PrintErr($"bugreport: save copy failed: {ex.Message}"); }
        r.Files.Add("report.json");
        File.WriteAllText(Path.Combine(dir, "report.json"), BugReports.ToJson(r));
        GD.Print($"bugreport: wrote {Path.GetFullPath(dir)}");
        return dir;
    }

    public override void _Process(double delta)
    {
        clock += delta;
        string zid = ZoneId;
        if (zid != lastZone) { lastZone = zid; zoneSince = clock; }
        while (done.TryDequeue(out var d))
        {
            toast = d.StartsWith("failed") ? "Bug report " + d : "Bug report saved: " + d;
            toastLeft = 6;
        }
        if (toastLabel != null)
        {
            toastLeft = Math.Max(0, toastLeft - delta);
            toastLabel.Visible = toastLeft > 0;
            toastLabel.Text = toast;
        }
        // proof runs
        if (!autoDone && box == null && ((autoAt >= 0 && clock >= autoAt) || (autoZone != null && zid == autoZone && clock - zoneSince >= autoAfter)))
        {
            autoDone = true;
            OpenFresh();
            if (tester.Length == 0) tester = "Autopilot";
            nameEdit = null;
            titleEdit!.Text = "Autopilot proof report";
            descEdit!.Text = "made by --bug-auto-after";
            Send(true);
        }
        if (boxShotPath != null && boxShotAt >= 0 && clock >= boxShotAt)
        {
            if (box == null) { OpenFresh(); boxShotAt = clock + 1; }
            else
            {
                GetViewport().GetTexture().GetImage().SavePng(boxShotPath);
                GD.Print($"bugreport: box shot {boxShotPath}");
                boxShotPath = null;
                Cancel();
            }
        }
    }
}

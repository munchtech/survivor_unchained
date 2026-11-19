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
    public static bool Shooting => Instance?.shotsDir != null;
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
    bool boxShotTyped;

    public BugReporter(Game game)
    {
        g = game;
        Layer = 100;
        ProcessMode = ProcessModeEnum.Always;
        Instance = this;
    }

    public override void _Ready()
    {
        tester = Args.Get("bug-tester") ?? ReadPrefs();
        autoZone = Args.Get("bug-auto-zone");
        autoAfter = autoZone != null ? Args.Num("bug-auto-after", 5) : -1;
        autoAt = Args.Has("bug-auto-at") ? Args.Num("bug-auto-at", 5) : -1;
        boxShotPath = Args.Get("bug-box-shot");
        if (boxShotPath != null) boxShotAt = 3;
        shotsDir = Args.Get("bug-box-shots");
        shotsZone = Args.Get("bug-box-zone");
        shotsFresh = Args.Has("bug-box-fresh");
    }

    // --bug-box-shots <dir> [--bug-box-zone <zone>] [--bug-box-fresh]
    string? shotsDir, shotsZone;
    bool shotsFresh;
    int shotsStep;
    double shotsAt;

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
            if (g.Overlay != null) OpenFromPause(); else OpenFresh();
            GetViewport().SetInputAsHandled();
        }
        else if (k.Keycode == Key.Escape && box != null)
        {
            if (Typed() && !discardAsked)
            {
                discardAsked = true;
                if (hintLabel != null) { hintLabel.Text = "Esc again to discard"; }
            }
            else Cancel();
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
        askName = tester.Trim().Length == 0 || shotsFresh;
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

    static StyleBoxFlat Underline() => new() { DrawCenter = false, BorderColor = Style.Ember, BorderWidthBottom = 2, CornerRadiusBottomLeft = 3, CornerRadiusBottomRight = 3 };

    static void Tune(Control edit)
    {
        edit.AddThemeColorOverride("font_placeholder_color", Kit.Dim);
        edit.AddThemeColorOverride("caret_color", Style.EmberHi);
        edit.AddThemeColorOverride("selection_color", Style.Ember with { A = 0.35f });
        edit.AddThemeColorOverride("font_selected_color", Kit.Ink);
        edit.AddThemeConstantOverride("caret_width", 2);
        edit.AddThemeStyleboxOverride("focus", Underline());
    }

    static LineEdit Field(string placeholder, int size)
    {
        var edit = new LineEdit { PlaceholderText = placeholder, MaxLength = 120, CustomMinimumSize = new Vector2(440, 36), SizeFlagsHorizontal = Control.SizeFlags.ExpandFill, ContextMenuEnabled = false, CaretBlink = true };
        Style.Font(edit, Style.UiBold, size, Kit.Ink, false);
        Tune(edit);
        var well = Kit.WellBox(10); well.ContentMarginTop = 5; well.ContentMarginBottom = 5; edit.AddThemeStyleboxOverride("normal", well);
        return edit;
    }

    static VBoxContainer Group(Control head, Control field) => Style.V(Style.Gap2, head, field);

    void Build()
    {
        var root = new Control { MouseFilter = Control.MouseFilterEnum.Stop, Theme = Style.PageTheme };
        root.SetAnchorsPreset(Control.LayoutPreset.FullRect);
        root.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.55f), MouseFilter = Control.MouseFilterEnum.Ignore, AnchorRight = 1, AnchorBottom = 1 });
        var center = new CenterContainer { AnchorRight = 1, AnchorBottom = 1, MouseFilter = Control.MouseFilterEnum.Ignore };
        root.AddChild(center);
        var panel = Style.Panel(Kit.Window(Overlay.Margin, Overlay.Margin, Overlay.Margin));
        panel.CustomMinimumSize = new Vector2(500, 0);
        var stack = new MarginContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        foreach (var m in new[] { "margin_left", "margin_top", "margin_right", "margin_bottom" }) stack.AddThemeConstantOverride(m, 0);
        var backing = new ColorRect { Color = Kit.Tile, MouseFilter = Control.MouseFilterEnum.Ignore };
        stack.AddChild(backing);
        stack.AddChild(panel);
        center.AddChild(stack);
        var col = Style.V(Style.Gap5);
        panel.AddChild(col);
        col.AddChild(new Title("Report a bug", 30, false));
        col.AddChild(Kit.RuleH());

        if (askName)
        {
            nameEdit = Field("Signs every report you send", 18);
            nameEdit.MaxLength = 24;
            col.AddChild(Group(Kit.Head("Your name", "asked once"), nameEdit));
        }
        else nameEdit = null;

        titleEdit = Field("In a few words", 18);
        col.AddChild(Group(Kit.Head("What went wrong"), titleEdit));

        descEdit = new TextEdit { CustomMinimumSize = new Vector2(440, 110), WrapMode = TextEdit.LineWrappingMode.Boundary, PlaceholderText = "What you did, what you saw, what you expected", ContextMenuEnabled = false, CaretBlink = true };
        Style.Font(descEdit, Style.UiBold, 16, Kit.Ink, false);
        Tune(descEdit);
        descEdit.AddThemeStyleboxOverride("normal", Kit.WellBox(10));
        descEdit.Ready += () => descEdit.CustomMinimumSize = new Vector2(440, 5 * descEdit.GetLineHeight() + 20);
        col.AddChild(Group(Kit.Head("Details", "optional"), descEdit));

        bool withClip = clip is { Jpegs.Count: > 0 };
        var note = Style.Label(withClip ? $"A screenshot and the last {(int)Math.Round(clip!.Value.Jpegs.Count / clip.Value.Fps)} seconds of play are attached." : "Only a screenshot is attached: recording is off in Settings.", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Left, false);
        note.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        var folder = Kit.Word("Open reports folder", OpenFolder, Kit.Ink2, 15);
        foreach (var s in new[] { "normal", "hover", "pressed", "focus", "disabled" }) folder.AddThemeStyleboxOverride(s, new StyleBoxEmpty { ContentMarginLeft = 4, ContentMarginTop = 2, ContentMarginBottom = 2 });
        col.AddChild(Style.H(Style.Gap4, note, folder));

        sendBtn = Kit.Keyed(Act.Confirm, "Send", () => Send(false), Style.EmberHi);
        var cancel = Kit.Keyed(Act.Cancel, "Cancel", Cancel);
        // Enter sends from the one-line fields; in the description it adds a line, so the hint there says Ctrl+Enter
        var hint = Style.Label("", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Left, false);
        hint.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        hint.MouseFilter = Control.MouseFilterEnum.Ignore;
        hintLabel = hint;
        var row = Style.H(Style.Gap4, cancel, hint, sendBtn);
        col.AddChild(Style.V(Style.Gap3, Kit.RuleH(), row));

        void Refresh()
        {
            bool ok = Valid();
            sendBtn!.Disabled = !ok;
            sendBtn.Modulate = Colors.White with { A = ok ? 1f : 0.4f };
            sendBtn.MouseDefaultCursorShape = ok ? Control.CursorShape.PointingHand : Control.CursorShape.Arrow;
        }
        void Disarm() { if (!discardAsked) return; discardAsked = false; hint.Text = descEdit.HasFocus() ? HintDesc : ""; }
        titleEdit.TextChanged += _ => { Refresh(); Disarm(); };
        if (nameEdit != null) nameEdit.TextChanged += _ => { Refresh(); Disarm(); };
        descEdit.TextChanged += Disarm;
        titleEdit.TextSubmitted += _ => { if (Valid()) Send(false); };
        if (nameEdit != null) nameEdit.TextSubmitted += _ => titleEdit.GrabFocus();
        descEdit.FocusEntered += () => hint.Text = HintDesc;
        descEdit.FocusExited += () => { if (!discardAsked) hint.Text = ""; };
        descEdit.GuiInput += ev =>
        {
            if (ev is InputEventKey { Pressed: true, Echo: false } k && (k.Keycode == Key.Enter || k.Keycode == Key.KpEnter) && k.CtrlPressed)
            {
                descEdit.AcceptEvent();
                if (Valid()) Send(false);
            }
        };
        Refresh();

        AddChild(root);
        box = root;
        discardAsked = false;
        Control first = nameEdit != null && nameEdit.Text.Length == 0 ? nameEdit : titleEdit;
        first.CallDeferred(Control.MethodName.GrabFocus);
    }

    const string HintDesc = "Enter adds a line · Ctrl+Enter sends";
    bool discardAsked;
    Label? hintLabel;

    bool Typed() => (nameEdit != null && nameEdit.Text.Trim().Length > 0 && tester.Length == 0) || (titleEdit?.Text.Length ?? 0) > 0 || (descEdit?.Text.Length ?? 0) > 0;

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
        if (nameEdit != null) { tester = nameEdit.Text.Trim(); if (!shotsFresh) WritePrefs(tester); }
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

    static string ToastSub(string d)
    {
        var name = Path.GetFileName(d);
        var m = System.Text.RegularExpressions.Regex.Match(name, @"BR(\d{4})");
        return m.Success ? $"BR{m.Groups[1].Value} · in the reports folder" : name;
    }

    public override void _Process(double delta)
    {
        clock += delta;
        string zid = ZoneId;
        if (zid != lastZone) { lastZone = zid; zoneSince = clock; }
        while (done.TryDequeue(out var d))
        {
            g.Toast(d.StartsWith("failed") ? new Toast(ToastKind.Warning, "The bug report could not be saved.") : new Toast(ToastKind.World, "Bug report saved", ToastSub(d)));
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
        // --bug-box-shots: the box's six states in one run (a first, b details, c Esc once, e toast, f pause menu;
        // d, the box over play, is b and c shot in the --bug-box-zone zone). Real time: the tree is paused, this node is not.
        if (shotsDir != null && (shotsStep > 0 || (zid == shotsZone && clock - zoneSince >= 20) || (shotsZone == null && clock >= 3)) && clock >= shotsAt)
        {
            void Shot(string n) { GetViewport().GetTexture().GetImage().SavePng(Path.Combine(shotsDir, n + ".png")); }
            shotsAt = clock + 0.7;
            switch (shotsStep++)
            {
                case 0:   // opened fresh, empty, the first field focused
                    Directory.CreateDirectory(shotsDir);
                    OpenFresh();
                    (nameEdit ?? titleEdit)!.GrabFocus();
                    break;
                case 1:   // a; then name, title and three lines typed, the details field focused, caret at the end
                    Shot("a_first_empty");
                    if (nameEdit != null) nameEdit.Text = "Lead";
                    titleEdit!.Text = "The sword vanishes after the second dodge";
                    descEdit!.Text = "I was in the den.\nI dodged twice.\nThe sword was gone.";
                    descEdit.GrabFocus();
                    descEdit.SetCaretLine(2); descEdit.SetCaretColumn(descEdit.GetLine(2).Length);
                    sendBtn!.Disabled = false; sendBtn.Modulate = Colors.White;
                    break;
                case 2:   // b; then Esc as the player presses it
                    Shot("b_details_focus");
                    _Input(new InputEventKey { Keycode = Key.Escape, Pressed = true });
                    break;
                case 3:   // c; then Send for real (the toast comes on the next frame)
                    Shot("c_esc_once");
                    Send(true);
                    shotsAt = clock + 0.8;
                    break;
                case 4:   // e (about 0.6 s after the toast); then the pause menu as Esc in play opens it
                    Shot("e_toast");
                    g.Open("pause");
                    break;
                default:  // f; closed again
                    Shot("f_pause_menu");
                    g.CloseOverlay();
                    GD.Print($"bugreport: box shots {shotsDir}");
                    shotsDir = null;
                    break;
            }
        }
        if (boxShotPath != null && boxShotAt >= 0 && clock >= boxShotAt)
        {
            if (box == null) { OpenFresh(); boxShotAt = clock + 1; }
            else if (!boxShotTyped)
            {
                boxShotTyped = true;
                if (nameEdit != null) nameEdit.Text = "Lead";
                titleEdit!.Text = "The sword vanishes after the second dodge";
                descEdit!.Text = "I was in the den.\nI dodged twice.\nThe sword was gone.\nIt came back after a death.\nThe hit sound kept playing.\nThe frame rate dropped too.\nThis happened on the second room.";
                titleEdit.GrabFocus();
                titleEdit.CaretColumn = titleEdit.Text.Length;
                sendBtn!.Disabled = false; sendBtn.Modulate = Colors.White;
                boxShotAt = clock + 0.7;
            }
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

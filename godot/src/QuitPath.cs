using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained;

/// <summary>(L1 lead 21 QUIT) The one way the game quits: the window's close request and every in-game quit come to
/// <see cref="Request"/>. The quit used to hang, now and then and under load, in Godot's native teardown after the
/// compositor effects' release. So, at the REQUEST and before the tree quits: (1) no viewport draws 3D any more (no
/// effect callback can run again, whoever puts an effect back on a camera) and every camera's and environment's
/// compositor is taken off; (2) every effect of ours frees its RenderingDevice resources on the render thread (the ink
/// and the world-depth effects by their own release; any other by its own predelete handler, which the engine never
/// delivers to a C# RefCounted: MarkPass, BrushEffect); (3) ONE frame is drawn; (4) the static ramp textures go, the
/// <see cref="QuitGuard"/> is armed (the saves are flushed by then: Game.QuitGame saves before it asks) and the tree quits.
/// Made by Game (<see cref="Install"/>); a request without it makes its own.
/// Dev switches: --quit-at-play [N] quits through Game.QuitGame N drawn frames into play (the 20-start proof,
/// tools/experience/quit_starts.py); --quit-guard off leaves a hung quit hanging (to see one).</summary>
public partial class QuitPath : Node
{
    static QuitPath? node;
    static bool requested, sent;
    static int code;
    static ulong atProcess;
    static int atDrawn;
    Play.Game? game;
    int playFrames = -1, quitAtPlay = -1;

    public static bool Requested => requested;

    public static void Install(Play.Game host)
    {
        if (node != null && IsInstanceValid(node)) return;
        node = Make();
        node.game = host;
        if (Args.Has("quit-at-play")) node.quitAtPlay = Math.Max(1, (int)Args.Num("quit-at-play", 30));
        host.GetTree().AutoAcceptQuit = false;
        host.GetTree().Root.CallDeferred(Node.MethodName.AddChild, node);
    }

    static QuitPath Make() => new() { Name = "QuitPath", ProcessMode = ProcessModeEnum.Always, ProcessPriority = int.MaxValue };

    /// <summary>Asks for the quit (the first ask counts): release now, one frame, then the tree quits with the code.</summary>
    public static void Request(SceneTree tree, int exitCode = 0, string why = "game")
    {
        if (requested) return;
        requested = true; code = exitCode;
        atProcess = Engine.GetProcessFrames(); atDrawn = Engine.GetFramesDrawn();
        GD.Print($"quit: requested ({why})");
        if (Args.Has("quit-trace")) GD.Print("quit: asked from " + System.Environment.StackTrace);
        if (node == null || !IsInstanceValid(node)) { node = Make(); tree.Root.CallDeferred(Node.MethodName.AddChild, node); }
        try { ReleaseEarly(tree); } catch (Exception e) { GD.PushError($"quit: early release failed ({e.Message})"); }
        // (should the node never tick: a tree mid-change)
        tree.CreateTimer(0.5, true, false, true).Timeout += () => Finish(tree);
    }

    public override void _Notification(int what)
    {
        if (what == NotificationWMCloseRequest) Request(GetTree(), 0, "window close");
    }

    public override void _Process(double delta)
    {
        if (!requested)
        {
            if (quitAtPlay < 0 || game == null || game.Mode != "play") return;
            if (playFrames < 0) playFrames = Engine.GetFramesDrawn();
            if (Engine.GetFramesDrawn() - playFrames < quitAtPlay) return;
            GD.Print($"quit-at-play: {quitAtPlay} frames into play, quitting by the game's own path");
            quitAtPlay = -1;
            game.QuitGame();
            return;
        }
        if (sent) return;
        Dark(GetTree().Root, null);   // (last in the frame: nothing turned 3D back on, a storybook's end does)
        ulong f = Engine.GetProcessFrames();
        if (f > atProcess && (Engine.GetFramesDrawn() > atDrawn || f >= atProcess + 3)) Finish(GetTree());
    }

    static void Finish(SceneTree tree)
    {
        if (sent) return;
        sent = true;
        try { Atmosphere.ReleaseStatics(); } catch (Exception e) { GD.PushError($"quit: static textures not released ({e.Message})"); }
        bool guard = Args.Get("quit-guard") is not ("off" or "0") && QuitGuard.ArmForProcess(() => GD.Print(QuitGuard.FiredLine), code) != null;
        GD.Print($"quit: released, the tree quits (guard {(guard ? "armed" : "off")})");
        tree.Quit(code);
    }

    /// <summary>Steps 1 and 2 of the class summary, at the request.</summary>
    static void ReleaseEarly(SceneTree tree)
    {
        var fx = new List<CompositorEffect>();
        Dark(tree.Root, fx);
        FxAfter.DropMarks();   // (lead 23: before MarkPass's mask is freed; the frame after still draws the layer)
        InkRelease.Release();
        if (FxWorldDepth.On) FxWorldDepth.Release();
        var own = typeof(QuitPath).Assembly;
        var rest = fx.FindAll(e => e is not InkRelease.IRids and not FxWorldDepth.IRids && e.GetType().Assembly == own);
        if (rest.Count == 0) return;
        RenderingServer.CallOnRenderThread(Callable.From(() =>
        {
            foreach (var e in rest)
                try { e._Notification((int)NotificationPredelete); GD.Print($"quit: released {e.GetType().Name}"); }
                catch (Exception x) { GD.PushError($"quit: {e.GetType().Name} not released ({x.Message})"); }
        }));
    }

    /// <summary>No viewport under <paramref name="n"/> draws 3D; with <paramref name="fx"/>, every compositor comes off
    /// its camera or environment and its effects are listed there (once each).</summary>
    static void Dark(Node n, List<CompositorEffect>? fx)
    {
        if (n is Viewport vp && !vp.Disable3D) vp.Disable3D = true;
        if (fx != null)
        {
            Compositor? c = null;
            if (n is Camera3D cam) { c = cam.Compositor; cam.Compositor = null; }
            else if (n is WorldEnvironment we) { c = we.Compositor; we.Compositor = null; }
            if (c != null)
                foreach (var e in c.CompositorEffects)
                    if (e != null && !fx.Contains(e)) fx.Add(e);
        }
        foreach (var k in n.GetChildren()) Dark(k, fx);
    }
}

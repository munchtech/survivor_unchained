using System;
using System.Linq;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>
/// --b3-cams NAMES (L1 B3 round 2; tools/look/calib.py, bakeoff.py): a per-item close-up camera on the lookdev stage. In each
/// rig's close window (settle + 0.5 to settle + 1.8: spotClose held, the close view's own lighting live), the close camera is copied and moved so it
/// looks at each named stage item (barrel, boulder, setts, or "swatches": both swatch rows) from the close view's own
/// direction and distance, and one frame is taken: godot/.shots/lookdev_RIG_item_NAME_1.png (its camera in the log's
/// "camera" line, as every shot). "swatches" looks from the close view's bearing at 35 degrees of pitch, pulled back until the
/// rows fit the frame (the world's light is the rig's whatever the lens; the close view's own key and rim light people only). Then the close camera is made current again before the stage's close frame.
/// Without the flag nothing runs.
/// </summary>
public partial class Game
{
    static readonly string[] B3Cams = Args.Get("b3-cams") is string bc ? bc.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries) : Array.Empty<string>();
    Camera3D? b3Cam;
    int b3Done = -1;
    Camera3D? b3Back;

    void LookItems()
    {
        if (B3Cams.Length == 0 || lookBuiltAt < 0 || lookRigs == null || scene == null) return;
        // (the stage's own timeline, GameLookdev.Lookdev: per rig, settle; the play frame at settle, the close view held from
        // then until its frame at settle + 2, then the side view's frame at settle + 3.5)
        double settle = Args.Num("lookdev-settle", 2.5f), per = settle + 4.0, t0 = lookBuiltAt + 1.5, t = Shots.Clock;
        if (t < t0) return;
        int k = (int)((t - t0) / per);
        if (k >= lookRigs.Length) return;
        double u = t - t0 - k * per, a = settle + 0.5, slot = Math.Min(0.3, 1.3 / (B3Cams.Length + 1));
        int i = (int)Math.Floor((u - a) / slot);
        if (u < a || i > B3Cams.Length) return;
        int id = k * 100 + i;
        if (i == B3Cams.Length)
        {
            if (b3Done == id) return;
            b3Done = id;
            Shots.Want($"{lookRigs[k]}_item_{B3Cams[i - 1]}", 0);
            if (b3Back != null && IsInstanceValid(b3Back)) b3Back.MakeCurrent();
            GD.Print($"b3-cams: {lookRigs[k]} done, close camera back");
            return;
        }
        // each slot: the frame of the one before it taken (as the stage does), then this item's camera set
        if (b3Done == id) return;
        if (i > 0) Shots.Want($"{lookRigs[k]}_item_{B3Cams[i - 1]}", 0);
        if (i == 0) b3Back = GetViewport().GetCamera3D();
        b3Done = id;
        var close = b3Back;
        if (close == null || !IsInstanceValid(close)) return;
        var name = B3Cams[i];
        var target = ItemCenter(name, out float width);
        if (target is not Vector3 c) { GD.Print($"b3-cams: no item {name}"); return; }
        if (b3Cam == null || !IsInstanceValid(b3Cam))
        {
            b3Cam = new Camera3D { Name = "B3ItemCam", Far = 600 };
            scene.AddChild(b3Cam);
        }
        b3Cam.Fov = close.Fov; b3Cam.Near = close.Near;
        // the close view's offset from her (her chest), put on the item
        var her = lookP + Vector3.Up * 1.25f;
        var off = close.GlobalPosition - her;
        if (width > 0)
        {
            var vs = GetViewport().GetVisibleRect().Size;
            float hfov = 2 * Mathf.Atan(Mathf.Tan(Mathf.DegToRad(close.Fov) / 2) * vs.X / vs.Y);
            float need = width * 1.1f / (2 * Mathf.Tan(hfov / 2));
            // (raised to 35 degrees of pitch on the close view's own bearing, so the rows' tops show: the world's light is
            // the rig's whatever the lens, and the close view's own key and rim light people only)
            var back = new Vector3(off.X, 0, off.Z).Normalized();
            off = (back * Mathf.Cos(Mathf.DegToRad(35)) + Vector3.Up * Mathf.Sin(Mathf.DegToRad(35))) * Mathf.Max(off.Length(), need);
            b3Cam.GlobalTransform = Transform3D.Identity.LookingAt(-off, Vector3.Up).Translated(c + off);
        }
        else b3Cam.GlobalTransform = new Transform3D(close.GlobalTransform.Basis, c + off);
        b3Cam.MakeCurrent();
        GD.Print($"b3-cams: {lookRigs[k]} {name} at {c} from {off.Length():0.00} m");
    }

    /// <summary>An item's middle (a stage item's box, or the swatch rows' middle and width).</summary>
    Vector3? ItemCenter(string name, out float width)
    {
        width = 0;
        if (name == "swatches")
        {
            var root = scene?.GetNodeOrNull<Node3D>("Lookdev");
            var sw = root?.GetChildren().OfType<MeshInstance3D>().Where(m => m.Name.ToString().StartsWith("Swatch_")).ToList();
            if (sw == null || sw.Count == 0) return null;
            var c = sw.Aggregate(Vector3.Zero, (s, m) => s + m.GlobalPosition) / sw.Count;
            width = sw.Max(m => (m.GlobalPosition - c).Dot(lookR)) - sw.Min(m => (m.GlobalPosition - c).Dot(lookR)) + 0.6f;
            return c;
        }
        var it = lookItems.FirstOrDefault(x => x.Name == name);
        return it.Box?.Invoke() is Aabb b ? b.GetCenter() : null;
    }
}

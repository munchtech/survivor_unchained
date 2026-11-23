using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using Godot;

namespace SurvivorUnchained.Fx;

/// <summary>
/// (P2 task 5, dev) --glyphs-check [full]: every painted glyph (art/ui/icons/glyph_color and icons/glyph) and a few drawn
/// ones, asked of Ui.Glyphs.Texture in the tints the HUD asks in (bright, the boss arrow's BloodHi, a dim grey, a faint
/// gold), each answer's pixels as a SHA-256, and one hash over all of them: a change to how glyph textures are made or
/// kept proves itself by the same lines before and after. Then what one more call costs once everything is kept (the
/// HUD's marks ask every frame): ms a call over 40 calls, for the boss's arrow, an elite's, and a bright horns.
/// </summary>
public static class GlyphsCheck
{
    public static string Run(bool full)
    {
        var keys = new SortedSet<string>(StringComparer.Ordinal);
        foreach (var set in new[] { "glyph_color", "glyph" })
            foreach (var f in DirAccess.GetFilesAt($"{Ui.UiArt.Root}icons/{set}"))
            {
                string name = f.EndsWith(".import", StringComparison.Ordinal) ? f[..^7] : f;
                if (name.EndsWith(".png", StringComparison.Ordinal)) keys.Add(name[..^4]);
            }
        foreach (var k in new[] { "horns", "skull", "relic", "sword", "shield", "flame" }) keys.Add(k);
        (string Name, Color C)[] tints = { ("bright", Ui.Style.EmberHi), ("blood", Ui.Style.BloodHi), ("dim", new Color(0.4f, 0.4f, 0.4f)), ("faint", Ui.Style.GoldDim with { A = 0.5f }) };
        var sb = new StringBuilder();
        using var all = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        int lines = 0;
        foreach (var key in keys)
            foreach (var (name, c) in tints)
            {
                string line;
                try
                {
                    var img = Ui.Glyphs.Texture(key, 48, c).GetImage();
                    line = $"{key}|{name}: {img.GetWidth()}x{img.GetHeight()} {img.GetFormat()} {Convert.ToHexString(SHA256.HashData(img.GetData()))[..24]}";
                }
                catch (Exception e) { line = $"{key}|{name}: {e.GetType().Name}"; }
                all.AppendData(Encoding.UTF8.GetBytes(line + "\n"));
                lines++;
                if (full) sb.AppendLine(line);
            }
        sb.AppendLine($"glyphs-check: {keys.Count} keys x {tints.Length} tints = {lines} lines, sha256 of all {Convert.ToHexString(all.GetHashAndReset())[..24]}");
        foreach (var (what, key, c) in new[] { ("the boss's arrow (horns, BloodHi)", "horns", Ui.Style.BloodHi), ("an elite's (skull, EmberHi)", "skull", Ui.Style.EmberHi), ("horns, bright (EmberHi)", "horns", Ui.Style.EmberHi) })
        {
            Ui.Glyphs.Texture(key, 48, c);
            long t0 = Stopwatch.GetTimestamp();
            for (int i = 0; i < 40; i++) Ui.Glyphs.Texture(key, 48, c);
            sb.AppendLine($"glyphs-check: one more call for {what}: {Stopwatch.GetElapsedTime(t0).TotalMilliseconds / 40:0.0000} ms");
        }
        return sb.ToString().TrimEnd();
    }

    /// <summary>--glyphs-arrow PNG: the boss's edge arrow (horns in BloodHi) and an elite's (skull in EmberHi) as the game's
    /// own Ui.EdgeMarks draws them, over a ground colour on a layer above everything, cropped 1:1 round the two marks.</summary>
    public static async void Arrow(Node host, string png)
    {
        var tree = host.GetTree();
        var size = tree.Root.GetVisibleRect().Size;
        var mid = size / 2;
        var layer = new CanvasLayer { Layer = 128 };
        layer.AddChild(new ColorRect { Color = new Color("#56653a"), Size = size });
        var edges = new Ui.EdgeMarks { Size = size };
        layer.AddChild(edges);
        tree.Root.AddChild(layer);
        var marks = new List<Ui.Beyond> { new(mid + new Vector2(-4000, -300), "horns", Ui.Style.BloodHi, 1), new(mid + new Vector2(-4000, 300), "skull", Ui.Style.EmberHi, 1) };
        for (int i = 0; i < 4; i++)
        {
            edges.Show(marks);
            await host.ToSignal(tree, SceneTree.SignalName.ProcessFrame);
        }
        await host.ToSignal(RenderingServer.Singleton, RenderingServerInstance.SignalName.FramePostDraw);
        var img = tree.Root.GetTexture().GetImage();
        // (the canvas may be scaled to the frame: the crop is cut in the frame's own pixels, round both marks on the left border)
        float k = img.GetWidth() / size.X, reach = 300 * (mid.X - 64) / 4000 + 60;
        var crop = img.GetRegion(new Rect2I(0, (int)((mid.Y - reach) * k), (int)(130 * k), (int)(2 * reach * k)));
        crop.SavePng(png);
        GD.Print($"glyphs-arrow: saved {png} ({crop.GetWidth()}x{crop.GetHeight()}, 1:1 from a {img.GetWidth()}x{img.GetHeight()} frame; the boss's arrow above, an elite's below)");
        tree.Quit();
    }
}

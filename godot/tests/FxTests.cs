using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>
/// The effects' pictures hold their whole effect inside their frame: no
/// flipbook cell, sprite or ground mark may carry light to its edge, where it
/// would show in the game as the square of its quad (the owner caught that
/// early on). tools/comfy/flipbook.py refuses such a cell as it cuts an
/// atlas; this keeps every picture in the game to the same rule.
/// </summary>
public class FxTests
{
    static readonly string Art = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../art/fx"));

    /// <summary>The worst light (0..255, colour times alpha) on the outermost
    /// texels of a square region, and past 0.97 of the way to its edge.</summary>
    static (int Border, int Rim) Edge(Png p, int x0, int y0, int n)
    {
        int b = Math.Max(1, n / 64), border = 0, rim = 0;
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                int v = p.Light(x0 + x, y0 + y);
                if (v == 0) continue;
                if (x < b || y < b || x >= n - b || y >= n - b) border = Math.Max(border, v);
                double u = (x + 0.5) / n * 2 - 1, w = (y + 0.5) / n * 2 - 1;
                if (u * u + w * w > 0.97 * 0.97) rim = Math.Max(rim, v);
            }
        return (border, rim);
    }

    [Fact]
    public void FlipbookCellsKeepTheirLightInside()
    {
        var bad = new List<string>();
        foreach (var file in Directory.GetFiles(Path.Combine(Art, "fb"), "*.png"))
        {
            var meta = JsonDocument.Parse(File.ReadAllText(Path.ChangeExtension(file, ".json"))).RootElement;
            int grid = meta.GetProperty("grid").GetInt32(), frames = meta.GetProperty("frames").GetInt32();
            var p = Png.Read(file);
            p.Premultiplied = true;
            int cell = p.Width / grid;
            for (int k = 0; k < frames; k++)
            {
                var (border, rim) = Edge(p, k % grid * cell, k / grid * cell, cell);
                if (border > 1 || rim > 4) bad.Add($"{Path.GetFileName(file)} frame {k}: border {border}, rim {rim}");
            }
        }
        Assert.True(bad.Count == 0, string.Join("\n", bad.Take(20)));
    }

    [Fact]
    public void SpritesAndMarksKeepTheirLightInside()
    {
        var bad = new List<string>();
        var sprites = Png.Read(Path.Combine(Art, "sprites.png"));
        int s = sprites.Width;
        for (int l = 0; l < sprites.Height / s; l++)
        {
            var (border, _) = Edge(sprites, 0, l * s, s);
            if (border > 2) bad.Add($"sprites layer {l}: border {border}");
        }
        foreach (var file in Directory.GetFiles(Path.Combine(Art, "marks"), "*.png").Concat(new[] { "runes_a.png", "runes_b.png", "embers.png", "puff.png" }.Select(f => Path.Combine(Art, f))))
        {
            var p = Png.Read(file);
            var (border, rim) = Edge(p, 0, 0, Math.Min(p.Width, p.Height));
            if (border > 2 || rim > 6) bad.Add($"{Path.GetFileName(file)}: border {border}, rim {rim}");
        }
        Assert.True(bad.Count == 0, string.Join("\n", bad));
    }

    /// <summary>Just enough of PNG to read the effects' pictures: 8-bit RGB or
    /// RGBA, not interlaced.</summary>
    sealed class Png
    {
        public int Width, Height, Channels;
        public byte[] Pixels = Array.Empty<byte>();

        /// <summary>Colour stored already multiplied by its alpha (the flipbooks).</summary>
        public bool Premultiplied;

        /// <summary>How much a texel shows: its brightest channel times its alpha,
        /// or for premultiplied colour the greater of the two.</summary>
        public int Light(int x, int y)
        {
            int o = (y * Width + x) * Channels;
            int c = Math.Max(Pixels[o], Math.Max(Pixels[o + 1], Pixels[o + 2]));
            if (Channels == 3) return c;
            return Premultiplied ? Math.Max(c, (int)Pixels[o + 3]) : c * Pixels[o + 3] / 255;
        }

        public static Png Read(string path)
        {
            var data = File.ReadAllBytes(path);
            int pos = 8, depth = 0, type = 0;
            var p = new Png();
            using var idat = new MemoryStream();
            while (pos < data.Length)
            {
                int len = (data[pos] << 24) | (data[pos + 1] << 16) | (data[pos + 2] << 8) | data[pos + 3];
                string kind = System.Text.Encoding.ASCII.GetString(data, pos + 4, 4);
                if (kind == "IHDR")
                {
                    p.Width = (data[pos + 8] << 24) | (data[pos + 9] << 16) | (data[pos + 10] << 8) | data[pos + 11];
                    p.Height = (data[pos + 12] << 24) | (data[pos + 13] << 16) | (data[pos + 14] << 8) | data[pos + 15];
                    depth = data[pos + 16];
                    type = data[pos + 17];
                    Assert.True(data[pos + 20] == 0, $"{path} is interlaced");
                }
                else if (kind == "IDAT") idat.Write(data, pos + 8, len);
                else if (kind == "IEND") break;
                pos += 12 + len;
            }
            Assert.True(depth == 8 && (type == 6 || type == 2), $"{path}: depth {depth}, colour type {type}");
            p.Channels = type == 6 ? 4 : 3;
            idat.Position = 0;
            using var z = new ZLibStream(idat, CompressionMode.Decompress);
            using var raw = new MemoryStream();
            z.CopyTo(raw);
            var r = raw.ToArray();
            int stride = p.Width * p.Channels, bpp = p.Channels;
            p.Pixels = new byte[stride * p.Height];
            for (int y = 0; y < p.Height; y++)
            {
                int f = r[y * (stride + 1)], src = y * (stride + 1) + 1, dst = y * stride;
                for (int i = 0; i < stride; i++)
                {
                    int a = i >= bpp ? p.Pixels[dst + i - bpp] : 0;
                    int b = y > 0 ? p.Pixels[dst - stride + i] : 0;
                    int c = i >= bpp && y > 0 ? p.Pixels[dst - stride + i - bpp] : 0;
                    int v = r[src + i];
                    v += f switch
                    {
                        1 => a,
                        2 => b,
                        3 => (a + b) / 2,
                        4 => Paeth(a, b, c),
                        _ => 0,
                    };
                    p.Pixels[dst + i] = (byte)v;
                }
            }
            return p;
        }

        static int Paeth(int a, int b, int c)
        {
            int p = a + b - c, pa = Math.Abs(p - a), pb = Math.Abs(p - b), pc = Math.Abs(p - c);
            return pa <= pb && pa <= pc ? a : pb <= pc ? b : c;
        }
    }
}

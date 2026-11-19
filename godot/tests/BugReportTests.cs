using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using SurvivorUnchained.Core;
using Xunit;

namespace SurvivorUnchained.Tests;

public class BugReportTests
{
    static List<byte[]> Frames(int n)
    {
        var l = new List<byte[]>();
        for (int i = 0; i < n; i++)
        {
            var b = new byte[20 + i * 3 + (i % 2)];
            for (int k = 0; k < b.Length; k++) b[k] = (byte)(i * 17 + k);
            l.Add(b);
        }
        return l;
    }

    static byte[] Make(int n, out List<byte[]> frames)
    {
        frames = Frames(n);
        var ms = new MemoryStream();
        MjpegAvi.Write(ms, 640, 360, 30, frames);
        return ms.ToArray();
    }

    [Fact]
    public void FramesRoundTrip()
    {
        var bytes = Make(12, out var frames);
        var back = MjpegAvi.ReadFrames(new MemoryStream(bytes));
        Assert.Equal(12, back.Count);
        for (int i = 0; i < 12; i++) Assert.Equal(frames[i], back[i]);
    }

    [Fact]
    public void HeaderRoundTrip()
    {
        var bytes = Make(12, out _);
        var h = MjpegAvi.ReadHeader(new MemoryStream(bytes));
        Assert.Equal(640, h.Width); Assert.Equal(360, h.Height);
        Assert.Equal(30.0, h.Fps, 3); Assert.Equal(12, h.Frames);
    }

    [Fact]
    public void RiffSizeAndIndex()
    {
        var bytes = Make(12, out var frames);
        Assert.Equal("RIFF", Encoding.ASCII.GetString(bytes, 0, 4));
        Assert.Equal(bytes.Length - 8, BitConverter.ToInt32(bytes, 4));
        Assert.Equal("AVI ", Encoding.ASCII.GetString(bytes, 8, 4));
        int movi = 0, idx = 0;
        for (int p = 12; p + 12 <= bytes.Length;)
        {
            string id = Encoding.ASCII.GetString(bytes, p, 4);
            int size = BitConverter.ToInt32(bytes, p + 4);
            if (id == "LIST" && Encoding.ASCII.GetString(bytes, p + 8, 4) == "movi") movi = p + 8;
            if (id == "idx1") idx = p;
            p += 8 + size + (size & 1);
        }
        Assert.True(movi > 0 && idx > 0);
        Assert.Equal(12 * 16, BitConverter.ToInt32(bytes, idx + 4));
        Assert.Equal(bytes.Length, idx + 8 + 12 * 16);
        for (int i = 0; i < 12; i++)
        {
            int e = idx + 8 + i * 16;
            Assert.Equal("00dc", Encoding.ASCII.GetString(bytes, e, 4));
            Assert.Equal(0x10, BitConverter.ToInt32(bytes, e + 4));
            int off = BitConverter.ToInt32(bytes, e + 8), sz = BitConverter.ToInt32(bytes, e + 12);
            Assert.Equal(frames[i].Length, sz);
            Assert.Equal("00dc", Encoding.ASCII.GetString(bytes, movi + off, 4));
            Assert.Equal(sz, BitConverter.ToInt32(bytes, movi + off + 4));
            Assert.Equal(frames[i], bytes.Skip(movi + off + 8).Take(sz).ToArray());
        }
    }

    [Fact]
    public void ZeroFrames()
    {
        var bytes = Make(0, out _);
        Assert.Equal(bytes.Length - 8, BitConverter.ToInt32(bytes, 4));
        Assert.Empty(MjpegAvi.ReadFrames(new MemoryStream(bytes)));
        Assert.Equal(0, MjpegAvi.ReadHeader(new MemoryStream(bytes)).Frames);
    }

    [Fact]
    public void TruncatedTailIsTolerated()
    {
        var bytes = Make(12, out _);
        var cut = bytes.Take(bytes.Length / 2).ToArray();
        var back = MjpegAvi.ReadFrames(new MemoryStream(cut));
        Assert.InRange(back.Count, 1, 11);
    }

    [Fact]
    public void FolderNameFormatAndSanitising()
    {
        var t = new DateTime(2026, 11, 18, 21, 41, 0);
        Assert.Equal("Sam_BR0007_20261118-2141_hollow", BugReports.FolderName("Sam", 7, t, "hollow"));
        Assert.Equal("Sam-J-K_BR0001_20261118-2141_the-den", BugReports.FolderName("  Sam / J!! K ", 1, t, "the  den"));
        Assert.Equal("tester_BR0012_20261118-2141_title", BugReports.FolderName("", 12, t, "?!"));
        string longName = BugReports.FolderName(new string('a', 40), 1, t, "z");
        Assert.StartsWith(new string('a', 24) + "_BR", longName);
    }

    [Fact]
    public void NextNumberMixed()
    {
        Assert.Equal(1, BugReports.NextNumber(new string[0]));
        Assert.Equal(1, BugReports.NextNumber(new[] { "random", "notes.txt" }));
        Assert.Equal(9, BugReports.NextNumber(new[] { "Sam_BR0007_20261118-2141_hollow", "Al_BR0008_20261118-2200_den", "junk", "Al_BR0003_x_y" }));
    }

    [Fact]
    public void JsonRoundTripOmitsNulls()
    {
        var r = new BugReport { Title = "Stuck", Number = 7, Seed = 42, DenClears = null, X = 1.5, ClipFrames = 3, Files = { "shot.png" }, Extra = { ["k"] = "v" } };
        string j = BugReports.ToJson(r);
        Assert.Contains("\"title\"", j);
        Assert.Contains("\"clip_frames\"", j);
        Assert.DoesNotContain("den_clears", j);
        Assert.DoesNotContain("gpu_driver", j);
        var b = BugReports.FromJson(j);
        Assert.Equal("Stuck", b.Title); Assert.Equal(7, b.Number); Assert.Equal(42L, b.Seed);
        Assert.Null(b.DenClears); Assert.Equal(1.5, b.X); Assert.Equal(3, b.ClipFrames);
        Assert.Equal("shot.png", Assert.Single(b.Files)); Assert.Equal("v", b.Extra["k"]);
    }

    [Fact]
    public void FrameStatsWork()
    {
        Assert.Equal((0.0, 0.0, 0.0), BugReports.FrameStats(new double[0]));
        var v = Enumerable.Range(1, 100).Select(x => (double)x).ToList();
        var s = BugReports.FrameStats(v);
        Assert.Equal(50.5, s.Avg, 6); Assert.Equal(99.0, s.P99); Assert.Equal(100.0, s.Max);
    }
}

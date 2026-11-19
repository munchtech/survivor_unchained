using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace SurvivorUnchained.Core;

/// <summary>
/// Motion-JPEG in an AVI: the layout Godot's MovieWriter MJPEG uses (RIFF 'AVI ',
/// hdrl, movi of '00dc' chunks, idx1). Used by the bug-report clip.
/// </summary>
public static class MjpegAvi
{
    public static void WriteFile(string path, int width, int height, double fps, IReadOnlyList<byte[]> jpegFrames)
    {
        using var f = File.Create(path);
        Write(f, width, height, fps, jpegFrames);
    }

    public static void Write(Stream s, int width, int height, double fps, IReadOnlyList<byte[]> jpegFrames)
    {
        if (fps <= 0) fps = 30;
        int n = jpegFrames.Count;
        uint rate = (uint)Math.Max(1, Math.Round(fps * 1000));
        uint usPerFrame = (uint)Math.Max(1, Math.Round(1_000_000.0 / fps));
        uint maxFrame = 0; long total = 0;
        foreach (var fr in jpegFrames) { maxFrame = Math.Max(maxFrame, (uint)fr.Length); total += fr.Length; }
        double secs = n / fps;
        uint maxBps = secs > 0 ? (uint)Math.Min(uint.MaxValue, total / secs) : 0;

        var ms = new MemoryStream();
        var w = new BinaryWriter(ms, Encoding.ASCII, true);
        void Fcc(string c) => w.Write(Encoding.ASCII.GetBytes(c));
        void U32(uint v) => w.Write(v);
        long Begin(string id, string? form = null)
        {
            Fcc(id); long at = ms.Position; U32(0);
            if (form != null) Fcc(form);
            return at;
        }
        void End(long at)
        {
            long pos = ms.Position;
            ms.Position = at; U32((uint)(pos - at - 4)); ms.Position = pos;
        }

        long riff = Begin("RIFF", "AVI ");
        long hdrl = Begin("LIST", "hdrl");
        long avih = Begin("avih");
        U32(usPerFrame); U32(maxBps); U32(0); U32(0x10); U32((uint)n); U32(0); U32(1);
        U32(Math.Max(maxFrame, 1)); U32((uint)width); U32((uint)height); U32(0); U32(0); U32(0); U32(0);
        End(avih);
        long strl = Begin("LIST", "strl");
        long strh = Begin("strh");
        Fcc("vids"); Fcc("MJPG"); U32(0); U32(0); U32(0); U32(1000); U32(rate); U32(0); U32((uint)n);
        U32(Math.Max(maxFrame, 1)); U32(0xFFFFFFFF); U32(0);
        w.Write((short)0); w.Write((short)0); w.Write((short)width); w.Write((short)height);
        End(strh);
        long strf = Begin("strf");
        U32(40); U32((uint)width); U32((uint)height); w.Write((short)1); w.Write((short)24);
        Fcc("MJPG"); U32((uint)(width * height * 3)); U32(0); U32(0); U32(0); U32(0);
        End(strf);
        End(strl);
        End(hdrl);

        long movi = Begin("LIST", "movi");
        long moviFcc = movi + 4; // position of the 'movi' fourcc
        var offs = new uint[n]; var sizes = new uint[n];
        for (int i = 0; i < n; i++)
        {
            var fr = jpegFrames[i];
            offs[i] = (uint)(ms.Position - moviFcc);
            sizes[i] = (uint)fr.Length;
            Fcc("00dc"); U32((uint)fr.Length); w.Write(fr);
            if ((fr.Length & 1) == 1) w.Write((byte)0);
        }
        End(movi);

        long idx = Begin("idx1");
        for (int i = 0; i < n; i++) { Fcc("00dc"); U32(0x10); U32(offs[i]); U32(sizes[i]); }
        End(idx);
        End(riff);
        w.Flush();
        ms.Position = 0;
        ms.CopyTo(s);
    }

    public static List<byte[]> ReadFrames(string path)
    {
        using var f = File.OpenRead(path);
        return ReadFrames(f);
    }

    public static List<byte[]> ReadFrames(Stream s)
    {
        var d = ReadAll(s);
        var list = new List<byte[]>();
        if (d.Length >= 12 && Id(d, 0) == "RIFF") Walk(d, 12, d.Length, list);
        return list;
    }

    public static (int Width, int Height, double Fps, int Frames) ReadHeader(string path)
    {
        using var f = File.OpenRead(path);
        return ReadHeader(f);
    }

    public static (int Width, int Height, double Fps, int Frames) ReadHeader(Stream s)
    {
        var d = ReadAll(s);
        int w = 0, h = 0, frames = 0; double fps = 0;
        bool Hdr(int pos, int end)
        {
            end = Math.Min(end, d.Length);
            while (pos + 8 <= end)
            {
                string id = Id(d, pos); long size = U32(d, pos + 4);
                int body = pos + 8;
                if (id == "LIST" || id == "RIFF")
                {
                    if (Id(d, body) == "movi") return false;
                    if (Hdr(body + 4, (int)Math.Min(end, body + size))) return true;
                }
                else if (id == "avih" && body + 40 <= d.Length)
                {
                    frames = (int)U32(d, body + 16); w = (int)U32(d, body + 32); h = (int)U32(d, body + 36);
                    uint us = (uint)U32(d, body); if (us > 0) fps = 1_000_000.0 / us;
                }
                else if (id == "strh" && body + 28 <= d.Length)
                {
                    uint sc = (uint)U32(d, body + 20), rt = (uint)U32(d, body + 24);
                    if (sc > 0 && rt > 0) fps = (double)rt / sc;
                    return true;
                }
                long next = body + size + (size & 1);
                if (next > end) break;
                pos = (int)next;
            }
            return false;
        }
        if (d.Length >= 12 && Id(d, 0) == "RIFF") Hdr(12, d.Length);
        return (w, h, fps, frames);
    }

    static byte[] ReadAll(Stream s)
    {
        using var ms = new MemoryStream();
        s.CopyTo(ms);
        return ms.ToArray();
    }

    static string Id(byte[] d, int p) => p + 4 <= d.Length ? Encoding.ASCII.GetString(d, p, 4) : "";
    static long U32(byte[] d, int p) => p + 4 <= d.Length ? BitConverter.ToUInt32(d, p) : 0;

    // Returns false when the data ran out (stop everything).
    static bool Walk(byte[] d, int pos, int end, List<byte[]> outList)
    {
        end = Math.Min(end, d.Length);
        while (pos + 8 <= end)
        {
            string id = Id(d, pos); long size = U32(d, pos + 4);
            int body = pos + 8;
            if (id == "LIST" || id == "RIFF")
            {
                if (body + size > d.Length) { Walk(d, body + 4, d.Length, outList); return false; }
                if (!Walk(d, body + 4, (int)(body + size), outList)) return false;
            }
            else if (id.Length == 4 && char.IsDigit(id[0]) && char.IsDigit(id[1]) && (id.EndsWith("dc") || id.EndsWith("db")))
            {
                if (body + size > d.Length) return false;
                var b = new byte[size];
                Buffer.BlockCopy(d, body, b, 0, (int)size);
                outList.Add(b);
            }
            long next = body + size + (size & 1);
            if (next > d.Length) return false;
            if (next > end) return true;
            pos = (int)next;
        }
        return true;
    }
}

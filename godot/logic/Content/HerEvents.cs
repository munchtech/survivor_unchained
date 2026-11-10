using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* Her clips' timed events (data/anim/her_events.json; A1's schema, ARPG_NOTES): per clip, frames from its start at the
 * file's fps (60) in clip time: contact (the blade's frames of contact), hold, cancel, loop, events; every key optional.
 * M3 measured today's swings into it (tools/anim/contact_measure.py); A1's P4 pack overwrites the file with its new
 * clips, and the sim reads it by clip name, so the swap needs no code. */
public static class HerEvents
{
    public sealed class ClipEvents
    {
        public int[]? Contact;
        public int[]? Hold;
        public int? Cancel;
        /// <summary>The clip's whole length in frames (a chain's cut fills its period with it: Sim/SwingChain.cs).</summary>
        public double? Len;
        public int[]? Loop;
        /// <summary>Which way the blade crosses at the contact, as the sim's angles run (atan2(dz, dx)): -1 toward the
        /// lesser angle, +1 toward the greater (Ev.Slash.Side). Measured from the clip in play (BattleFx.Grip's `grip cut`
        /// line under --clip prints it); absent: the cut's side alternates from the weapon's count.</summary>
        public int? Side;
    }

    public sealed class File
    {
        public double Fps = 60;
        public Dictionary<string, ClipEvents> Clips = new();
    }

    static File? file;
    static File F => file ??= Load();

    static File Load()
    {
        try { return Json.Parse<File>(DataFiles.Text("anim/her_events.json")); }
        catch (System.IO.IOException) { return new File(); }
    }

    /// <summary>The clip's first contact, in seconds of clip time (null: the clip or its contact is not in the file).</summary>
    public static double? Contact(string clip) =>
        F.Clips.TryGetValue(clip, out var c) && c.Contact is { Length: > 0 } k ? k[0] / (F.Fps > 0 ? F.Fps : 60) : null;

    /// <summary>The clip's first contact frame as written (tests).</summary>
    public static int? ContactFrame(string clip) => F.Clips.TryGetValue(clip, out var c) && c.Contact is { Length: > 0 } k ? k[0] : null;

    /// <summary>The clip's side (-1 or +1), or null when the file names none.</summary>
    public static int? Side(string clip) => F.Clips.TryGetValue(clip, out var c) && c.Side is int s && s != 0 ? Math.Sign(s) : null;

    public static double Fps => F.Fps;

    /// <summary>The clip's length and its cancel beat as written, in seconds of clip time (null: not in the file).</summary>
    public static double? Len(string clip) => F.Clips.TryGetValue(clip, out var c) && c.Len is double l && l > 0 ? l / (F.Fps > 0 ? F.Fps : 60) : null;
    public static double? Cancel(string clip) => F.Clips.TryGetValue(clip, out var c) && c.Cancel is int k ? k / (F.Fps > 0 ? F.Fps : 60) : null;

    /// <summary>A chain cut's beats in seconds of clip time: its length, its contact and its cancel beat.</summary>
    public readonly record struct Beats(double Len, double Contact, double Cancel);

    /// <summary>The timing contract's cut and its heavy (frames at 60 fps): what a clip that writes no beat falls back to.</summary>
    public const double CutLen = 42, CutContact = 14, CutCancel = 22, HeavyLen = 54, HeavyContact = 20, HeavyCancel = 30;

    /// <summary>A chain cut's beats (Sim/SwingChain.cs): the clip's written len, contact and cancel; each one not written
    /// falls back by itself: the length to the contract's (42 f, the heavy 54), the contact and the cancel to the
    /// contract's share of the length (14/42 and 22/42; the heavy 20/54 and 30/54). No clip: the contract's cut.</summary>
    public static Beats ChainBeats(string? clip, bool heavy)
    {
        double len = (clip != null ? Len(clip) : null) ?? (heavy ? HeavyLen : CutLen) / 60;
        double contact = (clip != null ? Contact(clip) : null) ?? len * (heavy ? HeavyContact / HeavyLen : CutContact / CutLen);
        double cancel = (clip != null ? Cancel(clip) : null) ?? len * (heavy ? HeavyCancel / HeavyLen : CutCancel / CutLen);
        contact = Math.Clamp(contact, 0, len);
        return new Beats(len, contact, Math.Clamp(cancel, contact, len));
    }

    /// <summary>Read the file again (a test that changed it).</summary>
    public static void Reload() => file = null;
}

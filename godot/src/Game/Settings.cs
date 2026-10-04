using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>
/// What the player has set (the web game kept these in local storage):
/// the picture's quality, the sound, the voices, how much gore, how much the screen
/// shakes, a window or the whole screen, and that they are an adult. Kept in
/// the user folder as JSON; changes apply at once.
/// </summary>
public sealed class Settings
{
    public string Quality = "high";
    public string Sound = "on";
    public string Gore = "full";
    public string Motion = "full";
    public bool Fullscreen = true;
    /// <summary>The survivor's health drawn under them in a night's fight.</summary>
    public bool UnderBar = true;
    public bool Mature;
    /// <summary>The recorded voices on (subtitles show either way), and how loud, 0..1.</summary>
    public bool Voices = true;
    public float VoiceVolume = 1;
    /// <summary>Cinematics seen on this machine: they can be skipped from their first frame.</summary>
    public List<string> SeenCinematics = new();

    const string File = "user://settings.json";
    public static Settings Current { get; private set; } = Load();

    static Settings Load()
    {
        var s = Read();
        // Tools taking pictures are taken as having agreed (the web game's ?manual).
        if (Args.Has("shot")) s.Mature = true;
        return s;
    }

    static Settings Read()
    {
        try
        {
            if (!FileAccess.FileExists(File)) return new Settings();
            using var f = FileAccess.Open(File, FileAccess.ModeFlags.Read);
            return Core.Json.Parse<Settings>(f.GetAsText()) ?? new Settings();
        }
        catch (Exception) { return new Settings(); }
    }

    public void Save()
    {
        using var f = FileAccess.Open(File, FileAccess.ModeFlags.Write);
        f?.StoreString(Core.Json.Write(this));
    }

    /// <summary>How much blood and how much of a body comes apart (1, 0.35, 0).</summary>
    public float GoreLevel => Gore switch { "reduced" => 0.35f, "off" => 0, _ => 1 };
    /// <summary>How much the camera shakes (the heavy blow's pause goes with it when off).</summary>
    public float ShakeLevel => Motion switch { "reduced" => 0.4f, "off" => 0, _ => 1 };
    public bool Hitstop => Motion != "off";
    public float Volume => Sound switch { "quiet" => 0.4f, "off" => 0, _ => 1 };

    public static string Next(string now, params string[] among) => among[(Array.IndexOf(among, now) + 1) % among.Length];

    /// <summary>A window or the whole screen (not in runs without a screen).</summary>
    public void ApplyWindow()
    {
        if (DisplayServer.GetName() == "headless" || OS.GetCmdlineUserArgs().Length > 0 && Args.Has("shot")) return;
        DisplayServer.WindowSetMode(Fullscreen ? DisplayServer.WindowMode.Fullscreen : DisplayServer.WindowMode.Windowed);
    }
}

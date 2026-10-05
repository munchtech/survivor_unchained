using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The townsfolk's own clips (tools/anim/folk.py: captured and generated
/// motion retargeted onto the kit's women and men, packed into
/// art/anim/folk.res and played as "folk/f_..." or "folk/m_..."), and which
/// answers each clip the game asks of an unarmed townsperson. Anything else
/// plays from the Universal Animation Library as before.
/// </summary>
public static class FolkClips
{
    const string LibPath = "res://art/anim/folk.res", MetaPath = "res://art/anim/folk_clips.json";
    public const string Prefix = "folk/";
    static AnimationLibrary? lib;
    static Godot.Collections.Dictionary? meta;
    static bool tried;

    public static AnimationLibrary? Library()
    {
        if (tried) return lib;
        tried = true;
        if (!ResourceLoader.Exists(LibPath)) return null;
        lib = GD.Load<AnimationLibrary>(LibPath);
        if (FileAccess.FileExists(MetaPath))
            meta = Json.ParseString(FileAccess.GetFileAsString(MetaPath)).AsGodotDictionary();
        return lib;
    }

    /// <summary>How fast a walk carries them, in metres a second of their
    /// own skeleton; 0 for none.</summary>
    public static float Speed(string clip)
    {
        Library();
        if (clip.StartsWith(Prefix)) clip = clip[Prefix.Length..];
        if (meta == null || !meta.ContainsKey(clip)) return 0;
        var m = meta[clip].AsGodotDictionary();
        return m.ContainsKey("speed") ? (float)m["speed"] : 0;
    }

    /// <summary>The folk clip for one the game names ("folk/..."), for a
    /// woman or a man, or null for the library's.</summary>
    public static string? For(bool woman, string game)
    {
        var want = game switch
        {
            "Walk_Loop" or "Walk" or "Walking_A" or "Walking_B" or "Walking_C" => "walk",
            "Idle" or "Idle_Loop" or "Idle_B" or "Unarmed_Idle" => "idle",
            "Idle_Talking_Loop" or "Idle_Talking" => "talk",
            "Idle_FoldArms_Loop" or "Idle_FoldArms" => "arms_crossed",
            "Sit_Chair_Idle" or "Sitting_Idle_Loop" or "Sitting_Idle" => "sit_chair",
            "Sit_Floor_Idle" => "sit_floor",
            "Cheer" => "cheer",
            "Wave" => "wave",
            "Interact" => "work",
            "PickUp" or "PickUp_Table" => "pick_up",
            _ => null,
        };
        return Named(woman, want);
    }

    /// <summary>The crowd's own motion (tools/anim/crowd.py) for one the game
    /// names, or null: the Risen's lurch at the crowd's pace rather than
    /// skating on the library's slow zombie walk (armed, the weapon hangs
    /// and the other hand reaches); a caster's rally, the weapon or the fist
    /// thrust up and shaken; a heavy's slam, both fists (armed: the axe)
    /// brought down from overhead into the ground, and the get-up after it;
    /// a crossbow's drop to one knee and aim, and the shot, the kick and the
    /// rise.</summary>
    public static string? Crowd(bool woman, bool armed, string game) => game switch
    {
        "Zombie_Walk_Fwd_Loop" or "Zombie_Walk_Fwd" or "Walking_D_Skeletons" => Named(woman, armed ? "lurch_armed" : "lurch"),
        "Rally" => Named(woman, armed ? "rally_armed" : "rally"),
        "Slam" => Named(woman, armed ? "slam_armed" : "slam"),
        "KneelAim" => Named(woman, "kneel_aim"),
        "KneelShot" => Named(woman, "kneel_shot"),
        _ => null,
    };

    /// <summary>The crowd's three ways to fall (crowd.py), for the roles
    /// "die", "die2" and "die3": over onto the back, onto the face, and in
    /// a heap on the side; or null where the library has none. A field of
    /// the dead picks among them so no two neighbours lie alike.</summary>
    public static string[]? Deaths(bool woman, bool armed, bool pistol = false)
    {
        var all = new[] { "die_back", "die_front", "die_side" };
        var named = new string[all.Length];
        for (int i = 0; i < all.Length; i++)
        {
            // Armed, what is held is laid flat with the hand (a crossbow on its side), not stood on end.
            var n = (pistol ? Named(woman, all[i] + "_pistol") : null) ?? (armed ? Named(woman, all[i] + "_armed") : null) ?? Named(woman, all[i]);
            if (n == null) return null;
            named[i] = n;
        }
        return named;
    }

    static string? Named(bool woman, string? want)
    {
        if (want == null || Library() is not { } l) return null;
        var name = (woman ? "f_" : "m_") + want;
        return l.HasAnimation(name) ? Prefix + name : null;
    }
}

import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Ui/Front.cs', [
    ('''        var foot = Style.Label($"BETA  ·  THE FIRST CHAPTER{Built()}", Style.UiBold, Style.Badge, Style.InkFaint);
        foot.Position = new Vector2(134, 1040);
        AddChild(foot);
    }

    /// <summary>When this build of the game was made, so an old build is seen for what it is
    /// (the owner once ran a build older than the work they were looking for).</summary>
    static string Built()
    {
        try
        {
            var at = typeof(TitleScreen).Assembly.Location;
            if (string.IsNullOrEmpty(at) || !System.IO.File.Exists(at)) return "";
            var t = System.IO.File.GetLastWriteTime(at);
            return $"  ·  BUILT {t:d MMMM, HH:mm}".ToUpperInvariant();
        }
        catch (Exception) { return ""; }
    }
''', '''        var (built, stale) = Build;
        var foot = Style.Label($"BETA  ·  THE FIRST CHAPTER{(built is DateTime t ? $"  ·  BUILT {t:d MMMM, HH:mm}".ToUpperInvariant() : "")}", Style.UiBold, Style.Badge, Style.InkFaint);
        foot.Position = new Vector2(134, 1040);
        AddChild(foot);
        if (stale)
        {
            var warn = Style.Label("This build is older than the game's code, so the newest work is not in it. Open the project in Godot and press Play (it builds first).",
                Style.UiBold, Style.Caption, Style.EmberHi, true);
            warn.Position = new Vector2(134, 1000);
            warn.Size = new Vector2(900, 0);
            AddChild(warn);
        }
    }

    static (DateTime?, bool)? build;

    /// <summary>When the game's code was last built, and whether any of it has changed since:
    /// run from the project manager, Godot starts the last build without making a new one, and
    /// the owner once looked for work that was not in the build they ran. (Godot loads the code
    /// from memory, so the build is read from where the editor writes it; an exported game has
    /// neither, and says nothing.)</summary>
    static (DateTime?, bool) Build => build ??= ReadBuild();

    static (DateTime?, bool) ReadBuild()
    {
        try
        {
            var dll = ProjectSettings.GlobalizePath("res://.godot/mono/temp/bin/Debug/SurvivorUnchained.dll");
            if (!System.IO.File.Exists(dll)) return (null, false);
            var t = System.IO.File.GetLastWriteTime(dll);
            bool stale = false;
            foreach (var dir in new[] { "res://src", "res://logic" })
            {
                var path = ProjectSettings.GlobalizePath(dir);
                if (System.IO.Directory.Exists(path) && System.IO.Directory.EnumerateFiles(path, "*.cs", System.IO.SearchOption.AllDirectories)
                    .Any(f => System.IO.File.GetLastWriteTime(f) > t.AddMinutes(1))) stale = true;
            }
            return (t, stale);
        }
        catch (Exception) { return (null, false); }
    }
'''),
])

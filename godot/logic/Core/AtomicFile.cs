using System;
using System.IO;

namespace SurvivorUnchained.Core;

/// <summary>A file replaced whole or not at all: written beside, then moved over, so a crash or a
/// full disk mid-write never leaves the only copy truncated (saves, settings, key bindings).</summary>
public static class AtomicFile
{
    /// <summary>True when the new text is in place; false (the old file untouched) when it could not be written.</summary>
    public static bool Write(string path, string text)
    {
        var tmp = path + ".tmp";
        try
        {
            File.WriteAllText(tmp, text);
            File.Move(tmp, path, true);
            return true;
        }
        catch (Exception e) when (e is IOException or UnauthorizedAccessException)
        {
            try { if (File.Exists(tmp)) File.Delete(tmp); } catch (Exception x) when (x is IOException or UnauthorizedAccessException) { }
            return false;
        }
    }
}

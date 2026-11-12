namespace SurvivorUnchained.View;

public sealed partial class TeleRank
{
    static TeleRank? cur;
    const string DataPath = "res://data/content/tele_rank.json";
    /// <summary>The game's table, read once from the data file, else the fallback (equal to the data).</summary>
    public static TeleRank Current => cur ??= Parse(Godot.FileAccess.FileExists(DataPath) ? Godot.FileAccess.GetFileAsString(DataPath) : Fallback);
}

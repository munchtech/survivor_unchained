using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained;

/// <summary>
/// --mem-tex-jump MB (dev, the tester lane, 24 Nov: a den loop run's texture monitor stepped +240 MB at one loop, +264 at
/// another run's loop 8, with nothing in the log to say what loaded): every 2 s, once 30 s in, the texture monitor is read; the
/// first read takes a census (the textures the tree reaches and the ones only the resource cache holds), and whenever the
/// monitor stands MB or more over the last census, a new census is taken and the textures in it that the last one lacked are
/// printed, biggest first ("mem tex jump"). Textures are matched by what they are and where they are held (digits in a node
/// path folded), not by RID, so a place rebuilt with the same textures is not news. The census is slow (a cache scan): dev only.
/// </summary>
public partial class MemLog
{
    readonly double jumpMb = Args.Has("mem-tex-jump") ? Args.Num("mem-tex-jump", 50) : -1;
    double jumpLast, jumpT;
    Dictionary<string, (long B, string What, string Where)>? jumpSeen;

    void JumpTick(double delta)
    {
        if (jumpMb < 0 || Time.GetTicksMsec() < 30000 || (jumpT += delta) < 2) return;
        jumpT = 0;
        double now = Performance.GetMonitor(Performance.Monitor.RenderTextureMemUsed) / 1048576.0;
        if (jumpSeen != null && now - jumpLast < jumpMb) return;
        var (tex, _) = Reach(GetTree().Root);
        CachedOnly(tex.Keys.ToHashSet(), tex);
        var keyed = new Dictionary<string, (long B, string What, string Where)>();
        foreach (var v in tex.Values)
        {
            string k = System.Text.RegularExpressions.Regex.Replace(v.Where, "[0-9]+", "#") + " | " + v.What;
            for (int n = 2; !keyed.TryAdd(k, v); n++) k = k.Split(" ~")[0] + " ~" + n;   // the same kind held twice: counted twice
        }
        if (jumpSeen != null)
        {
            var fresh = keyed.Where(kv => !jumpSeen.ContainsKey(kv.Key)).Select(kv => kv.Value).OrderByDescending(v => v.B).ToList();
            GD.Print($"mem tex jump: monitor {jumpLast:0} -> {now:0} MB at {Time.GetTicksMsec() / 1000.0:0} s (zone {(GetParent() is Play.Game g ? g.Zone?.Id ?? "-" : "-")}); " +
                     $"{fresh.Count} textures held now that the last census lacked, {fresh.Sum(v => v.B) / 1048576.0:0.0} MB (mips assumed)");
            foreach (var v in fresh.Take(25)) GD.Print($"mem tex jump new: {v.B / 1048576.0:0.0} MB {v.What} {v.Where}");
        }
        else GD.Print($"mem tex jump: first census at {Time.GetTicksMsec() / 1000.0:0} s, monitor {now:0} MB, {keyed.Count} textures");
        jumpSeen = keyed;
        jumpLast = now;
    }
}

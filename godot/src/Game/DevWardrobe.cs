using System.Linq;
using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained;

/// <summary>Pictures of the wardrobe (bd-ui W18): `--looks id,id` collects those looks, `--shown head:id,body:id,feet:id` shows them,
/// `--wardrobe-dye body:metal=gilt,body:cloth=crimson` dyes a zone, `--wardrobe-slot body` picks the screen's slot (read by it);
/// reach the screen with `--open wardrobe@T`.</summary>
public static class DevWardrobe
{
    public static void Apply(CharacterData ch)
    {
        Wardrobe.BackFill(ch);
        if (Args.Get("looks") is string looks)
            foreach (var id in looks.Split(',', System.StringSplitOptions.RemoveEmptyEntries)) GD.Print($"looks {id}: {(Wardrobe.Collect(ch, id.Trim()) ? "found" : "not a new look of hers")}");
        if (Args.Get("shown") is string shown)
            foreach (var p in shown.Split(',', System.StringSplitOptions.RemoveEmptyEntries).Select(x => x.Split(':')))
                if (p.Length == 2) Wardrobe.SetShown(ch, p[0], p[1]);
        if (Args.Get("wardrobe-dye") is string dyes)
            foreach (var p in dyes.Split(',', System.StringSplitOptions.RemoveEmptyEntries).Select(x => x.Split(':', '=')))
                if (p.Length == 3) Wardrobe.SetDye(ch, p[0], p[1], p[2]);
    }
}

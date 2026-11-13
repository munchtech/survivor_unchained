using System.Linq;
using Godot;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained;

/// <summary>Pictures of the socket panel (bd-ui W11): `--gems id:n,id:n` grants owned gems, `--socket skill:index:gem,...`
/// sets them (through Supports.Socket at the skill's rank), after --veteran. `--arts-skill ID[:index]` is read by the
/// Arts screen: it opens on the Skills page with that skill chosen (and that socket's chooser open); reach it with `--open arts@T`.</summary>
public static class DevSockets
{
    public static void Apply(CharacterData ch)
    {
        if (Args.Get("gems") is string gems)
            foreach (var kv in gems.Split(',', System.StringSplitOptions.RemoveEmptyEntries).Select(x => x.Split(':')))
                ch.Gems.Owned[kv[0]] = ch.Gems.Owned.GetValueOrDefault(kv[0]) + (kv.Length > 1 ? int.Parse(kv[1]) : 1);
        if (Args.Get("socket") is string socks)
            foreach (var p in socks.Split(',', System.StringSplitOptions.RemoveEmptyEntries).Select(x => x.Split(':')))
            {
                bool ok = p.Length == 3 && Supports.Socket(ch.Gems, p[0], SkillBook.RankOf(ch, p[0]), int.Parse(p[1]), p[2] == "-" ? null : p[2]);
                GD.Print($"socket {string.Join(":", p)}: {(ok ? "set" : "refused")}");
            }
    }
}

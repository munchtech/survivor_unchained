using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* A lit lamp-post's menu (docs/design/ARPG.md section 2 'Lamp-posts', 3.5, 7.3), engine-free: what it offers where she stands,
 * built from the world and the post registry (lamp_posts.json), so it is tested without a screen. The game's screen
 * (Ui/PostScreen.cs) shows it; the look is the UI lead's.
 *   Travel: every other lit post, grouped by zone; hidden until the night is over (prologue.done: the night is one road);
 *     refused in a fight (a foe within LampRise.Calm of the post, the Light prompt's lock).
 *   World tier: I-IV, the current one marked, the locked ones with what opens them; a pick re-scales the live fight.
 *   Lamps: the respec bench (LampBook.LayoutsOpen: a town, or a lit post out of a fight).
 *   Rest: her rise point here, mended (out of a fight); before the Ford is done (FullMenu) the menu is Rest and Leave only.
 *   Leave. */
public static class PostMenu
{
    /// <summary>Travel is offered once this world fact is true (the night is one road).</summary>
    public const string TravelFact = "prologue.done";

    /// <summary>The zones' names as their runtimes give them (ZoneRuntime.Name), for travel's groups.</summary>
    static readonly Dictionary<string, string> Names = new()
    {
        ["lowford"] = "The Low Ford Road", ["waystation"] = "The Waystation", ["verge"] = "Thornhollow Verge",
    };

    public static string ZoneName(string zone) => Names.TryGetValue(zone, out var n) ? n : zone;

    /// <summary>One zone's lit posts to travel to.</summary>
    public sealed record Group(string Zone, string Name, IReadOnlyList<LampPosts.Post> Posts);

    /// <summary>One world tier's line: its numbers in short, whether it is hers now, open, and if not, what opens it.</summary>
    public sealed record TierLine(int N, string Name, string Numbers, bool Current, bool Open, string? Opens);

    public static bool TravelShown(WorldState w) => w.Fact(TravelFact).Truthy;

    /// <summary>No hostile foe on its feet within LampRise.Calm of the post (no fight: always calm).</summary>
    public static bool Calm(Battle? b, LampPosts.Post at) => b == null || LampRise.Crowd(b, at.X, at.Z, LampRise.Calm) == 0;

    /// <summary>Why travel is refused here now, or null.</summary>
    public static string? TravelRefused(Battle? b, LampPosts.Post at) => Calm(b, at) ? null : "Not with them on you";

    /// <summary>Where she can travel from the post: every other lit post (placeholders left out), grouped by zone, her own
    /// zone first, then the registry's order; empty while travel is hidden.</summary>
    public static List<Group> Travel(WorldState w, LampPosts.Post here)
    {
        if (!TravelShown(w)) return new();
        var to = LampPosts.All.Where(p => !p.Draft && p.Id != here.Id && LampBook.PostLit(w, p.Id)).ToList();
        return to.GroupBy(p => p.Zone).OrderBy(g => g.Key == here.Zone ? 0 : 1)
            .Select(g => new Group(g.Key, ZoneName(g.Key), g.ToList())).ToList();
    }

    static string X(double v) => $"×{v:0.##}";

    /// <summary>A tier's numbers in one short line ("Foes ×2.5 health, ×1.8 damage · +5 item levels · Rare+ ×1.6 · Legendary ×1.5").</summary>
    public static string Numbers(WorldTiers.Tier t)
    {
        var parts = new List<string> { $"Foes {X(t.Health)} health, {X(t.Damage)} damage" };
        if (t.ItemLevels > 0) parts.Add($"+{t.ItemLevels} item levels");
        if (t.Rare != 1) parts.Add($"Rare+ {X(t.Rare)}");
        if (t.Legendary != 1) parts.Add($"Legendary {X(t.Legendary)}");
        return string.Join("  ·  ", parts);
    }

    /// <summary>What an unlock fact means in words.</summary>
    public static string OpensWhen(string fact) => fact switch
    {
        "act1.done" => "Opens after Act 1",
        "campaign.done" => "Opens after the campaign",
        _ => "Not yet open",
    };

    public static List<TierLine> Tiers(WorldState w)
    {
        int now = WorldTiers.Of(w);
        return WorldTiers.Numbers.Select(n =>
        {
            var t = WorldTiers.Get(n);
            bool open = WorldTiers.Open(w, n);
            return new TierLine(n, t.Name, Numbers(t), n == now, open, open || t.Opens == null ? null : OpensWhen(t.Opens));
        }).ToList();
    }

    /// <summary>Her world tier set to n (refused if locked or unknown: false). With a live fight on the tier (Journey.WorldTierOn),
    /// the fight takes it at once: the new scale for foes spawned from now, and every living foe (never her allies or
    /// neutrals, as Battle.SpawnEnemy scales them) has its health, max health and damage scaled by new/old.</summary>
    public static bool SetTier(WorldState w, Battle? b, bool live, int n)
    {
        if (!WorldTiers.Set(w, n)) return false;
        if (b == null || !live) return true;
        var t = WorldTiers.Get(n);
        double hp = t.Health / b.WorldHealth, dmg = t.Damage / b.WorldDamage;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Faction is Faction.Ally or Faction.Town or Faction.Wild or Faction.Player) continue;
            e.MaxHp *= hp;
            e.Hp *= hp;
            e.Damage *= dmg;
        }
        b.WorldHealth = t.Health; b.WorldDamage = t.Damage; b.KitDamageMul = t.Kit; b.KitEveryMul = t.KitEvery; b.StoryStand = t.Stand;
        return true;
    }

    /// <summary>The respec bench (the Lamps with layouts open) at this post now: in a town, or at a lit post out of a fight.</summary>
    public static bool LampsOpen(WorldState w, Battle? b, LampPosts.Post at) =>
        LampBook.LayoutsOpen(w, at.Zone, LampBook.PostLit(w, at.Id) && Calm(b, at) ? at.Id : null);

    /// <summary>She stands at the post's bench now: the Lamps open there (LampsOpen: a lit post, calm), alive, and in its
    /// reach. LampBook.Bench reads it while the bench is open (GamePostMenu.PostLamps).</summary>
    public static bool AtBench(WorldState w, Battle? b, LampPosts.Post at) =>
        LampsOpen(w, b, at) && (b == null || b.Player.Alive
            && Math.Pow(b.Player.X - at.X, 2) + Math.Pow(b.Player.Z - at.Z, 2) <= Math.Pow(Zones.LampRise.Reach + 1, 2));

    /// <summary>(SU-043) The Lamps' edits (a lamp lit or put out, a wick planned, a layout taken up) may run now: out of a
    /// fight, or in one at the bench the post menu opened (AtBench, its post in this zone). The screen asks again as each
    /// act runs, so walking off or a foe coming closes it.</summary>
    public static bool EditsOpen(WorldState? w, string? zone, Battle? b) =>
        b is not { Combat: true }
        || w != null && LampBook.Bench?.Invoke(w) is { } id && LampPosts.Get(id) is { } at && at.Zone == zone && AtBench(w, b, at);

    public enum Option { Rest, Travel, Tier, Lamps, Unions, Leave }

    /// <summary>(M5 r3) The post's full menu (travel, the world tier, the Lamps bench) opens once the Low Ford is done
    /// (TravelFact): before it, its first post offered WORLD TIER II and LAMPS to a player who had just learned to walk.</summary>
    public static bool FullMenu(WorldState w) => w.Fact(TravelFact).Truthy;

    /// <summary>The menu's lines at the post, in order, each with why it is refused now (or null): Rest first (her rise point
    /// here, mended out of a fight); then, once the Ford is done (FullMenu), travel, the tier and the Lamps; and leave.</summary>
    public static List<(Option Option, string? Refused)> Options(WorldState w, Battle? b, LampPosts.Post at, CharacterData? ch = null)
    {
        var o = new List<(Option, string?)>();
        o.Add((Option.Rest, Calm(b, at) ? null : "Not with them on you"));
        if (FullMenu(w))
        {
            if (TravelShown(w)) o.Add((Option.Travel, TravelRefused(b, at) ?? (Travel(w, at).Count == 0 ? "No other lamp burns yet" : null)));
            o.Add((Option.Tier, null));
            o.Add((Option.Lamps, LampsOpen(w, b, at) ? null : "Not with them on you"));
            if (ch != null && UnionJoin.Open(ch)) o.Add((Option.Unions, UnionsRefused(w, b, at, ch)));
        }
        o.Add((Option.Leave, null));
        return o;
    }

    /* ------------------------------------------------------------ unions -- */

    /// <summary>One Union's line at the post: joined on this layout, learned (paid for) already, and why it can't be
    /// joined (or unjoined, when joined) now, or null.</summary>
    public sealed record UnionLine(UnionDef Union, bool Joined, bool Known, int Price, string? Refused);

    /// <summary>Why the Unions are refused here now (Level 15 and the post are asked; a line's own reasons are its), or null.</summary>
    public static string? UnionsRefused(WorldState w, Battle? b, LampPosts.Post at, CharacterData ch) =>
        !UnionJoin.Open(ch) ? UnionJoin.Why(UnionNo.Level)
        : !LampsOpen(w, b, at) ? "Not with them on you"
        : UnionJoin.Offered(ch).Count == 0 ? "No Union yet: carry two skills that join" : null;

    /// <summary>Her calling's Unions she can reach (UnionJoin.Offered), joined ones first.</summary>
    public static List<UnionLine> Unions(CharacterData ch) =>
        UnionJoin.Offered(ch).Select(u =>
        {
            bool joined = UnionJoin.Joined(ch).Contains(u.Id);
            var no = joined ? UnionJoin.CanUnjoin(ch, u.Id) : UnionJoin.CanJoin(ch, u.Id);
            return new UnionLine(u, joined, UnionJoin.Known(ch, u.Id), UnionJoin.PriceFor(ch, u), UnionJoin.Why(no, u));
        }).OrderBy(l => l.Joined ? 0 : 1).ToList();

    /// <summary>Join or unjoin a Union at the post (only there: a lit post, out of a fight). Null: done; else why not.
    /// The first join pays its price (UnionJoin.Join: the cheapest rare items unless named).</summary>
    public static string? ToggleUnion(WorldState w, Battle? b, LampPosts.Post at, CharacterData ch, string id, IReadOnlyCollection<string>? pay = null)
    {
        if (UnionsRefused(w, b, at, ch) is { } no) return no;
        var u = Content.Unions.Find(id);
        var r = UnionJoin.Joined(ch).Contains(id) ? UnionJoin.Unjoin(ch, id) : UnionJoin.Join(ch, id, pay);
        return UnionJoin.Why(r, u);
    }

    /// <summary>Rest at the post (out of a fight): it is her rise point in its zone, and she is mended whole. False: refused.</summary>
    public static bool Rest(WorldState w, Battle? b, LampPosts.Post at)
    {
        if (!Calm(b, at) || !LampBook.PostLit(w, at.Id)) return false;
        LampBook.SetLastPost(w, at.Zone, at.Id);
        if (b is { Player.Alive: true }) b.Player.Hp = b.MaxHp;
        return true;
    }
}

using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/// <summary>
/// The ember draft: three cards (four, with the right gear) each time the
/// survivor's ember rises a level, from two kinds of skill:
///
///   - combat skills (the weapons, up to six): a new one, or a rank in one
///     you carry, to rank 8. Anyone can take any; a calling leans a little
///     toward its own style.
///   - passive skills (up to six), ranked the same way. Each weapon's
///     evolutions name a passive: at rank 8 with one rank of it, the weapon
///     is offered what it can become (the choice is always the player's).
///
/// Blessings are not in it: they change how the fight works, and come as
/// milestones (a great blessing as an arena begins and at its fifteenth
/// minute, first of all; one more at every Boons.Milestones ember level,
/// after that level's own draft).
///
/// It leans, never forces. Cards that share tags with what the build already
/// does are likelier; a passive that would evolve a weapon you carry is
/// likelier still (much more so once that weapon is at rank 8); rarer cards
/// get likelier with luck.
/// </summary>
public static class LevelUp
{
    static double RarityWeight(Rarity r) => r switch
    {
        Rarity.Common => 10, Rarity.Uncommon => 6.5, Rarity.Rare => 3.6, Rarity.Epic => 1.7, _ => 0.7,
    };

    /// <summary>Statuses the build applies, from weapons, evolutions and triggers.</summary>
    public static HashSet<StatusKind> BuildStatuses(Battle b)
    {
        var o = new HashSet<StatusKind>();
        foreach (var w in b.Weapons) if (w.StatusOf is { } s) o.Add(s.Kind);
        foreach (var t in b.Triggers)
            foreach (var fx in t.Def.Effects)
            {
                if (fx is Effect.Apply st) o.Add(st.Payload.Kind);
                else if (fx is Effect.Explode { Status: { } es }) o.Add(es.Kind);
            }
        if (b.Boons.ContainsKey("serration")) o.Add(StatusKind.Bleed);
        if (b.Boons.ContainsKey("chilling")) o.Add(StatusKind.Chill);
        if (b.Boons.ContainsKey("searing")) o.Add(StatusKind.Sear);
        foreach (var g in b.GearStatuses) o.Add(g);
        return o;
    }

    public static HashSet<Tag> BuildTags(Battle b)
    {
        var o = new HashSet<Tag>();
        foreach (var w in b.Weapons) foreach (var t in w.Tags) o.Add(t);
        foreach (var (id, r) in b.Boons)
            if (r > 0 && Boons.Find(id) is { } d) foreach (var t in d.Tags) o.Add(t);
        if (b.Boons.ContainsKey("spirit_companion") || b.Boons.ContainsKey("grave_call") || b.Boons.ContainsKey("soul_harvest")) o.Add(Tag.Summon);
        return o;
    }

    static bool Meets(Battle b, Requirement? req, HashSet<StatusKind> statuses, HashSet<Tag> tags)
    {
        if (req == null) return true;
        if (req.Any != null) return req.Any.Any(r => Meets(b, r, statuses, tags));
        if (req.Status is { } s) return statuses.Contains(s);
        if (req.Tag is { } t) return tags.Contains(t);
        if (req.Boon != null) return b.Boons.GetValueOrDefault(req.Boon) > 0;
        return true;
    }

    /// <summary>What a weapon at full rank can become now: each branch whose
    /// passive the survivor holds (a rank is enough). With both, the choice
    /// is theirs.</summary>
    public static List<Evolution> EarnedBranches(Battle b, string weaponId)
    {
        var w = b.Weapons.Find(x => x.Id == weaponId);
        if (w == null || w.Evolution != null || w.Rank < Content.Weapons.MaxRank) return new();
        return w.Def.Evolutions.Where(evo => evo.Catalysts.Any(c => b.Boons.GetValueOrDefault(c) > 0)).ToList();
    }

    /// <summary>The passive skills that would evolve a weapon, by branch.</summary>
    public static List<(Evolution Branch, string[] Passives)> EvolvesWith(string weaponId) =>
        Content.Weapons.All.TryGetValue(weaponId, out var d) ? d.Evolutions.Select(e => (e, e.Catalysts)).ToList() : new();

    /// <summary>Passive skills held (blessings are not passives).</summary>
    public static int PassivesHeld(Battle b) => b.Boons.Count(kv => kv.Value > 0 && Boons.Find(kv.Key)?.Kind == BoonKind.Passive);

    static string Names(IEnumerable<string> ids)
    {
        var n = ids.Select(id => Boons.Find(id)?.Name ?? id).ToList();
        return n.Count > 1 ? $"{string.Join(", ", n.Take(n.Count - 1))} or {n[^1]}" : n.FirstOrDefault() ?? "";
    }

    static double Affinity(IEnumerable<Tag> cardTags, HashSet<Tag> build)
    {
        int n = 0;
        foreach (var t in cardTags) if (build.Contains(t)) n++;
        return 1 + n * 0.6;
    }

    /// <summary>Is the next draft a great blessing? (Before anything else.)</summary>
    public static bool GreatNext(Battle b) => b.GreatOwed > 0;

    /// <summary>Is the next draft a milestone's blessing? (Skills owed come first.)</summary>
    public static bool BlessingNext(Battle b) => !GreatNext(b) && b.PendingLevels == 0 && b.PendingBlessings.Count > 0;

    /// <summary>The level the next draft is for (several can be owed at once).</summary>
    public static int DraftLevel(Battle b) => GreatNext(b) ? b.EmberLevel : BlessingNext(b) ? b.PendingBlessings[0] : b.EmberLevel - b.PendingLevels + 1;

    /// <summary>Drafts still owed after this one.</summary>
    public static int Queued(Battle b) => b.GreatOwed + b.PendingLevels + b.PendingBlessings.Count - 1;

    /// <summary>Weighted pick without replacement.</summary>
    static Offer? TakeFrom(Battle b, List<(Offer O, double W)> pool)
    {
        if (pool.Count == 0) return null;
        double total = 0;
        foreach (var p in pool) total += p.W;
        double roll = b.Rng.Next() * total;
        int k = 0;
        for (; k < pool.Count; k++) { roll -= pool[k].W; if (roll <= 0) break; }
        k = System.Math.Min(k, pool.Count - 1);
        var o = pool[k].O;
        pool.RemoveAt(k);
        return o;
    }

    public static List<Offer> Draft(Battle b, int count = 3)
    {
        var statuses = BuildStatuses(b);
        var tags = BuildTags(b);
        double luck = b.Stats.Get(Stat.Luck);
        var offers = new List<Offer>();
        double Weight(Rarity r) => RarityWeight(r) * (r != Rarity.Common ? 1 + (luck - 1) * 0.6 : 1);

        // A great blessing: any of them, whoever the survivor is, or the next
        // rank of one held.
        if (GreatNext(b))
        {
            var pool = new List<(Offer, double)>();
            foreach (var id in Boons.Great)
            {
                var d = Boons.All[id];
                int r = b.Boons.GetValueOrDefault(id);
                if (r >= d.Max || b.BannedCards.Contains(id)) continue;
                bool deeper = r > 0 && d.DeeperText is { } dt && r - 1 < dt.Length;
                string text = deeper ? $"Rank {r + 1}: {d.DeeperText![r - 1]}" : d.Text;
                pool.Add((new Offer { Kind = OfferKind.Boon, Id = id, Rarity = d.Rarity, Title = d.Name, Text = text, From = r, To = r + 1, Icon = d.Icon, Tags = d.Tags, Blessing = true, Great = true },
                    deeper ? 3 : 1));
            }
            for (int i = 0; i < count; i++) if (TakeFrom(b, pool) is { } o) offers.Add(o);
            return offers.Count > 0 ? offers : Respite(blessing: true, great: GreatNext(b));
        }

        // A milestone's blessing: game-changers only.
        if (BlessingNext(b))
        {
            var pool = new List<(Offer, double)>();
            foreach (var id in Boons.Order)
            {
                var d = Boons.All[id];
                if (d.Kind != BoonKind.Blessing) continue;
                int r = b.Boons.GetValueOrDefault(d.Id);
                if (r >= d.Max || b.BannedCards.Contains(d.Id) || !Meets(b, d.Requires, statuses, tags)) continue;
                // The great blessings are an arena's own gift: a milestone only deepens one held.
                if (r == 0 && Boons.IsGreat(d.Id)) continue;
                // A blessing held can be deepened instead: what its next rank adds.
                bool deeper = r > 0 && d.DeeperText is { } dt && r - 1 < dt.Length;
                string text = deeper ? $"Rank {r + 1}: {d.DeeperText![r - 1]}" : d.Text;
                pool.Add((new Offer { Kind = OfferKind.Boon, Id = d.Id, Rarity = d.Rarity, Title = d.Name, Text = text, From = r, To = r + 1, Icon = d.Icon, Tags = d.Tags, Blessing = true },
                    Weight(d.Rarity) * Affinity(d.Tags, tags) * (deeper ? 2.5 : 1)));
            }
            for (int i = 0; i < count; i++) if (TakeFrom(b, pool) is { } o) offers.Add(o);
            return offers.Count > 0 ? offers : Respite(blessing: true, great: GreatNext(b));
        }

        // Evolutions come first and are not left to chance: one weapon at a
        // time, every branch it has earned.
        var ready = b.Weapons.Find(w => EarnedBranches(b, w.Id).Count > 0);
        if (ready != null)
            foreach (var evo in EarnedBranches(b, ready.Id))
                offers.Add(new Offer
                {
                    Kind = OfferKind.Evolve, Id = ready.Id, Branch = evo.Id, Rarity = Rarity.Legendary, Title = evo.Name,
                    Text = $"{ready.Def.Name} becomes {evo.Name}. {evo.Description}", Icon = evo.Art ?? ready.Def.Art, Tags = ready.Tags,
                });

        // Combat skills: new weapons, and ranks in the ones you carry.
        var combat = new List<(Offer, double)>();
        foreach (var w in b.Weapons)
        {
            if (w.Rank >= Content.Weapons.MaxRank) continue;
            int next = w.Rank + 1;
            string extra = next == 4 || next == 7 ? " One more projectile." : "";
            string hint = next == Content.Weapons.MaxRank && w.Evolution == null
                ? $" At rank 8, with {Names(EvolvesWith(w.Id).SelectMany(e => e.Passives).Distinct())}, it evolves." : "";
            combat.Add((new Offer
            {
                Kind = OfferKind.Rank, Id = w.Id, Rarity = Rarity.Common, Title = w.Evolution?.Name ?? w.Def.Name,
                Text = $"+20% damage (+{(next - 1) * 20}% in all).{extra}{hint}", From = w.Rank, To = next, Icon = w.Evolution?.Art ?? w.Def.Art, Tags = w.Tags,
            }, 9 * Affinity(w.Tags, tags)));
        }
        if (b.Weapons.Count < Content.Weapons.MaxWeapons)
        {
            // A small arsenal wants new weapons more than a full one does.
            double want = b.Weapons.Count < 3 ? 2.4 : b.Weapons.Count < 5 ? 1.4 : 1;
            foreach (var id in Content.Weapons.Pool)
            {
                if (b.Weapons.Exists(w => w.Id == id) || b.BannedCards.Contains(id)) continue;
                var d = Content.Weapons.All[id];
                // A slight lean toward the calling's own style; anyone can take anything.
                double lean = b.Favours.Count > 0 && d.Tags.Any(b.Favours.Contains) ? 1.35 : 1;
                combat.Add((new Offer { Kind = OfferKind.Weapon, Id = id, Rarity = Rarity.Uncommon, Title = d.Name, Text = d.Description, Icon = d.Art, Tags = d.Tags },
                    3.2 * want * lean * Affinity(d.Tags, tags)));
            }
        }

        // Passive skills: new ones while there is room, and ranks in the ones held.
        var passive = new List<(Offer, double)>();
        bool room = PassivesHeld(b) < Boons.MaxPassives;
        foreach (var bid in Boons.Order)
        {
            var d = Boons.All[bid];
            if (d.Kind != BoonKind.Passive) continue;
            int r = b.Boons.GetValueOrDefault(d.Id);
            if (r >= d.Max || b.BannedCards.Contains(d.Id) || (r == 0 && !room) || !Meets(b, d.Requires, statuses, tags)) continue;
            // Name what it would evolve among the weapons carried.
            var evolves = b.Weapons.Where(w => w.Evolution == null && EvolvesWith(w.Id).Any(e => e.Passives.Contains(d.Id))).ToList();
            bool ready8 = evolves.Any(w => w.Rank >= Content.Weapons.MaxRank);
            string note = r == 0 && evolves.Count > 0 ? $" Evolves {string.Join(" and ", evolves.Select(w => w.Def.Name))} at rank 8." : "";
            double wgt = Weight(d.Rarity) * 0.75 * Affinity(d.Tags, tags);
            if (r > 0) wgt *= 1.35;
            if (r == 0 && evolves.Count > 0) wgt *= ready8 ? 4 : 1.6;
            passive.Add((new Offer { Kind = OfferKind.Boon, Id = d.Id, Rarity = d.Rarity, Title = d.Name, Text = d.Text + note, From = r, To = r + 1, Icon = d.Icon, Tags = d.Tags }, wgt));
        }

        // At least one combat skill when there is one to offer; the rest from both.
        int open = System.Math.Max(0, count - offers.Count);
        if (open > 0 && (TakeFrom(b, combat) ?? TakeFrom(b, passive)) is { } first) offers.Add(first);
        var both = combat.Concat(passive).ToList();
        for (int i = offers.Count; i < System.Math.Max(count, offers.Count); i++)
        {
            if (TakeFrom(b, both) is { } o) offers.Add(o);
            else break;
        }
        if (offers.Count == 0) offers = Respite(blessing: false, great: false);
        return offers.Take(System.Math.Max(count, offers.Count(o => o.Kind == OfferKind.Evolve))).ToList();
    }

    /// <summary>When there is nothing left to offer: a breath, or coin (standing in
    /// for whatever draft was owed).</summary>
    static List<Offer> Respite(bool blessing, bool great) =>
    [
        new Offer { Kind = OfferKind.Heal, Id = "heal", Rarity = Rarity.Common, Title = "Second Wind", Text = "Recover 35% of your health.", Icon = "heart", Blessing = blessing, Great = great },
        new Offer { Kind = OfferKind.Gold, Id = "gold", Rarity = Rarity.Common, Title = "Scavenged Coin", Text = "+25 gold.", Icon = "coin", Blessing = blessing, Great = great },
    ];

    /// <summary>A chest opened in an arena: an evolution earned comes out
    /// first, then ranks in what the survivor carries. What it gave, by name.</summary>
    public static List<string> OpenChest(Battle b, int count)
    {
        var got = new List<string>();
        var ready = b.Weapons.Find(w => EarnedBranches(b, w.Id).Count > 0);
        if (ready != null)
        {
            var evo = EarnedBranches(b, ready.Id)[0];
            b.Evolve(ready.Id, evo.Id);
            got.Add(evo.Name);
            count--;
        }
        for (int i = 0; i < count; i++)
        {
            var ranks = b.Weapons.Where(w => w.Rank < Content.Weapons.MaxRank).Select(w => (w.Id, Name: w.Evolution?.Name ?? w.Def.Name, Weapon: true))
                .Concat(b.Boons.Where(kv => Boons.All.TryGetValue(kv.Key, out var d) && d.Kind == BoonKind.Passive && kv.Value < d.Max)
                    .Select(kv => (Id: kv.Key, Name: Boons.All[kv.Key].Name, Weapon: false))).ToList();
            if (ranks.Count == 0) { b.HealPlayer(b.MaxHp * 0.3, "chest"); b.GoldGained += 25; got.Add("gold and a draught"); break; }
            var pick = ranks[b.Rng.Int(0, ranks.Count - 1)];
            if (pick.Weapon) b.RankWeapon(pick.Id); else b.AddBoon(pick.Id);
            got.Add(pick.Name);
        }
        return got;
    }

    public static void Choose(Battle b, Offer o)
    {
        switch (o.Kind)
        {
            case OfferKind.Weapon: b.AddWeapon(o.Id, 1); break;
            case OfferKind.Rank: b.RankWeapon(o.Id); break;
            case OfferKind.Boon: b.AddBoon(o.Id); break;
            case OfferKind.Evolve: b.Evolve(o.Id, o.Branch!); break;
            case OfferKind.Heal: b.HealPlayer(b.MaxHp * 0.35, "draft"); break;
            case OfferKind.Gold: b.GoldGained += 25; break;
        }
        if (o.Great) b.GreatOwed = System.Math.Max(0, b.GreatOwed - 1);
        else if (o.Blessing) { if (b.PendingBlessings.Count > 0) b.PendingBlessings.RemoveAt(0); }
        else b.PendingLevels = System.Math.Max(0, b.PendingLevels - 1);
    }
}

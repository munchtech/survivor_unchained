using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/// <summary>What one thing out of a chest is: an evolution, a rank in a combat skill, a rank
/// in a passive, or (when nothing is left to raise) gold and a draught.</summary>
public enum ChestItemKind { Evolution, Rank, Passive, Gold }

/// <summary>One thing out of a chest, as its opening shows it: what it raised, its name and
/// glyph, the ranks it went between, how rare it reads, its school (a combat skill's), and for
/// an evolution what it grew from.</summary>
public sealed record ChestItem(ChestItemKind Kind, string Id, string Name, string Icon, int From, int To, Rarity Rarity, School? School, string? Before);

/// <summary>A chest opened: where it lay, what came out, whose hoard it was (a boss's, else
/// null), and how many chests this night has opened (later ones open quicker).</summary>
public sealed record ChestOpened(double X, double Z, int Seed, IReadOnlyList<ChestItem> Items, string? Hoard, int Opened);

/// <summary>What the draft remembers between drafts: what it showed last (so a
/// reroll shows something new), how long since anything rare, how long a
/// weapon ready to evolve has waited for its passive, and how many cards this
/// draft deals.</summary>
public sealed class DraftMemory
{
    /// <summary>Cards in the draft being decided (0: not dealt yet).</summary>
    public int Cards;
    /// <summary>What the draft being decided showed (card keys), for a reroll to avoid.</summary>
    public readonly HashSet<string> Shown = new();
    /// <summary>Skill drafts since a rare card was offered.</summary>
    public int RarePity;
    /// <summary>Drafts each weapon at rank 7 or more has waited for its passive.</summary>
    public readonly Dictionary<string, int> CatalystWait = new();
    /// <summary>Drafts skipped, and great blessings taken (the fifteenth minute's deals four).</summary>
    public int Skipped, Greats;
    /// <summary>Skill drafts dealt this arena (a reroll is the same draft).</summary>
    public int SkillDrafts;
    /// <summary>The calling's own great blessing has been in a hand this night.</summary>
    public bool OwnShown;
}

/// <summary>
/// The ember draft (docs/SKILLS_DESIGN.md, "The offer"): three cards each time
/// the survivor's ember rises a level (a fourth, now and then, with luck),
/// from two kinds of skill:
///
///   - combat skills (the weapons, up to six): a new one, or a rank in one
///     carried, to rank 8, then what it evolves into, then honing.
///   - passive skills (up to six), ranked the same way. Each weapon's
///     evolutions name the passives that evolve it.
///
/// Blessings come as their own drafts (a great blessing as an arena begins and
/// at its fifteenth minute; one more at every Boons.Milestones ember level).
///
/// It leans, never forces, and it guarantees a few things so a draft is never
/// a dud: an evolution earned is always offered; there is always a combat
/// skill; once two weapons are carried, always a card that ranks what you
/// carry; until three are carried, always a new one; a weapon ready to evolve
/// never waits more than two drafts for its passive. The leans: what the
/// build already does (its tags, and the paths it walks), the calling's
/// paths, skills learned by day (familiar), luck for the rare. Rare cards
/// have bad-luck protection; any rank can surge (two at once).
/// </summary>
public static class LevelUp
{
    static double RarityWeight(Rarity r) => r switch
    {
        Rarity.Common => 10, Rarity.Uncommon => 6.5, Rarity.Rare => 3.6, Rarity.Epic => 1.7, _ => 0.7,
    };

    /// <summary>Leans, as multipliers on a card's weight.</summary>
    public const double PathLean = 1.5, CallingLean = 1.3, AttunedLean = 2.0, FamiliarLean = 1.3, PassivePathLean = 1.3;
    /// <summary>The first skill drafts of an arena in which an attuned skill not yet
    /// taken is always among the cards.</summary>
    public const int AttunedDrafts = 4;
    /// <summary>Drafts a weapon ready to evolve may wait for its passive.</summary>
    public const int CatalystPity = 2;
    /// <summary>Skill drafts a rare passive may go missing for (the weight rises long before).</summary>
    public const int RareFloor = 10;
    /// <summary>Times a finished weapon can be honed, and what each does.</summary>
    public const int MaxHone = 10;
    public const double HoneStep = 0.12;

    /// <summary>The passives that only touch some kinds of combat skill, and
    /// which: offered to a build with none of them, they are a trap.</summary>
    public static readonly Dictionary<string, Tag[]> Affects = new()
    {
        ["duplicity"] = [Tag.Projectile, Tag.Orbit, Tag.Chain, Tag.Melee, Tag.Summon, Tag.Storm],
        ["velocity"] = [Tag.Projectile],
        ["emberblood"] = [Tag.Fire],
        ["conduit"] = [Tag.Storm],
        ["venom"] = [Tag.Dot, Tag.Steel],
        ["kinship"] = [Tag.Summon],
        ["perennial"] = [Tag.Zone, Tag.Orbit, Tag.Summon, Tag.Explosion],
        ["serration"] = [Tag.Physical, Tag.Steel],
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
                else if (fx is Effect.Zone { Status: { } zs }) o.Add(zs.Kind);
                else if (fx is Effect.Missiles { Status: { } ms }) o.Add(ms.Kind);
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

    /// <summary>The paths the build walks (up to two): those it carries two
    /// weapons of, the most invested first.</summary>
    public static List<PathDef> BuildPaths(Battle b)
    {
        var o = new List<(PathDef P, double S)>();
        foreach (var p in Paths.All)
        {
            int n = 0;
            double s = 0;
            foreach (var w in b.Weapons)
                if (p.Weapons.Contains(w.Id)) { n++; s += 1 + w.Rank / 8.0 + (w.Evolution != null ? 0.5 : 0); }
            if (n < 2) continue;
            foreach (var (id, r) in b.Boons)
                if (r > 0 && (p.Passives.Contains(id) || p.Blessings.Contains(id) || p.Great.Contains(id))) s += 0.4;
            o.Add((p, s));
        }
        return o.OrderByDescending(x => x.S).Take(2).Select(x => x.P).ToList();
    }

    static bool Meets(Battle b, Requirement? req, HashSet<StatusKind> statuses, HashSet<Tag> tags)
    {
        if (req == null) return true;
        if (req.Any != null) return req.Any.Any(r => Meets(b, r, statuses, tags));
        if (req.All != null) return req.All.All(r => Meets(b, r, statuses, tags));
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
        return w.Def.Evolutions.Where(evo => evo.Catalysts.Any(c => Holds(b, c))).ToList();
    }

    /// <summary>A passive held for a recipe: drafted, or stood in for by kindled gear.</summary>
    public static bool Holds(Battle b, string passive) => b.Boons.GetValueOrDefault(passive) > 0 || b.Stands.Contains(passive);

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
        return 1 + n * 0.5;
    }

    /// <summary>Is the next draft a great blessing? (Before anything else.)</summary>
    public static bool GreatNext(Battle b) => b.GreatOwed > 0;

    /// <summary>Is the next draft a milestone's blessing? (Skills owed come first.)</summary>
    public static bool BlessingNext(Battle b) => !GreatNext(b) && b.PendingLevels == 0 && b.PendingBlessings.Count > 0;

    /// <summary>Is the next draft a level's own skill draft?</summary>
    public static bool SkillNext(Battle b) => !GreatNext(b) && !BlessingNext(b) && b.PendingLevels > 0;

    /// <summary>The level the next draft is for (several can be owed at once).</summary>
    public static int DraftLevel(Battle b) => GreatNext(b) ? b.EmberLevel : BlessingNext(b) ? b.PendingBlessings[0] : b.EmberLevel - b.PendingLevels + 1;

    /// <summary>Drafts still owed after this one.</summary>
    public static int Queued(Battle b) => b.GreatOwed + b.PendingLevels + b.PendingBlessings.Count - 1;

    /// <summary>How many cards the draft being decided deals: three; a fourth
    /// with chance 1 - 1/luck (none at luck 1, a third of the time at 1.5);
    /// four for the fifteenth minute's great blessing. Dealt once a draft,
    /// so a reroll keeps it.</summary>
    public static int Count(Battle b)
    {
        var m = b.Drafting;
        if (m.Cards > 0) return m.Cards;
        if (GreatNext(b)) return m.Cards = m.Greats >= 1 || b.Omens ? 4 : 3;
        double luck = b.Stats.Get(Stat.Luck);
        return m.Cards = 3 + (SkillNext(b) && (b.Roads || b.Rng.Next() < 1 - 1 / System.Math.Max(1, luck)) ? 1 : 0);
    }

    /// <summary>A card's key, as the draft remembers what it showed.</summary>
    public static string Key(Offer o) => $"{o.Kind}:{o.Id}:{o.Branch}";

    sealed class Cand
    {
        public Offer O = null!;
        public double W;
        /// <summary>Ranks something carried (a weapon or a passive held).</summary>
        public bool Advancing;
        /// <summary>The weapons it would evolve, if it is their passive.</summary>
        public HashSet<string> Catalyst = new();
        public bool NewWeapon, Attuned;
    }

    /// <summary>Weighted pick without replacement (among those that pass `only`).</summary>
    static Cand? TakeFrom(Battle b, List<Cand> pool, System.Func<Cand, bool>? only = null)
    {
        double total = 0;
        foreach (var p in pool) if (only == null || only(p)) total += p.W;
        if (total <= 0) return null;
        double roll = b.Rng.Next() * total;
        int last = -1;
        for (int k = 0; k < pool.Count; k++)
        {
            if (only != null && !only(pool[k])) continue;
            last = k;
            roll -= pool[k].W;
            if (roll <= 0) break;
        }
        if (last < 0) return null;
        var c = pool[last];
        pool.RemoveAt(last);
        return c;
    }

    /// <summary>The draft owed next. Count: how many cards (0: as Count says).</summary>
    public static List<Offer> Draft(Battle b, int count = 0)
    {
        if (count <= 0) count = Count(b);
        var mem = b.Drafting;
        var statuses = BuildStatuses(b);
        var tags = BuildTags(b);
        var paths = BuildPaths(b);
        double luck = b.Stats.Get(Stat.Luck);
        var offers = new List<Offer>();
        // Rare cards: likelier with luck, and the longer since one was offered.
        double Weight(Rarity r) => RarityWeight(r) * (r != Rarity.Common ? 1 + (luck - 1) * 0.6 : 1) *
            (r >= Rarity.Rare ? System.Math.Min(4, 1 + 0.3 * mem.RarePity) : 1);
        // A reroll looks again: what was just shown is far less likely.
        double Again(Offer o) => mem.Shown.Contains(Key(o)) ? 0.15 : 1;
        bool OnPath(string id, System.Func<PathDef, string[]> of) => paths.Any(p => of(p).Contains(id));

        // A great blessing: any of them, whoever the survivor is, or the next
        // rank of one held.
        if (GreatNext(b))
        {
            var pool = new List<Cand>();
            foreach (var id in Boons.Great)
            {
                var d = Boons.All[id];
                int r = b.Boons.GetValueOrDefault(id);
                if (r >= d.Max || b.BannedCards.Contains(id) || (d.Calling != null && d.Calling != b.Calling)) continue;
                bool deeper = r > 0 && d.DeeperText is { } dt && r - 1 < dt.Length;
                string text = deeper ? $"Rank {r + 1}: {d.DeeperText![r - 1]}" : d.Text;
                var o = new Offer { Kind = OfferKind.Boon, Id = id, Rarity = d.Rarity, Title = d.Name, Text = text, From = r, To = r + 1, Icon = d.Icon, Tags = d.Tags, Blessing = true, Great = true };
                bool suits = OnPath(id, p => p.Great);
                if (d.Calling != null) o.Why.Add("Your calling's own");
                else if (suits) o.Why.Add("Suits your path");
                pool.Add(new Cand { O = o, W = (deeper ? 3 : 1) * (suits || d.Calling != null ? 1.5 : 1) * Again(o) });
            }
            // Dealt by role: a ward and a power in every hand, then an answer to
            // champions or a quickening, then (a fourth card) anything.
            Boons.GreatRole Role(Cand c) => Boons.GreatRoles[c.O.Id];
            System.Func<Cand, bool>?[] order =
            [
                c => Role(c) == Boons.GreatRole.Ward, c => Role(c) == Boons.GreatRole.Power,
                c => Role(c) is Boons.GreatRole.Answer or Boons.GreatRole.Tempo, null,
            ];
            // The calling's own comes once a night: as Dusk's power half the time, else at Midnight.
            var own = pool.FirstOrDefault(c => Boons.All[c.O.Id].Calling != null && c.O.From == 0);
            bool ownNow = own != null && !mem.OwnShown && (mem.Greats >= 1 || b.Rng.Next() < 0.5);
            if (ownNow) { pool.Remove(own!); mem.OwnShown = true; order = [order[0], order[2], null]; }
            for (int i = 0; i < count - (ownNow ? 1 : 0); i++)
                if ((TakeFrom(b, pool, order[System.Math.Min(i, order.Length - 1)]) ?? TakeFrom(b, pool)) is { } c) offers.Add(c.O);
            if (ownNow) offers.Insert(System.Math.Min(1, offers.Count), own!.O);
            return Shown(b, offers.Count > 0 ? offers : Respite(blessing: true, great: GreatNext(b)));
        }

        // A milestone's blessing: game-changers only.
        if (BlessingNext(b))
        {
            var pool = new List<Cand>();
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
                var o = new Offer { Kind = OfferKind.Boon, Id = d.Id, Rarity = d.Rarity, Title = d.Name, Text = text, From = r, To = r + 1, Icon = d.Icon, Tags = d.Tags, Blessing = true };
                double w = Weight(d.Rarity) * Affinity(d.Tags, tags) * (deeper ? 2.5 : 1) * Again(o);
                if (OnPath(id, p => p.Blessings)) { w *= PathLean; o.Why.Add($"For {paths.First(p => p.Blessings.Contains(id)).Name}"); }
                if (d.Requires?.All != null) o.Why.Add("A duo: two of your families at once");
                pool.Add(new Cand { O = o, W = w });
            }
            for (int i = 0; i < count; i++) if (TakeFrom(b, pool) is { } c) offers.Add(c.O);
            return Shown(b, offers.Count > 0 ? offers : Respite(blessing: true, great: GreatNext(b)));
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
                    Path = Paths.All.FirstOrDefault(p => p.Capstones.Contains(evo.Id))?.Id,
                });

        // So are unions, once both halves are evolved.
        if (offers.Count == 0 && ReadyUnions(b).FirstOrDefault() is { } un)
        {
            var wa = b.Weapons.First(w => w.Id == un.A);
            var wb = b.Weapons.First(w => w.Id == un.B);
            offers.Add(new Offer
            {
                Kind = OfferKind.Union, Id = un.Id, Rarity = Rarity.Legendary, Title = un.Name,
                Text = $"{wa.Evolution!.Name} and {wb.Evolution!.Name} become one. {un.Description} A combat slot is free again.",
                Icon = Content.Weapons.All[un.Into].Art, Tags = Content.Weapons.All[un.Into].Tags,
                Path = Paths.All.FirstOrDefault(p => p.Capstones.Contains(un.Id))?.Id,
            });
        }

        int passiveRoom = Boons.MaxPassives - PassivesHeld(b);
        // The weapons waiting on a passive to evolve (rank 7 or more, none held).
        var waiting = b.Weapons.Where(w => w.Evolution == null && w.Rank >= Content.Weapons.MaxRank - 1 &&
            !w.Def.Evolutions.Any(e => e.Catalysts.Any(c => Holds(b, c)))).ToList();

        // Combat skills: ranks in the ones you carry, new ones while there is room.
        var combat = new List<Cand>();
        foreach (var w in b.Weapons)
        {
            if (b.BannedCards.Contains(w.Id)) continue;
            if (w.Rank >= Content.Weapons.MaxRank)
            {
                // Finished (evolved, or nothing to become): honing, for the endless dark.
                if ((w.Evolution != null || w.Def.Evolutions.Length == 0) && w.Honed < MaxHone)
                {
                    var ho = new Offer
                    {
                        Kind = OfferKind.Hone, Id = w.Id, Rarity = Rarity.Uncommon, Title = $"{w.Evolution?.Name ?? w.Def.Name}, honed",
                        Text = $"+{HoneStep * 100:0}% damage ({w.Honed + 1} of {MaxHone}).", From = w.Honed, To = w.Honed + 1,
                        Icon = w.Evolution?.Art ?? w.Def.Art, Tags = w.Tags,
                    };
                    combat.Add(new Cand { O = ho, W = 4 * Again(ho), Advancing = true });
                }
                continue;
            }
            int next = w.Rank + 1;
            string extra = next == Content.Weapons.ProjRankA || next == Content.Weapons.ProjRankB ? " One more projectile." : "";
            var cats = EvolvesWith(w.Id).SelectMany(e => e.Passives).Distinct().ToList();
            bool held = cats.Any(c => Holds(b, c));
            string hint = "";
            if (next >= Content.Weapons.MaxRank - 1 && w.Evolution == null)
                hint = held ? (cats.Any(c => b.Boons.GetValueOrDefault(c) > 0) ? " At rank 8 it evolves." : $" At rank 8 it evolves: your gear stands in for {Names(cats.Where(b.Stands.Contains))}.") : passiveRoom > 0 ? $" At rank 8, with {Names(cats)}, it evolves." : $" It evolves with {Names(cats)}, but your passives are full.";
            var o = new Offer
            {
                Kind = OfferKind.Rank, Id = w.Id, Rarity = Rarity.Common, Title = w.Evolution?.Name ?? w.Def.Name, Recipe = w.Evolution == null ? Recipe(w.Id) : null,
                Text = $"+{w.Def.Growth * 100:0}% damage (+{(next - 1) * w.Def.Growth * 100:0}% in all).{extra}{hint}",
                From = w.Rank, To = next, Icon = w.Evolution?.Art ?? w.Def.Art, Tags = w.Tags,
            };
            // Pushing toward an evolution already in hand.
            double near = w.Rank >= 6 && w.Evolution == null && held ? 1.3 : 1;
            combat.Add(new Cand { O = o, W = 9 * Affinity(w.Tags, tags) * near * Again(o), Advancing = true });
        }
        if (b.Weapons.Count < Content.Weapons.MaxWeapons)
        {
            // A small arsenal wants new weapons more than a full one does.
            double want = b.Weapons.Count < 2 ? 2.4 : b.Weapons.Count < 4 ? 1.4 : 0.8;
            foreach (var id in Content.Weapons.Pool)
            {
                if (b.Weapons.Exists(w => w.Id == id) || b.BannedCards.Contains(id)) continue;
                var d = Content.Weapons.All[id];
                var o = new Offer { Kind = OfferKind.Weapon, Id = id, Rarity = Rarity.Uncommon, Title = d.Name, Text = d.Description, Icon = d.Art, Tags = d.Tags, From = 0, To = 1, Recipe = Recipe(id) };
                double w = 3.2 * want * Affinity(d.Tags, tags) * Again(o);
                var mine = paths.FirstOrDefault(p => p.Weapons.Contains(id));
                if (mine != null) { w *= PathLean; o.Path = mine.Id; o.Why.Add($"On your path: {mine.Name}"); }
                // A slight lean toward the calling's own style; anyone can take anything.
                if (b.CallingPaths.Any(p => Paths.Find(p)?.Weapons.Contains(id) == true) || (b.Favours.Count > 0 && d.Tags.Any(b.Favours.Contains)))
                {
                    w *= CallingLean;
                    if (mine == null) o.Why.Add("Your calling's");
                }
                // Carried by day: attuned, it comes first and comes in higher.
                if (b.Attuned.TryGetValue(id, out int at))
                {
                    w *= AttunedLean;
                    o.Attuned = true;
                    o.To = at;
                    o.Why.Insert(0, $"Banked: carried through the day, it wakes at rank {at}");
                }
                else if (b.Familiar.Contains(id))
                {
                    w *= FamiliarLean;
                    o.Why.Add("Familiar: you have learned it");
                }
                combat.Add(new Cand { O = o, W = w, NewWeapon = true, Attuned = o.Attuned });
            }
        }

        // Passive skills: new ones while there is room, and ranks in the ones held.
        var passive = new List<Cand>();
        foreach (var bid in Boons.Order)
        {
            var d = Boons.All[bid];
            if (d.Kind != BoonKind.Passive) continue;
            int r = b.Boons.GetValueOrDefault(d.Id);
            if (r >= d.Max || b.BannedCards.Contains(d.Id) || (r == 0 && passiveRoom <= 0) || !Meets(b, d.Requires, statuses, tags)) continue;
            // Name what it would evolve among the weapons carried.
            var evolves = b.Weapons.Where(w => w.Evolution == null && EvolvesWith(w.Id).Any(e => e.Passives.Contains(d.Id))).ToList();
            bool soon = evolves.Any(w => w.Rank >= Content.Weapons.MaxRank - 1);
            string note = r == 0 && evolves.Count > 0 ? $" Evolves {string.Join(" and ", evolves.Select(w => w.Def.Name))} at rank 8." : "";
            var o = new Offer { Kind = OfferKind.Boon, Id = d.Id, Rarity = d.Rarity, Title = d.Name, Text = d.Text + note, From = r, To = r + 1, Icon = d.Icon, Tags = d.Tags };
            double wgt = Weight(d.Rarity) * 0.75 * Affinity(d.Tags, tags) * Again(o);
            if (r > 0) wgt *= 1.35;
            // A passive for kinds of skill the build has none of is a trap: far
            // less likely, and the card says so.
            if (Affects.TryGetValue(d.Id, out var kinds) && !b.Weapons.Any(w => kinds.Any(w.Tags.Contains)) && evolves.Count == 0)
            {
                wgt *= 0.3;
                o.Why.Add("Little use to what you carry now");
            }
            if (r == 0 && evolves.Count > 0)
            {
                wgt *= soon ? 4 : 1.6;
                o.Why.Add(soon ? $"Evolves {evolves[0].Def.Name} now" : $"Evolves {evolves[0].Def.Name}");
            }
            if (OnPath(d.Id, p => p.Passives)) { wgt *= PassivePathLean; o.Path = paths.First(p => p.Passives.Contains(d.Id)).Id; }
            passive.Add(new Cand { O = o, W = wgt, Advancing = r > 0, Catalyst = r == 0 ? evolves.Select(w => w.Id).ToHashSet() : new() });
        }

        // The guarantees, then the rest from everything.
        int Open() => System.Math.Max(0, count - offers.Count);
        // What a guarantee put there stays there (the last guarantee does not swap it out).
        var kept = new HashSet<Offer>(offers);
        void Add(Cand? c)
        {
            if (c == null) return;
            offers.Add(c.O);
            kept.Add(c.O);
            combat.Remove(c);
            passive.Remove(c);
        }
        bool IsCombat(Offer o) => o.Kind is OfferKind.Rank or OfferKind.Weapon or OfferKind.Evolve or OfferKind.Hone;
        // A rare passive does not go missing for more than RareFloor drafts.
        if (Open() > 0 && mem.RarePity >= RareFloor && !offers.Any(o => o.Kind == OfferKind.Boon && o.Rarity >= Rarity.Rare))
            Add(TakeFrom(b, passive, c => c.O.Rarity >= Rarity.Rare));
        // A weapon ready to evolve does not wait more than CatalystPity drafts for its passive.
        foreach (var w in waiting)
            if (Open() > 0 && mem.CatalystWait.GetValueOrDefault(w.Id) >= CatalystPity && !offers.Any(o => IsCatalyst(o, w)))
                Add(TakeFrom(b, passive, c => c.Catalyst.Contains(w.Id)));
        // The first drafts bring what was carried by day.
        if (Open() > 0 && mem.SkillDrafts < AttunedDrafts && !offers.Any(o => o.Attuned))
            Add(TakeFrom(b, combat, c => c.Attuned));
        // At least one combat skill; until three are carried, a new one among them.
        bool young = b.Weapons.Count < 3;
        if (Open() > 0 && young && !offers.Any(o => o.Kind == OfferKind.Weapon)) Add(TakeFrom(b, combat, c => c.NewWeapon));
        if (Open() > 0 && !offers.Any(IsCombat)) Add(TakeFrom(b, combat));
        var both = combat.Concat(passive).ToList();
        while (Open() > 0 && TakeFrom(b, both) is { } c) { offers.Add(c.O); combat.Remove(c); passive.Remove(c); }
        // Once two are carried, always something that ranks what you carry.
        bool Advances(Offer o) => o.Kind is OfferKind.Rank or OfferKind.Evolve or OfferKind.Hone || (o.Kind == OfferKind.Boon && !o.Blessing && o.From > 0);
        if (b.Weapons.Count >= 2 && !offers.Any(Advances))
        {
            var adv = TakeFrom(b, combat.Concat(passive).Where(c => c.Advancing).ToList());
            int swap = offers.FindLastIndex(o => !kept.Contains(o));
            if (adv != null && swap >= 0) offers[swap] = adv.O;
            else if (adv != null) offers.Add(adv.O);
        }

        if (offers.Count == 0) offers = Respite(blessing: false, great: false);
        // Surges: now and then a rank comes two at once (likelier with luck).
        double surge = System.Math.Max(0.05, 0.05 + 0.15 * (luck - 1));
        foreach (var o in offers)
        {
            bool can = o.Kind switch
            {
                OfferKind.Rank => o.To < Content.Weapons.MaxRank,
                OfferKind.Weapon => true,
                OfferKind.Boon when !o.Blessing && o.From > 0 => o.To < Boons.All[o.Id].Max,
                _ => false,
            };
            if (!can || b.Rng.Next() >= surge) continue;
            o.Surge = 1;
            o.To += 1;
            if (o.Rarity < Rarity.Rare) o.Rarity = Rarity.Rare;
            o.Why.Insert(0, o.Kind == OfferKind.Weapon ? "Surge: it comes a rank higher" : "Surge: two ranks at once");
        }

        // What the draft remembers: how long since something rare, how long
        // each weapon has waited for its passive.
        if (offers.Any(o => o.Rarity >= Rarity.Rare && o.Kind == OfferKind.Boon)) mem.RarePity = 0;
        else mem.RarePity++;
        if (!mem.Shown.Any()) mem.SkillDrafts++;
        foreach (var w in waiting)
            mem.CatalystWait[w.Id] = offers.Any(o => IsCatalyst(o, w)) ? 0 : mem.CatalystWait.GetValueOrDefault(w.Id) + 1;
        var list = offers.Take(System.Math.Max(count, offers.Count(o => o.Kind is OfferKind.Evolve or OfferKind.Union))).ToList();
        return Shown(b, list);
    }

    /// <summary>What becomes of a combat skill, in a line: each evolution and
    /// the passives that make it, and the union it is half of.</summary>
    public static string Recipe(string weaponId)
    {
        if (!Content.Weapons.All.TryGetValue(weaponId, out var d) || d.Evolutions.Length == 0) return "";
        var parts = d.Evolutions.Select(e => $"{e.Name} with {Names(e.Catalysts)}").ToList();
        string s = $"Evolves: {string.Join("; ", parts)}.";
        if (Unions.Of(weaponId) is { } u)
            s += $" With {Content.Weapons.All[u.A == weaponId ? u.B : u.A].Name}, both evolved: {u.Name}.";
        return s;
    }

    /// <summary>A carried combat skill as the draft's arsenal shows it.</summary>
    public sealed record ArsenalLine(string Id, string Name, string Icon, School School, int Rank, bool Evolved, string Note, bool Ready);

    /// <summary>The arsenal, each skill with where it stands: what evolves it,
    /// whether it can now, what it joins.</summary>
    public static List<ArsenalLine> Arsenal(Battle b)
    {
        var o = new List<ArsenalLine>();
        foreach (var w in b.Weapons)
        {
            string note;
            bool ready = false;
            if (w.Evolution != null)
            {
                var u = Unions.Of(w.Id);
                var mate = u == null ? null : b.Weapons.Find(x => x.Id == (u.A == w.Id ? u.B : u.A));
                note = u == null ? (w.Honed > 0 ? $"Honed {w.Honed}" : "Evolved")
                    : mate?.Evolution != null ? $"Unites now: {u.Name}" : $"Joins {Content.Weapons.All[u.A == w.Id ? u.B : u.A].Name} for {u.Name}";
                ready = mate?.Evolution != null;
            }
            else if (w.Def.Evolutions.Length == 0) note = w.Honed > 0 ? $"Honed {w.Honed}" : "";
            else
            {
                var held = w.Def.Evolutions.Where(e => e.Catalysts.Any(c => Holds(b, c))).ToList();
                ready = held.Count > 0 && w.Rank >= Content.Weapons.MaxRank;
                note = held.Count > 0
                    ? (ready ? $"Evolves now: {string.Join(" or ", held.Select(e => e.Name))}" : $"At rank 8: {string.Join(" or ", held.Select(e => e.Name))}")
                    : $"Needs {Names(w.Def.Evolutions.SelectMany(e => e.Catalysts).Distinct())}";
            }
            o.Add(new ArsenalLine(w.Id, w.Evolution?.Name ?? w.Def.Name, w.Evolution?.Art ?? w.Def.Art, w.School, w.Rank, w.Evolution != null, note, ready));
        }
        return o;
    }

    /// <summary>The unions whose two halves are carried, both evolved.</summary>
    public static IEnumerable<UnionDef> ReadyUnions(Battle b) =>
        Unions.All.Where(u => b.Weapons.Any(w => w.Id == u.A && w.Evolution != null) && b.Weapons.Any(w => w.Id == u.B && w.Evolution != null));

    static bool IsCatalyst(Offer o, WeaponInst w) => o.Kind == OfferKind.Boon && !o.Blessing && w.Def.Evolutions.Any(e => e.Catalysts.Contains(o.Id));

    static List<Offer> Shown(Battle b, List<Offer> offers)
    {
        b.Drafting.Shown.Clear();
        foreach (var o in offers) b.Drafting.Shown.Add(Key(o));
        return offers;
    }

    /// <summary>When there is nothing left to offer: a breath, or coin (standing in
    /// for whatever draft was owed).</summary>
    static List<Offer> Respite(bool blessing, bool great) =>
    [
        new Offer { Kind = OfferKind.Heal, Id = "heal", Rarity = Rarity.Common, Title = "Second Wind", Text = "Recover 35% of your health.", Icon = "heart", Blessing = blessing, Great = great },
        new Offer { Kind = OfferKind.Gold, Id = "gold", Rarity = Rarity.Common, Title = "Scavenged Coin", Text = "+25 gold.", Icon = "coin", Blessing = blessing, Great = great },
    ];

    /// <summary>A chest's size before luck, as the genre's chests pay: one thing most often,
    /// three now and then, five rarely (docs/feel/SUGGESTIONS.md, S-09). The odds keep a chest
    /// worth 1.4 things on average, as the old 1 + 30% + 10% did, so the night is not re-priced;
    /// what changes is the jackpot. A roll in [0, 1).</summary>
    public static int ChestCount(double roll) => roll < 0.04 ? 5 : roll < 0.16 ? 3 : 1;

    /// <summary>A chest opened in an arena: an evolution earned comes out
    /// first (and costs the chest nothing), then ranks in what the survivor
    /// carries. What it gave, one thing at a time, for its opening to show.</summary>
    public static List<ChestItem> OpenChest(Battle b, int count)
    {
        var got = new List<ChestItem>();
        var ready = b.Weapons.Find(w => EarnedBranches(b, w.Id).Count > 0);
        if (ready != null)
        {
            var evo = EarnedBranches(b, ready.Id)[0];
            b.Evolve(ready.Id, evo.Id, chest: true);
            got.Add(new ChestItem(ChestItemKind.Evolution, ready.Id, evo.Name, evo.Art ?? ready.Def.Art, ready.Rank, ready.Rank, Rarity.Legendary, ready.School, ready.Def.Name));
        }
        for (int i = 0; i < count; i++)
        {
            var ranks = b.Weapons.Where(w => w.Rank < Content.Weapons.MaxRank).Select(w => (w.Id, Name: w.Evolution?.Name ?? w.Def.Name, Weapon: true))
                .Concat(b.Boons.Where(kv => Boons.All.TryGetValue(kv.Key, out var d) && d.Kind == BoonKind.Passive && kv.Value < d.Max)
                    .Select(kv => (Id: kv.Key, Name: Boons.All[kv.Key].Name, Weapon: false))).ToList();
            if (ranks.Count == 0)
            {
                b.HealPlayer(b.MaxHp * 0.3, "chest");
                b.GoldGained += 25;
                got.Add(new ChestItem(ChestItemKind.Gold, "gold", "Gold and a draught", "coin", 0, 0, Rarity.Common, null, null));
                break;
            }
            var pick = ranks[b.Rng.Int(0, ranks.Count - 1)];
            if (pick.Weapon)
            {
                var w = b.Weapons.Find(x => x.Id == pick.Id)!;
                int from = w.Rank;
                b.RankWeapon(pick.Id);
                got.Add(new ChestItem(ChestItemKind.Rank, w.Id, pick.Name, w.Art, from, w.Rank, Rarity.Uncommon, w.School, null));
            }
            else
            {
                int from = b.Boons.GetValueOrDefault(pick.Id);
                b.AddBoon(pick.Id);
                var d = Boons.All[pick.Id];
                got.Add(new ChestItem(ChestItemKind.Passive, pick.Id, pick.Name, d.Icon, from, b.Boons.GetValueOrDefault(pick.Id), d.Rarity, null, null));
            }
        }
        return got;
    }

    public static void Choose(Battle b, Offer o)
    {
        switch (o.Kind)
        {
            case OfferKind.Weapon:
                b.AddWeapon(o.Id, System.Math.Max(1, o.To ?? 1));
                break;
            case OfferKind.Rank:
                for (int i = 0; i <= o.Surge; i++) b.RankWeapon(o.Id);
                break;
            case OfferKind.Boon:
                for (int i = 0; i <= o.Surge; i++) b.AddBoon(o.Id);
                break;
            case OfferKind.Evolve: b.Evolve(o.Id, o.Branch!); break;
            case OfferKind.Hone: b.Hone(o.Id); break;
            case OfferKind.Union: b.Unite(o.Id); break;
            case OfferKind.Heal: b.HealPlayer(b.MaxHp * 0.35, "draft"); break;
            case OfferKind.Gold: b.GoldGained += 25; break;
        }
        Settle(b, o.Great, o.Blessing);
    }

    /// <summary>The draft owed is decided: the next one deals afresh.</summary>
    static void Settle(Battle b, bool great, bool blessing)
    {
        var m = b.Drafting;
        m.Cards = 0;
        m.Shown.Clear();
        if (great) { b.GreatOwed = System.Math.Max(0, b.GreatOwed - 1); m.Greats++; }
        else if (blessing) { if (b.PendingBlessings.Count > 0) b.PendingBlessings.RemoveAt(0); }
        else b.PendingLevels = System.Math.Max(0, b.PendingLevels - 1);
    }

    /// <summary>Look again (a reroll spent): the same number of cards, and
    /// what was just shown far less likely. Null if there is none to spend.</summary>
    public static List<Offer>? Reroll(Battle b)
    {
        if (b.Rerolls <= 0 || !b.DraftOwed) return null;
        b.Rerolls--;
        return Draft(b);
    }

    /// <summary>Never see this card again this arena (a banish spent); the draft deals again.</summary>
    public static List<Offer>? Banish(Battle b, Offer o)
    {
        if (b.Banishes <= 0 || o.Kind is OfferKind.Evolve or OfferKind.Union or OfferKind.Heal or OfferKind.Gold || !b.DraftOwed) return null;
        b.Banishes--;
        b.BannedCards.Add(o.Id);
        b.Drafting.Shown.Clear();
        return Draft(b);
    }

    /// <summary>The share of a level's ember a skipped draft gives back.</summary>
    public const double SkipRefund = 0.4;

    /// <summary>Can this draft be passed over? A level's own skill draft can;
    /// a blessing cannot.</summary>
    public static bool CanSkip(Battle b) => SkillNext(b);

    /// <summary>Take none of it: the level is spent, and some of its ember comes
    /// back, so the next level comes sooner.</summary>
    public static bool Skip(Battle b)
    {
        if (!CanSkip(b)) return false;
        int level = DraftLevel(b);
        b.Drafting.Skipped++;
        Settle(b, false, false);
        b.GainEmber(Battle.EmberNeed(System.Math.Max(1, level - 1)) * SkipRefund, raw: true);
        return true;
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Rpg;

/// <summary>One way of lighting the board: the type (the road given at creation), the lamps lit
/// and the Flare carried. A survivor keeps two (docs/design/CLASSES.md §2.4).</summary>
public sealed class LampLayout
{
    public string Type = "";
    public List<string> Lit = new();
    public string Flare = "";
}

public sealed class LampState
{
    public List<LampLayout> Layouts = new() { new(), new() };
    public int Active;
    /// <summary>Light my way: the suggested lamp is lit for you every level (§2.5).</summary>
    public bool LightMyWay;
    public LampLayout Now => Layouts[Math.Clamp(Active, 0, Layouts.Count - 1)];
}

/// <summary>Why a lamp can't be lit or put out (None: it can).</summary>
public enum LampNo { None, Unknown, Lit, Unlit, NoLamps, NotHome, Dark, Gate, Free, Holds }

/* The lamps a survivor has lit (docs/design/CLASSES.md §2.4-2.5).
 *
 * Lamps come from levels (one a level from 2 to 30), the story's bosses
 * (one each, the first win) and the atlas (eight, placed by its
 * milestones): about fifty at the end of everything. Three are free: the
 * hearth's first lamp, and the chosen type's entry and Strike.
 *
 * A lamp is lit next to a lit one, past its road's depth gate. Lamps go out
 * free, by day, at a town's lamp-post (the caller asks Journey.LampsOpen):
 * one at a time while what's left still hangs together, or all at once.
 * Changing the type puts every lamp out. */
public static class LampBook
{
    public const int AtlasLamps = 8;

    public static LampState State(CharacterData ch)
    {
        if (ch.Lamps != null) return ch.Lamps;
        Begin(ch, null);
        return ch.Lamps!;
    }

    /// <summary>The board as creation leaves it: the chosen type (one of the calling's roads; anything
    /// else walks the default) lit on every layout, so switching layouts never drops the pick.</summary>
    public static void Begin(CharacterData ch, string? type)
    {
        if (type == null || !Lamps.Roads.TryGetValue(type, out var r) || r.Calling != ch.Archetype) type = DefaultType(ch.Archetype);
        ch.Lamps = new LampState();
        foreach (var l in ch.Lamps.Layouts) Reset(ch, l, type);
    }

    public static LampLayout Now(CharacterData ch) => State(ch).Now;

    /// <summary>A calling's first road: the type a survivor who never chose one walks.</summary>
    public static string DefaultType(string calling) => Lamps.RoadsOf(calling).First().Id;

    /// <summary>Lamps earned: levels, the story's bosses beaten, the atlas's milestones.</summary>
    public static int Earned(CharacterData ch, WorldState? w) => Math.Max(0, ch.Level - 1) + StoryLamps(w) + AtlasLit(w);

    public static int StoryLamps(WorldState? w) => w == null ? 0 : Lamps.StoryFights.Count(id => w.Fact($"arena.{id}").Str == "won");

    /// <summary>The atlas's lamps (the experience lead's milestones set the fact), eight at most.</summary>
    public static int AtlasLit(WorldState? w) => w == null ? 0 : Math.Clamp((int)w.Fact("lamps.atlas").Number, 0, AtlasLamps);

    /// <summary>The lamps that cost nothing: the hearth's first, the type's entry and its Strike.</summary>
    public static HashSet<string> Free(CharacterData ch, LampLayout? l = null)
    {
        l ??= Now(ch);
        var o = new HashSet<string> { Lamps.Start(ch.Archetype) };
        if (Lamps.Roads.TryGetValue(l.Type, out var road))
        {
            o.Add(Lamps.Entry(road.Id));
            if (Lamps.FlareLamp(road.Strike) is { } s) o.Add(s);
        }
        return o;
    }

    public static int Spent(CharacterData ch) { var free = Free(ch); return Now(ch).Lit.Count(id => !free.Contains(id)); }

    public static int Spare(CharacterData ch, WorldState? w) => Earned(ch, w) - Spent(ch);

    public static bool IsLit(CharacterData ch, string id) => Now(ch).Lit.Contains(id);

    /// <summary>Lamps lit on a road (the free Strike counts): what its depth gates read.</summary>
    public static int Depth(CharacterData ch, string road) => Depth(Now(ch).Lit, road);

    static int Depth(IEnumerable<string> lit, string road) => lit.Count(id => Lamps.Find(id)?.Road == road);

    public static LampNo CanLight(CharacterData ch, WorldState? w, string id)
    {
        if (Lamps.Find(id) is not { } def) return LampNo.Unknown;
        var lit = Now(ch).Lit;
        if (lit.Contains(id)) return LampNo.Lit;
        if (def.Home && def.Calling != ch.Archetype) return LampNo.NotHome;
        if (!Lamps.Next(id).Any(lit.Contains)) return LampNo.Dark;
        if (def.Road != null && Depth(lit, def.Road) < def.Gate) return LampNo.Gate;
        if (Spare(ch, w) <= 0) return LampNo.NoLamps;
        return LampNo.None;
    }

    public static bool Light(CharacterData ch, WorldState? w, string id)
    {
        if (CanLight(ch, w, id) != LampNo.None) return false;
        Now(ch).Lit.Add(id);
        return true;
    }

    /// <summary>Can it go out (the caller has checked the place)? Not a free lamp, and what stays lit
    /// must still hang together from the hearth and meet its gates.</summary>
    public static LampNo CanUnlight(CharacterData ch, string id)
    {
        var l = Now(ch);
        if (!l.Lit.Contains(id)) return LampNo.Unlit;
        if (Free(ch).Contains(id)) return LampNo.Free;
        var rest = l.Lit.Where(x => x != id).ToList();
        return Holds(ch, rest) ? LampNo.None : LampNo.Holds;
    }

    public static bool Unlight(CharacterData ch, string id)
    {
        if (CanUnlight(ch, id) != LampNo.None) return false;
        var l = Now(ch);
        l.Lit.Remove(id);
        if (!Learned(ch).Contains(l.Flare)) l.Flare = Lamps.Road(l.Type).Strike;
        return true;
    }

    /// <summary>Every lamp out but the free ones.</summary>
    public static void Clear(CharacterData ch) => Reset(ch, Now(ch), Now(ch).Type);

    /// <summary>Walk another of the calling's roads: every lamp goes out, and the new type's are lit.</summary>
    public static bool SetType(CharacterData ch, string road)
    {
        if (!Lamps.Roads.TryGetValue(road, out var r) || r.Calling != ch.Archetype) return false;
        Reset(ch, Now(ch), road);
        return true;
    }

    /// <summary>Take up the other saved layout.</summary>
    public static bool Switch(CharacterData ch, int index)
    {
        var s = State(ch);
        if (index < 0 || index >= s.Layouts.Count) return false;
        s.Active = index;
        if (s.Now.Type == "") Reset(ch, s.Now, DefaultType(ch.Archetype));
        return true;
    }

    static void Reset(CharacterData ch, LampLayout l, string type)
    {
        l.Type = type;
        l.Lit = Free(ch, l).ToList();
        l.Flare = Lamps.Road(type).Strike;
    }

    /// <summary>Does this set of lamps hang together (every lamp reached from the hearth through lit
    /// lamps) and meet every gate?</summary>
    static bool Holds(CharacterData ch, List<string> lit)
    {
        var set = lit.ToHashSet();
        var seen = new HashSet<string>();
        var q = new Queue<string>(Free(ch).Where(set.Contains));
        foreach (var f in q) seen.Add(f);
        while (q.Count > 0)
            foreach (var n in Lamps.Next(q.Dequeue()))
                if (set.Contains(n) && seen.Add(n)) q.Enqueue(n);
        if (seen.Count != set.Count) return false;
        var free = Free(ch);
        return lit.All(id => free.Contains(id) || Lamps.Get(id) is var d && (d.Road == null || Depth(lit, d.Road) >= d.Gate));
    }

    /* ------------------------------------------------------- the Flare -- */

    /// <summary>The Flares the lit lamps have learned (the calling's own only).</summary>
    public static List<string> Learned(CharacterData ch) =>
        Now(ch).Lit.Select(Lamps.Find).Where(d => d != null && d.Kind == LampKind.Ultimate && d.Calling == ch.Archetype)
            .SelectMany(d => d!.Effects.Where(e => e.Do == LampDo.Flare).Select(e => e.Flare!)).ToList();

    /// <summary>The Flare carried: chosen by day, or at a night's start before the first draft.</summary>
    public static string Carried(CharacterData ch)
    {
        var l = Now(ch);
        var learned = Learned(ch);
        return learned.Contains(l.Flare) ? l.Flare : learned.FirstOrDefault() ?? "";
    }

    public static bool Carry(CharacterData ch, string flare)
    {
        if (!Learned(ch).Contains(flare)) return false;
        Now(ch).Flare = flare;
        return true;
    }

    /* --------------------------------------------------- light my way -- */

    /// <summary>The lamp the board suggests next (§2.5): along the survivor's own road first, what
    /// changes most for what they carry. Null when none can be lit.</summary>
    public static string? Suggest(CharacterData ch, WorldState? w)
    {
        if (Spare(ch, w) <= 0) return null;
        var l = Now(ch);
        var carried = SkillBook.Carried(ch).Select(s => s.Id).ToHashSet();
        foreach (var s in Items.EquipSlots) if (ch.Equipment[s] is { } it && Items.Find(it.Def)?.Weapon is { } wd) carried.Add(wd.Id);
        string? best = null;
        double bestScore = double.MinValue;
        foreach (var id in l.Lit.SelectMany(Lamps.Next).Distinct())
        {
            if (CanLight(ch, w, id) != LampNo.None) continue;
            var d = Lamps.Get(id);
            // Banked Flame is a choice, never a suggestion: it pays only to a hand that holds a charge back, and
            // spent as it fills it is a trap (the owner, 12 October: Light my way never lights it).
            if (d.Effects.Any(e => e.Rule == "flare.banked")) continue;
            // Before Act 1 is done it lights only the modifier marked early: the strong ones stay a hand's choice (§7).
            if (d.Kind == LampKind.UltimateMod && !d.Early && w != null && !w.Fact("chapter.done").Truthy) continue;
            double sc = d.Road == l.Type ? 100 : d.Region == LampRegion.Hearth ? 60 : 0;
            sc += d.Kind switch
            {
                LampKind.Ultimate => 40, LampKind.Reflex => 35, LampKind.Notable => 30, LampKind.Blue => 5,
                LampKind.Form or LampKind.ReflexUp or LampKind.FlareLamp => 20, LampKind.UltimateMod => 18,
                LampKind.Skill => d.Feeds.Any(carried.Contains) ? 32 : 2, _ => 10,
            };
            // Nothing live yet is no gift (a later phase's lamp).
            if (d.Effects.Length > 0 && d.Effects.All(e => e.Phase > Lamps.LivePhase)) sc -= 50;
            // Deterministic: ties go to the board's order.
            if (sc > bestScore) { bestScore = sc; best = id; }
        }
        return best;
    }

    /// <summary>Light my way: the suggested lamps, while there are lamps to light.</summary>
    public static int LightSuggested(CharacterData ch, WorldState? w)
    {
        int n = 0;
        while (Suggest(ch, w) is { } id && Light(ch, w, id)) n++;
        return n;
    }

    /* ------------------------------------------------ into the fight -- */

    /// <summary>What the lit lamps bring a fight. By night (an ember arena, a story fight) sizes run at
    /// a quarter, counts add one at most, and small lamps only lean the draft (§2.10).</summary>
    public static LampLoadout Loadout(CharacterData ch, bool night)
    {
        var l = Now(ch);
        var o = new LampLoadout { Night = night, Type = l.Type, Flare = Carried(ch), Lit = l.Lit.Count };
        var counts = new Dictionary<string, double>();
        foreach (var id in l.Lit)
        {
            if (Lamps.Find(id) is not { } d) continue;
            bool small = d.Kind is LampKind.Small or LampKind.Attribute;
            foreach (var e in d.Effects)
            {
                if (e.Phase > Lamps.LivePhase) continue;
                switch (e.Do)
                {
                    case LampDo.Mod when e.Stat != null:
                        if (night && small) break;
                        if (night && Lamps.IsCount(e.Stat) && !e.Price)
                        {
                            counts[e.Stat] = counts.GetValueOrDefault(e.Stat) + e.Value;
                            break;
                        }
                        o.Mods.Add(new StatMod(e.Stat, e.Mod, night && !e.Price ? e.Value * Lamps.NightSize : e.Value, $"lamp:{id}", e.When));
                        break;
                    case LampDo.Attr when e.Attr != null:
                        if (!night) o.Attributes[e.Attr] = o.Attributes.GetValueOrDefault(e.Attr) + (int)e.Value;
                        break;
                    // By night a small lamp gives nothing but its road's lean (CLASSES.md §2.10).
                    case LampDo.Rule when e.Rule != null:
                        if (night && small) break;
                        o.Add(e);
                        break;
                    case LampDo.Facet when e.Facet != null: o.Facets.Add(e.Facet); break;
                    case LampDo.Form when e.Art != null: o.Kin = e.Art; o.KinWait = e.Wait; break;
                    case LampDo.Reflex when e.Art != null: o.Reflexes.Add(new ReflexDef(e.Art, e.Trigger ?? "", e.Wait, e.Args)); break;
                    case LampDo.FlareMod when e.Flare != null: o.FlareMods.Add(e.Rule ?? id); break;
                }
            }
        }
        foreach (var (stat, v) in counts) o.Mods.Add(new StatMod(stat, ModKind.Flat, Math.Min(Lamps.NightCount, v), "lamps:counts"));
        o.Lean = LeanRoad(ch);
        return o;
    }

    /// <summary>The road lit deepest (the type's own on a tie): its cards lean by night.</summary>
    public static string LeanRoad(CharacterData ch)
    {
        var l = Now(ch);
        return Lamps.Roads.Keys.OrderByDescending(r => Depth(l.Lit, r) + (r == l.Type ? 0.5 : 0)).First();
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The story's fights by night (docs/design/STORY_NIGHTS_AND_TIME.md): which are open tonight, and
 * the arena each one is. They live here, not in the Verge, because the night calls them from
 * anywhere (the dusk line, "Answer the night"), the town included; the Verge keeps only where
 * each stands.
 *
 *   the Hollow by Night       Greymuzzle in his own Hollow (the Beast Problem, settled with blood)
 *   Raid on the Roost         Redcowl's camp taken in the dark (the Missing Caravan, by force)
 *   the Dig Boils Over        when the Dig has turned on her
 *   Behind the Sealed Door    with the sigil's fragment, the door wakes after dark
 *
 * Won or lost, the story is told how it went; a lost one waits for another night. */
public static class StoryFights
{
    /// <summary>One story fight: its id (the Verge's `night:ID`), the Verge spot it stands at and
    /// its reach there, what the prompt says, the place's name, when it is open (it stands in the
    /// wood to be taken), and when the night calls it by name (the story has pointed her at it: a
    /// fight open by default, the Pack hunted or the Roost raided, is the violent road, and the
    /// night never pushes her down it unasked).</summary>
    public sealed record Fight(string Id, string Spot, double Reach, string Verb, string Place, Func<Ctx, bool> Open, Func<Ctx, bool> Called);

    static Fact F(Ctx c, string k) => c.World.Fact(k);
    static bool Quest(Ctx c, string id, string entry) => Rules.Test(new Cond { Quest = new QuestCond { Id = id, Entry = entry } }, c);
    /// <summary>The stream runs clean: the sickness is out of it, or the Pack is cured.</summary>
    static bool StreamClean(Ctx c) => F(c, "stream.clear").Truthy || F(c, "beasts.outcome").Str == "cured";

    public static readonly Fight[] All =
    [
        new("hollow", "hollow", 6.5, "Hunt the Pack", "Wolf Hollow",
            c => !Standings.WolvesFriendly(c) && !Standings.HollowCalm(c) && F(c, "greymuzzle").Str != "dead",
            // Holloway's bounty on the Pack's old dog, or a hunt already begun there.
            c => Quest(c, "beasts", "holloway_bounty") || F(c, "hollow.hostile").Truthy),
        new("roost", "roost", 7, "Raid the Roost", "Redcowl's Roost",
            c => !Standings.KerchiefsFriendly(c) && F(c, "redcowl").Str is not ("dead" or "tricked") && !F(c, "roost.cleared").Truthy,
            // She knows where the Roost is, and the Kerchiefs are against her.
            c => Quest(c, "caravan", "roost_found") || F(c, "roost.hostile").Truthy),
        new("dig", "dig", 7, "Hold the Dig's edge", "The Dig",
            c => F(c, "dig.hostile").Truthy && !F(c, "dig.broken").Truthy, _ => true),
        new("vault", "vault", 5, "Set the sigil in the door", "The Sealed Door",
            c => Quest(c, "vault", "fragment") && !F(c, "vault.opened").Truthy, _ => true),
    ];

    public static Fight? Get(string id) => Array.Find(All, f => f.Id == id);

    /// <summary>The story's fights open now (standing in the wood to be taken).</summary>
    public static List<Fight> Open(Ctx c) => All.Where(f => f.Open(c)).ToList();

    /// <summary>The story's fights the night calls by name: open, and pointed at by the story.</summary>
    public static List<Fight> Called(Ctx c) => All.Where(f => f.Open(c) && f.Called(c)).ToList();

    /// <summary>A fight's arena, pulled from (zone, x, z, facing): where the story goes on after it.</summary>
    public static ArenaSpec Spec(string id, Ctx c, string returnZone, double x, double z, double facing)
    {
        var w = c.World;
        int tier = Math.Max(1, Math.Min(4, 1 + (w.Day - 1) / 2 + (int)w.Fact("arena.best").Number / 2));
        ArenaSpec Night(string sid, string name, string people, int seed, string boss, string bossName, string bossTitle,
            string onWin, string onLose, string endWon, string endLost) => new()
        {
            Id = sid, Name = name, Sub = $"Tier {tier} · held by {Maps.MapOffers.People(people).Name}", Seed = seed, Tier = tier, People = people,
            Theme = people == "dead" ? "blight" : "wood", Story = true, Boss = boss, BossName = bossName, BossTitle = bossTitle,
            // The story's nights are twenty minutes, the table's thirty (the owner: the story is to be
            // two fifths of the game early on): the same night, told quicker (ArenaRun.Minute).
            Minutes = 20,
            ReturnZone = returnZone, ReturnX = x, ReturnZ = z, ReturnFacing = facing, OnWin = onWin, OnLose = onLose,
            EndWon = endWon, EndLost = endLost,
        };
        switch (id)
        {
            case "hollow":
            {
                // Greymuzzle let go (docs/STORY_BIBLE.md, "The nights"), narrowly: only if she knelt
                // and promised and the stream already runs clean. Then it is her choice at his side
                // (the owner, 4 October): let go, he gets up and goes to his sick, beasts.outcome
                // stands, and Maeca hears of it, the one fight that raises her regard; finished, the
                // promise she knelt to make is broken with him. Otherwise he dies.
                bool spare = F(c, "promise.pack").Truthy && !F(c, "promise.broken").Truthy && StreamClean(c);
                string killed = $$"""{ "set": { "greymuzzle": "dead", "hollow.hostile": true } }, { "add": { "beasts.population": -30 } }, { "quest": { "id": "beasts", "entry": "alpha_dead" } }, { "give": "greymuzzle_fang" }, {{ZoneRuntime.Hist("killed_greymuzzle", "killed Greymuzzle, the Pack's old dog-wolf, in his own Hollow by night", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": -50, "respect": -20 }, "holloway": { "respect": 20 } }""")}}""";
                string broken = spare ? $$""", { "set": { "promise.broken": true } }, {{ZoneRuntime.Hist("broke_promise", "knelt to Greymuzzle and promised him a cure, and finished him on his own den floor", ["beasts", "wolves", "betrayal"], 2, null, """{ "maeca": { "trust": -30, "affection": -20 } }""")}}""" : "";
                var spec = Night("hollow_by_night", "The Hollow by Night", "pack", 311, "boss_pack", "Greymuzzle", "Who Kept the Cold Off",
                    $"[{killed}{broken}]",
                    """[{ "add": { "beasts.population": 10 } }, { "set": { "hollow.hostile": true } }, { "quest": { "id": "beasts", "entry": "hollow_lost" } }]""",
                    "The Hollow is quiet. The only breath in it is yours, and it does not show in the cold.",
                    "The last thing you know is the stream, very loud, and the Pack standing round you in a ring. None of them comes in.");
                if (spare)
                {
                    spec.OnSpare = $$"""[{ "set": { "greymuzzle": "spared" } }, {{ZoneRuntime.Hist("spared_greymuzzle", "brought Greymuzzle down in his own Hollow by night, and let him get up and go to his sick", ["beasts", "wolves"], 2, null, """{ "maeca": { "affection": 15, "respect": 20 } }""")}}]""";
                    spec.EndSpared = "Behind you, in the den's mouth, an old wolf is breathing. You leave him to it.";
                    spec.SpareVerb = "Let him go";
                }
                spec.Spare = spare;
                return spec;
            }
            case "roost":
            {
                // The Missing Caravan, by force. At his knee it is her choice (the owner, 4 October):
                // finished, his last words (C11) and the red hat in the mud; spared, he owes her,
                // strikes the camp before first light and takes his people off the Old Road (Act 2
                // brings him back), and the Coyle cargo is left in the empty Roost. The six crates go
                // with him only if he swore to keep them (be.crates = redcowl).
                var spec = Night("roost_raid", "Raid on the Roost", "kerchiefs", 523, "boss_kerchiefs", "Redcowl", "Of the Kerchiefs",
                    $$"""[{ "set": { "redcowl": "dead", "roost.cleared": true, "roost.hostile": true } }, { "quest": { "id": "caravan", "entry": "roost_raided" } }, { "if": { "fact": "redcowl.ashford_said", "eq": true }, "then": [{ "set": { "redcowl.last_words": "ashford" } }], "else": [{ "set": { "redcowl.last_words": "leg" } }] }, {{PackLed}}, {{ZoneRuntime.Hist("killed_redcowl", "took Redcowl's Roost by night and killed him in it", ["kerchief", "caravan"], 2, """{ "fear": 10 }""", """{ "holloway": { "respect": 25 }, "rav": { "affection": -20 } }""")}}]""",
                    """[{ "set": { "roost.hostile": true } }, { "quest": { "id": "caravan", "entry": "roost_repelled" } }]""",
                    "The red hat lies in the mud. By the fires, someone is telling the children to hush, and they do.",
                    "The last thing you know is the fire going small, and a big hand closing your eyes for you.");
                spec.OnSpare = $$"""[{ "set": { "redcowl": "spared", "roost.cleared": true } }, { "quest": { "id": "caravan", "entry": "roost_spared" } }, {{PackLed}}, {{ZoneRuntime.Hist("spared_redcowl", "brought Redcowl to his knee in his own camp by night, and let him get up", ["kerchief", "caravan"], 2, """{ "respect": 15 }""", """{ "rav": { "affection": 20, "trust": 10 }, "maeca": { "respect": 10 }, "holloway": { "respect": 10 } }""")}}]""";
                spec.EndSpared = "He walks back through his people, and does not limp until he is past the fires. Behind the carts, someone is waking the children and telling them to hush.";
                spec.SpareVerb = "Spare him";
                return spec;
            }
            case "dig":
            {
                bool running = F(c, "dig.pump").Str is not ("broken" or "blown" or "moved");
                string pump = running ? """{ "set": { "dig.pump": "blown" } }, { "quest": { "id": "beasts", "entry": "pump_blown" } }, """ : "";
                return Night("dig_boils", "The Dig Boils Over", "lamplings", 739, "grimtunnel_roused", "Grimtunnel", "Ever So Grateful",
                    $$"""[{ "set": { "dig.broken": true } }, {{pump}}{ "quest": { "id": "beasts", "entry": "dig_overrun" } }, {{ZoneRuntime.Hist("broke_dig", "held the Dig's edge by night until nothing more came up, and drove Grimtunnel back down", ["beasts", "lampling"], 2, """{ "respect": 10 }""", """{ "wenna": { "respect": 20 }, "maeca": { "respect": 20 } }""")}}]""",
                    """[{ "quest": { "id": "beasts", "entry": "dig_held" } }]""",
                    "Nothing more comes up. A long way under your feet, the ground goes still, the way a room does when someone has said your name.",
                    "The last thing you know is little hands, a great many of them, lifting you.");
            }
            case "vault":
                return Night("vault_opened", "Behind the Sealed Door", "dead", 947, "boss_dead", "The Barrow Lord", "Of the Seventh Legion",
                    $$"""[{ "set": { "vault.opened": true } }, { "quest": { "id": "vault", "entry": "opened" } }, {{ZoneRuntime.Hist("opened_vault", "opened the old empire's door in the Verge and came back out of it", ["vault", "mystery"], 3, """{ "fear": 5, "respect": 10 }""", """{ "vonnra": { "trust": -10 }, "chid": { "respect": 15 } }""")}}]""",
                    """[{ "quest": { "id": "vault", "entry": "shut" } }]""",
                    // She fights at the head of the stair and never goes down it (STORY_BOSSES 4): the dead let
                    // her go back down the hall, open to the moon, past the bootprints that only go in (Jessop's).
                    "The dead stand on the stair in their ranks, and let you go. At the door, yours are the only bootprints coming out.",
                    "The last thing you know is the moon going by over the broken roof, and the dead carrying you under it, in step.");
            default:
                throw new ArgumentException($"no story fight {id}");
        }
    }

    /// <summary>The Pack led by her (pack.allied) settles the Beast Problem's leading entry.</summary>
    const string PackLed = """{ "if": { "fact": "pack.allied", "eq": true }, "then": [{ "quest": { "id": "beasts", "entry": "pack_led" } }] }""";
}

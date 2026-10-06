using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

/// <summary>The approved story rewrite, Act 1 (docs/story/TREATMENT.md §0, the owner's choices; the
/// editor's notes, docs/story/notes/01_treatment.md): the rules a later edit must not quietly undo.
/// Maeca is just Maeca; nobody dies of boots; the confession never points at a survivor; the beats
/// that carry the act are scenes on every road; the mercy comes before the knife at the forge; the
/// fortune says both halves; the ledger's twenty-sixth line is innocent.</summary>
public class StoryRewriteTests
{
    static Conversation Convo(string id) => Dialogue.Find(id) ?? throw new KeyNotFoundException(id);

    static Setup Q(string bg = "hunter")
    {
        var s = Make(bg, "Wren", 5);
        s.World.Facts["prologue.done"] = true;
        return s;
    }

    /// <summary>Every line a person says, wherever it is written: their own conversation's lines
    /// that are theirs, and every node in any other conversation given to them as speaker.</summary>
    static IEnumerable<string> LinesOf(string who) =>
        Dialogue.All.SelectMany(c => c.Value.Nodes.Values
            .Where(n => (n.Speaker ?? c.Value.Npc) == who)
            .SelectMany(n => n.Text.Select(v => v.Text)));

    /// <summary>A scene read from its first line, picking choices by a fragment of their text: every
    /// line said, in order, and the node it stopped on.</summary>
    static (List<string> Said, Presented? Last) Play(string id, Setup s, params string[] picks)
    {
        var r = new DialogueRunner(Convo(id), s.C);
        var p = r.Start();
        var said = new List<string>();
        int i = 0;
        while (p != null)
        {
            said.Add(p.Text);
            if (p.Choices.Count == 0) { p = r.Advance(); continue; }
            if (i >= picks.Length) break;
            var pick = picks[i++];
            var c = p.Choices.FirstOrDefault(x => x.Text.Contains(pick, StringComparison.OrdinalIgnoreCase))
                ?? throw new InvalidOperationException($"no choice \"{pick}\" in [{string.Join(" | ", p.Choices.Select(x => x.Text))}]");
            p = r.Choose(c.Index).Next;
        }
        return (said, p);
    }

    static IEnumerable<string> ContentStrings()
    {
        var dir = Path.Combine(DataFiles.Dir, "content");
        foreach (var f in Directory.GetFiles(dir, "*.json"))
            foreach (Match m in Regex.Matches(File.ReadAllText(f), @"""((?:[^""\\]|\\.)*)"""))
                yield return m.Groups[1].Value;
    }

    [Fact]
    public void Maeca_is_just_Maeca()
    {
        // The owner: "she is just Maeca"; "the barefoot thing is a little silly". Her feet stay hers, at
        // the Blind, as a word in the prose; never her name, never a grievance.
        Assert.DoesNotContain(ContentStrings(), t => t.Contains("Barefoot"));
        Assert.Equal("Maeca", Lore.Person("maeca")!.Name);
        Assert.DoesNotContain("barefoot", Convo("maeca").Nodes.Keys);
        Assert.Contains("I track for the Watch, before you ask.", Convo("maeca").Nodes["first"].Text[0].Text);
        // Her three words about Ashford, and nothing else.
        Assert.Equal("(She doesn't look up from her cup.) The cave mouths.", Convo("maeca").Nodes["ashford"].Text[0].Text);
    }

    [Fact]
    public void Nobody_dies_of_boots_and_Holloway_never_mentions_them()
    {
        // The owner: "nobody dies because of footwear". Holloway's act is the lid; the roll is who each
        // man left. Nell's new boots are the one boot image left (the prologue's ditch, Brannoc's pride).
        Assert.DoesNotContain(LinesOf("holloway"), t => Regex.IsMatch(t, @"\bboots?\b", RegexOptions.IgnoreCase));
        Assert.DoesNotContain(Convo("pell").Nodes["t_pell"].Text[0].Text, "boot");
        Assert.Contains("Abbot. Two bairns. Ancell. His mam. Bede. Nobody.", Convo("holloway").Nodes["roll"].Text[0].Text);
    }

    [Fact]
    public void The_confession_has_the_lamp_in_his_eyes_and_never_asks_whether_anyone_came_out()
    {
        // Option (b), planted: he counted with the lamp in his eyes. The leading question (notes 01, 1a)
        // is gone: the eye goes to red and to ledgers, never to the woman who walks him home.
        var s = Q();
        var (said, _) = Play("scene_knocking", s, "(Listen.)", "Ashford", "What did you see", "anyone else know");
        var all = string.Join(" ", said);
        Assert.Contains("Lamp in my eyes.", all);
        Assert.Contains("Ninety-one. Then I looked down.", all);
        Assert.Contains("Lid down. Bar across. Sat on it.", all);
        Assert.Contains("Pell.", all);
        Assert.Contains("Always somebody still out.", said.Last());
        Assert.True(s.World.Fact("holloway.confessed").Truthy);
        foreach (var n in Convo("scene_knocking").Nodes.Values)
            foreach (var c in n.Choices ?? new())
                Assert.DoesNotContain("come out", Dialogue.PickText(c.Text, s.C), StringComparison.OrdinalIgnoreCase);
        // He never says sorry (VOICES: it is written once, found after his death).
        Assert.DoesNotContain(LinesOf("holloway"), t => Regex.IsMatch(t, @"\bsorry\b", RegexOptions.IgnoreCase));
    }

    [Fact]
    public void The_gate_at_dawn_comes_the_morning_after_her_first_night_and_plays_once()
    {
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter",
            Palette = Callings.Archetype("warden").Palettes[0].Id, WeaponItem = Callings.Archetype("warden").Weapons[0],
            Ability = Callings.Archetype("warden").Abilities[0],
        }, 42);
        j.World.Facts["prologue.done"] = true;
        Assert.Null(j.TakeScene(dusk: false));
        // A night fight: the arena writes "ago 0"; the morning after, the gate stood open all night.
        j.World.Facts["arena.last.ago"] = 0;
        Simulation.AdvanceDay(j.Ctx, () => 0.5);
        Assert.True(j.SceneWaiting(dusk: false));
        Assert.Equal("scene_gate_dawn", j.TakeScene(dusk: false));
        Assert.False(j.SceneWaiting(dusk: false));
        // The next night fight is not the first: the scene does not come again.
        j.World.Facts["arena.last.ago"] = 0;
        Simulation.AdvanceDay(j.Ctx, () => 0.5);
        Assert.NotEqual("scene_gate_dawn", j.World.Fact("scene.morning").Str);
    }

    [Fact]
    public void The_scene_at_the_gate_is_a_kindness_with_a_loaded_crossbow_in_it()
    {
        var (said, _) = Play("scene_gate_dawn", Q(), "Thank you");
        var all = string.Join(" ", said);
        Assert.Contains("crossbow across her knees", all);
        Assert.Contains("One in.", all);
        Assert.Contains("Count's right.", all);
        Assert.Equal("That's your last.", said.Last());
    }

    [Fact]
    public void After_the_knocking_she_comes_to_you_and_every_answer_ends_in_did_he()
    {
        // "Tell Maeca" is on the trunk (notes 01, 1b): if the player does not go to her, she comes. Each
        // answer gets the same three words: the coldest line in the game, on the re-read.
        foreach (var pick in new[] { "the shaft", "It was nothing", "(Say nothing.)" })
        {
            var s = Q();
            var (said, _) = Play("scene_did_he", s, pick);
            Assert.Equal("...Did he.", said.Last());
            Assert.True(s.World.Fact("maeca.told_lid").Str is { Length: > 0 });
        }
        // The morning after the confession sets it; that dusk, her cup at the gate.
        var t = Q();
        t.World.Facts["holloway.confessed"] = true;
        Simulation.AdvanceDay(t.C, () => 0.5);
        Assert.Equal("scene_did_he", t.World.Fact("scene.morning").Str);
        t.World.Facts.Remove("scene.morning");
        t.World.Facts["maeca.told_lid"] = "told";
        Simulation.AdvanceDay(t.C, () => 0.5);
        Assert.Equal("scene_his_cup", t.World.Fact("scene.dusk").Str);
    }

    [Fact]
    public void At_the_forge_the_mercy_comes_before_the_knife()
    {
        // Notes 01, item 7: "Was it quick?" and its answer, then his eyes on the iron at her belt, then
        // "She'd have thought I'd come for her.", then "Forge is shut.", then his lantern.
        var s = Q();
        s.World.Day = 2;
        s.World.Time = TimeOfDay.Day;
        Rules.Apply(Es("[{ give: 'wardens_lampiron' }]"), s.C);
        s.World.Npc("brannoc").Flags["met"] = true;
        var r = new DialogueRunner(Convo("brannoc"), s.C);
        var p = r.Start()!;
        Assert.Equal("nell", p.Node.Id);
        var said = new List<string>();
        foreach (var pick in new[] { "A girl had the reins", "I put her down", "It was quick", "Out of the fist", "It does", "show you" })
        {
            while (p!.Choices.Count == 0) { said.Add(p.Text); p = r.Advance(); }
            said.Add(p.Text);
            p = r.Choose(p.Choices.First(c => c.Text.Contains(pick)).Index).Next;
        }
        while (p != null) { said.Add(p.Text); p = p.Choices.Count == 0 ? r.Advance() : null; }
        int At(string line) => said.FindIndex(t => t.Contains(line));
        Assert.True(At("Was it quick?") < At("Thank you."));
        Assert.True(At("Thank you.") < At("Where'd you get that."));
        Assert.True(At("To see your face.") < At("She'd have thought I'd come for her."));
        Assert.True(At("She'd have thought I'd come for her.") < At("Forge is shut."));
        Assert.True(At("Forge is shut.") < At("You know the place."));
        Assert.Equal("with", s.World.Fact("nell.road").Str);
        Assert.True(s.World.Fact("brannoc.knew_iron").Truthy);
        // The road, held: his hand round the light. The truth costs nothing at the bench (the owner:
        // no gameplay punishment for either answer): the next day he works, one-handed.
        var heard = string.Join(" ", Simulation.AdvanceDay(s.C, () => 0.5).Lines);
        Assert.Contains("closed his bare hand round the light", heard);
        Assert.Contains("Steel or fur?", Greet(Convo("brannoc"), s.C).Text);
        Assert.Contains(Greet(Convo("brannoc"), s.C).Choices, c => c.Action == "craft");
    }

    [Fact]
    public void Brannoc_calls_her_over_at_dusk_so_every_road_hears_his_question()
    {
        // C07 on the trunk (the treatment §5): from day 2, at the first dusk in the town, he asks; she
        // does not have to come to him. Never by day as a scene, and dropped once she has been asked.
        var s = Q();
        s.World.Npc("brannoc").Flags["met"] = true;
        s.World.Day = 1;
        Simulation.AdvanceDay(s.C, () => 0.5);
        Assert.Equal("brannoc:dusk_call", s.World.Fact("scene.dusk").Str);
        s.World.Time = TimeOfDay.Day;
        Assert.Equal("nell", new DialogueRunner(Convo("brannoc"), s.C).Start()!.Node.Id);
        s.World.Time = TimeOfDay.Dusk;
        Assert.Equal("brannoc", Journey.TakeScene(s.C, dusk: true));
        var r = new DialogueRunner(Convo("brannoc"), s.C);
        var p = r.Start()!;
        Assert.Equal("dusk_call", p.Node.Id);
        Assert.Equal("nell", r.Advance()!.Node.Id);
        // Asked by day first: the dusk's scene has passed, and is dropped.
        var t = Q();
        t.World.Npc("brannoc").Flags["met"] = true;
        t.World.Npc("brannoc").Flags["asked_nell"] = true;
        t.World.Facts["scene.dusk"] = "brannoc:dusk_call";
        Assert.Null(Journey.TakeScene(t.C, dusk: true));
        Assert.False(t.World.Fact("scene.dusk").Truthy);
    }

    [Fact]
    public void Brannoc_is_proud_of_his_irons_until_he_knows()
    {
        var s = Q();
        Assert.Contains("Best I've done.", Greet(Convo("brannoc"), s.C).Text);
        var pride = Lore.Person("brannoc")!.Said!.Where(x => x.Text.Contains("walk where it's lit")).Single();
        Assert.True(Rules.Test(pride.When, s.C));
        s.World.Facts["nell.told"] = "risen";
        Assert.False(Rules.Test(pride.When, s.C));
    }

    [Fact]
    public void Rook_tells_her_a_kind_lie_and_the_ledger_never_says_lamp()
    {
        // Twist B's false belief, named (notes 01, item 3): Mam went in her sleep. The ledger's
        // twenty-sixth line is in Vonnra's register and points elsewhere; never "a woman with a lamp".
        var s = Q();
        var all = string.Join(" ", Play("rook", Q(), "My mother sent for me", "Where is she").Said);
        Assert.Contains("She went in her sleep, pet.", all);
        Assert.Contains("It's been free a week.", all);
        var q = Q();
        Play("rook", q, "My mother sent for me", "Where is she");
        Assert.Contains("rook", q.World.Quests["home"].Entries);
        var chart = string.Join(" ", Convo("vonnra").Nodes["f_chart"].Text.Select(v => v.Text));
        Assert.Contains("The twenty-sixth: Rook's lodger.", chart);
        Assert.Contains("From the ford. Got up.", chart);
        Assert.DoesNotContain("woman with a lamp", chart);
    }

    [Fact]
    public void Vonnra_says_both_halves_and_quotes_her_answer_at_the_ford()
    {
        Assert.EndsWith("You stopped the drowning, traveller. You also did this.", Convo("vonnra").Nodes["f_did"].Text[0].Text);
        var s = Q();
        Assert.EndsWith("You told him it was morning.", Dialogue.PickText(Convo("vonnra").Nodes["f_ford"].Text, s.C));
        Play("warden_answer", s, "(Say nothing.)");
        Assert.EndsWith("He let go anyway.", Dialogue.PickText(Convo("vonnra").Nodes["f_ford"].Text, s.C));
        // The continuity fix: Corran's book says "Not oil."
        Assert.Contains("So somebody had ember, and irons to burn it in.", Convo("holloway").Nodes["post2"].Text[0].Text);
    }

    [Fact]
    public void Her_mothers_word_is_Spark_and_the_dawns_take_it_away()
    {
        Assert.Contains("\"Lamp's lit, Spark. Stay where it reaches.\"", Convo("cin_first_light").Nodes["face"].Text[0].Text);
        // Never "Wick" (players hear John Wick), and no one else uses her word for a joke.
        Assert.DoesNotContain(ContentStrings(), t => Regex.IsMatch(t, @"\bWick\b|Spark-"));
        var s = Q();
        s.World.Day = 2;
        var heard = string.Join(" ", Simulation.AdvanceDay(s.C, () => 0.5).Lines);
        Assert.Contains("You still have the word.", heard);
        // Written down at Chid's asking, in her own hand: the journal keeps what the dawns take.
        var c = Q();
        c.World.Day = 3;
        c.World.Npc("chid").Flags["met"] = true;
        c.World.Npc("chid").Flags["say:calling"] = true;
        Play("chid", c, "Write down what she called you");
        Assert.Contains("word", c.World.Quests["home"].Entries);
        Assert.Contains("\"Spark. What she called me, at dusk.\"", Lore.Quests["home"].Entries["word"]);
    }
}

"""Harness switches for the clock's checks (run from godot/)."""
p = "src/Game/Game.cs"
s = open(p, encoding="utf-8").read()

old = """        if (z != "lowford")
        {
            // Skipping ahead: the prologue counts as done.
            World.Facts["prologue.done"] = true;
            World.Time = Enum.TryParse<TimeOfDay>(Args.Get("time") ?? "day", true, out var t) ? t : TimeOfDay.Day;
            EnterZone(z, "lowford", at);
        }"""
new = """        // --night ID: straight into a story fight by night (a StoryFights id: hollow, roost, dig, vault),
        // back to the Verge at its place after (pictures of a story night, its falls and its loss).
        if (Args.Get("night") is string nid && StoryFights.Get(nid) is { } nf)
        {
            var spot = ZoneMeta.Load("verge").Place("V", nf.Spot);
            Arenas.Begin(World, StoryFights.Spec(nid, Journey.Ctx, "verge", spot.X, spot.Z, 0));
            z = "arena";
        }
        if (z != "lowford")
        {
            // Skipping ahead: the prologue counts as done.
            World.Facts["prologue.done"] = true;
            World.Time = Enum.TryParse<TimeOfDay>(Args.Get("time") ?? "day", true, out var t) ? t : TimeOfDay.Day;
            // --clock S: the day's clock at S seconds of free play since dawn, running (pictures of its
            // turns: 585 is a quarter minute before dusk, 1065 before the night's end).
            if (Args.Has("clock"))
            {
                World.Clock = Args.Num("clock", 0);
                World.Time = DayClock.At(World.Clock);
                World.Facts["clock.started"] = true;
            }
            EnterZone(z, "lowford", at);
        }"""
assert old in s
s = s.replace(old, new, 1)

old = """        if (!dieDone && Args.Has("die") && Battle is { } kb && Journey.Playtime >= Args.Num("die", 1))
        {
            dieDone = true;
            var killer = kb.SpawnEnemy("risen", kb.Player.X, kb.Player.Z + (Args.Has("behind") ? -1.2 : 1.2));
            kb.HurtPlayerRaw(kb.Player.Hp + 1e6, School.Physical, "test", killer);
        }"""
new = """        // --die T1,T2: again at each time listed (a story night's falls: the rise, then the loss).
        var dies = (Args.Get("die") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries);
        if (dieIx < dies.Length && Battle is { } kb && kb.Player.Alive
            && Journey.Playtime >= double.Parse(dies[dieIx] == "" ? "1" : dies[dieIx], System.Globalization.CultureInfo.InvariantCulture))
        {
            dieIx++;
            var killer = kb.SpawnEnemy("risen", kb.Player.X, kb.Player.Z + (Args.Has("behind") ? -1.2 : 1.2));
            kb.HurtPlayerRaw(kb.Player.Hp + 1e6, School.Physical, "test", killer);
        }
        // --answer T: the night answered T seconds in, as if the key were held (pictures of the pull).
        if (!answerDone && Args.Has("answer") && Journey.Playtime >= Args.Num("answer", 1) && World.Time == TimeOfDay.Night && zone is { ClockRuns: true })
        {
            answerDone = true;
            AnswerNight();
        }"""
assert old in s
s = s.replace(old, new, 1)

old = "    bool hordeDone, dropsDone, castDone, giveDone, minuteDone, dieDone, chestDone, barksDone;"
assert old in s
s = s.replace(old, "    bool hordeDone, dropsDone, castDone, giveDone, minuteDone, chestDone, barksDone, answerDone;\n    int dieIx;", 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Game/GameFall.cs"
s = open(p, encoding="utf-8").read()
old = """            hud.Prompt(new PromptView(controls.UsingPad ? "A" : KeyLabel("interact"), "Get up", "",
                $"{KeyLabel("cancel")}: Let the night go", null, Act.Confirm));
        });"""
new = """            hud.Prompt(new PromptView(controls.UsingPad ? "A" : KeyLabel("interact"), "Get up", "",
                $"{KeyLabel("cancel")}: Let the night go", null, Act.Confirm));
            Shots.Want("fall", 0.6);
            // --choose rise|letgo: the choice made for a run, after the card has been seen.
            if (Args.Get("choose") is string ch) Wait(2.0, () => { if (hudMode == "fall") FallKey(ch == "letgo" ? Act.Cancel : Act.Confirm); });
        });"""
assert old in s
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Game/GameClock.cs"
s = open(p, encoding="utf-8").read()
for old, new in [
("""            case ClockTurn.Day:
                Turn(TimeOfDay.Day, 40);
                break;""", """            case ClockTurn.Day:
                Turn(TimeOfDay.Day, 40);
                Shots.Want("day", 20);
                break;"""),
("""                Turn(TimeOfDay.Dusk, 60);""", """                Turn(TimeOfDay.Dusk, 60);
                Shots.Want("dusk", 1.5); Shots.Want("dusk", 6.5); Shots.Want("dusk", 30); Shots.Want("dusk", 59);"""),
("""                Turn(TimeOfDay.Night, 50);""", """                Turn(TimeOfDay.Night, 50);
                Shots.Want("night", 1.0); Shots.Want("night", 25); Shots.Want("night", 52);"""),
("""            case ClockTurn.Nudge:
                Say(Journey.DayLines.Nudge, null, 4);""", """            case ClockTurn.Nudge:
                Say(Journey.DayLines.Nudge, null, 4);
                Shots.Want("nudge", 1.0);"""),
("""            Save("dawn");
            hud.Fade(0, 1.4);""", """            Save("dawn");
            hud.Fade(0, 1.4);
            Shots.Want("dawn", 1.6); Shots.Want("dawn", 6);"""),
("""        hud.Fade(1, 1.2, "Dawn", $"Day {World.Day + 1}");""", """        hud.Fade(1, 1.2, "Dawn", $"Day {World.Day + 1}");
        Shots.Want("dawnfade", 1.25);"""),
]:
    assert old in s, old[:50]
    s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Game/Game.cs"
s = open(p, encoding="utf-8").read()
old = """            Wait(3.9, () => { talkDone = () => Morning(lines); Talk("chid"); });"""
assert old in s
s = s.replace(old, """            Wait(3.9, () => { talkDone = () => { Morning(lines); Shots.Want("morning", 1.5); }; Talk("chid"); Shots.Want("chid", 0.8); });""", 1)
open(p, "w", encoding="utf-8", newline="").write(s)

p = "src/Game/Autopilot.cs"
s = open(p, encoding="utf-8").read()
old = """        if (g.Overlay == "dialogue") { g.Advance(); return; }"""
assert old in s
s = s.replace(old, """        // A line is read at a reader's pace (pictures of conversations need the line on screen).
        if (g.Overlay == "dialogue") { if ((lineT += dt) > 2.4) { lineT = 0; g.Advance(); } return; }
        lineT = 0;""", 1)
old = """    string lastStage = "";"""
assert old in s
s = s.replace(old, """    string lastStage = "";
    double lineT;""", 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")

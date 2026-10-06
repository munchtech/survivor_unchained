import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/src/Game/Game.cs', [
    ('''<<<<<<< HEAD
    bool hordeDone, dropsDone, castDone, giveDone, minuteDone, dieDone, barksDone;
=======
    bool hordeDone, dropsDone, castDone, giveDone, minuteDone, dieDone, chestDone;
>>>>>>> origin/claude/vigilant-galileo-l6jqyx
''', '''    bool hordeDone, dropsDone, castDone, giveDone, minuteDone, dieDone, chestDone, barksDone;
'''),
])
edit('godot/src/Ui/ArenaResult.cs', [
    ('''<<<<<<< HEAD
        if (r.Longest && r.Seconds > 120)
            wrap.AddChild(Beat(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center), cue, Sound.Sfx.Discovery));
        cue += 0.4;
        // (how it ended, in a line, comes last: below)
=======
        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest night yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center));
        // How it ended, and how near it came (docs/feel S-16: the end tells the run's story).
>>>>>>> origin/claude/vigilant-galileo-l6jqyx
''', '''        if (r.Longest && r.Seconds > 120)
            wrap.AddChild(Beat(Style.Label("Your longest night yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center), cue, Sound.Sfx.Discovery));
        cue += 0.4;
        // (how it ended and how near it came, in a line, comes last: below; docs/feel S-16)
'''),
    ('''<<<<<<< HEAD
        // Beat four: how it went, in a line; what comes of it; and back to the road.
        string after = r.Spec.Story
            ? r.Won ? "The story goes on." : "The story goes on without the win. The Wayfinder will let you take this fight again."
            : r.Won ? "The Wayfinder will want to hear of it." : "The Wayfinder's table will have other maps.";
        if (story != "") wrap.AddChild(Beat(Style.Label(story, Style.TextItalic, Style.Body, r.Won ? Style.Ink : Style.BloodHi, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page));
        cue += 0.5;
        wrap.AddChild(Beat(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center), cue));
        cue += 0.3;
        var go = Style.Button("", () => { if (Told) G.LeaveArena(r); else told = true; }, true);
=======
        // A story night ends on the narrator's line for how it went (docs/WRITING_PASS.md §20), and a
        // lost one says beneath it where it waits; a table night ends with the Wayfinder, who writes it down.
        string after = r.Spec.Story
            ? r.Won ? r.Spec.EndWon ?? "The valley will hear of it." : r.Spec.EndLost ?? "The valley will hear of it."
            : r.Won ? "The Wayfinder will want it for her margins." : "The Wayfinder's table will have other maps.";
        wrap.AddChild(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
        if (r.Spec.Story && !r.Won)
            wrap.AddChild(Style.Label("The fight waits on the Wayfinder's table, to be taken again.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
        var go = Style.Button("", () => G.LeaveArena(r), true);
>>>>>>> origin/claude/vigilant-galileo-l6jqyx
''', '''        // Beat four: how it went, in a line; then a story night's narrator line for how it went
        // (docs/WRITING_PASS.md §20), a lost one saying where it waits; a table night ends with the
        // Wayfinder, who writes it down; and back to the road.
        string after = r.Spec.Story
            ? r.Won ? r.Spec.EndWon ?? "The valley will hear of it." : r.Spec.EndLost ?? "The valley will hear of it."
            : r.Won ? "The Wayfinder will want it for her margins." : "The Wayfinder's table will have other maps.";
        if (story != "") wrap.AddChild(Beat(Style.Label(story, Style.TextItalic, Style.Body, r.Won ? Style.Ink : Style.BloodHi, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page));
        cue += 0.5;
        wrap.AddChild(Beat(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center), cue));
        cue += 0.3;
        if (r.Spec.Story && !r.Won)
        {
            wrap.AddChild(Beat(Style.Label("The fight waits on the Wayfinder's table, to be taken again.", Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center), cue));
            cue += 0.3;
        }
        // (the autopilot's Confirm, like a player's, first tells the rest, then leaves)
        var go = Style.Button("", () => { if (Told) G.LeaveArena(r); else told = true; }, true);
'''),
])

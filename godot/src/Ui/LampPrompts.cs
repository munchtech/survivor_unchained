using System.Collections.Generic;

namespace SurvivorUnchained.Ui;

/// <summary>The Lamps page's prompt rows, pure: read-only (the arena) hides every prompt whose action only denies.</summary>
public static class LampPrompts
{
    /// <summary>The header's keys. Read-only (the arena): Light my way only denies, so it is not offered.</summary>
    public static List<(string, string)> HeaderRow(bool pad, bool wide, bool readOnly)
    {
        var r = new List<(string, string)>();
        if (!readOnly) r.Add(pad ? ("Y", "Light my way") : ("Space", "Light my way"));
        r.Add(pad ? ("D-pad up", "Find") : ("F", "Find"));
        r.Add(wide ? pad ? ("B", "Close") : ("Esc", "Close") : pad ? ("R3", "Open wide") : ("Z", "Open wide"));
        return r;
    }

    /// <summary>The foot row (narrow). Read-only: the board's Light and Light my way only deny and go; the wick's Plan and Light
    /// my way stay while the wick still takes them (it denies both out of a safe place).</summary>
    public static List<(string, string)> FootRow(bool pad, bool wickOpen, bool readOnly, bool wickSafe)
    {
        if (wickOpen)
        {
            var w = new List<(string, string)>();
            if (!(readOnly && !wickSafe)) { w.Add(pad ? ("A", "Plan") : ("Click", "Plan")); w.Add(pad ? ("Y", "Light my way") : ("Space", "Light my way")); }
            w.Add(pad ? ("B", "Board") : ("Tab", "Board"));
            return w;
        }
        var b = new List<(string, string)>();
        if (!readOnly) { b.Add(pad ? ("A", "Light") : ("Click", "Light")); b.Add(pad ? ("Y", "Light my way") : ("Space", "Light my way")); }
        if (pad) { b.Add(("L3", "Home")); b.Add(("R3", "Open wide")); }
        else { b.Add(("H", "Home")); b.Add(("F", "Find")); b.Add(("Z", "Open wide")); }
        return b;
    }

    /// <summary>The wide page's foot, row by row (same rule as FootRow).</summary>
    public static List<(string, string)[]> WideFootRows(bool pad, bool wickOpen, bool readOnly, bool wickSafe)
    {
        if (wickOpen)
        {
            var rows = new List<(string, string)[]>();
            if (!(readOnly && !wickSafe))
            {
                rows.Add(pad ? [("A", "Plan")] : [("Click", "Plan")]);
                rows.Add(pad ? [("Y", "Light my way")] : [("Space", "Light my way")]);
            }
            rows.Add(pad ? [("B", "Back")] : [("Tab", "Back")]);
            return rows;
        }
        return pad ? [[("LT", ""), ("RT", "Zoom"), ("D-pad", "Next lamp")], [("L3", "Home"), ("R3", "The book")]]
                   : [[("Wheel", "Zoom")], [("H", "Home"), ("Z", "The book")]];
    }
}

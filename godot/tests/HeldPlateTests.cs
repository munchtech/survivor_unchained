using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>creator-jiggle (18 Nov; the owner: "jiggling cups non stop" on the starter's steel top). The tops' holds are
/// formed plate (squash 0). On B, before the fix, such a hold only set support 1: the breast springs stiffened but kept
/// swinging, and their rest turned with the world's down. The steel cups, skinned to those bones, rode 2.5-3.6 mm a
/// second against her chest in the creator's Look idle and 19 mm on the flourish. Here, on a toy chest swaying, bobbing
/// and kicked: under every shipped plate top's hold (warden.top, kit_bodice) the cups' drawn points stay fixed in the
/// chest's frame. Without the hold they move, which is the old path, and the check that this test can fail. The held rest is
/// the upright worn rest the cups were fitted to (tools/armor/worn_rest.py: the Frozen rest, upright).</summary>
public class HeldPlateTests
{
    readonly ITestOutputHelper log;
    public HeldPlateTests(ITestOutputHelper o) { log = o; }

    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static JsonElement Doc(string rel) => JsonDocument.Parse(File.ReadAllText(Path.Combine(Root(), rel))).RootElement;
    static P1M4 Tr(double x, double y, double z) { var m = P1M4.Id; m[0, 3] = x; m[1, 3] = y; m[2, 3] = z; return m; }

    static readonly string[] Names = { "root", "spine_04", "breast_l", "breast_tip_l", "breast_r", "breast_tip_r" };
    static readonly int[] Parent = { -1, 0, 1, 2, 1, 4 };
    static readonly P1M4[] Rest = { P1M4.Id, Tr(0, 1.3, 0), Tr(0.1, 1.3, 0.04), Tr(0.1, 1.3, 0.1011), Tr(-0.1, 1.3, 0.04), Tr(-0.1, 1.3, 0.1011) };

    /// <summary>Her world over 4 s: a lean sway (8 deg at 0.4 Hz), a stride's bob (2 cm at 2.2 Hz), a turn (90 deg/s) and a
    /// kick at 1 s (a landing, 1.5 m/s). Each frame the drawn points (each spring's tip) in the chest's frame; returns the
    /// largest span of any one point from 0.5 s on (m).</summary>
    static double Ride(P1Springs sp, double dt = 1 / 60.0)
    {
        sp.Reset();
        var lo = new P1V[sp.Springs.Count]; var hi = new P1V[sp.Springs.Count];
        for (int i = 0; i < sp.Springs.Count; i++) { lo[i] = new P1V(1e9, 1e9, 1e9); hi[i] = new P1V(-1e9, -1e9, -1e9); }
        int n = (int)(4 / dt);
        for (int f = 0; f < n; f++)
        {
            double t = f * dt, lean = 8 * Math.PI / 180 * Math.Sin(2 * Math.PI * 0.4 * t), yaw = Math.PI / 2 * t;
            var W = Rot(1, yaw) * Rot(0, lean); W[1, 3] = 0.02 * Math.Sin(2 * Math.PI * 2.2 * t); W[2, 3] = 0.5 * t;
            if (Math.Abs(t - 1) < dt / 2) foreach (var s in sp.Springs) s.V += new P1V(0, -1.5, 0);
            sp.Step(W, Rest, dt, collide: false);
            if (t < 0.5) continue;
            for (int i = 0; i < sp.Springs.Count; i++)
            {
                var s = sp.Springs[i];
                int chest = s.Of >= 0 ? sp.Springs[s.Of].Parent : s.Parent;
                var p = Rest[chest].Inverse() * (s.G * s.Tip);
                lo[i] = new P1V(Math.Min(lo[i].X, p.X), Math.Min(lo[i].Y, p.Y), Math.Min(lo[i].Z, p.Z));
                hi[i] = new P1V(Math.Max(hi[i].X, p.X), Math.Max(hi[i].Y, p.Y), Math.Max(hi[i].Z, p.Z));
            }
        }
        return Enumerable.Range(0, sp.Springs.Count).Max(i => (hi[i] - lo[i]).Len());
    }

    static P1M4 Rot(int axis, double a)
    {
        double c = Math.Cos(a), s = Math.Sin(a);
        var m = P1M4.Id;
        if (axis == 0) { m[1, 1] = c; m[1, 2] = -s; m[2, 1] = s; m[2, 2] = c; }
        else { m[0, 0] = c; m[0, 2] = s; m[2, 0] = -s; m[2, 2] = c; }
        return m;
    }

    static ArmorHold HoldOf(string id)
    {
        var rows = Doc("art/gear/out/body_p1/gear_index.json").GetProperty("rows");
        var row = rows.EnumerateArray().First(r => r.GetProperty("id").GetString() == id);
        return JsonSerializer.Deserialize<ArmorHold>(row.GetProperty("hold").GetRawText())!;
    }

    [Theory]
    [InlineData("warden.top")]
    [InlineData("kit_bodice")]
    public void PlateTopCupsRideTheChest(string top)
    {
        var hold = HoldOf(top);
        Assert.True(hold.RigidValue, $"{top}: its hold (squash {hold.Squash}) is formed plate");
        var sp = new P1Springs(Doc("data/body/springs.json"), "p1", null, Names, Parent, Rest);
        sp.Support["top"] = hold.SupportValue; sp.Squash = hold.Squash;
        double old = Ride(sp);                                     // the old path: the hold's support only
        sp.Held["top"] = hold.RigidValue;
        double held = Ride(sp);
        log.WriteLine($"{top}: cups' largest span in her chest's frame {old * 1000:F2} mm before, {held * 1000:F4} mm held");
        Assert.True(old > 1e-3, $"{top}: the unheld springs move the cups {old * 1000:F2} mm (the test can fail)");
        Assert.True(held < 1e-5, $"{top}: the held cups move {held * 1000:F4} mm in her chest's frame");
    }

    [Fact]
    public void HeldRestIsTheFittedWornRest()
    {
        // upright and still, held equals the Frozen rest (worn_rest.py's fit: support 1, the skeleton's down)
        var sp = new P1Springs(Doc("data/body/springs.json"), "p1", null, Names, Parent, Rest);
        sp.Support["top"] = 1; sp.Squash = 0;   // (worn_rest.py fits upright, squash 0: a plate hold's)
        sp.Frozen = true; sp.Reset(); sp.Step(P1M4.Id, Rest, 1 / 60.0, collide: false);
        var frozen = sp.Springs.Select(s => s.G * s.Tip).ToArray();
        sp.Frozen = false; sp.Held["top"] = true; sp.Reset();
        for (int i = 0; i < 3; i++) sp.Step(P1M4.Id, Rest, 1 / 60.0, collide: false);
        for (int i = 0; i < sp.Springs.Count; i++)
            Assert.True((sp.Springs[i].G * sp.Springs[i].Tip - frozen[i]).Len() < 1e-9, sp.Springs[i].Name);
        Assert.False(new ArmorHold { Amount = 0.8, Squash = 0.5 }.RigidValue);   // fabric's hold gives: not held
        Assert.False(new ArmorHold { Squash = 0, Rigid = false }.RigidValue);
    }

    /// <summary>Round 2 (the owner, 18 Nov: "thats not jiggle thats mishapen"): kit_bodice (built on her bind:
    /// kit_build.py her_a; its row's hold says "rest": "bind") is held at her bind, offset 0, its bones exactly the clip's,
    /// so its steel keeps the shape it was built in; the starter top (warden.top, fitted at the worn rest by gear_fit) and
    /// any row that says nothing (Marionette's pieces fit on the worn skin) keep the worn rest.</summary>
    [Theory]
    [InlineData("kit_bodice", true)]
    [InlineData("warden.top", false)]
    public void HeldAtTheRestItWasBuiltIn(string top, bool atBind)
    {
        var rows = Doc("art/gear/out/body_p1/gear_index.json").GetProperty("rows");
        var row = JsonSerializer.Deserialize<ArmorPiece>(rows.EnumerateArray().First(r => r.GetProperty("id").GetString() == top).GetRawText())!;
        Assert.Equal(atBind, row.Hold!.RestsAtBind);
        Assert.False(new ArmorHold { Squash = 0 }.RestsAtBind);   // (no "rest": the worn rest, what gear_fit and Marionette fit to)
        var sp = new P1Springs(Doc("data/body/springs.json"), "p1", null, Names, Parent, Rest);
        sp.Support["top"] = row.Hold.SupportValue; sp.Squash = row.Hold.Squash;
        sp.Held["top"] = true; sp.HeldAtBind["top"] = atBind;
        Assert.True(Ride(sp) < 1e-5, $"{top}: held cups move in her chest's frame");
        sp.Reset(); sp.Step(P1M4.Id, Rest, 1 / 60.0, collide: false);   // (upright, the clip at her bind)
        double off = sp.Springs.Max(s => (s.G * s.Tip - Rest[s.Bone] * s.Tip).Len());
        log.WriteLine($"{top}: held {(atBind ? "at bind" : "at the worn rest")}, largest offset from her bind {off * 1000:F2} mm");
        if (atBind) Assert.True(off < 1e-9, $"{top}: at bind, offset {off * 1000:F4} mm");
        else Assert.True(off > 5e-3, $"{top}: the worn rest lifts the tips off her bind ({off * 1000:F2} mm)");
    }

    [Fact]
    public void BareStillSwings()
    {
        // no plate: the springs keep their life (the same world moves the cups' points by millimetres)
        var sp = new P1Springs(Doc("data/body/springs.json"), "p1", null, Names, Parent, Rest);
        double bare = Ride(sp);
        log.WriteLine($"bare: largest span {bare * 1000:F2} mm");
        Assert.True(bare > 3e-3);
    }
}

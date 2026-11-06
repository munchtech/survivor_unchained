using System;
using System.IO;
using System.Linq;
using System.Numerics;
using System.Text.Json;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>B's (P1) own grip and sheath as data (WeaponSockets): the sword's axis on B's fist by the grip standard, and
/// the sheathed hilt hung at B's hip bone (MOTION_BIBLE s11).</summary>
public class P1GripTests
{
    static string Repo()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d!.Parent!.FullName;
    }

    // The knuckle frame (index_01 -> pinky_01 line reversed, the knuckles' reach) in hand_r's space, columns.
    static Matrix4x4 Frame(Func<string, Vector3> at)
    {
        var k = Vector3.Normalize(at("index_01_r") - at("pinky_01_r"));
        var f = (at("index_01_r") + at("middle_01_r") + at("pinky_01_r")) / 3;
        f = Vector3.Normalize(f - k * Vector3.Dot(f, k));
        var z = Vector3.Cross(k, f);
        return new Matrix4x4(k.X, f.X, z.X, 0, k.Y, f.Y, z.Y, 0, k.Z, f.Z, z.Z, 0, 0, 0, 0, 1);
    }

    static Vector3 V(JsonElement e, int i0 = 0) => new(e[i0].GetSingle(), e[i0 + 1].GetSingle(), e[i0 + 2].GetSingle());

    [Fact]
    public void SwordAxisOnBsGripLine_Within3Deg()
    {
        var root = Repo();
        var b = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "tools", "body", "rig", "b_skeleton.json"))).RootElement.GetProperty("bones");
        var bones = b.EnumerateArray().ToDictionary(x => x.GetProperty("name").GetString()!);
        var hb = bones["hand_r"];
        var ax = hb.GetProperty("axes");                       // rows: the bone's local x, y, z in skeleton space
        var (bx, by, bz, bh) = (V(ax[0]), V(ax[1]), V(ax[2]), V(hb.GetProperty("head")));
        Vector3 InB(string n) { var d = V(bones[n].GetProperty("head")) - bh; return new(Vector3.Dot(d, bx), Vector3.Dot(d, by), Vector3.Dot(d, bz)); }
        var a = JsonDocument.Parse(File.ReadAllText(Path.Combine(root, "godot", "art", "people", "body_p1", "a_skeleton.json"))).RootElement;
        var names = a.GetProperty("names").EnumerateArray().Select(x => x.GetString()).ToList();
        var rest = a.GetProperty("rest");
        Vector3 Col(JsonElement m, int c) => new(m[0][c].GetSingle(), m[1][c].GetSingle(), m[2][c].GetSingle());
        var ma = rest[names.IndexOf("hand_r")];
        var (ox, oy, oz, oh) = (Col(ma, 0), Col(ma, 1), Col(ma, 2), Col(ma, 3));
        Vector3 InA(string n) { var d = Col(rest[names.IndexOf(n)], 3) - oh; return new(Vector3.Dot(d, ox), Vector3.Dot(d, oy), Vector3.Dot(d, oz)); }
        var fa = Frame(InA);
        var fb = Frame(InB);
        Matrix4x4.Invert(fa, out var fai);
        // A's fitted pocket carried onto B's knuckle frame: B's grip line by the standard
        var want = Vector3.Normalize(Vector3.TransformNormal(Vector3.TransformNormal(WeaponSockets.BladeDirR, Matrix4x4.Transpose(fai)), Matrix4x4.Transpose(fb)));
        var pocket = WeaponSockets.Pocket(WeaponKind.Blade1H, "hand_r", isB: true)!.Value;
        double deg = Math.Acos(Math.Clamp(Vector3.Dot(Vector3.Normalize(pocket.Dir), want), -1, 1)) * 180 / Math.PI;
        Assert.True(deg <= 3, $"B's sword axis {deg:F2} deg off B's grip line");
        // and the guard at the index side: the axis keeps A's angle to the knuckle line
        double aa = Math.Acos(Vector3.Dot(WeaponSockets.BladeDirR, Vector3.Normalize(WeaponSockets.KnuckleLineRA))) * 180 / Math.PI;
        double bb = Math.Acos(Vector3.Dot(Vector3.Normalize(pocket.Dir), Vector3.Normalize(WeaponSockets.KnuckleLineRB))) * 180 / Math.PI;
        Assert.InRange(bb - aa, -3, 3);
        Assert.Equal(WeaponSockets.BladeDirR, WeaponSockets.Pocket(WeaponKind.Blade1H, "hand_r", isB: false)!.Value.Dir);
        Assert.Equal(WeaponSockets.DaggerDirR, WeaponSockets.Pocket(WeaponKind.Dagger, "hand_r", isB: true)!.Value.Dir);
    }

    [Fact]
    public void SheathedHiltOnB_AtTheHipBone_12To15cmLower()
    {
        var a = WeaponSockets.PommelAt(WeaponSockets.HipBladeAtA);
        var b = WeaponSockets.PommelAtB();
        Assert.InRange(b.Y, WeaponSockets.HipBoneYB - 0.01f, WeaponSockets.HipBoneYB + 0.005f);
        Assert.InRange(a.Y - b.Y, 0.12f, 0.15f + 1e-4f);
    }

    [Fact]
    public void SheathOnB_BeltCarry_HiltForwardAndUp_30To40OffVertical()
    {
        var s = Vector3.Normalize(WeaponSockets.HipBladeShaftB);
        double off = Math.Acos(-s.Y) * 180 / Math.PI;
        Assert.InRange(off, 30, 40);
        Assert.True(s.Z < 0, "the scabbard runs back, so the hilt points forward");
        Assert.True(WeaponSockets.PommelAtB().Z > WeaponSockets.HipBladeAtB.Z + 0.08f, "the pommel forward of her hip");
    }
}

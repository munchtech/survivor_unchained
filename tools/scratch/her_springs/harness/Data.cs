using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Numerics;

namespace H;

/// <summary>Godot's Transform3D in System.Numerics: basis columns X, Y, Z and origin O.</summary>
public struct Aff
{
    public Vector3 X, Y, Z, O;
    public Aff(Vector3 x, Vector3 y, Vector3 z, Vector3 o) { X = x; Y = y; Z = z; O = o; }
    public static readonly Aff I = new(Vector3.UnitX, Vector3.UnitY, Vector3.UnitZ, Vector3.Zero);
    public Vector3 Basis(Vector3 v) => X * v.X + Y * v.Y + Z * v.Z;
    public Vector3 Apply(Vector3 v) => X * v.X + Y * v.Y + Z * v.Z + O;
    public static Aff operator *(Aff a, Aff b) => new(a.Basis(b.X), a.Basis(b.Y), a.Basis(b.Z), a.Apply(b.O));
    public static Vector3 operator *(Aff a, Vector3 v) => a.Apply(v);
    public Aff Inverse()
    {
        // (general 3x3 inverse: rows of the inverse are the cross products over the determinant)
        var c0 = Vector3.Cross(Y, Z); var c1 = Vector3.Cross(Z, X); var c2 = Vector3.Cross(X, Y);
        float det = Vector3.Dot(X, c0);
        float id = 1f / det;
        // inverse basis M^-1 has rows c0, c1, c2 (scaled): its columns are (c0.x, c1.x, c2.x) etc.
        var ix = new Vector3(c0.X, c1.X, c2.X) * id; var iy = new Vector3(c0.Y, c1.Y, c2.Y) * id; var iz = new Vector3(c0.Z, c1.Z, c2.Z) * id;
        var r = new Aff(ix, iy, iz, Vector3.Zero);
        r.O = -r.Basis(O);
        return r;
    }
    public Matrix4x4 M4 => new(X.X, X.Y, X.Z, 0, Y.X, Y.Y, Y.Z, 0, Z.X, Z.Y, Z.Z, 0, O.X, O.Y, O.Z, 1);
    public float ScaleX => X.Length();
    /// <summary>The basis orthonormalised (Gram-Schmidt as Godot's Basis.Orthonormalized).</summary>
    public Aff Ortho()
    {
        var x = Vector3.Normalize(X);
        var y = Y - x * Vector3.Dot(x, Y); y = Vector3.Normalize(y);
        var z = Z - x * Vector3.Dot(x, Z) - y * Vector3.Dot(y, Z); z = Vector3.Normalize(z);
        return new Aff(x, y, z, O);
    }
    public Quaternion Rot()
    {
        var o = Ortho();
        var m = new Matrix4x4(o.X.X, o.X.Y, o.X.Z, 0, o.Y.X, o.Y.Y, o.Y.Z, 0, o.Z.X, o.Z.Y, o.Z.Z, 0, 0, 0, 0, 1);
        return Quaternion.Normalize(Quaternion.CreateFromRotationMatrix(m));
    }
    public static Aff FromRot(Quaternion q, Vector3 o)
    {
        var m = Matrix4x4.CreateFromQuaternion(q);
        return new Aff(new Vector3(m.M11, m.M12, m.M13), new Vector3(m.M21, m.M22, m.M23), new Vector3(m.M31, m.M32, m.M33), o);
    }
    /// <summary>A pure rotation (as a basis) times this basis.</summary>
    public Aff RotBasis(Quaternion q)
    {
        return new Aff(Vector3.Transform(X, q), Vector3.Transform(Y, q), Vector3.Transform(Z, q), O);
    }
    public static Aff Read(BinaryReader r) => new(V(r), V(r), V(r), V(r));
    static Vector3 V(BinaryReader r) => new(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
}

public sealed class Skel
{
    public string[] Name = Array.Empty<string>();
    public int[] Parent = Array.Empty<int>();
    public Aff[] Rest = Array.Empty<Aff>();
    public int Find(string n) => Array.IndexOf(Name, n);
    public static Skel Load(string path)
    {
        var s = new Skel();
        var lines = File.ReadAllLines(path).Where(l => l.Trim() != "").ToArray();
        s.Name = new string[lines.Length]; s.Parent = new int[lines.Length]; s.Rest = new Aff[lines.Length];
        foreach (var l in lines)
        {
            var p = l.Split(' ');
            int i = int.Parse(p[0]);
            s.Name[i] = p[1]; s.Parent[i] = int.Parse(p[2]);
            var f = p.Skip(3).Select(x => float.Parse(x, System.Globalization.CultureInfo.InvariantCulture)).ToArray();
            s.Rest[i] = new Aff(new(f[0], f[1], f[2]), new(f[3], f[4], f[5]), new(f[6], f[7], f[8]), new(f[9], f[10], f[11]));
        }
        return s;
    }
}

public sealed class Shape { public string Name = ""; public int[] Idx = Array.Empty<int>(); public Vector3[] DP = Array.Empty<Vector3>(), DN = Array.Empty<Vector3>(); }

public sealed class MeshD
{
    public string Name = "", Slot = "";
    public Vector3[] Pos = Array.Empty<Vector3>(), Nrm = Array.Empty<Vector3>();
    public int[] Bones = Array.Empty<int>(), Tris = Array.Empty<int>(), BindBone = Array.Empty<int>();
    public float[] Weights = Array.Empty<float>();
    public int K;
    public Aff[] Bind = Array.Empty<Aff>();
    public Shape[] Shapes = Array.Empty<Shape>();
    public static MeshD Load(string path)
    {
        using var r = new BinaryReader(File.OpenRead(path));
        var m = new MeshD { Name = r.ReadString(), Slot = r.ReadString() };
        int nv = r.ReadInt32(); m.K = r.ReadInt32(); int nt = r.ReadInt32(); int nb = r.ReadInt32(); int ns = r.ReadInt32();
        m.Pos = new Vector3[nv]; for (int i = 0; i < nv; i++) m.Pos[i] = new(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
        m.Nrm = new Vector3[nv]; for (int i = 0; i < nv; i++) m.Nrm[i] = new(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
        m.Bones = new int[nv * m.K]; for (int i = 0; i < m.Bones.Length; i++) m.Bones[i] = r.ReadInt32();
        m.Weights = new float[nv * m.K]; for (int i = 0; i < m.Weights.Length; i++) m.Weights[i] = r.ReadSingle();
        m.Tris = new int[nt]; for (int i = 0; i < nt; i++) m.Tris[i] = r.ReadInt32();
        m.BindBone = new int[nb]; for (int i = 0; i < nb; i++) m.BindBone[i] = r.ReadInt32();
        m.Bind = new Aff[nb]; for (int i = 0; i < nb; i++) m.Bind[i] = Aff.Read(r);
        m.Shapes = new Shape[ns];
        for (int s = 0; s < ns; s++)
        {
            var sh = new Shape { Name = r.ReadString() };
            int c = r.ReadInt32();
            sh.Idx = new int[c]; for (int i = 0; i < c; i++) sh.Idx[i] = r.ReadInt32();
            sh.DP = new Vector3[c]; for (int i = 0; i < c; i++) sh.DP[i] = new(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
            sh.DN = new Vector3[c]; for (int i = 0; i < c; i++) sh.DN[i] = new(r.ReadSingle(), r.ReadSingle(), r.ReadSingle());
            m.Shapes[s] = sh;
        }
        return m;
    }
}

public sealed class Frame
{
    public long F; public string Clip = ""; public double T;
    public Aff W;
    public Aff[] G = Array.Empty<Aff>();
    public float[][] ShapeW = Array.Empty<float[]>();
}

public static class Dump
{
    public static List<Frame> Frames(string path, int nb, MeshD[] meshes)
    {
        var o = new List<Frame>();
        using var r = new BinaryReader(File.OpenRead(path));
        while (r.BaseStream.Position < r.BaseStream.Length)
        {
            try
            {
                var f = new Frame { F = r.ReadInt64(), Clip = r.ReadString(), T = r.ReadDouble(), W = Aff.Read(r) };
                f.G = new Aff[nb]; for (int b = 0; b < nb; b++) f.G[b] = Aff.Read(r);
                f.ShapeW = meshes.Select(m => { var a = new float[m.Shapes.Length]; for (int s = 0; s < a.Length; s++) a[s] = r.ReadSingle(); return a; }).ToArray();
                o.Add(f);
            }
            catch (EndOfStreamException) { break; }
        }
        return o;
    }
}

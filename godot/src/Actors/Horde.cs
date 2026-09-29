using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Actors;

/// <summary>
/// The Risen: the dead of the Verge got up again, Quaternius people with
/// grave-grey skin and rotten clothes on the Universal Animation Library's
/// zombie cycles. Each has its own skeleton and animation (they climb out of
/// the ground, lurch, claw, flinch when cut and fall), so a hit reads on the
/// body it lands on. A pool, reused as they die.
/// </summary>
public sealed class Risen
{
    public required People.Person Person;
    public Vector3 Pos;
    public Vector3 Push;
    public float Facing, Hp, HitFlash, AttackCd, StateT;
    public string State = "down"; // down, rising, walk, attack, dying, dead
    public readonly List<StandardMaterial3D> Mats = new();
    public bool Alive => State is "rising" or "walk" or "attack";
}

public partial class Horde : Node3D
{
    public readonly List<Risen> All = new();
    readonly RandomNumberGenerator rng = new() { Seed = 3 };
    static readonly Color[] Skins = { new("#8e9680"), new("#7f8a78"), new("#9a9888"), new("#76806f") };
    static readonly Color[] Rags = { new("#5a5448"), new("#4a4238"), new("#626a5a"), new("#6a5a50") };
    static readonly string?[] Hair = { "Hair_Long", "Hair_Buzzed", null, "Hair_SimpleParted", "Hair_Buns" };

    public void Fill(int count)
    {
        for (int i = 0; i < count; i++)
        {
            bool female = i % 3 == 1;
            var hair = Hair[i % Hair.Length];
            if (!female && hair == "Hair_Buns") hair = "Hair_Long";
            var p = People.Build(new People.Look(female ? "female" : "male", female ? People.FemalePeasant : People.MalePeasant,
                Hair: hair, HairColor: new Color("#2a2622"), Skin: Skins[i % Skins.Length], Cloth: Rags[i % Rags.Length]));
            p.Root.Scale = Vector3.One * (0.98f + rng.Randf() * 0.1f);
            p.Root.Visible = false;
            AddChild(p.Root);
            var r = new Risen { Person = p };
            foreach (var mi in p.Meshes)
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    if (mi.GetSurfaceOverrideMaterial(s) is StandardMaterial3D m) { r.Mats.Add(m); m.EmissionEnabled = true; m.Emission = Colors.Black; }
            p.Anim.SpeedScale = 0.85f + rng.Randf() * 0.3f;
            All.Add(r);
        }
    }

    /// <summary>One climbs out of the ground here.</summary>
    public Risen? Raise(Vector3 at, float facing)
    {
        foreach (var r in All)
        {
            if (r.State is not ("down" or "dead")) continue;
            r.Pos = at; r.Facing = facing; r.Hp = 34; r.State = "rising"; r.StateT = 0; r.Push = Vector3.Zero; r.AttackCd = 1;
            r.Person.Root.Visible = true;
            r.Person.Anim.Play("LayToIdle");
            return r;
        }
        return null;
    }

    public void Play(Risen r, string clip, float blend = 0.2f) => r.Person.Anim.Play(clip, blend);
}

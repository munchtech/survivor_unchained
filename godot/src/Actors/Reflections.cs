using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.View;

/// <summary>
/// The survivor in glass: the reflections a mirror step leaves, an echo
/// waiting to be stepped back into. Each is the survivor's own figure, armed
/// as they are, drawn in light (shaders/ghost.gdshader), cracking as it is
/// struck. Kept and reused, so a step does not build a person each time.
/// </summary>
public partial class Reflections : Node3D
{
    static readonly Shader GhostShader = GD.Load<Shader>("res://shaders/ghost.gdshader");
    static readonly Color Glass = new(0.55f, 0.82f, 1.0f), EchoTint = new(0.72f, 0.55f, 1.0f);
    // (Names made once, not a new one every frame for the collector.)
    static readonly StringName TintName = "tint", FadeName = "fade", CrackName = "crack";

    sealed class Ghost
    {
        public PersonView View = null!;
        public ShaderMaterial Mat = null!;
        public int Key = -1;
        public float Fade;
        public bool Used;
    }

    readonly Loadout loadout;
    readonly List<Ghost> ghosts = new();
    readonly HashSet<int> seen = new();

    public Reflections(Loadout lo)
    {
        loadout = lo;
        TopLevel = true;
        Name = "Reflections";
    }

    Ghost Take(int key)
    {
        foreach (var g in ghosts) if (g.Key == key) { g.Used = true; return g; }
        Ghost? free = null;
        foreach (var g in ghosts) if (g.Key == -1) { free = g; break; }
        if (free == null)
        {
            var v = new PersonView(loadout.Person, new Held { Right = loadout.Arms.Right, Left = loadout.Arms.Left, Forearm = loadout.Arms.Forearm }, 0.8);
            var mat = new ShaderMaterial { Shader = GhostShader };
            mat.SetShaderParameter("seed", ghosts.Count * 1.7f);
            Dress(v, mat);
            AddChild(v);
            free = new Ghost { View = v, Mat = mat };
            ghosts.Add(free);
        }
        free.Key = key;
        free.Fade = 0;
        free.Used = true;
        free.View.Visible = true;
        free.View.Loop(loadout.Arms.Idle, 0);
        return free;
    }

    /// <summary>Every surface drawn in glass, shadowless.</summary>
    static void Dress(Node n, Material mat)
    {
        if (n is GeometryInstance3D gi)
        {
            gi.MaterialOverride = mat;
            gi.CastShadow = GeometryInstance3D.ShadowCastingSetting.Off;
        }
        foreach (var c in n.GetChildren()) Dress(c, mat);
    }

    /// <summary>A reflection swings at what came for it.</summary>
    public void Strike(int key)
    {
        foreach (var g in ghosts)
            if (g.Key == key) g.View.Act(loadout.Arms.Attack[0], 1.6);
    }

    public void Update(Battle b, double dt, System.Func<double, double, double> heightAt)
    {
        foreach (var g in ghosts) g.Used = false;
        float fdt = (float)dt;
        foreach (var d in b.Decoys)
        {
            if (!d.Alive || d.State == EnemyState.Dying) continue;
            var g = Take(d.Id);
            g.Fade = Mathf.Min(1, g.Fade + fdt / 0.15f);
            // The last moments: guttering.
            float life = d.LifeT > 0 ? Mathf.Clamp((float)d.LifeT / 0.6f, 0, 1) : 1;
            float flick = life < 1 ? 0.6f + 0.4f * Mathf.Sin((float)(b.Time * 40 + d.Id)) : 1;
            bool echo = d == b.Art.Echo;
            g.Mat.SetShaderParameter(TintName, echo ? EchoTint : Glass);
            g.Mat.SetShaderParameter(FadeName, g.Fade * life * flick);
            g.Mat.SetShaderParameter(CrackName, (float)(1 - d.Hp / System.Math.Max(1, d.MaxHp)));
            g.View.Place(d.X, heightAt(d.X, d.Z), d.Z, Mathf.Pi / 2 - d.Facing, true);
        }
        // An echo with no body of its own: a still figure where it was left.
        var a = b.Art;
        if (a.EchoT > 0 && a.Echo == null)
        {
            var g = Take(-2);
            g.Fade = Mathf.Min(1, g.Fade + fdt / 0.2f);
            float life = Mathf.Clamp((float)a.EchoT / 0.8f, 0, 1);
            g.Mat.SetShaderParameter(TintName, EchoTint);
            g.Mat.SetShaderParameter(FadeName, g.Fade * life * 0.8f);
            g.Mat.SetShaderParameter(CrackName, 0f);
            g.View.Place(a.EchoX, heightAt(a.EchoX, a.EchoZ), a.EchoZ, a.EchoFacing, true);
        }
        foreach (var g in ghosts)
            if (!g.Used && g.Key != -1) { g.Key = -1; g.View.Visible = false; }
    }
}

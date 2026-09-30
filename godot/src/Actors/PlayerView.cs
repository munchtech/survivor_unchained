using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The survivor on screen (the web game's render/playerView.ts): the one
/// character with a full skeleton, blended clips and a light of their own.
/// Reads the fight's player state every frame and turns it into motion:
/// running that matches ground speed, a roll on a dash, the weapon arm
/// swinging when a blade fires (alternating cuts, a heavy swing for wide
/// arcs) on the upper body while the legs keep running, a flinch when
/// struck, a leap's arc, and a fall that stays down. The carried light is
/// the ember itself: it gutters when you are hurt and flares when you level.
/// </summary>
public partial class PlayerView : Node3D
{
    readonly Loadout loadout;
    readonly People.Person person;
    readonly AnimationTree tree;
    readonly AnimationNodeAnimation upper, full;
    public readonly OmniLight3D Light;
    /// <summary>The survivor in glass: reflections and echoes left behind.</summary>
    public readonly Reflections Reflections;
    readonly List<GeometryInstance3D> skin = new();
    readonly ShaderMaterial wraith = new() { Shader = GD.Load<Shader>("res://shaders/ghost.gdshader") };
    bool ghostly;
    Content.AbilityKind? rushSeen;
    double lastAttack = -1, hurtSeen, flare, castT, time;
    int swing;
    bool dashing, dead;
    float speed;
    const float LightBase = 5;

    public PlayerView(Loadout lo)
    {
        loadout = lo;
        Name = "Survivor";
        var v = new PersonView(lo.Person, new World.Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8);
        person = v.Person;
        AddChild(v);
        // Locomotion blended by speed; a swing on the upper body alone (the
        // hips and legs stay with the run); a roll, a leap or a fall on all of it.
        var bt = new AnimationNodeBlendTree();
        var move = new AnimationNodeBlendSpace1D { MinSpace = 0, MaxSpace = 6 };
        move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve(lo.Arms.Idle) }, 0);
        move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve("Walk_Loop") }, 1.8f);
        move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve("Jog_Fwd_Loop") }, 4.4f);
        move.AddBlendPoint(new AnimationNodeAnimation { Animation = People.Resolve("Sprint_Loop") }, 6);
        upper = new AnimationNodeAnimation { Animation = People.Resolve(lo.Arms.Attack[0]) };
        full = new AnimationNodeAnimation { Animation = People.Resolve("Roll") };
        var upperShot = new AnimationNodeOneShot { FadeInTime = 0.05, FadeOutTime = 0.18, FilterEnabled = true };
        var fullShot = new AnimationNodeOneShot { FadeInTime = 0.05, FadeOutTime = 0.2 };
        var skel = person.Skeleton;
        for (int b = 0; b < skel.GetBoneCount(); b++)
        {
            var name = skel.GetBoneName(b);
            if (name is "root" or "pelvis" || name.StartsWith("thigh") || name.StartsWith("calf") || name.StartsWith("foot") || name.StartsWith("ball")) continue;
            upperShot.SetFilterPath($"Armature/Skeleton3D:{name}", true);
        }
        var upperScale = new AnimationNodeTimeScale();
        var fullScale = new AnimationNodeTimeScale();
        bt.AddNode("move", move, new Vector2(0, 0));
        bt.AddNode("upper", upper, new Vector2(0, 200));
        bt.AddNode("upperScale", upperScale, new Vector2(200, 200));
        bt.AddNode("upperShot", upperShot, new Vector2(400, 100));
        bt.AddNode("full", full, new Vector2(400, 300));
        bt.AddNode("fullScale", fullScale, new Vector2(600, 300));
        bt.AddNode("fullShot", fullShot, new Vector2(800, 150));
        bt.ConnectNode("upperScale", 0, "upper");
        bt.ConnectNode("upperShot", 0, "move");
        bt.ConnectNode("upperShot", 1, "upperScale");
        bt.ConnectNode("fullScale", 0, "full");
        bt.ConnectNode("fullShot", 0, "upperShot");
        bt.ConnectNode("fullShot", 1, "fullScale");
        bt.ConnectNode("output", 0, "fullShot");
        tree = new AnimationTree { TreeRoot = bt, RootNode = "..", Active = true };
        tree.AddAnimationLibrary("", People.Clips());
        person.Root.AddChild(tree);
        Light = new OmniLight3D { LightColor = new Color("#ffb070"), LightEnergy = LightBase / Mathf.Pi, OmniRange = 11, OmniAttenuation = 1.4f, ShadowEnabled = false };
        AddChild(Light);
        Reflections = new Reflections(lo);
        AddChild(Reflections);
        Gather(this);
        wraith.SetShaderParameter("tint", new Color(0.5f, 0.42f, 0.9f));
        wraith.SetShaderParameter("body", 0.05f);
        wraith.SetShaderParameter("rim", 0.9f);
    }

    void Gather(Node n)
    {
        if (n is GeometryInstance3D g && n is not global::SurvivorUnchained.View.Reflections) skin.Add(g);
        foreach (var c in n.GetChildren()) if (c is not global::SurvivorUnchained.View.Reflections) Gather(c);
    }

    /// <summary>Half a ghost (a wraith's walk): see-through, rimmed in cold light.</summary>
    void Ghostly(bool on)
    {
        if (on == ghostly) return;
        ghostly = on;
        foreach (var g in skin)
        {
            if (!IsInstanceValid(g)) continue;
            g.Transparency = on ? 0.55f : 0;
            g.MaterialOverlay = on ? wraith : null;
        }
    }

    public Vector3 FigurePosition => person.Root.GlobalPosition;

    void Upper(string clip, double speed)
    {
        upper.Animation = People.Resolve(clip);
        tree.Set("parameters/upperScale/scale", speed);
        tree.Set("parameters/upperShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    void Full(string clip, double speed)
    {
        full.Animation = People.Resolve(clip);
        tree.Set("parameters/fullScale/scale", speed);
        tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.Fire);
    }

    bool Busy => (bool)tree.Get("parameters/upperShot/active") || (bool)tree.Get("parameters/fullShot/active");

    public void LevelFlare() => flare = 1;

    /// <summary>An art used: the hands that go with it.</summary>
    public void OnAbility(string id)
    {
        switch (id)
        {
            case "mirror_step" or "echo_step" or "echo_recall" or "time_slip" or "blink":
                Upper("Spell_Simple_Shoot", 1.8);
                break;
            case "grapple" or "grapple_miss":
                Upper("OverhandThrow", 2.2);
                break;
            case "warcry" or "sprint" or "cinder_trail" or "wraith_walk":
                if (!Busy) Upper("Punch_Cross", 1.4);
                break;
        }
    }

    /// <summary>Up again after a fall (the prologue's second chances).</summary>
    public void Revive()
    {
        dead = false;
        tree.Active = true;
        Full("Lie_StandUp", 1.2);
    }

    public void Update(Battle b, double dt, double fightTime, System.Func<double, double, double> heightAt)
    {
        time += dt;
        var p = b.Player;
        double y = heightAt(p.X, p.Z);
        if (p.Leap is { } leap) y += Mathf.Sin((float)(Mathf.Min(1, leap.T / leap.Dur) * Mathf.Pi)) * 2.2;
        Position = new Vector3((float)p.X, (float)y, (float)p.Z);
        Reflections.Update(b, dt, heightAt);
        Ghostly(p.Alive && b.Art.WraithT > 0);
        if (!p.Alive)
        {
            if (!dead)
            {
                // A fall that stays down: the clip played out and held.
                dead = true;
                tree.Active = false;
                person.Anim.Play(People.Resolve("Death_A"), 0.1);
            }
            Light.LightEnergy = Mathf.Lerp(Light.LightEnergy, 0.6f / Mathf.Pi, 1 - Mathf.Exp(-2 * (float)dt));
            return;
        }
        float sp = (float)Mathf.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
        // Face where you are going, or where you just struck.
        if (p.AttackAnim is { } aa && fightTime - aa.T < 0.35) Rotation = new Vector3(0, (float)(Mathf.Pi / 2 - aa.Angle), 0);
        else if (sp > 0.4f) Rotation = new Vector3(0, Mathf.LerpAngle(Rotation.Y, Mathf.Atan2((float)p.Vx, (float)p.Vz), 1 - Mathf.Exp(-14 * (float)dt)), 0);
        // Dash: a roll.
        if (p.DashT > 0 && !dashing)
        {
            dashing = true;
            Rotation = new Vector3(0, Mathf.Atan2((float)p.DashDX, (float)p.DashDZ), 0);
            Full("Dodge_Forward", 1.9);
        }
        else if (p.DashT <= 0) dashing = false;
        if (p.Leap is { } l2 && l2.T < dt * 2) Full(l2.Kind == Content.AbilityKind.Vault ? "Jump_Start" : "Jump_Full_Short", l2.Kind == Content.AbilityKind.Vault ? 1.8 : 1.3);
        // A charge behind the shield; a haul on the chain, blade first.
        if (b.Art.Rush != rushSeen)
        {
            rushSeen = b.Art.Rush;
            if (rushSeen is { } rk)
            {
                Rotation = new Vector3(0, Mathf.Atan2((float)b.Art.RushDX, (float)b.Art.RushDZ), 0);
                Full(rk == Content.AbilityKind.BullRush ? "Shield_Dash" : "Sword_Dash", rk == Content.AbilityKind.BullRush ? 1.5 : 2.2);
            }
        }
        // Weapon swings: the blade drives the arm.
        if (p.AttackAnim is { } a && a.T != lastAttack)
        {
            lastAttack = a.T;
            var clip = a.Heavy ? loadout.Arms.Heavy : loadout.Arms.Attack[swing++ % loadout.Arms.Attack.Length];
            Upper(clip, 1.6);
        }
        // Casters raise a hand now and then as their spells go.
        castT -= dt;
        if (loadout.Arms.Cast != null && castT <= 0 && b.Weapons.Count > 0 && !Busy && sp < 3)
        {
            castT = 1.6;
            Upper(loadout.Arms.Cast, 1.4);
        }
        // Flinch.
        if (p.HurtT > 0.25 && hurtSeen <= 0)
        {
            hurtSeen = 0.4;
            if (!Busy) Upper("Hit_A", 1.6);
        }
        hurtSeen -= dt;
        speed = Mathf.Lerp(speed, sp, 1 - Mathf.Exp(-10 * (float)dt));
        tree.Set("parameters/move/blend_position", speed);
        // The carried light: steadier at full health, guttering when hurt.
        double hp = p.Hp / b.MaxHp;
        flare = Mathf.Max(0, flare - dt * 0.8);
        double flicker = Mathf.Sin((float)(time * 7.3)) * 0.25 + Mathf.Sin((float)(time * 17.1)) * 0.15 + (hp < 0.35 ? Mathf.Sin((float)(time * 31)) * 0.6 : 0);
        Light.LightEnergy = (float)((LightBase * (0.7 + 0.3 * hp) + flicker + flare * 20) / Mathf.Pi);
        Light.OmniRange = (float)(11 + flare * 6);
        Light.Position = new Vector3(0, 2.4f, 0.4f);
        // Unseen: a ghost, flickering.
        Visible = !(p.InvisibleT > 0 && (int)(time * 12) % 3 == 0);
    }
}

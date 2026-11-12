using System;
using System.Reflection;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>Run through tools/experience/closeup_lifetime.py so user storage is isolated before renderer startup.</summary>
public partial class CloseUpLifetime : Node
{
    const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
    Game game = null!;
    bool watching, done;
    int returnedFrames;
    static readonly string[] ZoneLights = ["closeKey", "closeKeyGear", "closeKeyHair", "closeRim", "closeRimGear", "closeBodyRim",
        "closeFill", "closeFillFolk", "keyFolk", "rimFolk", "coolFolk", "bodyRimFolk", "groundKey", "fireFill", "CloseKeySrcLamp",
        "keyLight", "bodyKey", "fillLight", "edgeLight", "rimLight", "bounceLight", "lookBodyRim", "herFire", "fireSrc"];

    static FieldInfo Field(string name) => typeof(Game).GetField(name, Private) ?? throw new Exception(name);
    T Get<T>(string name) => (T)Field(name).GetValue(game)!;
    void Set(string name, object? value) => Field(name).SetValue(game, value);
    object? Call(string name, params object[] args) => typeof(Game).GetMethod(name, Private)!.Invoke(game, args);
    static void Require(bool ok, string why) { if (!ok) throw new Exception(why); }

    public override async void _Ready()
    {
        try
        {
            // Moving user:// after renderer startup strands its shader-cache directories.
            const string userDir = "Survivor Unchained Codex closeup-blackscreen";
            Require(OS.GetUserDataDir().Contains(userDir), "Harness user directory was not isolated");
            GD.Print($"closeup lifetime: user directory {OS.GetUserDataDir()}");
            Settings.Current.Mature = true;
            Settings.Current.Fullscreen = false;

            game = new Game();
            AddChild(game);
            game.SetProcess(false);
            game.EnterZone("lowford", null);
            var lens = Get<Camera3D>("camera");
            var air = Get<Atmosphere>("air");
            uint worldMask = air.Key.LightCullMask;
            Call("CelRig", "close_day", 1f, lens, Vector3.Up, true);
            var oldKey = Get<DirectionalLight3D>("celKey");
            Require(GodotObject.IsInstanceValid(oldKey), "Old zone did not build a cel key");
            Require(air.Key.LightCullMask != worldMask, "Cel key did not take her layers");
            foreach (string name in ZoneLights)
            {
                var light = (Light3D)Activator.CreateInstance(Field(name).FieldType)!;
                game.Scene!.AddChild(light);
                Set(name, light);
            }

            game.EnterZone("waystation", "lowford");
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            Require(!GodotObject.IsInstanceValid(oldKey), "Old scene did not free its cel key");
            Require(Field("celKey").GetValue(game) == null, "Zone retained its cel key");
            foreach (string name in ZoneLights) Require(Field(name).GetValue(game) == null, $"Zone retained {name}");
            Require(air.Key.LightCullMask == worldMask, "World key did not regain her layers");

            var deadKey = new DirectionalLight3D();
            game.Scene!.AddChild(deadKey);
            Set("celKey", deadKey);
            deadKey.Free();
            Require(!(bool)typeof(Game).GetProperty("CelRigHeld", Private)!.GetValue(game)!, "Freed cel key is held");
            Call("UpdateCloseUp", 0.1);
            GD.Print("closeup lifetime: PASS freed cel key, tick without a throw");

            foreach (string name in new[] { "closeKey", "closeRim", "closeFill", "closeBodyRim", "closeKeyGear", "closeKeyHair",
                "keyFolk", "closeFillFolk", "coolFolk", "rimFolk", "bodyRimFolk" })
            {
                var light = new SpotLight3D();
                game.Scene.AddChild(light);
                Set(name, light);
                light.Free();
            }
            Call("FolkTwins", false, Vector3.Zero);
            Call("UpdateCloseUp", 0.1);
            Require(GodotObject.IsInstanceValid(Get<SpotLight3D>("closeKeyGear")), "Gear key was not retaken");
            Require(GodotObject.IsInstanceValid(Get<SpotLight3D>("closeKeyHair")), "Hair key was not retaken");
            GD.Print("closeup lifetime: PASS freed sibling lights, tick without a throw");

            Set("quick", false);
            Require(game.Cinematic("c04b"), "c04b did not start");
            watching = true;
            game.SetProcess(true);
        }
        catch (Exception e) { Fail(e); }
    }

    public override void _Process(double delta)
    {
        if (!watching || done) return;
        try
        {
            Require(!Get<FrameGuard>("closeUpFrame").Failed, "Close-up frame failed");
            if (game.InCinematic) return;
            if (++returnedFrames < 120) return;
            Require(game.Zone?.Id == "waystation" && game.Arrived, "c04b did not return to the waystation");
            done = true;
            GD.Print("closeup lifetime: PASS c04b done, waystation reached, 120 play frames continued");
            QuitPath.Request(GetTree(), why: "closeup lifetime passed");
        }
        catch (Exception e) { Fail(e); }
    }

    void Fail(Exception e)
    {
        done = true;
        GD.PushError($"closeup lifetime: FAIL {e}");
        QuitPath.Request(GetTree(), 1, "closeup lifetime failed");
    }
}

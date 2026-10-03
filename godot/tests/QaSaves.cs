using System;
using System.IO;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Saves at the Act 1 moments worth looking at in the real game
/// (the journal, the tracker, the long lines), played into by the Route
/// harness and written as the game writes them. Only with QA_SAVES=DIR:
/// dotnet test --filter QaSaves; then copy one to the game's saves as
/// slot0.json (with meta.json {"last":0}) and run the game with --continue.</summary>
public class QaSaves
{
    static void Write(string dir, string name, Route p, string zone, double x = 0, double z = 0)
    {
        p.Leave();
        File.WriteAllText(Path.Combine(dir, $"{name}.json"), Json.Write(p.J.ToSave(new SaveLocation { Zone = zone, X = x, Z = z })));
    }

    [Fact]
    public void Write_the_moments_worth_seeing()
    {
        var dir = Environment.GetEnvironmentVariable("QA_SAVES");
        if (string.IsNullOrEmpty(dir)) return;
        Directory.CreateDirectory(dir);

        // The caravan half-known: the ledger read for its date, the wreck found, the lamps begun.
        var a = Route.New("outcast", "Wren");
        a.Talk("rook", "talk");
        a.Talk("harlan", "goodbye");
        a.Night();
        a.Enter("waystation");
        a.Use("warehouse");
        a.Leave();
        a.Sleep();
        a.Talk("holloway", "found this book");
        a.Talk("holloway", "watch-post", "lit again");
        a.Talk("brannoc", "lamp-irons");
        a.Talk("tam", "listening");
        a.Enter("verge");
        a.Use("sample");
        a.Use("pipe");
        Write(dir, "ledger_read", a, "waystation", 2, 6);

        // The box carried out of an empty Roost, the crates there to be sunk.
        var b = Route.New("outcast", "Wren");
        b.Talk("harlan", "goodbye");
        b.Enter("verge");
        b.Use("wreck");
        b.Leave();
        b.Talk("harlan", "besides salt and cloth");
        b.Enter("verge");
        b.Walk("roost");
        b.Talk("redcowl", "watch is on its way");
        b.Walk("cages");
        b.Use("strongbox");
        var cargo = b.Meta!.Place("V", "cargo");
        Write(dir, "roost_emptied", b, "verge", cargo.X - 2, cargo.Z + 3);
        b.Enter("verge");
        b.Use("crates_sink");
        Write(dir, "roost_sunk", b, "verge", cargo.X - 2, cargo.Z + 3);

        // Both troubles settled, the lamps in hand: Vonnra's note under the door.
        var c = Route.New("scholar", "Wren");
        c.Talk("rook", "talk");
        c.Talk("rook", "low ford road", "what did she say");
        c.Talk("brannoc", "lamp-irons");
        c.Learn("clue.blasting_ember");
        c.Talk("redcowl", "six crates", "blasting ember", "deep enough", "keep them dry");
        c.Talk("sella", "how much", "15 gold", "where you come from");
        c.W.Facts["beasts.outcome"] = "cured";
        c.Apply("""[{ "quest": { "id": "beasts", "status": "resolved", "outcome": "cured", "entry": "pump_moved" } }]""");
        c.W.Facts["caravan.survivors"] = "rescued";
        c.Talk("jory", "what was in the crates", "blasting ember", "he knew");
        c.Sleep();
        Write(dir, "fortune", c, "waystation", 25.5, -4.4);

        // Met for the first time with the Roost on your boots (Harlan's longest greeting).
        var d = Route.New("hunter", "Wren");
        d.Apply("""[{ "quest": { "id": "caravan", "status": "active", "entry": "roost_found" } }]""");
        d.W.Facts["caravan.days"] = 2;
        Write(dir, "harlan_roost", d, "waystation", 32.5, 1.4);
    }
}

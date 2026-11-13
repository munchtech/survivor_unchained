using System;
using System.IO;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Tests;

public sealed class TestContent
{
    // Class fixtures reuse the board without sharing Hit's scratch list across classes.
    readonly Lazy<LampBoardModel> board = new(() => LampBoardModel.FromJson(
        File.ReadAllText(Path.Combine(DataFiles.Dir, "content", "lamps_v2.json"))));

    public LampBoardModel LampBoard => board.Value;

    static readonly Lazy<double> stationaryArenaSize = new(() =>
    {
        using var spec = JsonDocument.Parse(File.ReadAllText(Path.Combine(
            DataFiles.Dir, "..", "tests", "fixtures", "suite_speed.json")));
        return spec.RootElement.GetProperty("stationaryArenaSize").GetDouble();
    });

    // These melee dummies stay near the origin; their full runs need no distant navigation.
    public static double StationaryArenaSize => stationaryArenaSize.Value;
}

using System.Collections.Generic;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

public class MinimapRoadKeepTests
{
    [Fact]
    public void BlobJoinedByHairlineIsDroppedRoadKept()
    {
        const int w = 200, h = 100;
        var road = new bool[w * h];
        for (int x = 10; x < 190; x++) for (int y = 60; y < 66; y++) road[y * w + x] = true; // road 180 x 6
        for (int x = 40; x < 50; x++) for (int y = 20; y < 30; y++) road[y * w + x] = true;  // 10 px blob
        for (int y = 30; y < 60; y++) road[y * w + 45] = true;                               // 1 px hairline
        var dropped = new List<int>();
        var keep = RoadKeep.Build(road, w, h, 1f, 16, 3, dropped);
        Assert.Equal(255, keep[62 * w + 100]);
        Assert.Equal(255, keep[60 * w + 10]);
        Assert.Equal(0, keep[25 * w + 45]);
        Assert.Equal(0, keep[45 * w + 45]);
        Assert.Single(dropped);
    }

    [Fact]
    public void ThinJoinBetweenTwoRoadsIsKept()
    {
        const int w = 200, h = 60;
        var road = new bool[w * h];
        for (int x = 0; x < 80; x++) for (int y = 20; y < 26; y++) road[y * w + x] = true;
        for (int x = 120; x < 200; x++) for (int y = 20; y < 26; y++) road[y * w + x] = true;
        for (int x = 80; x < 120; x++) road[22 * w + x] = true;
        var keep = RoadKeep.Build(road, w, h, 1f, 16, 3, null);
        Assert.Equal(255, keep[22 * w + 100]);
    }
}

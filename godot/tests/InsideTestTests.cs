using System.Numerics;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The inside test (Play/InsideTest.cs): a unit cube of 12 triangles with corner normals.</summary>
public class InsideTestTests
{
    static InsideTest Cube()
    {
        var pos = new Vector3[8]; var nrm = new Vector3[8];
        for (int i = 0; i < 8; i++)
        {
            pos[i] = new Vector3((i & 1) - 0.5f, ((i >> 1) & 1) - 0.5f, ((i >> 2) & 1) - 0.5f);
            nrm[i] = Vector3.Normalize(pos[i]);
        }
        // each face as two triangles, wound outward (winding does not matter to the test)
        int[] t = { 0,1,3, 0,3,2, 4,6,7, 4,7,5, 0,4,5, 0,5,1, 2,3,7, 2,7,6, 0,2,6, 0,6,4, 1,5,7, 1,7,3 };
        return new InsideTest(pos, nrm, t);
    }

    [Fact]
    public void TheCentreIsInsideByHalfAMetre()
        => Assert.Equal(-0.5f, Cube().Query(Vector3.Zero, 1f).Dist, 1e-3f);

    [Fact]
    public void OneCentimetreOutsideAFaceIsOutside()
    {
        var (d, v) = Cube().Query(new Vector3(0.51f, 0.1f, 0.05f));
        Assert.Equal(0.01f, d, 1e-4f);
        Assert.True(v >= 0);
    }

    [Fact]
    public void OneCentimetreInsideAFaceIsInside()
        => Assert.Equal(-0.01f, Cube().Query(new Vector3(0.1f, -0.49f, 0.05f)).Dist, 1e-4f);

    [Fact]
    public void FarPointsCountAsOutside()
    {
        var (d, v) = Cube().Query(new Vector3(0.7f, 0, 0));
        Assert.True(d > 0);
        Assert.Equal(-1, v);
        Assert.True(Cube().Query(new Vector3(0, 0.5f + 0.11f, 0)).Dist > 0);
    }
}

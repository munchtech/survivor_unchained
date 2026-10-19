import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
def sub(a, b):
    global s
    a, b = a.replace("\n", "\r\n"), b.replace("\n", "\r\n")
    assert s.count(a) == 1, a
    s = s.replace(a, b)
sub("""    readonly List<MeshInstance3D> fulls = new();
""", """    readonly List<MeshInstance3D> fulls = new();
    /// <summary>The full meshes after the first a gameplay mesh stands for (its other slots' meshes of one material):
    /// it wears the first one's materials.</summary>
    readonly HashSet<MeshInstance3D> follow = new();
    /// <summary>Her outfit's slots (tools/armor/slot_map.json's layers).</summary>
    static readonly string[] Slots = { "ink", "top", "bottom", "legwear", "gloves", "skirt", "belt", "collar", "bracers", "greaves", "boots", "pauldrons", "cloak", "head" };

    /// <summary>Whether a full mesh is one slot's of an outfit's material: SET_SLOT_MAT (heroine_outfits.py's SET.SLOT.MAT,
    /// the dots made underscores on import).</summary>
    public static bool IsSlotMesh(string name, string set, string mat) => Slots.Any(s => name == $"{set}_{s}_{mat}");
""")
sub("""                lod.pairs.Add((full, mi, map, own));
                lod.fulls.Add(full);
""", """                if (lod.pairs.Any(q => q.Lod == mi)) lod.follow.Add(full);
                lod.pairs.Add((full, mi, map, own));
                lod.fulls.Add(full);
""")
sub("""        foreach (var (f, l, map, own) in pairs)
        {
            for (int s = 0;""", """        foreach (var (f, l, map, own) in pairs)
        {
            if (follow.Contains(f)) continue;
            for (int s = 0;""")
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")

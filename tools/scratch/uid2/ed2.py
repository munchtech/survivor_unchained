import re
def edit(p, pairs):
    s = open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in s else '\n'
    s = s.replace('\r\n', '\n')
    for a, b in pairs:
        assert a in s, (p, a[:60])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))

edit('godot/logic/World/Lore.cs', [
('''/// <summary>One of her own hairstyles (the view's heroine_hair_ID), and how it is worn.</summary>
public sealed class HairCut { public string Id = "", Name = "", Words = ""; }

/// <summary>Paint on her face (the view's art/people/paint/ID.png): how it reads,''',
'''/// <summary>One of a hero's own hairstyles (the heroine's: the view's heroine_hair_ID), and how it is worn.</summary>
public sealed class HairCut { public string Id = "", Name = "", Words = ""; }

/// <summary>
/// What a hero's own body offers to be shaped with in creation (looks.json's
/// heroes, by sex: the heroine's now, the male hero's when his body has them):
/// its own hairstyles, eyes (an iris to dye), paints for the face, faces to
/// start from and the face's sliders. A body without one is shaped as the
/// kit's people are (a Quaternius cut, a beard).
/// </summary>
public sealed class HeroLook
{
    public List<HairCut> Cuts = new();
    public List<LookChoice> Eyes = new();
    public List<FacePaint> Paints = new();
    public List<FaceShape> Faces = new();
    public List<FaceSlider> Sliders = new();
}

/// <summary>Paint on a face (the view's art/people/paint/ID.png): how it reads,'''),
('''        public List<LookChoice> Cloaks = new(), Skins = new(), Hairs = new(), Eyes = new();
        public Dictionary<string, List<string>> HairStyles = new();
        public List<HairCut> HerHairs = new();
        public List<FacePaint> Paints = new();
        public List<FaceShape> Faces = new();
        public List<FaceSlider> Sliders = new();
    }''',
'''        public List<LookChoice> Cloaks = new(), Skins = new(), Hairs = new();
        public Dictionary<string, List<string>> HairStyles = new();
        public Dictionary<string, HeroLook> Heroes = new();
    }'''),
('''    /// <summary>Her own hairstyles, the first hers unless another is chosen.</summary>
    public static List<HairCut> HerHairs => L.HerHairs;
    public static List<LookChoice> Eyes => L.Eyes;
    public static List<FacePaint> Paints => L.Paints;
    /// <summary>Faces to start from (the first her own), and her face's sliders by group.</summary>
    public static List<FaceShape> Faces => L.Faces;
    public static List<FaceSlider> Sliders => L.Sliders;''',
'''    /// <summary>What a hero's own body of that sex offers to be shaped with, or null.</summary>
    public static HeroLook? Hero(Sex sex) => L.Heroes.TryGetValue(sex.Key(), out var h) ? h : null;
    /// <summary>The heroine's: her own cuts (the first hers unless another is
    /// chosen), eyes, paints, faces to start from (the first her own) and sliders.</summary>
    public static HeroLook Her => Hero(Sex.Female)!;'''),
])
print('lore ok')

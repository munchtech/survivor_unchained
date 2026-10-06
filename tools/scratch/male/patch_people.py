p = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2de192cce8298ca/godot/src/Actors/People.cs'
s = open(p, encoding='utf-8').read()
rep = [
('''        if (body == SurvivorUnchained.Play.Loadouts.HerBody && Args.Get("body") != "woman" && ResourceLoader.Exists("res://art/people/heroine.glb")) body = "heroine";
        var p = body switch { SurvivorUnchained.Play.Loadouts.HerBody => Woman(look), "heroine" => Heroine(look), "anime" => Her(look), _ => Build(look) };''',
'''        if (body == SurvivorUnchained.Play.Loadouts.HerBody && Args.Get("body") != "woman" && ResourceLoader.Exists("res://art/people/heroine.glb")) body = "heroine";
        // The man survivor is the hero (tools/assets/hero_male_body.py) once
        // his outfits are made; till then the kit's man, and --body hero shows him.
        if (body == SurvivorUnchained.Play.Loadouts.HisBody && ResourceLoader.Exists("res://art/people/hero.glb") && Args.Get("body") == "hero") body = "hero";
        var p = body switch { SurvivorUnchained.Play.Loadouts.HerBody => Woman(look), "heroine" => Heroine(look), "hero" => Hero(look), "anime" => Her(look), _ => Build(look) };
        if (body == "hero" && look.Face != null) HerFace(p, look.Face);'''),
('''        var parts = new List<string>(look.Outfit);''', '''        // (Not the hero's own outfit, "him:<calling>", which the kit has no part for.)
        var parts = look.Outfit.Where(o => !o.StartsWith("him:")).ToList();'''),
('''    static Material HerPart(BaseMaterial3D src, Look look, Mesh mesh)
    {''', '''    static Material HerPart(BaseMaterial3D src, Look look, Mesh mesh, string who = "heroine")
    {'''),
('''                e.SetShaderParameter("iris", GD.Load<Texture2D>("res://art/people/head_tex/heroine_iris.png"));''',
 '''                var iris = $"res://art/people/head_tex/{who}_iris.png";
                e.SetShaderParameter("iris", GD.Load<Texture2D>(ResourceLoader.Exists(iris) ? iris : "res://art/people/head_tex/heroine_iris.png"));'''),
('''            default:
                return Skin(src, look, mesh);
        }
    }''', '''            default:
                return Skin(src, look, mesh, who == "hero" ? HisTone : null);
        }
    }'''),
('''    static Material Skin(BaseMaterial3D src, Look look, Mesh mesh)
    {''', '''    static Material Skin(BaseMaterial3D src, Look look, Mesh mesh, Color? own = null)
    {'''),
('''        m.SetShaderParameter("tone", SkinTone(look));''', '''        m.SetShaderParameter("tone", look.Skin is Color ? SkinTone(look) : own ?? SkinTone(look));
        // A body's relief baked from its sculpt (the hero's), under the pores.
        if (src.NormalTexture != null)
        {
            m.SetShaderParameter("relief", src.NormalTexture);
            m.SetShaderParameter("has_relief", true);
        }'''),
]
for a, b in rep:
    assert a in s, a[:80]
    s = s.replace(a, b)
anchor = '''    /// <summary>Her hairstyles (tools/assets/heroine_head.py: a file each,'''
hero = '''    /// <summary>The man survivor, the hero: the owner's sculpt, rigged by
    /// AccuRIG and bound to the game's own skeleton by
    /// tools/assets/hero_male_body.py, with a head of his own
    /// (hero_male_head.py: eyes, lashes, teeth, his face's shapes). His skin,
    /// eyes and head are drawn as hers are (HerPart), his skin with the relief
    /// baked from his sculpt.</summary>
    public static Person Hero(Look look)
    {
        var root = GD.Load<PackedScene>("res://art/people/hero.glb").Instantiate<Node3D>();
        var skel = (Skeleton3D)root.FindChildren("*", "Skeleton3D", true, false)[0];
        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer(), Body = "hero" };
        // His carriage over the library's clips: fingers eased, his arms held
        // clear of his lats rather than in, his hips square.
        person.Pose = new HerPose { ArmsIn = -5f, HipTilt = 0f };
        skel.AddChild(person.Pose);
        int headBone = skel.FindBone("Head");
        if (headBone >= 0) skel.SkeletonUpdated += () => person.HeadPose = skel.GetBoneGlobalPose(headBone);
        skel.AddChild(new HerFaceLife());
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>())
        {
            person.Meshes.Add(mi);
            mi.Layers = 2;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                if (mi.Mesh.SurfaceGetMaterial(s) is BaseMaterial3D src)
                    mi.SetSurfaceOverrideMaterial(s, HerPart(src, look, mi.Mesh, "hero"));
        }
        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        return person;
    }

    /// <summary>His own skin's tone when none is chosen: his paint as it is,
    /// barely warmed (hers is warmed further: her paint is paler).</summary>
    static readonly Color HisTone = new(1.0f, 0.95f, 0.9f);

'''
assert anchor in s
s = s.replace(anchor, hero + anchor, 1)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

q = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2de192cce8298ca/godot/logic/Play/Loadout.cs'
s = open(q, encoding='utf-8').read()
a = '''    public const string HerBody = "woman";
'''
assert a in s
s = s.replace(a, a + '''
    /// <summary>A man survivor's own body (People.Hero: the hero, once his
    /// outfits are made; the kit's man till then, in the outfit listed beside
    /// his own).</summary>
    public const string HisBody = "man";

    /// <summary>A man survivor's own outfit for his calling, as the view knows
    /// it ("him:" and its name).</summary>
    public static string HisOutfit(string archetype) => "him:" + (archetype == "stalker" ? "ranger" : archetype);
''')
a = '''Sex = sex, Body = her ? HerBody : null, Outfit = her ? new List<string> { HerOutfit(ch.Archetype) } : OutfitOf(ch.Archetype, sex, hood),'''
assert a in s
s = s.replace(a, '''Sex = sex, Body = her ? HerBody : HisBody,
            Outfit = her ? new List<string> { HerOutfit(ch.Archetype) } : OutfitOf(ch.Archetype, sex, hood).Append(HisOutfit(ch.Archetype)).ToList(),''')
open(q, 'w', encoding='utf-8', newline='\n').write(s)
print("ok")

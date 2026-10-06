p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a435f4dd0ac80df75\godot\src\Actors\People.cs"
s = open(p, encoding="utf-8").read()
rep = [
('''        if (body == "heroine") p.Calling = HerClips.Calling(look.Outfit);''',
 '''        if (p.Own != null) p.Calling = HerClips.Calling(look.Outfit);'''),
('''        public bool Kit, Woman, Folk;
    }''',
 '''        public bool Kit, Woman, Folk;
        /// <summary>The survivor's own clips (hers or his), when they have them.</summary>
        public OwnClips? Own;
    }'''),
('''    /// <summary>The clip a person plays for one the game names: the heroine's
    /// own where she has it ("her/..."), the library's otherwise.</summary>
    public static string Clip(Person p, string name)
    {
        if (p.Body != "heroine") return p.Folk && FolkClips.For(p.Woman, name) is string folk ? folk : Resolve(name);
        // (One of hers asked for by her own name.)
        if (name.StartsWith(HerClips.Prefix)) return HerClips.Has(name[HerClips.Prefix.Length..]) ? name : Resolve("Idle");
        return HerClips.For(p.Calling, p.Kind, name) is string her ? her : Resolve(name);
    }''',
 '''    /// <summary>The clip a person plays for one the game names: a survivor's
    /// own where they have it ("her/...", "him/..."), the library's otherwise.</summary>
    public static string Clip(Person p, string name)
    {
        if (p.Own is not { } own) return p.Folk && FolkClips.For(p.Woman, name) is string folk ? folk : Resolve(name);
        // (One of their own asked for by its own name.)
        if (own.Owns(name)) return own.Has(name[own.Prefix.Length..]) ? name : Resolve("Idle");
        return own.For(p.Calling, p.Kind, name) is string mine ? mine : Resolve(name);
    }'''),
('''        // Her own clips beside the library's (tools/anim).
        if (HerClips.Library() is AnimationLibrary her) person.Anim.AddAnimationLibrary("her", her);
        return person;''',
 '''        // Her own clips beside the library's (tools/anim).
        if (OwnClips.Her.Library() is AnimationLibrary her)
        {
            person.Own = OwnClips.Her;
            person.Anim.AddAnimationLibrary(OwnClips.Her.Name, her);
        }
        return person;'''),
('''        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        return person;
    }

    /// <summary>His own skin's tone''',
 '''        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        // His own clips beside the library's (tools/anim: hers, given a man's carriage).
        if (OwnClips.Him.Library() is AnimationLibrary him)
        {
            person.Own = OwnClips.Him;
            person.Anim.AddAnimationLibrary(OwnClips.Him.Name, him);
        }
        return person;
    }

    /// <summary>His own skin's tone'''),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")

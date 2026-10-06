from pathlib import Path
W = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035\godot\src\Actors')
p = W / 'People.cs'
s = p.read_text(encoding='utf-8')
rep = [
    ("""        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer() };
        foreach (var c in skel.GetChildren())
            if (c is MeshInstance3D mi)
            {
                person.Meshes.Add(mi);
                Shape(mi, look.Figure);""",
     """        var person = new Person { Root = root, Skeleton = skel, Anim = new AnimationPlayer(), Kit = true, Woman = look.Sex == "female" };
        foreach (var c in skel.GetChildren())
            if (c is MeshInstance3D mi)
            {
                person.Meshes.Add(mi);
                Shape(mi, look.Figure);"""),
    ("""        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        return person;
    }

    /// <summary>The woman survivor's body""",
     """        root.AddChild(person.Anim);
        person.Anim.RootNode = "..";
        person.Anim.AddAnimationLibrary("", Clips());
        // The townsfolk's own clips beside the library's (tools/anim/folk.py).
        if (FolkClips.Library() is AnimationLibrary folk) person.Anim.AddAnimationLibrary("folk", folk);
        return person;
    }

    /// <summary>The woman survivor's body"""),
    ("""        /// <summary>Her corrective layer, told how much of what plays is her own.</summary>
        public HerPose? Pose;""",
     """        /// <summary>Her corrective layer, told how much of what plays is her own.</summary>
        public HerPose? Pose;
        /// <summary>A kit body (People.Build), a woman's or a man's; and, set
        /// by its view, whether it goes unarmed: the townsfolk, who play
        /// their own clips (FolkClips) where they have them.</summary>
        public bool Kit, Woman, Folk;"""),
    ("""        if (p.Body != "heroine") return Resolve(name);""",
     """        if (p.Body != "heroine") return p.Folk && FolkClips.For(p.Woman, name) is string folk ? folk : Resolve(name);"""),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
p.write_text(s, encoding='utf-8')

p = W / 'PersonView.cs'
s = p.read_text(encoding='utf-8')
rep = [
    ("""        person.Kind = HerClips.Kind(arms?.Right, arms?.Left, arms?.Forearm);""",
     """        person.Kind = HerClips.Kind(arms?.Right, arms?.Left, arms?.Forearm);
        person.Folk = person.Kit && arms?.Right == null && arms?.Left == null && arms?.Forearm == null;"""),
    ("""            loopSpeed = natural > 0 ? Mathf.Clamp(speed / natural, 0.4, 1.6)
                : want == WalkClip ? Mathf.Clamp(speed / 1.5, 0.6, 1.5) : Mathf.Clamp(speed / 3.6, 0.7, 1.5);""",
     """            // A townsperson's own walk, at the rate that keeps their feet planted.
            string walk = People.Clip(person, WalkClip);
            float stride = walk.StartsWith(FolkClips.Prefix) ? FolkClips.Speed(walk) * person.Root.Scale.X : 0;
            loopSpeed = natural > 0 ? Mathf.Clamp(speed / natural, 0.4, 1.6)
                : want == WalkClip ? Mathf.Clamp(speed / (stride > 0 ? stride : 1.5), 0.6, 1.5) : Mathf.Clamp(speed / 3.6, 0.7, 1.5);"""),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
p.write_text(s, encoding='utf-8')
print('ok')

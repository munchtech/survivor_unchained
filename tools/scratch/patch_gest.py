ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a435f4dd0ac80df75\godot\src\Actors"


def patch(path, rep):
    s = open(path, encoding="utf-8").read()
    for a, b in rep:
        assert s.count(a) == 1, (path, a[:70])
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8").write(s)


patch(ROOT + r"\People.cs", [
    ('''        /// <summary>The survivor's own clips (hers or his), when they have them.</summary>
        public OwnClips? Own;''',
     '''        /// <summary>The survivor's own clips (hers or his), when they have them.</summary>
        public OwnClips? Own;
        /// <summary>Gestures laid over whatever plays (a nod, an exhale).</summary>
        public Gestures? Gestures;'''),
    ('''        person.Pose = new HerPose();
        skel.AddChild(person.Pose);''',
     '''        person.Pose = new HerPose();
        skel.AddChild(person.Pose);
        person.Gestures = new Gestures();
        skel.AddChild(person.Gestures);'''),
    ('''        person.Pose = new HerPose { ArmsIn = -5f, HipTilt = 0f, NeckPitch = HisNeckPitch };
        skel.AddChild(person.Pose);''',
     '''        person.Pose = new HerPose { ArmsIn = -5f, HipTilt = 0f, NeckPitch = HisNeckPitch };
        skel.AddChild(person.Pose);
        person.Gestures = new Gestures();
        skel.AddChild(person.Gestures);'''),
])

patch(ROOT + r"\PersonView.cs", [
    ('''        Cinema = true;
        var name = People.Clip(person, clip);
        if (!person.Anim.HasAnimation(name)) { GD.PushWarning($"cinema: no clip {clip}"); return; }''',
     '''        Cinema = true;
        var name = People.Clip(person, clip);
        if (!person.Anim.HasAnimation(name)) { GD.PushWarning($"cinema: no clip {clip}"); return; }
        // A gesture (a nod, an exhale) is laid over what plays, not played in its place.
        if (person.Own is { } own && own.Owns(name) && own.Gesture(name[own.Prefix.Length..]) && person.Gestures is { } g)
        {
            g.Play(person.Anim.GetAnimation(name), speed, own.Holds(name[own.Prefix.Length..]));
            return;
        }
        person.Gestures?.Release();'''),
])
print("ok")

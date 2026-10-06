W = r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ae2de192cce8298ca/'
for p, a, b in [
    ('godot/src/Actors/People.cs', 'person.Pose = new HerPose { ArmsIn = -5f, HipTilt = 0f };',
     'person.Pose = new HerPose { ArmsIn = -5f, HipTilt = 0f, NeckPitch = HisNeckPitch };'),
    ('godot/src/Actors/People.cs', '''    static readonly Color HisTone = new(1.0f, 0.95f, 0.9f);''', '''    static readonly Color HisTone = new(1.0f, 0.95f, 0.9f);

    /// <summary>His neck leans further forward at rest than the library's
    /// body's: the library's clips throw his head back by about this much
    /// (HerPose.NeckPitch), till his own clips are made.</summary>
    const float HisNeckPitch = 22f;'''),
    ('godot/tools_scenes/lookdev.gd', '''				pose.HipTilt = 0.0
''', '''				pose.HipTilt = 0.0
				pose.NeckPitch = float(OS.get_environment("NECK")) if OS.get_environment("NECK") != "" else 22.0
'''),
]:
    s = open(W + p, encoding='utf-8').read()
    assert a in s, a
    s = s.replace(a, b)
    open(W + p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')

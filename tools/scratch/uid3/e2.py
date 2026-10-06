import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/tools_scenes/Portraits.cs', [
    ('''        Put(job);
        Hold(job.ContainsKey("seek") ? (double)job["seek"] : Seek);''', '''        Put(job);
        Hold(job.ContainsKey("seek") ? (double)job["seek"] : Seek);
        Chin(job.ContainsKey("chin") ? (float)job["chin"] : 0);'''),
    ('''    void Studio()
    {''', '''    /// <summary>Her chin lifted so many degrees (her idle carries her head a little low for a portrait).</summary>
    void Chin(float degrees)
    {
        if (her == null || degrees == 0) return;
        foreach (var (bone, share) in new[] { ("Neck", 0.4f), ("Head", 0.6f) })
        {
            int b = her.Skeleton.FindBone(bone);
            if (b < 0) continue;
            her.Skeleton.SetBonePoseRotation(b, her.Skeleton.GetBonePoseRotation(b) * new Quaternion(Vector3.Right, -Mathf.DegToRad(degrees * share)));
        }
    }

    void Studio()
    {'''),
    ('''        var (lift, tall, dist) = view switch { "bust" => (-0.12f, 0.62f, 1.6f), "head" => (-0.05f, 0.42f, 1.4f), _ => (-0.035f, 0.3f, 1.2f) };''',
     '''        var (lift, tall, dist) = view switch { "bust" => (-0.12f, 0.62f, 1.6f), "head" => (-0.07f, 0.5f, 1.5f), _ => (-0.02f, 0.34f, 1.3f) };'''),
    ('''        cam.GlobalPosition = look + toCam * dist + Vector3.Up * 0.03f;''', '''        cam.GlobalPosition = look + toCam * dist;'''),
])
edit('tools/assets/creation_portraits.py', [
    ("""VIEW = {'hair': ('bust', -38), 'face': ('face', -14), 'paint': ('face', -10), 'look': ('head', -22)}""",
     """VIEW = {'hair': ('head', -40), 'face': ('face', -14), 'paint': ('face', -10), 'look': ('head', -22)}
# Her chin lifted a little (degrees) for each kind.
CHIN = {'hair': 4, 'face': 7, 'paint': 7, 'look': 6}"""),
    ("""# Her shoulders bare (the stalker's outfit shows none of itself so high), and her head up in its idle.
OUTFIT = 'stalker'""", """# Her shoulders bare in the face's pictures (the stalker's outfit shows none of itself so high, and
# her head is up in its idle); the hair's go lower, so she wears the warden's mail there.
OUTFIT = 'stalker'
HAIR_OUTFIT = 'warden'"""),
    ("""'hair': cut['id'], 'hairColor': colour, 'outfit': OUTFIT})""", """'hair': cut['id'], 'hairColor': colour, 'outfit': HAIR_OUTFIT, 'chin': CHIN['hair']})"""),
    ("""'face': f.get('shape', {}), 'outfit': OUTFIT})""", """'face': f.get('shape', {}), 'outfit': OUTFIT, 'chin': CHIN['face']})"""),
    ("""'paint': p['id'] if p['id'] != 'none' else '', 'outfit': OUTFIT})""", """'paint': p['id'] if p['id'] != 'none' else '', 'outfit': OUTFIT, 'chin': CHIN['paint']})"""),
    ("""'hair': 'long', 'outfit': OUTFIT})""", """'hair': 'long', 'outfit': OUTFIT, 'chin': CHIN['look']})"""),
])

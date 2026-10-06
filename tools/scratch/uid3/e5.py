import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/tools_scenes/Portraits.cs', [
    ('''        var look = eyes + new Vector3(0, lift, 0);
        var toCam = Vector3.Back;''', '''        // (a cut that hangs behind her, seen in profile: the frame moved back to hold it)
        float back = job.ContainsKey("back") ? (float)job["back"] : 0;
        var look = eyes + new Vector3(0, lift, 0) - her.Root.GlobalBasis.Z.Normalized() * back;
        var toCam = Vector3.Back;'''),
    ('''/// JOBS=a JSON file: [{"name", "view": "bust"|"face", "yaw", "outfit", "hair",''', '''/// JOBS=a JSON file: [{"name", "view": "bust"|"head"|"face", "yaw", "back", "chin", "seek", "outfit", "hair",'''),
])
edit('tools/assets/creation_portraits.py', [
    ("""CUT_YAW = {'ponytail': -78, 'braid': -100}""", """CUT_YAW = {'ponytail': -78, 'braid': -100}
CUT_BACK = {'ponytail': 0.07, 'braid': 0.09}"""),
    ("""'view': view, 'yaw': CUT_YAW.get(cut['id'], yaw),""", """'view': view, 'yaw': CUT_YAW.get(cut['id'], yaw), 'back': CUT_BACK.get(cut['id'], 0),"""),
])

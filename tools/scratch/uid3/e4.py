import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('godot/tools_scenes/Portraits.cs', [
    ('''        var (lift, tall, dist) = view switch { "bust" => (-0.12f, 0.62f, 1.6f), "head" => (-0.07f, 0.5f, 1.5f), _ => (-0.02f, 0.34f, 1.3f) };''',
     '''        var (lift, tall, dist) = view switch { "bust" => (-0.12f, 0.62f, 1.6f), "head" => (-0.06f, 0.4f, 1.5f), _ => (-0.03f, 0.26f, 1.3f) };'''),
])
edit('tools/assets/creation_portraits.py', [
    ("""# Her chin lifted a little (degrees) for each kind.""", """# A cut that hangs behind her is seen nearer her profile.
CUT_YAW = {'ponytail': -78, 'braid': -100}
# Her chin lifted a little (degrees) for each kind."""),
    ("""                jobs.append({'name': f"hair_{cut['id']}_{tag}", 'view': view, 'yaw': yaw,""",
     """                jobs.append({'name': f"hair_{cut['id']}_{tag}", 'view': view, 'yaw': CUT_YAW.get(cut['id'], yaw),"""),
])

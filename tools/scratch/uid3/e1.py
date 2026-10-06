import os
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69858664f1d3dd29'


def edit(rel, pairs):
    p = os.path.join(W, rel)
    s = open(p, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    for a, b in pairs:
        if crlf:
            a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
        n = s.count(a)
        assert n == 1, (rel, n, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)
    print('edited', rel)


edit('godot/tools_scenes/Portraits.cs', [
    ('AmbientLightEnergy = 0.32f', 'AmbientLightEnergy = 0.2f'),
    ('LightColor = new Color(1f, 0.8f, 0.62f), LightEnergy = 1.7f', 'LightColor = new Color(1f, 0.8f, 0.62f), LightEnergy = 2.1f'),
    ('LightColor = new Color(0.62f, 0.7f, 0.92f), LightEnergy = 0.38f', 'LightColor = new Color(0.62f, 0.7f, 0.92f), LightEnergy = 0.3f'),
    ('LightColor = new Color(0.78f, 0.86f, 1f), LightEnergy = 1.1f, LightSpecular = 0.6f', 'LightColor = new Color(0.78f, 0.86f, 1f), LightEnergy = 2.6f, LightSpecular = 0.7f'),
    ('-toCam * 1.8f + side * 0.3f + Vector3.Up * 1.0f', '-toCam * 1.6f - side * 0.5f + Vector3.Up * 1.1f'),
])
edit('tools/assets/creation_portraits.py', [
    ("SIZE = 640          # rendered", "SIZE = 1024         # rendered (twice what is written: the hair's hashed edges average out)"),
    ("""            jobs.append({'name': f"face_{f['id']}", 'view': view, 'yaw': yaw, 'hair': 'ponytail', 'face': f.get('shape', {})})""",
     """            jobs.append({'name': f"face_{f['id']}", 'view': view, 'yaw': yaw, 'hair': 'ponytail', 'face': f.get('shape', {}), 'outfit': OUTFIT})"""),
    ("""'paint': p['id'] if p['id'] != 'none' else ''})""", """'paint': p['id'] if p['id'] != 'none' else '', 'outfit': OUTFIT})"""),
    ("""        jobs.append({'name': 'look', 'view': view, 'yaw': yaw, 'hair': 'long'})""", """        jobs.append({'name': 'look', 'view': view, 'yaw': yaw, 'hair': 'long', 'outfit': OUTFIT})"""),
    ("""'hair': cut['id'], 'hairColor': colour})""", """'hair': cut['id'], 'hairColor': colour, 'outfit': OUTFIT})"""),
    ("""VIEW = {""", """# Her shoulders bare (the stalker's outfit shows none of itself so high), and her head up in its idle.
OUTFIT = 'stalker'
VIEW = {"""),
])

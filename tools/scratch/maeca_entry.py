import json, subprocess
b = json.loads(subprocess.run(['git', 'show', 'e1ff6374a2d6c396c38ed150c858cf64a4be1a7e:godot/data/content/dialogue.json'], capture_output=True).stdout.decode('utf-8'))
d = json.load(open('docs/romance/data/maeca.json', encoding='utf-8'))
d = d.get('maeca', d)
l = json.load(open('godot/data/content/dialogue.json', encoding='utf-8'))
for name, x in (('base', b['maeca']['entry']), ('draft', d['entry']), ('live', l['maeca']['entry'])):
    print('==', name)
    for e in x:
        print('  ', e.get('node'), json.dumps(e.get('when'), ensure_ascii=False)[:200])

"""Hugging Face lookups for licence research.
    python hf.py author <name>          models by an author, with licence tags
    python hf.py search <words>         models matching words
    python hf.py files <repo>           a repo's files and licence tag
    python hf.py get <repo> <file>      print a file (e.g. LICENSE, README.md)"""
import json
import sys
import urllib.parse
import urllib.request

UA = {'User-Agent': 'Mozilla/5.0 legal-research'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode('utf-8', 'ignore')


def lic(tags):
    return ','.join(t for t in (tags or []) if t.startswith('license'))


cmd, args = sys.argv[1], sys.argv[2:]
if cmd == 'author':
    for m in json.loads(get(f'https://huggingface.co/api/models?author={args[0]}&limit=100&full=true')):
        print(m['id'], '|', lic(m.get('tags')), '|', m.get('createdAt', '')[:10], '| gated' if m.get('gated') else '')
elif cmd == 'search':
    q = urllib.parse.quote(' '.join(args))
    for m in json.loads(get(f'https://huggingface.co/api/models?search={q}&limit=40&full=true')):
        print(m['id'], '|', lic(m.get('tags')), '|', m.get('createdAt', '')[:10])
elif cmd == 'files':
    m = json.loads(get(f'https://huggingface.co/api/models/{args[0]}'))
    print('licence:', lic(m.get('tags')), '| gated:', m.get('gated'), '| created:', m.get('createdAt'), '| modified:', m.get('lastModified'))
    for s in m.get('siblings', []):
        print(' ', s['rfilename'])
elif cmd == 'get':
    print(get(f'https://huggingface.co/{args[0]}/raw/main/{args[1]}'))

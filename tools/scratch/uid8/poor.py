"""A copy of fortune.json with no gold (pictures of the lamp refusing a bed)."""
import json
import os

S = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(S, 'fortune.json'), encoding='utf-8'))


def walk(o, path=''):
    if isinstance(o, dict):
        for k, v in o.items():
            if k.lower() == 'gold' and isinstance(v, (int, float)):
                print('gold at', path + '/' + k, v)
                o[k] = 2
            else:
                walk(v, path + '/' + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f'{path}[{i}]')


walk(d)
json.dump(d, open(os.path.join(S, 'poor.json'), 'w', encoding='utf-8'))

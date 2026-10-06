import json, sys
rs = [json.loads(l) for l in open(sys.argv[1])]
for r in rs:
    if r['Won']:
        continue
    st = [x for x in r['Stages'] if x['Falls'] > 0]
    if st and len(sys.argv) < 3:
        continue
    print(r['Spec']['Key'], round(r['Minutes'], 1), r['KilledBy'], r['BossPhase'], r['BossSoft'], '|', r['Where'], '|', [(x['Name'], round(x['Seconds']), x['Falls']) for x in r['Stages']])

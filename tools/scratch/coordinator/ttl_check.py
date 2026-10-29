"""Sum a subagent's cache writes by TTL bucket: python ttl_check.py <agent-id> [...]"""
import glob, json, os, re, sys

root = os.path.expanduser('~/.claude/projects/C--Users-munch-Desktop-survivorsunchained')
for aid in sys.argv[1:]:
    for f in glob.glob(f'{root}/*/subagents/agent-{aid}.jsonl'):
        h1 = m5 = 0
        for line in open(f, encoding='utf-8', errors='ignore'):
            for c in re.findall(r'"cache_creation":(\{[^}]*\})', line):
                d = json.loads(c)
                h1 += d.get('ephemeral_1h_input_tokens', 0)
                m5 += d.get('ephemeral_5m_input_tokens', 0)
        meta = f[:-6] + '.meta.json'
        kind = json.load(open(meta)).get('agentType', '?') if os.path.exists(meta) else '?'
        print(f'{aid} {kind}: 1h writes {h1:,}  5m writes {m5:,}')

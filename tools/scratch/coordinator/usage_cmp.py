"""Weekly usage audit from Claude Code transcripts (read-only), this week against the week before.

Moved from survivorsunchained_inputs/scratch_usage_cmp/cmp2.py (13 Nov 2026) and generalized: the periods
are the last --days days ending --end (default today, PST days) and the same span before. Prints, per period:
list-price dollars by model and by part, cold rewrites (a big cache write after a gap: >1h, 5-60m, <5m),
compactions vs handoffs (successor = first message matches a take-over pattern) and their rewrite dollars,
shell-output dollars (Bash/PowerShell results carried until the next compaction), fixed per-agent overhead
(first-request context carried), then a table by agent type.

  python tools/scratch/coordinator/usage_cmp.py                 # last 7 days vs the 7 before
  python tools/scratch/coordinator/usage_cmp.py --end 2026-11-13 --days 4

Estimates: tool-result tokens are chars/2.1 (our content, calibrated 13 Nov in where_tokens_go); carried $ =
tokens x (write price + read price x later requests of that agent until a compaction). List prices below.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import statistics as st

HOME = os.path.expanduser('~/.claude/projects')
PR = {  # $/M: input, 5m write, 1h write, cache read, output
    'fable': (8, 10, 16, 0.20, 40), 'opus': (4, 5, 8, 0.20, 20),
    'sonnet': (2, 2.5, 4, 0.10, 10), 'haiku': (0.5, 0.625, 1, 0.05, 2.5)}
CHARS_PER_TOK = 2.1
SUCC = re.compile(r"you take over|taking over from|took over from|take over from|successor to|you are the successor|"
                  r"your predecessor|picking up a predecessor|predecessor (spent|ended|handed|ran|solver)|handed off at|"
                  r"ended at (its|the) (context )?cap|ran out of (room|context)|continuing from a previous|your handoff top|"
                  r"YOUR handoff|read (the|your) handoff|from (its|your) handoff|lead \d+ handed off|previous coordinator|"
                  r"coordinator #\d+|at its context limit", re.I)


def fam(m):
    m = (m or '').lower()
    for k in PR:
        if k in m:
            return k
    return 'fable' if 'mythos' in m else None


def text_of(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return ' '.join(p.get('text', '') for p in c if isinstance(p, dict) and p.get('type') == 'text')
    return ''


def size_of(c):
    if isinstance(c, str):
        return len(c)
    if isinstance(c, list):
        return sum(len(p.get('text', '')) for p in c if isinstance(p, dict))
    return 0


def scan(f, per):
    """One transcript -> (agent type, rows) where rows are per-period counters for that agent."""
    atype = 'main'
    if (os.sep + 'subagents' + os.sep) in f or '/subagents/' in f:
        try:
            atype = json.load(open(f[:-6] + '.meta.json', encoding='utf-8')).get('agentType', 'sub?')
        except Exception:
            atype = 'sub?'
    seen, order, first_user, shell_ids, shell_out = {}, [], None, set(), []
    for line in open(f, encoding='utf-8', errors='ignore'):
        has_usage = '"usage"' in line
        if not (has_usage or first_user is None or '"tool_result"' in line or '"Bash"' in line or '"PowerShell"' in line):
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get('message') or {}
        c = m.get('content')
        if m.get('role') == 'user':
            if first_user is None and not d.get('isMeta'):
                first_user = text_of(c)[:4000]
            for p in c if isinstance(c, list) else []:
                if isinstance(p, dict) and p.get('type') == 'tool_result' and p.get('tool_use_id') in shell_ids:
                    shell_out.append((len(order), size_of(p.get('content')) / CHARS_PER_TOK))
        if m.get('role') == 'assistant' and isinstance(c, list):
            for p in c:
                if isinstance(p, dict) and p.get('type') == 'tool_use' and p.get('name') in ('Bash', 'PowerShell'):
                    shell_ids.add(p.get('id'))
        u, mid, ts = m.get('usage'), m.get('id'), d.get('timestamp')
        if not has_usage or not u or not mid or not ts or not fam(m.get('model')):
            continue
        if mid not in seen:
            order.append(mid)
        cc = u.get('cache_creation') or {}
        e = seen.setdefault(mid, dict(i=0, cw=0, cw5=0, cw1=0, cr=0, o=0, ts=ts, fm=fam(m.get('model'))))
        for k, src in (('i', 'input_tokens'), ('cw', 'cache_creation_input_tokens'), ('cr', 'cache_read_input_tokens'),
                       ('o', 'output_tokens')):
            e[k] = max(e[k], u.get(src, 0) or 0)
        e['cw5'] = max(e['cw5'], cc.get('ephemeral_5m_input_tokens', 0) or 0)
        e['cw1'] = max(e['cw1'], cc.get('ephemeral_1h_input_tokens', 0) or 0)
    if not order:
        return atype, {}
    rows = collections.defaultdict(collections.Counter)
    ctxs, pers, compact_at = [], [], []
    prev_t = prev_ctx = None
    for k, mid in enumerate(order):
        e = seen[mid]
        t = dt.datetime.fromisoformat(e['ts'].replace('Z', '+00:00'))
        p = per((t - dt.timedelta(hours=8)).date())
        ctx = e['i'] + e['cw'] + e['cr']
        ctxs.append(ctx); pers.append(p)
        dropped = bool(prev_ctx and prev_ctx > 100e3 and ctx < 0.6 * prev_ctx)
        if dropped:
            compact_at.append(k)
        if p:
            pi, p5, p1, pr, po = PR[e['fm']]
            if e['cw5'] + e['cw1'] == 0 and e['cw']:
                e['cw5'] = e['cw']  # no split logged: assume 5m
            c = dict(inp=e['i'] * pi, cw5=e['cw5'] * p5, cw1=e['cw1'] * p1, cr=e['cr'] * pr, out=e['o'] * po)
            D = rows[p]
            tot = sum(c.values()) / 1e6
            D['usd'] += tot
            for kk, v in c.items():
                D['usd_' + kk] += v / 1e6
            D['usd_m_' + e['fm']] += tot
            D['tok5'] += e['cw5']; D['tok1'] += e['cw1']; D['req'] += 1
            big = k > 0 and e['cw'] > 40e3 and e['cw'] > 0.6 * ctx
            if dropped:
                D['compact_n'] += 1
                D['compact_usd'] += (e['cw5'] * p5 + e['cw1'] * p1) / 1e6
            elif big:
                gap = (t - prev_t).total_seconds() if prev_t else 0
                b = 'gt1h' if gap > 3600 else 'm5_60' if gap > 300 else 'lt5m'
                D['cold_' + b] += 1
                D['coldusd_' + b] += (e['cw5'] * p5 + e['cw1'] * p1 - e['cw'] * pr) / 1e6
        prev_t, prev_ctx = t, ctx
    fm = seen[order[0]]['fm']
    _, p5, _, pr, _ = PR[fm]

    def carried(idx, tok):
        nxt = next((c for c in compact_at if c > idx), len(order))
        return tok * (p5 + pr * max(nxt - idx - 1, 0)) / 1e6

    p0 = pers[0]
    if p0:
        rows[p0]['agents'] += 1
        if first_user and SUCC.search(first_user):
            rows[p0]['handoff_n'] += 1
            rows[p0]['handoff_usd_first'] += carried(0, ctxs[0])  # the successor's start context, carried
        base = max(0, ctxs[0] - len(first_user or '') / CHARS_PER_TOK)
        rows[p0]['fixed_usd'] += carried(0, base)
        rows[p0]['first_ctx_sum'] += ctxs[0]
    for idx, tok in shell_out:
        p = pers[min(idx, len(pers) - 1)]
        if p:
            rows[p]['shell_tok'] += tok
            rows[p]['shell_usd'] += carried(min(idx, len(order) - 1), tok)
    return atype, {p: (D, [ctxs[k - 1] for k in compact_at if pers[k] == p]) for p, D in rows.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--end', default=None, help='last PST day of this week, YYYY-MM-DD (default today)')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--roots', default='survivorsunchained,Marionette', help='project folder name parts')
    a = ap.parse_args()
    end = dt.date.fromisoformat(a.end) if a.end else (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=8)).date()
    tw0 = end - dt.timedelta(days=a.days - 1)
    lw0, lw1 = tw0 - dt.timedelta(days=a.days), tw0 - dt.timedelta(days=1)

    def per(day):
        return 'TW' if tw0 <= day <= end else 'LW' if lw0 <= day <= lw1 else None

    start_ts = dt.datetime.combine(lw0, dt.time(), dt.timezone.utc).timestamp()
    parts = a.roots.split(',')
    roots = [d for d in glob.glob(HOME + '/*') if any(x in d for x in parts)]
    T = collections.defaultdict(collections.Counter)
    R = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    CB = collections.defaultdict(list)
    for r in roots:
        for f in glob.glob(r + '/**/*.jsonl', recursive=True):
            if os.path.getmtime(f) < start_ts:
                continue
            atype, res = scan(f, per)
            for p, (D, before) in res.items():
                T[p].update(D); R[p][atype].update(D); CB[(p, atype)] += before
    names = {'LW': f'LAST WEEK {lw0}..{lw1}', 'TW': f'THIS WEEK {tw0}..{end}'}
    for p in ('LW', 'TW'):
        D = T[p]; u = D['usd'] or 1
        cold = D['coldusd_gt1h'] + D['coldusd_m5_60'] + D['coldusd_lt5m']
        print(f"\n== {names[p]}: ${D['usd']:,.0f} list, {D['req']} requests, {D['agents']} agent transcripts")
        print('  by model: ' + ', '.join(f"{k[6:]} ${v:,.0f} ({100 * v / u:.0f}%)"
                                         for k, v in sorted(D.items(), key=lambda kv: -kv[1]) if k.startswith('usd_m_')))
        print(f"  by part: output {100 * D['usd_out'] / u:.0f}%, cache read {100 * D['usd_cr'] / u:.0f}%, 1h write "
              f"{100 * D['usd_cw1'] / u:.0f}%, 5m write {100 * D['usd_cw5'] / u:.0f}%, fresh in {100 * D['usd_inp'] / u:.0f}%")
        print(f"  cold rewrites: ${cold:,.0f} ({100 * cold / u:.1f}%): >1h {D['cold_gt1h']} (${D['coldusd_gt1h']:,.0f}), "
              f"5-60m {D['cold_m5_60']} (${D['coldusd_m5_60']:,.0f}), <5m {D['cold_lt5m']} (${D['coldusd_lt5m']:,.0f})")
        print(f"  compactions {D['compact_n']} (rewrite ${D['compact_usd']:,.0f}) vs handoffs {D['handoff_n']} "
              f"(successor start contexts carried ${D['handoff_usd_first']:,.0f}; onboarding reads not included)")
        print(f"  shell output: {D['shell_tok'] / 1e6:.1f}M tok, carried ${D['shell_usd']:,.0f}; fixed overhead (first-request "
              f"context carried) ${D['fixed_usd']:,.0f}, median-ish start {D['first_ctx_sum'] / max(D['agents'], 1) / 1e3:.0f}k")
        print(f"  {'type':18}{'n':>5}{'$':>8}{'%':>5}{'$/agent':>8}{'out%':>6}{'5m wr%':>8}{'cold>5m':>8}{'compacts':>9}"
              f"{'handoffs':>9}{'shell $':>8}{'fixed $':>8}{'med ctx@cmp':>12}")
        for t, A in sorted(R[p].items(), key=lambda kv: -kv[1]['usd']):
            if A['usd'] < 1:
                continue
            w = (A['tok5'] + A['tok1']) or 1
            cb = CB[(p, t)]
            print(f"  {t:18}{A['agents']:5}{A['usd']:8,.0f}{100 * A['usd'] / u:5.0f}{A['usd'] / max(A['agents'], 1):8.1f}"
                  f"{100 * A['usd_out'] / A['usd']:6.0f}{100 * A['tok5'] / w:7.0f}%{A['cold_m5_60'] + A['cold_gt1h']:8}"
                  f"{A['compact_n']:9}{A['handoff_n']:9}{A['shell_usd']:8,.0f}{A['fixed_usd']:8,.0f}"
                  f"{(st.median(cb) / 1e3 if cb else 0):11.0f}k")
    L, W = T['LW'], T['TW']
    print('\n== THIS WEEK vs LAST: ' + ', '.join(
        f"{lab} ${W[k]:,.0f} vs ${L[k]:,.0f}" for lab, k in (('spend', 'usd'), ('shell', 'shell_usd'), ('fixed', 'fixed_usd'),
                                                            ('compaction rewrites', 'compact_usd'))) +
          f", compactions {W['compact_n']} vs {L['compact_n']}, handoffs {W['handoff_n']} vs {L['handoff_n']}, cold rewrites $"
          f"{W['coldusd_gt1h'] + W['coldusd_m5_60'] + W['coldusd_lt5m']:,.0f} vs ${L['coldusd_gt1h'] + L['coldusd_m5_60'] + L['coldusd_lt5m']:,.0f}")


if __name__ == '__main__':
    main()

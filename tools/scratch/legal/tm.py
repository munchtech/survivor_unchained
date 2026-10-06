"""Trademark lookups for the name check.
    python tm.py uspto "<words>"    USPTO live and dead marks (tmsearch API)
"""
import json
import sys
import urllib.request

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126', 'Content-Type': 'application/json',
      'Accept': 'application/json', 'Origin': 'https://tmsearch.uspto.gov', 'Referer': 'https://tmsearch.uspto.gov/search/search-results'}


def uspto(words):
    body = {"query": {"bool": {"must": [{"bool": {"should": [
        {"query_string": {"query": words, "default_operator": "AND", "fields": ["markDescription", "WM", "WMP"]}}]}}]}},
        "size": 100, "track_total_hits": True,
        "_source": ["alive", "wordmark", "registrationId", "id", "goodsAndServices", "ownerName", "internationalClass", "filedDate", "statusCode"]}
    req = urllib.request.Request('https://tmsearch.uspto.gov/api-v1-0-0/tmsearch', data=json.dumps(body).encode(), headers=UA)
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    hits = r.get('hits', {}).get('hits', [])
    print('total', r.get('hits', {}).get('totalValue', r.get('hits', {}).get('total')))
    for h in hits:
        s = h.get('source', h.get('_source', {}))
        print(('LIVE' if s.get('alive') else 'dead'), '|', s.get('wordmark'), '|', s.get('id'), '| reg', s.get('registrationId'),
              '|', s.get('internationalClass'), '|', s.get('ownerName'), '|', (s.get('filedDate') or '')[:10])


if sys.argv[1] == 'uspto':
    uspto(sys.argv[2])

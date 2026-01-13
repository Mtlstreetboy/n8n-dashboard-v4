#!/usr/bin/env python3
import os, json, glob

BASE = '/data/files/companies'
files = glob.glob(os.path.join(BASE, '*_news.json'))

total = 0
ctx = 0
missing = 0
per_ticker = {}

for fp in files:
    ticker = os.path.basename(fp).replace('_news.json','')
    d = json.load(open(fp, 'r', encoding='utf-8'))
    arts = d.get('articles', [])
    t_total = len(arts)
    t_ctx = 0
    t_missing = 0
    for a in arts:
        total += 1
        s = a.get('sentiment', {})
        if s.get('method') == 'contextual' and 'relevance' in s:
            ctx += 1
            t_ctx += 1
        elif s:
            missing += 1
            t_missing += 1
    per_ticker[ticker] = (t_ctx, t_total, t_missing)

print('Total articles:', total)
print('Contextual:', ctx)
print('With sentiment but missing fields:', missing)
print('Coverage:', round(100*ctx/total,2), '%')
print('\nPer ticker:')
for t,(tc,tt,tm) in sorted(per_ticker.items()):
    print(f'{t}: contextual {tc}/{tt} ({round(100*tc/tt,2)}%), missing {tm}')

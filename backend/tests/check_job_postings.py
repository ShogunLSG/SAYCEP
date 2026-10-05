"""Step 0 for opportunity matching (plans/next-three.md §3): can Kaggle job
adverts be linked to O*NET occupations, and how well?

Data: Kaggle arshkon/linkedin-job-postings (CC BY-SA 4.0), unzipped anywhere.
Run:  JOBS=/path/to/unzipped python backend/tests/check_job_postings.py
Measures only; loads nothing into the database.
"""
import csv, sqlite3, re, collections, sys, datetime, os, random
csv.field_size_limit(10**9)
S = os.environ['JOBS'].rstrip('/') + '/'
con = sqlite3.connect('backend/saycep.db')
def norm(t):
    t = t.lower()
    t = re.sub(r'\(.*?\)|\[.*?\]', ' ', t)
    t = re.split(r'\s[-–|/,]\s|\s-\s|,', t)[0]           # drop "- Night shift", ", Cape Town"
    t = re.sub(r'\b(sr|senior|jr|junior|lead|i{1,3}|iv|level \d|entry level|part[- ]time|full[- ]time|remote|hybrid)\b\.?', ' ', t)
    t = re.sub(r'[^a-z ]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()
zone = dict(con.execute('select soc_code, job_zone from occupations'))
rated = {r[0] for r in con.execute('select distinct soc_code from occupation_skills')}
lookup = {}
for soc, t in con.execute('select soc_code, title from occupations'): lookup.setdefault(norm(t), set()).add(soc)
for soc, t, s in con.execute('select soc_code, title, short_title from occupation_alt_titles'):
    for x in (t, s):
        if x: lookup.setdefault(norm(x), set()).add(soc)
print('O*NET title keys', len(lookup))
rows = list(csv.DictReader(open(S + 'postings.csv', encoding='utf-8')))
print('postings', len(rows))
lvl = collections.Counter(r['formatted_experience_level'] or '(blank)' for r in rows); print('experience', lvl.most_common())
ts = sorted(int(float(r['listed_time'])) for r in rows if r['listed_time'])
f = lambda ms: datetime.datetime.utcfromtimestamp(ms / 1000).date()
print('listed', f(ts[0]), '→', f(ts[-1]), ' median', f(ts[len(ts)//2]))
loc = collections.Counter(r['location'].split(',')[-1].strip() for r in rows)
print('location tails', loc.most_common(8))
hit = amb = 0; socs = collections.Counter(); zones = collections.Counter(); miss = collections.Counter()
entry = collections.Counter()
for r in rows:
    k = norm(r['title']); m = lookup.get(k)
    e = r['formatted_experience_level'] in ('Entry level', 'Internship')
    entry['all'] += e
    if m:
        hit += 1; entry['hit'] += e
        if len(m) > 1: amb += 1
        s = sorted(m)[0]; socs[s] += 1; zones[zone[s]] += 1
        entry['rated'] += s in rated
    else: miss[k] += 1
n = len(rows)
print(f'title linked to O*NET: {hit} ({hit/n:.1%}); ambiguous {amb}; to an occupation with skill ratings {entry["rated"]}')
print('entry-level/internship: all', entry['all'], ' linked', entry['hit'])
print('linked by job zone', sorted(zones.items()))
print('distinct occupations reached', len(socs), 'top', [(con.execute('select title from occupations where soc_code=?',(s,)).fetchone()[0], c) for s, c in socs.most_common(12)])
print('top unlinked titles', miss.most_common(25))

print('\n--- what feeds the suspicious ones')
name = lambda s: con.execute('select title from occupations where soc_code=?', (s,)).fetchone()[0]
for target in ['Producers and Directors', 'Online Merchants', 'Advertising and Promotions Managers', 'Construction Managers']:
    c = collections.Counter(norm(r['title']) for r in rows if (m := lookup.get(norm(r['title']))) and name(sorted(m)[0]) == target)
    print(target, '<=', c.most_common(6))
random.seed(7)
lk = [r for r in rows if lookup.get(norm(r['title']))]
print('\n--- random 40 linked: advert title => candidate occupations')
for r in random.sample(lk, 40):
    m = lookup[norm(r['title'])]
    print(f"  {r['title'][:55]:<55} => {' | '.join(name(s) for s in sorted(m))[:110]}")

print('\n--- strict: one candidate occupation only, generic titles dropped')
GENERIC = {'director','manager','associate','supervisor','assistant manager','project manager','sales associate','account executive',
           'account manager','team member','intern','consultant','specialist','coordinator','analyst','engineer','technician','vp','vice president'}
strict = [(r, next(iter(lookup[k]))) for r in rows if (k := norm(r['title'])) not in GENERIC and len(lookup.get(k, ())) == 1]
print('strict links', len(strict), f'({len(strict)/n:.1%})')
per = collections.Counter(s for _, s in strict)
print('occupations with >=5 adverts', sum(1 for c in per.values() if c >= 5), 'of 879;  >=20:', sum(1 for c in per.values() if c >= 20))
z = collections.Counter(zone[s] for _, s in strict); print('strict by zone', sorted(z.items()))
zl = collections.Counter(zone[s] for s in per if per[s] >= 5); zall = collections.Counter(zone.values())
print('occupations with >=5 adverts, by zone', {k: f'{zl[k]}/{zall[k]}' for k in sorted(zall)})
ent = sum(1 for r, _ in strict if r['formatted_experience_level'] in ('Entry level', 'Internship')); print('strict entry-level/internship', ent)
for soc in ['47-2111.00', '49-9071.00', '35-2014.00', '43-4051.00', '51-4121.06', '53-3032.00']:
    if soc in zone: print(f'  {name(soc)[:45]:<45} zone {zone[soc]}: {per.get(soc,0)} adverts')
random.seed(11)
print('\n--- random 50 strict links')
for r, s in random.sample(strict, 50): print(f"  {r['title'][:55]:<55} => {name(s)[:70]}")

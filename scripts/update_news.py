#!/usr/bin/env python3
"""RSS headline indexer. Links to publishers; does not republish article bodies."""
import json, os, re, hashlib, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from news_signals import enrich, topics
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
 ('BBC Sport Football','https://feeds.bbci.co.uk/sport/football/rss.xml','en'),
 ('The Guardian Football','https://www.theguardian.com/football/rss','en'),
 ('RFI Afrique Foot','https://www.rfi.fr/fr/afrique-foot/rss','fr'),
 ('RFI Sports','https://www.rfi.fr/fr/sports/rss','fr'),
 ('France 24','https://www.france24.com/fr/rss','fr'),
]
MAX_ITEMS=75

def clean(s): return re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',s or '')).strip()
def canonical(url):
 p=urlsplit(url); q=urlencode([(k,v) for k,v in parse_qsl(p.query) if not k.startswith('utm_')]);return urlunsplit((p.scheme,p.netloc,p.path,q,''))
def category(s):
 s=s.lower()
 if any(w in s for w in ('transfer','signing','signs','contract','deal','mercato','transfert')):return 'transfers'
 if any(w in s for w in ('injury','injured','fitness','sidelined')):return 'injuries'
 if any(w in s for w in ('champions league','world cup','europa','tournament','ligue des champions','coupe du monde','coupe d’afrique')):return 'competitions'
 return 'clubs'
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'ZeroFootNewsReader/0.1 (RSS headline links; contact site owner)'})
 with urllib.request.urlopen(req,timeout=15) as res:return res.read(3_000_000)
def main():
 items=[]; errors=[]; seen=set()
 for source,url,language in SOURCES:
  try:
   root=ET.fromstring(fetch(url))
   entries=root.findall('.//item')
   source_count=0
   for e in entries[:70]:
    title=clean(e.findtext('title')); link=canonical((e.findtext('link') or '').strip()); date=e.findtext('pubDate')
    if not title or not link.startswith('https://'):continue
    if source in {'France 24','RFI Sports'} and not (
        '/sports/' in urlsplit(link).path
        and (topics(title) or re.search(r"\b(football|fifa|uefa|champions league|ligue des champions|can 20\d{2}|footballeur[s]?)\b",title,re.I))
    ):continue
    key=hashlib.sha256(re.sub(r'\W+','',title.lower()).encode()).hexdigest()[:16]
    if key in seen:continue
    seen.add(key)
    try: dt=parsedate_to_datetime(date).astimezone(timezone.utc).isoformat()
    except (TypeError,ValueError):dt=None
    items.append({'id':key,'title':title,'url':link,'source':source,'published_at':dt,'category':category(title),'language':language})
    source_count+=1
    if source_count>=15:break
  except Exception as exc: errors.append(f'{source}: {type(exc).__name__}: {exc}')
 now=datetime.now(timezone.utc)
 queries=[]
 try:
  trends=ET.fromstring(fetch('https://trends.google.com/trending/rss?geo=FR'))
  queries=[clean(entry.findtext('title')) for entry in trends.findall('.//item')][:100]
 except Exception as exc:
  errors.append(f'Google Trends France: {type(exc).__name__}')
 items=enrich(items,queries,now)
 items.sort(key=lambda i:i['published_at'],reverse=True)
 path=ROOT/'data/news.json'
 if not items:
  print('No valid feed entries. Existing news.json preserved. '+ '; '.join(errors));return 1
 payload={'updated_at':datetime.now(timezone.utc).isoformat(),'items':items[:MAX_ITEMS], 'source_errors':errors,'search_trends_fr':queries}
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(path)
 print(f'Saved {len(payload["items"])} headlines; errors: {errors}')
 return 0
if __name__=='__main__':raise SystemExit(main())

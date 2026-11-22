"""Render a crawlable French news page using collected headlines."""
import json
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from news_signals import enrich

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://footchrono.com/actualites/'
TITLE = 'Actualité football en français, mercato et grandes compétitions | FootChrono'
DESCRIPTION = ('Les titres récents du football en français. Suivez la Premier League, la Liga, '
               'la Ligue 1, la Ligue des champions, le mercato et les sujets du moment.')


def card(item):
    date = datetime.fromisoformat(item['published_at'])
    tags = ' · '.join(item['topics'])
    trend = item.get('search_trend_fr')
    metadata = ' · '.join(filter(None, [item['source'], tags, 'Recherche en hausse en France' if trend else '']))
    return (f'<article><p>{escape(metadata)} · <time datetime="{date.isoformat()}">{date:%d/%m/%Y}</time></p>'
            f'<h2><a href="{escape(item["url"], quote=True)}">{escape(item["title"])}</a></h2></article>')


def main():
    data = json.loads((ROOT / 'data/news.json').read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc)
    # Keep trend metadata produced at collection time, with the same editorial fallback for old snapshots.
    rows = enrich(data['items'], data.get('search_trends_fr', []), now)
    rows = [item for item in rows if item.get('language') == 'fr' and urlsplit(item['url']).scheme == 'https']
    rows.sort(key=lambda row: datetime.fromisoformat(row['published_at']) + timedelta(hours=row['priority']), reverse=True)
    cards = '\n'.join(map(card, rows[:30])) or '<p>Aucun titre francophone récent à afficher.</p>'
    output = ROOT / 'actualites/index.html'
    output.parent.mkdir(exist_ok=True)
    output.write_text(f'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title><meta name="description" content="{DESCRIPTION}">
<link rel="canonical" href="{URL}"><meta property="og:type" content="website">
<meta property="og:site_name" content="FootChrono"><meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESCRIPTION}"><meta property="og:url" content="{URL}"><meta property="og:locale" content="fr_FR">
<meta name="twitter:card" content="summary"><link rel="stylesheet" href="/footchrono-public.css"><script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7180571260643744" crossorigin="anonymous"></script><style>.fc-ad{{width:calc(100% - 32px);max-width:728px;margin:16px auto}}.fc-ad:has(ins[data-ad-status="unfilled"]){{display:none}}</style></head><body><header class="fc-header"><div class="fc-header-inner"><a class="fc-brand" href="/" aria-label="FootChrono, accueil"><span class="fc-mark" aria-hidden="true">F</span><span>Foot<b>Chrono</b></span></a><nav class="fc-nav" aria-label="Navigation principale"><a href="/">Accueil</a><a href="/scores">Scores</a><a href="/classements">Classements</a><a href="/#page=predictions">Pronostics</a><a href="/actualites/" aria-current="page">Actualités</a></nav></div></header><main><h1>Actualité football en français</h1>
<p>Les derniers titres des médias sur les grands championnats, les coupes internationales et le mercato.</p>
<p><a href="/#page=news">Ouvrir le fil avec les filtres</a></p>
<div class="fc-news-grid">{cards}</div></main>
<div class="fc-ad"><ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-7180571260643744" data-ad-slot="1991336459" data-ad-format="horizontal" data-full-width-responsive="false"></ins></div>
<script>(window.adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</body></html>
''', encoding='utf-8')


if __name__ == '__main__':
    main()

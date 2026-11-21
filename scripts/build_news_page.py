"""Render a crawlable French news page using collected headlines."""
import json
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

from news_signals import enrich

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://zero-foot.pages.dev/actualites/'
TITLE = 'Actualité football en français, mercato et grandes compétitions | MATCHSCOPE'
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
<meta property="og:site_name" content="MATCHSCOPE"><meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESCRIPTION}"><meta property="og:url" content="{URL}"><meta property="og:locale" content="fr_FR">
<meta name="twitter:card" content="summary"><style>
*{{box-sizing:border-box}}body{{margin:0;background:#0b1727;color:#e9f1fa;font:16px/1.55 system-ui,sans-serif}}
main,header{{max-width:960px;margin:auto;padding:24px}}header{{display:flex;gap:20px;flex-wrap:wrap}}
a{{color:#84edb6;text-underline-offset:3px}}h1{{font-size:clamp(2rem,6vw,3.25rem);line-height:1.1}}
article{{padding:16px 0;border-bottom:1px solid #304159}}article p{{margin:0;color:#b1c1d1;font-size:.85rem}}
article h2{{font-size:1.15rem;margin:6px 0 0}}
</style></head><body><header><a href="/">MATCHSCOPE</a><a href="/scores">Scores et matchs</a><a href="/classements">Classements</a>
<a href="/#page=news">Fil avec filtres</a></header><main><h1>Actualité football en français</h1>
<p>Les derniers titres des médias sur les grands championnats, les coupes internationales et le mercato.</p>
{cards}</main></body></html>
''', encoding='utf-8')


if __name__ == '__main__':
    main()

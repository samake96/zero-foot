"""Rank original headlines by recency, football relevance and observed interest."""
import re
import unicodedata
from datetime import datetime, timedelta

TOPICS = {
    'Premier League': ('premier league', 'arsenal', 'chelsea', 'liverpool', 'manchester city',
                       'manchester united', 'tottenham', 'newcastle'),
    'La Liga': ('la liga', 'liga espagnole', 'real madrid', 'barcelone', 'barcelona', 'atletico madrid'),
    'Bundesliga': ('bundesliga', 'bayern', 'dortmund', 'leverkusen'),
    'Serie A': ('serie a', 'juventus', 'ac milan', 'inter milan', 'napoli', 'naples', 'as roma'),
    'Ligue 1': ('ligue 1', 'psg', 'paris saint germain', 'marseille', 'olympique lyonnais', 'as monaco'),
    'Ligue des champions': ('ligue des champions', 'champions league'),
    'Sélections': ('coupe du monde', 'world cup', 'ligue des nations', 'nations league', 'can 2027'),
}


def normalized(text):
    value = unicodedata.normalize('NFKD', text.casefold())
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return ' '.join(re.findall(r'\w+', value))


def topics(title):
    text = f' {normalized(title)} '
    return [label for label, terms in TOPICS.items() if any(f' {term} ' in text for term in terms)]


def enrich(rows, queries, now):
    active = []
    for row in rows:
        date = row.get('published_at')
        if not date:
            continue
        published = datetime.fromisoformat(date)
        if not now - timedelta(days=7) <= published <= now:
            continue
        text = f' {normalized(row["title"])} '
        row['topics'] = topics(row['title'])
        age_hours = (now - published).total_seconds() / 3600
        # Single-word queries are too ambiguous to label an article as trending.
        matches = [query for query in queries if len(normalized(query).split()) >= 2
                   and f' {normalized(query)} ' in text and age_hours <= 48]
        if matches:
            row['search_trend_fr'] = matches[0]
        row['priority'] = ((12 if row['topics'] else 0)
                           + (8 if row.get('category') in {'transfers', 'injuries'} else 0)
                           + (24 if matches else 0))
        active.append(row)
    return active

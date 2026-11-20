#!/usr/bin/env python3
"""Regression tests for reviewed API-Football / football-data.org team names."""
import unittest
from generate_live_predictions import norm

PAIRS = [
    ("Espanyol", "RCD Espanyol de Barcelona"),
    ("Alaves", "Deportivo Alavés"),
    ("Como", "Como 1907"),
    ("Cagliari", "Cagliari Calcio"),
    ("Lazio", "SS Lazio"),
    ("Lecce", "US Lecce"),
    ("1899 Hoffenheim", "TSG 1899 Hoffenheim"),
    ("Union Berlin", "1. FC Union Berlin"),
    ("Bournemouth", "AFC Bournemouth"),
    ("Leeds", "Leeds United FC"),
    ("Parma", "Parma Calcio 1913"),
    ("Newcastle", "Newcastle United FC"),
    ("Napoli", "SSC Napoli"),
    ("Torino", "Torino FC"),
    ("Auxerre", "AJ Auxerre"),
    ("Le Havre", "Le Havre AC"),
    ("Monaco", "AS Monaco FC"),
    ("Bayer Leverkusen", "Bayer 04 Leverkusen"),
    ("RB Leipzig", "RB Leipzig"),
    ("Tottenham", "Tottenham Hotspur FC"),
]

class IdentityTests(unittest.TestCase):
    def test_verified_aliases(self):
        for fixture, historical in PAIRS:
            with self.subTest(fixture=fixture):
                self.assertEqual(norm(fixture), norm(historical))
    def test_distinct_clubs_not_conflated(self):
        for club in ("Coventry", "Estac Troyes", "SC Paderborn 07", "SV Elversberg", "FC Schalke 04", "Ipswich", "Deportivo La Coruna"):
            self.assertNotEqual(norm(club), norm("Arsenal FC"))

if __name__ == "__main__":
    unittest.main()

import json
import argparse
from dataclasses import asdict

from scraping.vlrscraper import VLRScraper

parser = argparse.ArgumentParser(description="vlr.gg scraper")
parser.add_argument("--outpath", "-o", type=str, help="Path for output file")
args = parser.parse_args()

# Initializing scraper object
scraper = VLRScraper()

# Event IDs from big tournaments (Masters, VCT Challengers, Champions...)
event_ids = [
    1015, 1111, 1130, 1117, 1083, 1084, 1014, 1113, 1085, 1086, 800, 911, 984, 1063,
    1013, 998, 988, 983, 1012, 882, 991, 972, 926
]

# Getting all match IDs from all events
events = [scraper.get_event_matches(event_id) for event_id in event_ids]
match_ids = [match.id for event in events for match in event]
print(f"Scraping {len(match_ids)} matches")

# Clearing output file
open(args.outpath, "w+", encoding="utf-8").close()

# Scraping all matches
with open(args.outpath, "a", encoding="utf-8") as f:
    for i, match_id in enumerate(match_ids):
        print(f" > Scraping match {match_id} ({i + 1:05d} / {len(match_ids):05d})")
        match_games = scraper.get_match_info(match_id)
        for game_info in match_games:
            f.write(json.dumps(asdict(game_info)) + "\n")

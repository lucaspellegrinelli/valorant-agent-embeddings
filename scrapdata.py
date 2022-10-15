import json
import argparse
import threading
import concurrent.futures
from dataclasses import asdict

from scraping.vlrscraper import VLRScraper

parser = argparse.ArgumentParser(description="vlr.gg scraper")
parser.add_argument("--outpath", "-o", type=str, help="Path for output file")
parser.add_argument("--threads", "-t", default=12, type=int, help="Number of threads to be used")
args = parser.parse_args()

# Scraping all matches
def process_match(i, match_id, file):
    """Scrapes a match and writes it to a file"""

    print(f" > Scraping match {match_id} ({i + 1:05d} / {len(match_ids):05d})")

    try:
        match_games = scraper.get_match_info(match_id)
        file_lock.acquire()
        for game_info in match_games:
            file.write(json.dumps(asdict(game_info)) + "\n")
        file_lock.release()
    except TypeError:
        print(f"   > Error scraping match {match_id}. Skipping...")

def main():
    """Main function"""

    print(f"Scraping {len(match_ids)} matches")

    # Clearing output file
    open(args.outpath, "w+", encoding="utf-8").close()

    # Scraping matches
    with open(args.outpath, "a", encoding="utf-8") as f:
        thread_data = ((i, match_id, f) for i, match_id in enumerate(match_ids))
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            executor.map(lambda x: process_match(*x), thread_data)

if __name__ == "__main__":
    # Initializing scraper object
    scraper = VLRScraper()

    # Event IDs from big tournaments (Masters, VCT Challengers, Champions...)
    event_ids = [
        1015, 1111, 1130, 1117, 1083, 1084, 1014, 1113, 1085, 1086, 800, 911, 984, 1063,
        1013, 998, 988, 983, 1012, 882, 991, 972, 926
    ]

    # Getting all match IDs from all events
    print("Getting match IDs")
    events = [scraper.get_event_matches(event_id) for event_id in event_ids]
    match_ids = [match.id for event in events for match in event]

    # Lock for writing to file
    file_lock = threading.Lock()

    main()
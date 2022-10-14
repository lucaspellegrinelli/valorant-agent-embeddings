import json
from dataclasses import dataclass, asdict
from matches import Matches
from events import Events
from typing import List

@dataclass()
class TeamMember:
    agent: str
    acs: int
    kills: int
    deaths: int
    assists: int
    adr: int
    fb: int
    fd: int
    
@dataclass
class Composition:
    match_id: str
    map: str
    a_score: int
    b_score: int
    a_team: List[TeamMember]
    b_team: List[TeamMember]

event_ids = [
    1015, 1111, 1130, 1117, 1083, 1084, 1014, 1113, 1085, 1086, 800, 911, 984, 1063,
    1013, 998, 988, 983, 1012, 882, 991, 972, 926
]

def get_match_ids(event_id):
    print("Loading data from event", event_id)

    events = Events()
    event_data = events.event(str(event_id))
    event_days = event_data["matches"]
    event_match_ids = []
    for day in event_days:
        for match in day["matches"]:
            event_match_ids.append(match["id"])
    return event_match_ids

all_match_ids = []
for event_id in event_ids:
    all_match_ids += get_match_ids(event_id)

print(all_match_ids)

open("comps.jsonl", "w+").close()
for match_id in all_match_ids:
    print("Loading data from match", match_id)

    try:
        match_data = Matches.match(match_id)
        for map_data in match_data:
            map = map_data["map"]

            if map == "All Maps":
                continue

            team_a = map_data["teams"][0]["name"]
            team_b = map_data["teams"][1]["name"]
            a_score = map_data["teams"][0]["score"]
            b_score = map_data["teams"][1]["score"]

            a_team = []
            b_team = []

            for i in range(5):
                member = map_data["members"]
                a_team.append(TeamMember(
                    member[i]["agents"][0]["name"],
                    member[i]["acs"],
                    member[i]["kills"],
                    member[i]["deaths"],
                    member[i]["assists"],
                    member[i]["adr"],
                    member[i]["fb"],
                    member[i]["fd"]
                ))

                b_team.append(TeamMember(
                    member[i+5]["agents"][0]["name"],
                    member[i+5]["acs"],
                    member[i+5]["kills"],
                    member[i+5]["deaths"],
                    member[i+5]["assists"],
                    member[i+5]["adr"],
                    member[i+5]["fb"],
                    member[i+5]["fd"]
                ))

            composition = Composition(match_id, map, a_score, b_score, a_team, b_team)
            composition_dict = asdict(composition)
            
            with open("comps.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(composition_dict) + "\n")
    except:
        continue
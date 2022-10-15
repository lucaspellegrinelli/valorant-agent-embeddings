import requests
from bs4 import BeautifulSoup

from scraping.datamodels import Match, TeamGameResult, PlayerGameResult, GameResult

class VLRScraper:
    def __init__(self):
        pass

    def get_match_info(self, match_id: int):
        """Get info of a specific match from VLR.gg"""

        # Download match page and parse it
        target_url = f"https://www.vlr.gg/{match_id}"
        content = requests.get(target_url).content
        soup = BeautifulSoup(content, "html.parser")

        # Get team names
        match_header = soup.find("div", { "class": "match-header-vs" })
        [team_a_name, team_b_name] = [tn.get_text().strip() for tn in match_header.find_all("div", { "class": "wf-title-med" })]

        # Get played maps
        stats_html = soup.find("div", { "class": "vm-stats" })
        match_maps = self._get_match_played_maps(stats_html)

        # Get game results
        game_results: list[GameResult] = []
        for played_map in stats_html.find_all("div", { "class": "vm-stats-game"}):
            game_id = played_map["data-game-id"]
            if game_id == "all":
                continue

            # Get team scores
            [score_a, score_b] = [s.get_text().strip() for s in played_map.find_all("div", { "class": "score" })]
            map_name = next((mm["map_name"] for mm in match_maps if mm["game_id"] == game_id), None)

            # Get player game stats/info
            team_a_players = []
            team_b_players = []
            scoreboard_table_html = played_map.find_all("tbody")
            for team_i, row_html in enumerate(scoreboard_table_html):
                for player_html in row_html.find_all("tr"):
                    item = self._get_player_game_result(player_html)
                    if team_i == 0:
                        team_a_players.append(item)
                    else:
                        team_b_players.append(item)

            if len(team_a_players) != 5 or len(team_b_players) != 5:
                continue

            game_result = GameResult(
                match_id=match_id,
                game_id=game_id,
                map_name=map_name,
                team_a=TeamGameResult(team=team_a_name, score=score_a, players=team_a_players),
                team_b=TeamGameResult(team=team_b_name, score=score_b, players=team_b_players),
            )

            game_results.append(game_result)

        return game_results

    def get_event_matches(self, event_id: int):
        """Get all matches of a specific event from VLR.gg"""

        # Download event page and parse it
        target_url = f"https://www.vlr.gg/event/matches/{event_id}/?series_id=all"
        content = requests.get(target_url).content
        soup = BeautifulSoup(content, "html.parser")

        # Get matches info
        matches: list[Match] = []
        dates = soup.find_all("div", { "class": "wf-label mod-large" })
        for (day, date) in enumerate(dates):
            date = date.get_text().strip()
            matches_on_day = soup.find_all("div", { "class": "wf-card" })[day + 1]
            matches.extend(self._get_matches(matches_on_day, date))

        return matches

    def _get_player_game_result(self, player_html):
        def get_stat(html, i: int):
            target_stat_html = html.find_all("td", { "class": "mod-stat" })[i]
            target_stat_span = target_stat_html.find("span", { "class": "stats-sq" })

            atk_stat = target_stat_span.find("span", { "class": "mod-t" }).get_text().strip()
            def_stat = target_stat_span.find("span", { "class": "mod-ct" }).get_text().strip()

            atk_stat = int(atk_stat.replace("%", "")) if atk_stat else 0
            def_stat = int(def_stat.replace("%", "")) if def_stat else 0
            return { "atk": atk_stat, "def": def_stat }

        player_info = player_html.find("td", { "class": "mod-player" })
        team_name = player_info.find("div", { "class": "ge-text-light" }).get_text().strip()
        agent_name = player_html.find("td", { "class": "mod-agents" }).find("img")["title"]
        player_name = player_info.find("div", { "class": "text-of" }).get_text().strip()

        stats = {
            "acs": get_stat(player_html, 0),
            "kills": get_stat(player_html, 1),
            "deaths": get_stat(player_html, 2),
            "assists": get_stat(player_html, 3),
            "kast": get_stat(player_html, 5),
            "adr": get_stat(player_html, 6),
            "hs": get_stat(player_html, 7),
            "fk": get_stat(player_html, 8),
            "fd": get_stat(player_html, 9),
        }

        return PlayerGameResult(player=player_name, team=team_name, agent=agent_name, **stats)

    def _get_match_played_maps(self, stats_html):
        match_maps = []
        for played_map in stats_html.find_all("div", {"class": "vm-stats-gamesnav-item" }):
            game_id = played_map["data-game-id"]
            if game_id == "all":
                continue

            map_name = played_map.get_text().strip().replace("\n", "").replace("\t", "")
            map_name = "".join(c for c in map_name if not c.isdigit())
            match_maps.append({ "game_id": game_id, "map_name": map_name })
        return match_maps

    def _get_matches(self, matches_html, date):
        match_list: list[Match] = []

        matches_list = matches_html.find_all("a", { "class": "match-item" })
        for match_html in matches_list:
            match_id = match_html["href"].split("/")[1]
            match_time = match_html.find("div", { "class": "match-item-time" }).get_text().strip()
            match_status = match_html.find("div", { "class": "ml-status" }).get_text().strip()
            
            match_round = match_html.find("div", { "class": "match-item-event text-of" }).get_text().strip().split("\n")[0].strip()
            match_stage = match_html.find("div", { "class": "match-item-event text-of" }).get_text().strip().split("\n")[1].strip()

            match_teams = []
            teams_html = match_html.find_all("div", { "class": "match-item-vs-team" })
            for team_html in teams_html:
                name = team_html.find("div", { "class": "match-item-vs-team-name" }).get_text().strip()
                match_teams.append(name)

            match_list.append(Match(
                id=match_id,
                date=date,
                time=match_time,
                status=match_status,
                round=match_round,
                stage=match_stage,
                teams=match_teams
            ))
            
        return match_list
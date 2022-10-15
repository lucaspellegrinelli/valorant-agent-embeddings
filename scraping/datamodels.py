from dataclasses import dataclass

@dataclass
class Match:
    id: str
    date: str
    time: str
    status: str
    round: str
    stage: str
    teams: list[str]

@dataclass
class PlayerGameResult:
    player: str
    team: str
    agent: str
    acs: int
    kills: int
    deaths: int
    assists: int
    kast: float
    adr: int
    hs: int
    fk: int
    fd: int

@dataclass
class TeamGameResult:
    team: str
    score: int
    players: list[PlayerGameResult]

@dataclass
class GameResult:
    match_id: int
    game_id: int
    map_name: str
    team_a: TeamGameResult
    team_b: TeamGameResult
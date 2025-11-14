from dataclasses import dataclass, field

CASHPOOL = 450

@dataclass
class Record:

    """
    Specific records on a on track
    """

    player: str
    score: str
    place: str
    points: str

@dataclass
class TrackBoard:

    """
    All record on ONE track
    """

    name: str
    table: list[Record]
    table_headers: list[str] = field(default_factory=lambda: ["TrackName", "PlayerName", "Score", "Place", "Points"])


@dataclass
class LeaderboardEntry:

    """
    Send out the leaderboard
    """
    player: str
    points: int
    cash: str

@dataclass
class KarmaEntry:

    """
    Votes class
    """

    track: str
    karma: str
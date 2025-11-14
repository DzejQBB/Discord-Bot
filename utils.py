import string
import re

from models import Record, TrackBoard, LeaderboardEntry, CASHPOOL, KarmaEntry

LIST_TM_FORMAT = [
    '\$[0-9a-fA-F]{3}',
    '\$w',
    '\$n',
    '\$m',
    '\$i',
    '\$t',
    '\$o',
    '\$s',
    '\$g',
    '\$z'
]

def clean_tm_formatting(text: str) -> str:

    for format in LIST_TM_FORMAT:
        text = re.sub(format, '', text)

    n_text = ""
    for char in text:
        if char in string.printable:
            n_text+=char
    n_text = n_text.strip()
    return n_text

def create_trackboards(fetchall) -> list[TrackBoard]:

    tabular = [list(x) for x in fetchall] # SQL list tuple output
    tables = []

    last_track = ""
    track_table = []

    # First put together same tracks in one table
    for i in range(1, len(tabular)):

        if last_track != tabular[i][0]:
            track_table = []
            track_table.append(tabular[i])
            last_track = tabular[i][0]
        else:
            track_table.append(tabular[i])
            continue

        tables.append(track_table)

    # Second convert these into objects
    list_trackboards = []
    for table in tables:

        records = []
        for record in table:
            
            obj_record = Record(
                player=clean_tm_formatting(record[1]),
                score=f'{int(record[2])/1000:.2f}',
                place=record[3],
                points=record[4]
            )
            records.append(obj_record)

        track_obj = TrackBoard(
            name=clean_tm_formatting(table[0][0]),
            table=records
        )

        list_trackboards.append(track_obj)

    return list_trackboards


def create_leaderboard(fetchall) -> list[LeaderboardEntry]:

    tabular = [list(x) for x in fetchall]

    # Sum of the first 3 places
    points_sum = sum([int(x[2]) for x in tabular[:3]])

    leaderboard = []
    for i, rank in enumerate(tabular):

        leaderboard.append(LeaderboardEntry(
            player=clean_tm_formatting(rank[0]),
            points=int(rank[2]),
            cash=f"{round(int(rank[2])*(CASHPOOL/points_sum),0)} CZK" if i < 3 else "0 CZK"
        ))

    return leaderboard


def create_karma_leaderboard(fetchall) -> list[KarmaEntry]:

    tabular = [list(x) for x in fetchall]

    karma_leaderboard = []
    for rank in tabular:

        karma_leaderboard.append(KarmaEntry(
                track=clean_tm_formatting(rank[0]),
                karma=rank[1]
        ))

    return karma_leaderboard
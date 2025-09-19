import csv
from pathlib import Path

from .wrapper import Follower


def write(followers: list[Follower], path: Path) -> None:
    with path.open("w+", newline="") as f:
        writer = csv.DictWriter(
            f,
            quoting=csv.QUOTE_NOTNULL,
            fieldnames=[*Follower.__required_keys__, *Follower.__optional_keys__],
        )
        writer.writeheader()
        writer.writerows(followers)

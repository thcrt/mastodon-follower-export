import csv
from inspect import get_annotations
from pathlib import Path

from .wrapper import Follower


def write(followers: list[Follower], path: Path) -> None:
    with path.open("w+", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            quoting=csv.QUOTE_NOTNULL,
            fieldnames=get_annotations(Follower).keys(),
        )
        writer.writeheader()
        writer.writerows(followers)

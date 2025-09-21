import csv
from dataclasses import asdict, fields
from pathlib import Path

from .wrapper import Follower


def write(followers: list[Follower], path: Path) -> None:
    with path.open("w+", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            quoting=csv.QUOTE_NOTNULL,
            fieldnames=[field.name for field in fields(Follower)],
        )
        writer.writeheader()
        writer.writerows([asdict(follower) for follower in followers])

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import csv
from dataclasses import asdict, fields
from typing import TYPE_CHECKING

from .wrapper import Follower

if TYPE_CHECKING:
    from pathlib import Path
    from typing import IO


def write(followers: list[Follower], f: "IO[str]", header: bool = True) -> None:
    writer = csv.DictWriter(
        f,
        quoting=csv.QUOTE_NOTNULL,
        fieldnames=[field.name for field in fields(Follower)],
    )
    if header:
        writer.writeheader()
    writer.writerows([asdict(follower) for follower in followers])


def write_file(followers: list[Follower], path: "Path", header: bool = True) -> None:
    with path.open("w+", newline="", encoding="utf-8") as f:
        write(followers, f, header)

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import functools
import sys
from collections.abc import Callable
from dataclasses import astuple, fields
from enum import StrEnum, auto
from io import StringIO
from pathlib import Path
from sys import exit as sys_exit
from typing import Annotated, ParamSpec, TypeVar

from mastodon import MastodonIllegalArgumentError, MastodonNetworkError
from rich import print  # noqa: A004
from rich.prompt import Prompt
from rich.table import Table
from typer import Argument, Option, Typer

from .wrapper import Follower, Mastodon
from .writer import write

app = Typer()
api = Mastodon()


class OutputMode(StrEnum):
    fancy = auto()
    csv = auto()
    auto = auto()


def error(msg: str, e: Exception, hint: str | None = None) -> None:
    print(f"[red b]{msg} [/red b]{f'[b]{hint}[/b] ' if hint else ''}[i bright_black]{e.args[0]}")


P = ParamSpec("P")
T = TypeVar("T")


def handle_mastodon(f: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return f(*args, **kwargs)
        except MastodonNetworkError as e:
            error(
                "Error communicating with the server!",
                e,
                "Make sure that's the address of a server compatible with the Mastodon API.",
            )
            sys_exit(1)

    return wrapper


@app.command()
@handle_mastodon
def login(
    instance_domain: Annotated[str, Argument(help="The domain name of the instance to log in to")],
    force: Annotated[
        bool, Option("--force", "-f", help="Log from scratch, whether already logged in or not")
    ] = False,
) -> int:
    api.instance_domain = instance_domain
    if force or not api.authed:
        url = api.get_auth_url()
        print("To log in, visit the following link:")
        print(f"[b]{url}")
        print()
        print("Then enter the code you get below.")
        while True:
            code = Prompt.ask("Code")
            try:
                api.auth(code)
                api.get_current_user()
                break
            except MastodonIllegalArgumentError as e:
                error("Incorrect code!", e)
                sys_exit(1)
    print(f"Logged in to [b]{api.instance_domain}[/b] as [b]{api.get_current_user()}[/b].")
    return 0


@app.command("list")
@handle_mastodon
def list_followers(
    mode: Annotated[
        OutputMode,
        Option("--mode", "-m", help="Output an ASCII table [b](fancy)[/b] or a CSV [b](csv)[/b]"),
    ] = OutputMode.auto,
    no_header: Annotated[bool, Option("--no-header", "-H", help="Remove the header line")] = True,
    output: Annotated[Path | None, Option("--output", "-o", help="Output to a file")] = None,
) -> None:
    header = not no_header
    interactive = sys.stdout.isatty() and output is None
    if mode == OutputMode.auto:
        mode = OutputMode.fancy if interactive else OutputMode.csv

    if mode == OutputMode.fancy:
        table = Table(title=f"Followers for user [b]{api.get_current_user()}", show_header=header)
        for field in fields(Follower):
            table.add_column(field.metadata["display"])
        for follower in api.get_followers():
            cells: list[str] = []
            for field in astuple(follower):
                if isinstance(field, bool):
                    cells.append("[green]yes" if field else "[red]no")
                else:
                    cells.append(str(field))
            table.add_row(*cells)
        buffer = StringIO()
        print(table, file=buffer)

    else:
        buffer = StringIO(newline="")
        write(api.get_followers(), buffer, header)

    output.write_text(buffer.getvalue(), "utf-8") if output else print(buffer.getvalue())

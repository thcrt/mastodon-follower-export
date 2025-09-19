# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from importlib.metadata import version
from typing import TYPE_CHECKING, TypedDict

from mastodon import Mastodon as MastodonAPI
from PySide6.QtGui import QDesktopServices

from . import __version__

if TYPE_CHECKING:
    from mastodon.return_types import Account
    from mastodon.types_base import PaginatableList


class Follower(TypedDict):
    username: str
    display_name: str
    note: str
    url: str
    mutual: bool


class Mastodon:
    scopes: list[str]
    instance_domain: str | None = None
    _user_agent = (
        f"mastodon-follower-export {__version__}, using mastodonpy {version('mastodon.py')}"
    )
    _client_id: str | None = None
    _client_secret: str | None = None
    _access_token: str | None = None

    def __init__(self) -> None:
        self.scopes = ["read:accounts", "read:follows"]

    def create_app(self, instance_domain: str) -> None:
        self.instance_domain = instance_domain
        self._client_id, self._client_secret = MastodonAPI.create_app(  # pyright: ignore[reportUnknownMemberType]
            "Mastodon Follower Export",
            api_base_url=instance_domain,
            scopes=self.scopes,
            user_agent=self._user_agent,
        )

    def prompt_auth(self) -> None:
        QDesktopServices.openUrl(
            MastodonAPI(
                api_base_url=self.instance_domain,
                client_id=self._client_id,
                client_secret=self._client_secret,
            ).auth_request_url(scopes=self.scopes)
        )

    def auth(self, code: str) -> None:
        self._access_token = MastodonAPI(
            api_base_url=self.instance_domain,
            client_id=self._client_id,
            client_secret=self._client_secret,
        ).log_in(
            code=code,
            scopes=self.scopes,
        )

    def get_followers(self) -> list[Follower]:
        api = MastodonAPI(
            api_base_url=self.instance_domain,
            access_token=self._access_token,
        )
        followers_response: PaginatableList[Account] = api.fetch_remaining(  # pyright: ignore[reportAssignmentType]
            api.account_followers(api.me())  # pyright: ignore[reportArgumentType]
        )
        followers: list[Follower] = []
        for follower in followers_response:
            rel = api.account_relationships(follower)[0]
            followers.append(
                Follower(
                    username=follower.acct,
                    display_name=follower.display_name,
                    note=rel.note.replace("\n", "\\n"),
                    url=follower.url,
                    mutual=rel.following,
                )
            )
        return followers

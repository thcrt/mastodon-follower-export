# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from dataclasses import dataclass
from importlib.metadata import version
from typing import TYPE_CHECKING

import keyring
from mastodon import Mastodon as MastodonAPI
from mastodon import MastodonError
from PySide6.QtGui import QDesktopServices

from . import __version__

if TYPE_CHECKING:
    from mastodon.return_types import Account
    from mastodon.types_base import PaginatableList


@dataclass
class Follower:
    username: str
    display_name: str
    note: str
    url: str
    mutual: bool


class Mastodon:
    scopes: list[str]
    _user_agent = (
        f"mastodon-follower-export {__version__}, using mastodonpy {version('mastodon.py')}"
    )

    def __init__(self) -> None:
        self.scopes = ["read:accounts", "read:follows"]

    @property
    def instance_domain(self) -> str | None:
        return keyring.get_password("mastodon_follower_export", "instance_domain")

    @instance_domain.setter
    def instance_domain(self, v: str) -> None:
        keyring.set_password("mastodon_follower_export", "instance_domain", v)

    @property
    def client_id(self) -> str | None:
        return keyring.get_password("mastodon_follower_export", "client_id")

    @client_id.setter
    def client_id(self, v: str) -> None:
        keyring.set_password("mastodon_follower_export", "client_id", v)

    @property
    def client_secret(self) -> str | None:
        return keyring.get_password("mastodon_follower_export", "client_secret")

    @client_secret.setter
    def client_secret(self, v: str) -> None:
        keyring.set_password("mastodon_follower_export", "client_secret", v)

    @property
    def access_token(self) -> str | None:
        return keyring.get_password("mastodon_follower_export", "access_token")

    @access_token.setter
    def access_token(self, v: str) -> None:
        keyring.set_password("mastodon_follower_export", "access_token", v)

    @property
    def needs_reauth(self) -> bool:
        if self.instance_domain is None or self.access_token is None:
            return True
        try:
            _ = self.get_current_user()
        except MastodonError:
            return True
        return False

    def create_app(self, instance_domain: str) -> None:
        self.instance_domain = instance_domain
        self.client_id, self.client_secret = MastodonAPI.create_app(
            "Mastodon Follower Export",
            api_base_url=instance_domain,
            scopes=self.scopes,
            user_agent=self._user_agent,
        )

    def prompt_auth(self) -> None:
        QDesktopServices.openUrl(
            MastodonAPI(
                api_base_url=self.instance_domain,
                client_id=self.client_id,
                client_secret=self.client_secret,
            ).auth_request_url(scopes=self.scopes)
        )

    def auth(self, code: str) -> None:
        self.access_token = MastodonAPI(
            api_base_url=self.instance_domain,
            client_id=self.client_id,
            client_secret=self.client_secret,
        ).log_in(
            code=code,
            scopes=self.scopes,
        )

    def get_current_user(self) -> str:
        user = MastodonAPI(
            api_base_url=self.instance_domain,
            access_token=self.access_token,
        ).account_verify_credentials()
        return f"@{user.username}@{self.instance_domain}"

    def get_followers(self) -> list[Follower]:
        api = MastodonAPI(
            api_base_url=self.instance_domain,
            access_token=self.access_token,
        )
        followers_response: PaginatableList[Account] = api.fetch_remaining(
            api.account_followers(api.me())
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

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from dataclasses import dataclass, field
from importlib.metadata import version
from typing import TYPE_CHECKING

import keyring
from mastodon import Mastodon as MastodonAPI
from mastodon import MastodonError

from . import __version__

if TYPE_CHECKING:
    from mastodon.return_types import Account
    from mastodon.types_base import PaginatableList


@dataclass
class Follower:
    username: str = field(metadata={"display": "Username"})
    display_name: str = field(metadata={"display": "Display name"})
    note: str = field(metadata={"display": "Note"})
    url: str = field(metadata={"display": "URL"})
    mutual: bool = field(metadata={"display": "Mutual"})


class Mastodon:
    _name = "Mastodon Follower Export"
    _scopes: list[str]
    _user_agent = (
        f"mastodon-follower-export {__version__}, using mastodonpy {version('mastodon.py')}"
    )

    def __init__(self) -> None:
        self._scopes = ["read:accounts", "read:follows"]

    @property
    def instance_domain(self) -> str | None:
        c = keyring.get_credential("mastodon-follower-export/instance-domain", None)
        return c.password if c else None

    @instance_domain.setter
    def instance_domain(self, v: str) -> None:
        keyring.set_password("mastodon-follower-export/instance-domain", "", v)
        if not (self._client_id and self._client_secret):
            self._client_id, self._client_secret = MastodonAPI.create_app(  # pyright: ignore[reportUnknownMemberType]
                self._name,
                api_base_url=self.instance_domain,
                scopes=self._scopes,
                user_agent=self._user_agent,
            )

    @property
    def is_logged_in(self) -> bool:
        if self.instance_domain and self._access_token:
            try:
                _ = self.get_current_user()
            except MastodonError:
                pass
            else:
                return True
        return False

    def get_auth_url(self) -> str:
        return MastodonAPI(
            api_base_url=self.instance_domain,
            user_agent=self._user_agent,
            client_id=self._client_id,
            client_secret=self._client_secret,
        ).auth_request_url(scopes=self._scopes)

    def _keyring_lookup(self, key: str) -> None | str:
        if not self.instance_domain:
            return None
        c = keyring.get_credential(f"mastodon-follower-export/{key}/{self.instance_domain}", None)
        return c.password if c else None

    def _keyring_set(self, key: str, v: str) -> None:
        if not self.instance_domain:
            msg = "Missing instance domain. This shouldn't happen!"
            raise RuntimeError(msg)
        keyring.set_password(f"mastodon-follower-export/{key}/{self.instance_domain}", "", v)

    @property
    def _client_id(self) -> str | None:
        return self._keyring_lookup("client-id")

    @_client_id.setter
    def _client_id(self, v: str) -> None:
        self._keyring_set("client-id", v)

    @property
    def _client_secret(self) -> str | None:
        return self._keyring_lookup("client-secret")

    @_client_secret.setter
    def _client_secret(self, v: str) -> None:
        self._keyring_set("client-secret", v)

    @property
    def _access_token(self) -> str | None:
        return self._keyring_lookup("access-token")

    @_access_token.setter
    def _access_token(self, v: str) -> None:
        self._keyring_set("access-token", v)

    def auth(self, code: str) -> None:
        self._access_token = MastodonAPI(
            api_base_url=self.instance_domain,
            client_id=self._client_id,
            client_secret=self._client_secret,
        ).log_in(
            code=code,
            scopes=self._scopes,
        )

    def get_current_user(self) -> str:
        user = MastodonAPI(
            api_base_url=self.instance_domain,
            access_token=self._access_token,
        ).account_verify_credentials()
        return f"@{user.username}@{self.instance_domain}"

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
                    note=rel.note,
                    url=follower.url,
                    mutual=rel.following,
                )
            )
        return followers

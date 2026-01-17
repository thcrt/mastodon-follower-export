# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from PySide6.QtCore import (
    QObject,
    QRunnable,
    Signal,
    Slot,
)

from mastodon_follower_export.wrapper import Mastodon


class GetFollowersWorker(QRunnable):
    class Signals(QObject):
        result = Signal(tuple)

    def __init__(self, api: Mastodon) -> None:
        super().__init__()
        self.api = api
        self.signals = GetFollowersWorker.Signals()

    @Slot()
    def run(self) -> None:
        followers = self.api.get_followers()
        self.signals.result.emit(followers)

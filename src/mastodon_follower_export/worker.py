from PySide6.QtCore import (
    QObject,
    QRunnable,
    Signal,
    Slot,
)

from .wrapper import Mastodon


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

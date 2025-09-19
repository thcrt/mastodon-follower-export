# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import datetime
from pathlib import Path
from typing import override

from mastodon import MastodonError
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from .util import CodeValidator, DomainValidator
from .wrapper import Mastodon
from .writer import write


class MainWizard(QWizard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Mastodon Follower Export")

        api = Mastodon()

        for page in (
            self.IntroPage(self, api),
            self.LoginPage(self, api),
            self.DestinationPage(self, api),
        ):
            self.addPage(page)

    class Page(QWizardPage):
        def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
            super().__init__(parent)
            self.api = api

    class IntroPage(Page):
        def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
            super().__init__(parent, api)
            self.setTitle("Introduction")
            layout = QVBoxLayout(self)

            text = QLabel(
                wordWrap=True,
                text="""This program will allow you to export a list of your Mastodon \
followers that you can save to your computer. It produces a CSV (Comma-Separated Values) file \
listing each follower's full username and profile URL.

To get started, please enter the domain name of the Mastodon instance where you have an account.
            """,
            )
            layout.addWidget(text)

            instance = QLineEdit()
            instance.setValidator(DomainValidator(self))
            layout.addWidget(instance)
            self.registerField("instance*", instance)

        @override
        def validatePage(self) -> bool:
            try:
                self.api.create_app(self.field("instance"))
            except MastodonError as e:
                QMessageBox.critical(self, "Mastodon API error", repr(e))
                return False
            return True

    class LoginPage(Page):
        def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
            super().__init__(parent, api)
            layout = QVBoxLayout(self)

            text = QLabel(
                wordWrap=True,
                text="""Sign in to the instance in the browser window that just opened, then \
enter the code here.""",
            )
            layout.addWidget(text)

            code = QLineEdit()
            code.setValidator(CodeValidator(self))
            layout.addWidget(code)
            self.registerField("token*", code)

        @override
        def initializePage(self) -> None:
            try:
                self.api.prompt_auth()
            except MastodonError as e:
                QMessageBox.critical(self, "Mastodon API error", repr(e))

        @override
        def validatePage(self) -> bool:
            try:
                self.api.auth(self.field("token"))
            except MastodonError as e:
                QMessageBox.critical(self, "Mastodon API error", repr(e))
                return False
            return True

    class DestinationPage(Page):
        def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
            super().__init__(parent, api)
            layout = QVBoxLayout(self)

            text = QLabel(
                wordWrap=True,
                text="""You were successfully logged in!

Choose the path to which your exported follower list should be saved.""",
            )
            layout.addWidget(text)

            file_select_bar = QFormLayout(self)
            layout.addLayout(file_select_bar)

            self.path_input = QLineEdit()
            file_select_bar.addWidget(self.path_input)
            self.registerField("path*", self.path_input)

            file_chooser = QFileDialog(self)
            file_chooser.selectFile(self.field("path"))
            file_chooser.setFileMode(QFileDialog.FileMode.AnyFile)
            file_chooser.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            file_chooser.currentChanged.connect(self.path_input.setText)

            file_select_button = QPushButton("Choose...", self)
            file_select_button.clicked.connect(file_chooser.open)
            file_select_bar.addWidget(file_select_button)

        @override
        def initializePage(self) -> None:
            self.path_input.setText(
                str(
                    Path(
                        f"~/followers_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
                    ).expanduser()
                )
            )

        @override
        def validatePage(self) -> bool:
            try:
                followers = self.api.get_followers()
                write(followers, Path(self.field("path")))

            except MastodonError as e:
                QMessageBox.critical(self, "Mastodon API error", repr(e))
                return False
            return True

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import override

from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from .util import DomainValidator


class MainWizard(QWizard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Mastodon Follower Export")

        for page in (
            self.IntroPage(self),
            self.LoginPage(self),
        ):
            self.addPage(page)

    class IntroPage(QWizardPage):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
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

    class LoginPage(QWizardPage):
        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            layout = QVBoxLayout(self)

            text = QLabel(wordWrap=True, text="Please log in to your instance.")
            layout.addWidget(text)

        @override
        def initializePage(self) -> None:
            pass

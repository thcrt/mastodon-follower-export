# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from datetime import datetime
from enum import IntEnum, auto
from pathlib import Path
from typing import Literal, override

from mastodon import MastodonError
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from .util import CodeValidator, DomainValidator
from .wrapper import Mastodon
from .writer import write


class PageID(IntEnum):
    Intro = auto()
    ConfirmAccount = auto()
    ChooseInstance = auto()
    GiveAuthCode = auto()
    ChooseDestination = auto()
    Finished = auto()


class Page(QWizardPage):
    def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
        super().__init__(parent)
        self.api = api


class MainWizard(QWizard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Mastodon Follower Export")

        api = Mastodon()

        self.setPage(PageID.Intro, IntroPage(self, api))
        self.setPage(PageID.ConfirmAccount, ConfirmAccountPage(self, api))
        self.setPage(PageID.ChooseInstance, ChooseInstancePage(self, api))
        self.setPage(PageID.GiveAuthCode, GiveAuthCodePage(self, api))
        self.setPage(PageID.ChooseDestination, ChooseDestinationPage(self, api))


class IntroPage(Page):
    def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
        super().__init__(parent, api)
        self.setTitle("Introduction")
        self.setSubTitle("")
        layout = QVBoxLayout(self)

        self.label_description = QLabel(textFormat=Qt.TextFormat.RichText, wordWrap=True)
        layout.addWidget(self.label_description)

    @override
    def initializePage(self) -> None:
        self.label_description.setText(f"""
            This program will allow you to export a list of your Mastodon followers that you can
            save to your computer. It produces a CSV (Comma-Separated Values) file listing each
            follower's full username and profile URL.<br />
            <br />
            Click '{self.buttonText(QWizard.WizardButton.NextButton)}' to get started.
        """)

    @override
    def nextId(self) -> PageID:
        if self.api.needs_reauth:
            return PageID.ChooseInstance
        return PageID.ConfirmAccount


class ConfirmAccountPage(Page):
    def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
        super().__init__(parent, api)
        self.setTitle("Confirm the account")
        layout = QVBoxLayout(self)

        self.label_description = QLabel(textFormat=Qt.TextFormat.RichText, wordWrap=True)
        layout.addWidget(self.label_description)

        self.radio_continue = QRadioButton("&Continue")
        self.radio_continue.setChecked(True)
        layout.addWidget(self.radio_continue)

        self.radio_reauth = QRadioButton("Sign in to a &different account")
        layout.addWidget(self.radio_reauth)

    @override
    def initializePage(self) -> None:
        self.label_description.setText(f"""
            You previously used this program while signed into the account
            <b>{self.api.get_current_user()}</b>. Do you want to continue as this account, or sign
            in to a different account?
        """)

    @override
    def nextId(self) -> PageID:
        if self.radio_continue:
            return PageID.ChooseDestination
        return PageID.ChooseInstance


class ChooseInstancePage(Page):
    def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
        super().__init__(parent, api)
        self.setTitle("Choose an instance")
        layout = QVBoxLayout(self)

        self.label_description = QLabel(textFormat=Qt.TextFormat.RichText, wordWrap=True)
        self.label_description.setText("""
            Enter the domain name of the Mastodon instance on which you have an account.
        """)
        layout.addWidget(self.label_description)

        self.line_instance = QLineEdit()
        self.line_instance.setValidator(DomainValidator(self))
        layout.addWidget(self.line_instance)
        self.registerField("instance*", self.line_instance)

    @override
    def validatePage(self) -> bool:
        try:
            self.api.create_app(self.field("instance"))
        except MastodonError as e:
            QMessageBox.critical(self, "Mastodon API error", repr(e))
            return False
        return True

    @override
    def nextId(self) -> Literal[PageID.GiveAuthCode]:
        return PageID.GiveAuthCode


class GiveAuthCodePage(Page):
    def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
        super().__init__(parent, api)
        self.setTitle("Enter authentication code")
        layout = QVBoxLayout(self)

        self.label_description = QLabel(textFormat=Qt.TextFormat.RichText, wordWrap=True)
        self.label_description.setText("""
            Sign in to the instance in the browser window that just opened, then enter the code
            here.
        """)
        layout.addWidget(self.label_description)

        self.line_code = QLineEdit()
        self.line_code.setValidator(CodeValidator(self))
        layout.addWidget(self.line_code)
        self.registerField("code*", self.line_code)

    @override
    def initializePage(self) -> None:
        try:
            self.api.prompt_auth()
        except MastodonError as e:
            QMessageBox.critical(self, "Mastodon API error", repr(e))

    @override
    def validatePage(self) -> bool:
        try:
            self.api.auth(self.field("code"))
        except MastodonError as e:
            QMessageBox.critical(self, "Mastodon API error", repr(e))
            return False
        return True

    @override
    def nextId(self) -> Literal[PageID.ChooseDestination]:
        return PageID.ChooseDestination


class ChooseDestinationPage(Page):
    def __init__(self, parent: "MainWizard", api: Mastodon) -> None:
        super().__init__(parent, api)
        self.setTitle("Choose a destination file")
        layout = QFormLayout(self)

        self.label_description = QLabel(textFormat=Qt.TextFormat.RichText, wordWrap=True)
        self.label_description.setText("""
            Enter a path, or select one in the file picker, at which to save the exported list.
        """)
        layout.addWidget(self.label_description)

        self.line_path = QLineEdit()
        layout.addWidget(self.line_path)
        self.registerField("path*", self.line_path)

        dialog = QFileDialog(self)
        dialog.selectFile(self.field("path"))
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.currentChanged.connect(self.line_path.setText)

        button_choose = QPushButton("Choose...", self)
        button_choose.clicked.connect(dialog.open)
        layout.addWidget(button_choose)

    @override
    def initializePage(self) -> None:
        self.line_path.setText(
            str(
                Path(f"~/followers_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv").expanduser()
            )
        )

    @override
    def validatePage(self) -> bool:
        try:
            write(self.api.get_followers(), Path(self.field("path")))

        except MastodonError as e:
            QMessageBox.critical(self, "Mastodon API error", repr(e))
            return False
        return True

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QDir, QStandardPaths, Qt, QThreadPool, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from mastodon_follower_export.wrapper import Mastodon
from mastodon_follower_export.writer import write_file

from .dialogs import AboutDialog, CodeDialog, InstanceDialog
from .table import FollowerTableModel, FollowerTableView
from .widgets import DisplayLabel, Throbber
from .worker import GetFollowersWorker

if TYPE_CHECKING:
    from mastodon_follower_export.wrapper import Follower


class CentralWidget(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setContentsMargins(11, 11, 11, 0)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.table_view = FollowerTableView()
        layout.addWidget(self.table_view)
        self.table_view.setVisible(False)

        self.hint_label = DisplayLabel(
            self,
            text="""
                This is where you'll see your followers. <br />
                You'll need to sign in to your Mastodon instance first.
            """,
        )
        layout.addWidget(self.hint_label)
        self.hint_label.setVisible(False)

        self.login_button = QPushButton(self)
        self.login_button.setText("Sign in")
        self.login_button.setVisible(False)
        layout.addWidget(self.login_button)

        self.data: list[Follower] = []

    @Slot()
    def fill_data(self, data: "list[Follower]") -> None:
        self.data = data
        self.table_view.setModel(FollowerTableModel(self, data))
        self.table_view.setVisible(True)
        self.hint_label.setVisible(False)
        self.login_button.setVisible(False)


class ActionStatus(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.throbber = Throbber()
        layout.addWidget(self.throbber)
        self.status = QLabel()
        layout.addWidget(self.status)


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.threadpool = QThreadPool(self)

        self.setWindowTitle("Mastodon Follower Export")

        menu_file = QMenu(self, title="&File")
        self.menuBar().addMenu(menu_file)
        menu_help = QMenu(self, title="&Help")
        self.menuBar().addMenu(menu_help)

        self.action_status = ActionStatus(self)
        self.action_status.setVisible(False)
        self.statusBar().addPermanentWidget(self.action_status, stretch=1)

        action_log_in = QAction(self, text="Sign In Again")
        action_log_in.triggered.connect(self.force_login)
        menu_file.addAction(action_log_in)

        action_change_instance = QAction(self, text="Change Instance")
        action_change_instance.triggered.connect(self.change_instance)
        menu_file.addAction(action_change_instance)

        action_refresh = QAction(self, text="Refresh List")
        action_refresh.triggered.connect(self.fill_data)
        menu_file.addAction(action_refresh)

        action_save = QAction(
            self,
            text="Save List",
            icon=QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave),
            shortcut=QKeySequence(QKeySequence.StandardKey.Save),
        )
        action_save.triggered.connect(self.save)
        menu_file.addAction(action_save)

        action_quit = QAction(
            self,
            text="Quit",
            statusTip="Quit this program",
            menuRole=QAction.MenuRole.QuitRole,
            icon=QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit),
            shortcut=QKeySequence(QKeySequence.StandardKey.Quit),
        )
        action_quit.triggered.connect(self.close)
        menu_file.addAction(action_quit)

        action_about = QAction(
            self,
            text="About",
            statusTip="About this program",
            menuRole=QAction.MenuRole.AboutRole,
            icon=QIcon.fromTheme(QIcon.ThemeIcon.HelpAbout),
        )
        action_about.triggered.connect(self.show_about)
        menu_help.addAction(action_about)

        self.central_widget = CentralWidget(self)
        self.central_widget.login_button.clicked.connect(self.login)
        self.setCentralWidget(self.central_widget)

        self.api = Mastodon()
        if self.api.authed:
            self.fill_data()
        else:
            self.central_widget.hint_label.setVisible(True)
            self.central_widget.login_button.setVisible(True)

        geometry = self.screen().availableGeometry()
        self.resize(int(geometry.width() * 0.8), int(geometry.height() * 0.8))

    def show_about(self) -> None:
        dialog = AboutDialog(self)
        dialog.show()

    @Slot()
    def force_login(self) -> None:
        self._prompt_instance()
        self._prompt_code()
        self.fill_data()

    @Slot()
    def change_instance(self) -> None:
        self._prompt_instance()
        self.fill_data()

    @Slot()
    def login(self) -> None:
        if not self.api.instance_domain:
            self._prompt_instance()
        if not self.api.check_auth():
            self._prompt_code()
        self.fill_data()

    @Slot()
    def _fill_data(self, data: "list[Follower]") -> None:
        self.central_widget.fill_data(data)
        self.action_status.setVisible(False)

    @Slot()
    def fill_data(self) -> None:
        worker = GetFollowersWorker(self.api)
        self.action_status.status.setText("Fetching followers list")
        self.action_status.setVisible(True)
        worker.signals.result.connect(self._fill_data)
        self.threadpool.start(worker)

    @Slot()
    def save(self) -> None:
        path = QFileDialog.getSaveFileName(
            self,
            dir=QDir(
                QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            ).filePath("followers.csv"),
        )[0]
        if path:
            write_file(self.central_widget.data, Path(path))

    def _prompt_instance(self) -> None:
        instance_dialog = InstanceDialog(self, previous=self.api.instance_domain)

        @Slot()
        def login_set_instance(domain: str) -> None:
            self.api.instance_domain = domain

        instance_dialog.text_updated.connect(login_set_instance)
        instance_dialog.exec()

    def _prompt_code(self) -> None:
        QDesktopServices.openUrl(self.api.get_auth_url())
        code_dialog = CodeDialog(self)

        @Slot()
        def login_update_auth(code: str) -> None:
            self.api.auth(code)

        code_dialog.text_updated.connect(login_update_auth)
        code_dialog.exec()

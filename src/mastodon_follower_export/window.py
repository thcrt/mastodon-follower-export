# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .dialogs import AboutDialog, CodeDialog, InstanceDialog
from .table import FollowerTableModel, FollowerTableView
from .widgets import DisplayLabel, Throbber
from .wrapper import Mastodon

if TYPE_CHECKING:
    from .wrapper import Follower


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

        self.login_button = QPushButton(self)
        self.login_button.setText("Sign in")
        layout.addWidget(self.login_button)

    def fill_data(self, data: "list[Follower]") -> None:
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

        action_refresh = QAction(self, text="Refresh List")
        action_refresh.triggered.connect(self.fill_data)
        menu_file.addAction(action_refresh)

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
    def login(self) -> None:
        if not self.api.instance_domain:
            self._prompt_instance()
        if not self.api.check_auth():
            self._prompt_code()
        self.fill_data()

    @Slot()
    def fill_data(self) -> None:
        self.central_widget.fill_data(self.api.get_followers())

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

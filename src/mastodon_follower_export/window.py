# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from dataclasses import astuple, fields
from typing import Literal, overload, override

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
)
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence, QValidator
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .validators import CodeValidator, DomainValidator
from .wrapper import Follower, Mastodon

TOP_LEVEL_INDEX = QModelIndex()


class FollowerTableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None, data: list[Follower] | None = None) -> None:
        super().__init__(parent)
        self._data = data or []

    @override
    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = TOP_LEVEL_INDEX) -> int:
        return len(self._data)

    @override
    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = TOP_LEVEL_INDEX) -> int:
        return len(fields(Follower))

    @overload
    def headerData(
        self,
        section: int,
        orientation: Literal[Qt.Orientation.Horizontal] | Literal[Qt.Orientation.Vertical],
        role: Literal[Qt.ItemDataRole.DisplayRole] = ...,
    ) -> str: ...
    @overload
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int,
    ) -> None: ...

    @override
    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> str | None:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        match orientation:
            case Qt.Orientation.Horizontal:
                return fields(Follower)[section].metadata["display"]
            case Qt.Orientation.Vertical:
                return str(section)
            case _:
                return None

    @overload
    def data(  # pyright: ignore[reportOverlappingOverload]
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: Literal[Qt.ItemDataRole.DisplayRole],
    ) -> str: ...
    @overload
    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int,
    ) -> None: ...

    @override
    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> str | None:
        follower = self._data[index.row()]
        value = astuple(follower)[index.column()]
        match role:
            case Qt.ItemDataRole.DisplayRole:
                if isinstance(value, str):
                    return value
                if isinstance(value, bool):
                    return "Yes" if value else "No"
                return str(value)
            case _:
                return None


class FollowerTableView(QTableView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.setFrameStyle(0)


class DisplayLabel(QLabel):
    def __init__(self, parent: QWidget | None = None, text: str | None = None) -> None:
        super().__init__(
            parent,
            text=text,
            alignment=Qt.AlignmentFlag.AlignCenter,
            textFormat=Qt.TextFormat.RichText,
        )


class CentralWidget(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setContentsMargins(11, 11, 11, 11)
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

    def fill_data(self, data: list[Follower]) -> None:
        self.table_view.setModel(FollowerTableModel(self, data))
        self.table_view.setVisible(True)
        self.hint_label.setVisible(False)
        self.login_button.setVisible(False)


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About this program")
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        text = DisplayLabel(
            self,
            text=f"""
            <h2>
                Mastodon Follower Export
            </h2>
            <h3>
                {__version__}
            </h3>
        """,
        )
        layout.addWidget(text)


class InputDialog(QDialog):
    text_updated = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        previous: str | None = None,
        description: str = "",
        validator: type[QValidator] | None = None,
        buttons: QDialogButtonBox.StandardButton = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        ),
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.description = DisplayLabel(self, description)
        layout.addWidget(self.description)

        self.input_box = QLineEdit()
        self.input_box.setText(previous)
        if validator:
            self.input_box.setValidator(validator(self))
        layout.addWidget(self.input_box)

        button_box = QDialogButtonBox(buttons)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.accepted.connect(self._update_text)
        self.rejected.connect(self.close)

    @Slot()
    def _update_text(self) -> None:
        self.text_updated.emit(self.input_box.text())


class InstanceDialog(InputDialog):
    def __init__(self, parent: QWidget | None = None, previous: str | None = None) -> None:
        super().__init__(
            parent,
            previous=previous,
            description="""
                Enter the domain name of the Mastodon instance on which you have an account.
            """,
            validator=DomainValidator,
        )
        self.setWindowTitle("Choose an instance")


class CodeDialog(InputDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            parent,
            description="""
                Sign in to the instance in the browser window that just opened, then enter the code
                here.
            """,
            validator=CodeValidator,
        )
        self.setWindowTitle("Enter authentication code")


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Mastodon Follower Export")

        menu_file = QMenu(self, title="&File")
        self.menuBar().addMenu(menu_file)
        menu_help = QMenu(self, title="&Help")
        self.menuBar().addMenu(menu_help)

        action_log_in = QAction(self, text="Sign In Again")
        action_log_in.triggered.connect(self._force_login)
        menu_file.addAction(action_log_in)

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
        self.central_widget.login_button.clicked.connect(self.fill_data)
        self.setCentralWidget(self.central_widget)

        self.api = Mastodon()
        if self.api.is_logged_in:
            self.fill_data()

        geometry = self.screen().availableGeometry()
        self.resize(int(geometry.width() * 0.8), int(geometry.height() * 0.8))

    def show_about(self) -> None:
        dialog = AboutDialog(self)
        dialog.show()

    @Slot()
    def fill_data(self) -> None:
        self._login()
        self.central_widget.fill_data(self.api.get_followers())

    def _prompt_instance(self) -> None:
        instance_dialog = InstanceDialog(self, previous=self.api.instance_domain)
        instance_dialog.text_updated.connect(self._login_set_instance)
        instance_dialog.exec()

    def _prompt_code(self) -> None:
        QDesktopServices.openUrl(self.api.get_auth_url())
        code_dialog = CodeDialog(self)
        code_dialog.text_updated.connect(self._login_update_auth)
        code_dialog.exec()

    def _login(self) -> None:
        if not self.api.instance_domain:
            self._prompt_instance()
        if not self.api.is_logged_in:
            self._prompt_code()

    @Slot()
    def _force_login(self) -> None:
        self._prompt_instance()
        self._prompt_code()
        self.fill_data()

    @Slot()
    def _login_set_instance(self, domain: str) -> None:
        self.api.instance_domain = domain

    @Slot()
    def _login_update_auth(self, code: str) -> None:
        self.api.auth(code)

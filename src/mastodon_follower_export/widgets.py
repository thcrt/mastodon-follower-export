# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import cast

from PySide6.QtCore import Property, QDir, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLineEdit, QPushButton, QWidget


class FileLine(QFrame):
    def __init__(
        self,
        parent: QWidget | None,
        filters: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        self.filters = filters if filters is not None else []
        self._path = QDir()

        self.line_path = QLineEdit(self)
        self.line_path.textChanged.connect(self.update_path)
        layout.addWidget(self.line_path)

        self.button = QPushButton("Browse...", self)
        self.button.clicked.connect(self.browse)
        layout.addWidget(self.button)

    def _get_path(self) -> str:
        return QDir.toNativeSeparators(self._path.path())

    def _set_path(self, v: str) -> None:
        self._path = QDir(v)

    # We need to cast it to the type it'll outwardly present as, since Pyright doesn't understand
    # that `PySide6.QtCore.Property` has the same effect as builtin `property`.
    path = cast("str", Property(str, _get_path, _set_path))
    path_changed = Signal(str)

    @Slot()
    def update_path(self, v: str) -> None:
        self.path = v
        self.line_path.setText(self.path)
        self.path_changed.emit(self.path)

    @Slot()
    def browse(self) -> None:
        new_path = QFileDialog.getSaveFileName(
            self,
            dir=self.path,
            filter=";;".join(self.filters),
            selectedFilter=self.filters[0] if self.filters else "",
        )[0]
        if new_path:
            self.update_path(new_path)

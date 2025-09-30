# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import cast, override

from PySide6.QtCore import Property, QDir, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QColorConstants, QPainter, QPaintEvent, QPen
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


class Throbber(QWidget):
    def __init__(  # noqa: PLR0913
        self,
        parent: QWidget | None = None,
        *,
        color: QColor = QColorConstants.Black,
        line_count: int = 8,
        line_length: int = 5,
        line_width: int = 2,
        inner_radius: int = 4,
        speed: float = 2,
    ) -> None:
        super().__init__(parent)

        self.color = QColor(color)
        self.line_count = line_count

        self.line_length = line_length
        self.line_width = line_width
        self.inner_radius = inner_radius

        self.setFixedSize(self._size, self._size)

        self._counter = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.setInterval(int(1000 / (self.line_count * speed)))
        self._timer.start()

    @property
    def _size(self) -> int:
        """The height and width of the throbber. A scalar value, since throbbers are square."""
        # Because we're using round caps, which extend past the end points of the lines by half
        # their width, we need to add the line width here.
        return ((self.inner_radius + self.line_length) * 2) + self.line_width

    @override
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, on=True)
        pen = QPen(
            self.color,
            self.line_width,
            c=Qt.PenCapStyle.RoundCap,
        )
        painter.setPen(pen)

        painter.translate(
            self._size / 2,
            self._size / 2,
        )
        for i in range(self.line_count):
            painter.save()
            painter.rotate(360 / self.line_count * i)
            painter.translate(self.inner_radius, 0)

            distance = (self._counter - i) % self.line_count
            self.color.setAlphaF(distance / self.line_count)
            pen.setBrush(self.color)
            painter.setPen(pen)

            painter.drawLine(0, 0, self.line_length, 0)
            painter.restore()

    @Slot()
    def _advance(self) -> None:
        self._counter = (self._counter + 1) % self.line_count
        self.update()

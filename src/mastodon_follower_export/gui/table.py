# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from dataclasses import astuple, fields
from typing import TYPE_CHECKING, Literal, overload, override

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import QHeaderView, QTableView

from mastodon_follower_export.wrapper import User

TOP_LEVEL_INDEX = QModelIndex()

if TYPE_CHECKING:
    from PySide6.QtCore import QObject, QPersistentModelIndex
    from PySide6.QtWidgets import QWidget


class FollowerTableModel(QAbstractTableModel):
    def __init__(self, parent: "QObject | None" = None, data: list[User] | None = None) -> None:
        super().__init__(parent)
        self._data = data or []

    @override
    def rowCount(self, parent: "QModelIndex | QPersistentModelIndex" = TOP_LEVEL_INDEX) -> int:
        return len(self._data)

    @override
    def columnCount(self, parent: "QModelIndex | QPersistentModelIndex" = TOP_LEVEL_INDEX) -> int:
        return len(fields(User))

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
                return fields(User)[section].metadata["display"]
            case Qt.Orientation.Vertical:
                return str(section)
            case _:
                return None

    @overload
    def data(  # pyright: ignore[reportOverlappingOverload]
        self,
        index: "QModelIndex | QPersistentModelIndex",
        role: Literal[Qt.ItemDataRole.DisplayRole],
    ) -> str: ...
    @overload
    def data(
        self,
        index: "QModelIndex | QPersistentModelIndex",
        role: int,
    ) -> None: ...

    @override
    def data(
        self,
        index: "QModelIndex | QPersistentModelIndex",
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
    def __init__(self, parent: "QWidget | None" = None) -> None:
        super().__init__(parent)

        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        self.setFrameStyle(0)

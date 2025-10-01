from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .validators import CodeValidator, DomainValidator
from .widgets import DisplayLabel


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

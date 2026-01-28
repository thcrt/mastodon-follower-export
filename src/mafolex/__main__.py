# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from sys import argv

from rich import print  # noqa: A004

if __name__ == "__main__":
    if len(argv) > 1:
        from .cli import app

        app()

    else:
        print(
            "Opening mafolex in GUI mode.",
            "To learn about CLI mode, use the --help flag.",
            sep="\n",
        )

        from PySide6.QtWidgets import QApplication

        from .gui.window import MainWindow

        app = QApplication()
        window = MainWindow()
        window.show()
        app.exec()

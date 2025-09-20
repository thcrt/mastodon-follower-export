# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from PySide6.QtWidgets import QApplication, QWizard

from .wizard import MainWizard

if __name__ == "__main__":
    app = QApplication()
    wizard = MainWizard()
    wizard.setWizardStyle(QWizard.WizardStyle.ModernStyle)
    wizard.show()
    app.exec()

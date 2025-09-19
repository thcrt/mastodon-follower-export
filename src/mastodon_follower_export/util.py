# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from re import fullmatch
from typing import ClassVar, override
from urllib.parse import urlparse

import validators
from PySide6.QtGui import QValidator


class CodeValidator(QValidator):
    CODE_REGEX: ClassVar[str] = r"[a-zA-Z0-9_-]+"
    CODE_LENGTH: ClassVar[int] = 43

    @override
    def validate(self, text: str, _: int) -> QValidator.State:
        if fullmatch(self.CODE_REGEX, text):
            if len(text) == self.CODE_LENGTH:
                return QValidator.State.Acceptable
            return QValidator.State.Intermediate
        return QValidator.State.Invalid


class DomainValidator(QValidator):
    @override
    def validate(self, text: str, _: int) -> QValidator.State:
        if validators.domain(text):
            return QValidator.State.Acceptable
        return QValidator.State.Intermediate

    @override
    def fixup(self, text: str) -> str:
        hostname = urlparse(text).hostname
        return hostname if hostname else text

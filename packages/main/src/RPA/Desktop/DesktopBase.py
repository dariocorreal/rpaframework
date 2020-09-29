# pylint: disable=c-extension-no-member
import json
import logging
import os
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError

from RPA.core.helpers import delay, clean_filename
from RPA.core.decorators import operating_system_required

from RPA.Desktop.new_implementations import (
    Application,
    Clipboard,
    DragAndDrop,
    Elements,
    Keyboard,
    Mouse,
    OperatingSystem,
    Screen,
    Windows,
)


class DesktopBase(
    Application,
    Clipboard,
    DragAndDrop,
    Elements,
    Keyboard,
    Mouse,
    OperatingSystem,
    Screen,
):
    """Desktop base class, handles state and exposed as the robot library RPA.Desktop"""

    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    # TODO: Move windows backend init from here to somewhere it's less intrusive on other platforms
    # TODO?: figure out if app state should be in Application.py or other struct
    def __init__(self, backend: str = "uia") -> None:
        self._apps = {}
        self._app_instance_id = 0
        self._active_app_instance = -1
        self.set_windows_backend(backend)
        self.app = None
        self.dlg = None
        self.windowtitle = None
        self.logger = logging.getLogger(__name__)
        self.clipboard = Clipboard()

    def __del__(self):
        try:
            # TODO: Do this as RF listener instead of __del__?
            self.clipboard.clear_clipboard()
        except RuntimeError as err:
            self.logger.debug("Failed to clear clipboard: %s", err)

    @operating_system_required("Windows")
    def _add_app_instance(
        self,
        app: Any = None,
        dialog: bool = True,
        params: dict = None,
    ) -> int:
        return Windows._add_app_instance(self, app, dialog, params)

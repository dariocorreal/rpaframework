# pylint: disable=c-extension-no-member
import logging


from RPA.Desktop.new_implementations import (
    ApplicationManager,
    Clipboard,
    DragAndDrop,
    Elements,
    Keyboard,
    Mouse,
    OperatingSystem,
    Screen,
)


class Desktop(
    ApplicationManager,
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

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        super().__init__()

    def __del__(self):
        try:
            # TODO: Do this as RF listener instead of __del__?
            self.clipboard.clear_clipboard()
        except RuntimeError as err:
            self.logger.debug("Failed to clear clipboard: %s", err)

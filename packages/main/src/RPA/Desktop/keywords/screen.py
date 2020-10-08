import os
from pathlib import Path
from typing import Optional, List
from robot.api.deco import keyword
from robot.libraries.BuiltIn import RobotNotRunningError, BuiltIn
from RPA.core.helpers import clean_filename
from RPA.core.geometry import Region
from RPA.Desktop import utils
from RPA.Desktop.keywords import LibraryContext

if utils.is_windows():
    import ctypes

    # Possible enum values:
    #  PROCESS_DPI_UNAWARE              Always assume 100% scaling
    #  PROCESS_SYSTEM_DPI_AWARE         Query DPI once for the lifetime of the app
    #  PROCESS_PER_MONITOR_DPI_AWARE    Adjust scale factor whenever DPI changes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

from RPA.Images import Images  # pylint: disable=wrong-import-position


class ScreenKeywords(LibraryContext):
    """Keywords for reading screen information and content."""

    @keyword
    def take_screenshot(
        self,
        filename: Optional[str] = None,
        locator: Optional[str] = None,
    ) -> None:
        """Take a screenshot of the whole screen, or an element
        identified by the given locator.
        """
        if locator is not None:
            # TODO: Use something else to get region instead of point
            region = self.find_element(locator)
        else:
            region = None

        if filename is not None:
            try:
                # TODO: Use artifacts directory when available
                dirname = BuiltIn().get_variable_value("${OUTPUT_DIR}")
            except (ModuleNotFoundError, RobotNotRunningError):
                dirname = Path.cwd()

            filename = Path(dirname, clean_filename(filename))
            os.makedirs(filename.parent, exist_ok=True)

        # TODO: Move implementation here / recognition package
        return Images().take_screenshot(filename=filename, region=region)

    @keyword
    def get_display_dimensions(self) -> List[Region]:
        """Returns a list of current displays. Index 0 contains a virtual display
        which consists of all the displays combined."""
        # TODO: Should we report just the virtual display
        #       and use those coordinates everywhere?
        return Images().display_rectangles

import os
from pathlib import Path
from typing import Optional

import mss
from PIL import Image
from robot.libraries.BuiltIn import RobotNotRunningError, BuiltIn
from RPA.core.helpers import clean_filename
from RPA.core.geometry import Region
from RPA.Desktop.keywords import LibraryContext, keyword


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
        with mss.mss() as sct:
            if locator is not None:
                # TODO: Use something else to get region instead of point
                match = self.find_element(locator)
                image = sct.grab(match.as_tuple())
            else:
                # First monitor is combined virtual display of all monitors
                image = sct.grab(sct.monitors[0])

        if filename is not None:
            try:
                # TODO: Use artifacts directory when available
                dirname = BuiltIn().get_variable_value("${OUTPUT_DIR}")
            except (ModuleNotFoundError, RobotNotRunningError):
                dirname = Path.cwd()

            filename = clean_filename(filename)
            path = Path(dirname / filename).with_suffix(".png")

            os.makedirs(path.parent, exist_ok=True)
            mss.tools.to_png(image.rgb, image.size, output=path)

            self.logger.info("Saved screenshot as '%s'", path)

        # Convert raw mss screenshot to Pillow Image. Might be a bit slow.
        return Image.frombytes("RGB", image.size, image.bgra, "raw", "BGRX")

    @keyword
    def get_display_dimensions(self) -> Region:
        """Returns the dimensions of the current virtual display,
        which is the combined size of all physical monitors.
        """
        with mss.mss() as sct:
            disp = sct.monitors[0]
            return Region.from_size(
                disp["left"], disp["top"], disp["width"], disp["height"]
            )

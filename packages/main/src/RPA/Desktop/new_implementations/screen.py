import os
from abc import ABCMeta
from pathlib import Path
from typing import Union, Literal

from RPA.Desktop.new_implementations.locator_helpers import locator_to_rectangle
from RPA.Desktop.new_implementations.shared_abc import SharedAbc
from RPA.Images import Images, Region
from RPA.core.helpers import clean_filename
from robot.api.deco import keyword
from robot.libraries.BuiltIn import RobotNotRunningError, BuiltIn


class Screen(SharedAbc, metaclass=ABCMeta):
    @keyword
    def screenshot(
        self,
        filename: str,
        target: Union[Literal["desktop"], str] = "desktop",
        overwrite: bool = False,
    ) -> None:
        """Save screenshot into filename.

        :param target: "desktop" or a locator pointing to an element to
        take screenshot of
        :param filename: name of the file
        :param overwrite: file is overwritten if True, defaults to False

        Example:

        .. code-block:: robotframework

            @{element}   Find Element  CalculatorResults
            Screenshot   element.png   ${elements[0][0]}
            Screenshot   desktop.png   desktop=True
            Screenshot   desktop.png   desktop=True  overwrite=True

        """
        if target == "desktop":
            region = None
        else:
            region = self.find_element(target)

        if region:
            left, top, right, bottom = region
            if right - left == 0 or bottom - top == 0:
                self.logger.info(
                    "Unable to take screenshot, because regions was: %s", region
                )
                return
        try:
            output_dir = BuiltIn().get_variable_value("${OUTPUT_DIR}")
        except (ModuleNotFoundError, RobotNotRunningError):
            output_dir = Path.cwd()

        filename = Path(output_dir, "images", clean_filename(filename))
        os.makedirs(filename.parent, exist_ok=overwrite)
        Images().take_screenshot(filename=filename, region=region)

        self.logger.info("Saved screenshot as '%s'", filename)

    @keyword
    def find_element(self, locator: str) -> Region:
        element_location = locator_to_rectangle(locator)
        return element_location

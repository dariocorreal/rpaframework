import logging
import time
from robot.api.deco import keyword
from robotlibcore import DynamicCore

from RPA.core.geometry import Region
from RPA.Desktop.keywords import (
    ApplicationKeywords,
    ClipboardKeywords,
    KeyboardKeywords,
    MouseKeywords,
    ScreenKeywords,
)


class TimeoutException(ValueError):
    """Timeout reached while waiting for condition."""


class Desktop(DynamicCore):
    """Cross-platform library for interacting with desktop environments."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.locators = None

        # Register keyword libraries to LibCore
        libraries = [
            ApplicationKeywords(self),
            ClipboardKeywords(self),
            KeyboardKeywords(self),
            MouseKeywords(self),
            ScreenKeywords(self),
        ]
        super().__init__(libraries)

    @keyword
    def find_element(self, locator: str) -> Region:
        """Find an element defined by locator, and return it's
        bounding rectangle.
        """
        # TODO: Add alias support
        # TODO: Add image/template support
        # TODO: Add offset/coordinates support
        del locator
        return Region(0, 0, 0, 0)

    def wait_for_element(
        self, locator: str, timeout: float = 10.0, interval: float = 0.5
    ):
        """Wait for an element defined by locator to exist or
        until timeout is reached.
        """
        interval = float(interval)
        end_time = time.time() + float(timeout)

        while time.time() <= end_time:
            try:
                return self.find_element(locator)
            except ValueError:
                time.sleep(interval)

        raise TimeoutException(f"No element found within timeout: {locator}")

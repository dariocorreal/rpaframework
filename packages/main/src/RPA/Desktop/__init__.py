import logging
import time
from robot.api.deco import keyword
from robotlibcore import DynamicCore

from RPA.core.geometry import Point
from RPA.core.locators import (
    LocatorsDatabase,
    Locator,
    Coordinates,
    Offset,
    ImageTemplate,
    templates,
)
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
    def find_element(self, locator: str) -> Point:
        """Find an element defined by locator, and return its position."""
        if ":" not in locator:
            locator = LocatorsDatabase.load_by_name(locator)
        else:
            locator = Locator.from_string(locator)

        if isinstance(locator, Coordinates):
            return Point(locator.x, locator.y)
        elif isinstance(locator, Offset):
            position = self.get_mouse_position()
            position.offset(locator.x, locator.y)
            return position
        elif isinstance(locator, ImageTemplate):
            match = templates.find(
                self.take_screenshot(),
                locator.path,
                confidence=locator.confidence,
                limit=1,
            )
            return match[0].center
        else:
            raise NotImplementedError(f"Unsupported locator: {locator}")

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

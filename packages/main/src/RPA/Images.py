import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PIL import Image
from PIL import ImageDraw
from RPA.core import geometry
from RPA.core.geometry import Region
from RPA.core.notebook import notebook_image
from RPA.core.locators import templates
from RPA.Desktop import Desktop


def to_image(obj):
    """Convert `obj` to instance of Pillow's Image class."""
    if obj is None or isinstance(obj, Image.Image):
        return obj
    return Image.open(obj)


@dataclass
class RGB:
    """Container for a single RGB value."""

    red: int
    green: int
    blue: int

    @classmethod
    def from_pixel(cls, value):
        """Create RGB value from pillow getpixel() return value."""
        # RGB(A), ignore possible alpha channel
        if isinstance(value, tuple):
            red, green, blue = value[:3]
        # Grayscale
        else:
            red, green, blue = [value] * 3

        return cls(red, green, blue)

    def luminance(self):
        """Approximate (perceived) luminance for RGB value."""
        return (self.red * 2 + self.green * 3 + self.blue) // 6


class Images:
    """Library for taking screenshots, matching templates, and
    manipulating images.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def take_screenshot(self, filename=None, region=None) -> Image:
        """Take a screenshot of the current desktop.

        :param filename:    Save screenshot to filename
        :param region:      Region to crop screenshot to
        """
        del region
        return Desktop().take_screenshot(filename)

    def crop_image(self, image, region, filename=None):
        """Crop an existing image.

        :param image:       Image to crop
        :param region:      Region to crop image to
        :param filename:    Save cropped image to filename
        """
        region = geometry.to_region(region)
        image = to_image(image)

        image = image.crop(region.as_tuple())
        image.load()

        if filename:
            # Suffix isn't created automatically here
            image.save(Path(filename).with_suffix(".png"), "PNG")
            notebook_image(filename)

    def find_template_on_screen(
        self, template, region=None, limit=None, tolerance=None
    ) -> List[Region]:
        """Attempt to find the template image from the current desktop.

        :param template:    Path to image or Image instance, used to search with
        :param limit:       Limit returned results to maximum of `limit`.
        :param region:      Area to search from. Can speed up search significantly.
        :param tolerance:   Tolerance for matching, value between 0.01 and 1.00
        :returns:           List of matching regions
        :raises ImageNotFoundError: No match was found
        """
        return templates.find(
            self.take_screenshot(), template, region, limit, tolerance
        )

    def wait_template_on_screen(self, template, timeout=5, **kwargs):
        """Wait for template image to appear on current desktop.
        For further argument descriptions, see ``find_template_on_screen()``

        :param timeout: Time to wait for template (in seconds)
        """
        start_time = time.time()
        while time.time() - start_time > timeout:
            try:
                return self.find_template_on_screen(template, **kwargs)
            except templates.ImageNotFoundError:
                time.sleep(0.1)

    def show_region_in_image(self, image, region, color="red", width=5):
        """Draw a rectangle onto the image around the given region.

        :param image:   image to draw onto
        :param region:  coordinates for region or Region object
        :param color:   color of rectangle
        :param width:   line width of rectangle
        """
        image = to_image(image)
        region = geometry.to_region(region)

        draw = ImageDraw.Draw(image)
        draw.rectangle(region.as_tuple(), outline=color, width=int(width))
        return image

    def show_region_on_screen(self, region, color="red", width=5):
        """Draw a rectangle around the given region on the current desktop.

        :param region:  coordinates for region or Region object
        :param color:   color of rectangle
        :param width:   line width of rectangle
        """
        image = self.take_screenshot()
        return self.show_region_in_image(image, region, color, width)

    def get_pixel_color_in_image(self, image, point):
        """Get the RGB value of a pixel in the image.

        :param image:   image to get pixel from
        :param point:   coordinates for pixel or Point object
        """
        point = geometry.to_point(point)
        pixel = image.getpixel(point.as_tuple())
        return RGB.from_pixel(pixel)

    def get_pixel_color_on_screen(self, point):
        """Get the RGB value of a pixel currently on screen.

        :param point:   coordinates for pixel or Point object
        """
        return self.get_pixel_color_in_image(self.take_screenshot(), point)

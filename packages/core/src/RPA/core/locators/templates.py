import logging
import time
from typing import List

from PIL import Image
from PIL import ImageOps
from RPA.core import geometry
from RPA.core.geometry import Region

try:
    from RPA import recognition

    HAS_RECOGNITION = True
except ImportError:
    HAS_RECOGNITION = False


class ImageNotFoundError(Exception):
    """Raised when template matching fails."""


def find(image, template, region=None, limit=None, confidence=None) -> List[Region]:
    """Attempt to find the template from the given image.

    :param image:       Path to image or Image instance, used to search from
    :param template:    Path to image or Image instance, used to search with
    :param limit:       Limit returned results to maximum of `limit`.
    :param region:      Area to search from. Can speed up search significantly.
    :param confidence:  Confidence for matching, value between 0.1 and 1.0
    :return:            List of matching regions
    :raises ImageNotFoundError: No match was found
    """
    # Ensure images are in Pillow format
    image = _to_image(image)
    template = _to_image(template)

    # Crop image if requested
    if region is not None:
        region = geometry.to_region(region)
        image = image.crop(region.as_tuple())

    # Verify template still fits in image
    if template.size[0] > image.size[0] or template.size[1] > image.size[1]:
        raise ValueError("Template is larger than search region")

    # Do the actual search
    matches = _find(image, template, confidence, limit)
    if not matches:
        raise ImageNotFoundError("No matches for given template")

    # Convert region coördinates back to full-size coördinates
    if region is not None:
        for match in matches:
            match.move(region.left, region.top)

    return matches


def _to_image(obj):
    """Convert `obj` to instance of Pillow's Image class."""
    if obj is None or isinstance(obj, Image.Image):
        return obj
    return Image.open(obj)


def _find(image, template, confidence, limit):
    """Use the correct find method to do template matching."""
    if HAS_RECOGNITION:
        func = recognition.templates.find
    else:
        func = _fallback

    start = time.time()

    matches = []
    for match in func(image, template, confidence):
        matches.append(match)
        if limit is not None and len(matches) >= int(limit):
            break

    logging.info("Scanned image in %.2f seconds", time.time() - start)

    return matches


def _fallback(image, template, confidence):
    """Brute-force search for template image in larger image.

    Use optimized string search for finding the first row and then
    check if whole template matches.
    """
    del confidence

    image = ImageOps.grayscale(image)
    template = ImageOps.grayscale(template)

    template_width, template_height = template.size
    template_rows = _chunks(tuple(template.getdata()), template_width)

    image_width, _ = image.size
    image_rows = _chunks(tuple(image.getdata()), image_width)

    for image_y, image_row in enumerate(image_rows[: -len(template_rows)]):
        for image_x in _search_string(image_row, template_rows[0]):
            match = True
            for match_y, template_row in enumerate(template_rows[1:], image_y):
                match_row = image_rows[match_y][image_x : image_x + template_width]
                if template_row != match_row:
                    match = False
                    break

            if match:
                yield Region.from_size(
                    image_x, image_y, template_width, template_height
                )


def _chunks(obj, size, start=0):
    """Convert `obj` container to list of chunks of `size`."""
    return [obj[i : i + size] for i in range(start, len(obj), size)]


def _search_string(text, pattern):
    """Python implementation of Knuth-Morris-Pratt string search algorithm."""
    pattern_len = len(pattern)

    # Build table of shift amounts
    shifts = [1] * (pattern_len + 1)
    shift = 1
    for idx in range(pattern_len):
        while shift <= idx and pattern[idx] != pattern[idx - shift]:
            shift += shifts[idx - shift]
        shifts[idx + 1] = shift

    # Do the actual search
    start_idx = 0
    match_len = 0
    for char in text:
        while match_len == pattern_len or match_len >= 0 and pattern[match_len] != char:
            start_idx += shifts[match_len]
            match_len -= shifts[match_len]
        match_len += 1
        if match_len == pattern_len:
            yield start_idx

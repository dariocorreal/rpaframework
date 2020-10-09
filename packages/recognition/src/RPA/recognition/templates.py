import cv2
import numpy
from RPA.core.geometry import Region


DEFAULT_CONFIDENCE = 0.95


def find(image, template, confidence=DEFAULT_CONFIDENCE):
    """Use opencv's matchTemplate() to slide the `template` over
    `image` to calculate correlation coefficients, and then
    filter with a confidence to find all relevant global maximums.
    """
    confidence = max(0.01, min(confidence, 1.00))
    template_width, template_height = template.size

    if image.mode == "RGBA":
        image = image.convert("RGB")
    if template.mode == "RGBA":
        template = template.convert("RGB")

    image = numpy.array(image)
    template = numpy.array(template)

    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    template = cv2.cvtColor(template, cv2.COLOR_RGB2BGR)

    coefficients = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

    while True:
        _, match_coeff, _, (match_x, match_y) = cv2.minMaxLoc(coefficients)
        if match_coeff < confidence:
            break

        coefficients[
            match_y - template_height // 2 : match_y + template_height // 2,
            match_x - template_width // 2 : match_x + template_width // 2,
        ] = 0

        yield Region.from_size(match_x, match_y, template_width, template_height)

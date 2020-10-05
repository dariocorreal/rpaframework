from typing import Any

from RPA.Images import Region, Images


def determine_search_criteria(locator: str) -> Any:
    """Check search criteria from locator.

    Possible search criterias:
        - name
        - class / class_name
        - type / control_type
        - id / automation_id
        - partial name (wildcard search for 'name' attribute)
        - any (if none was defined)

    :param locator: name of the locator
    :return: criteria and locator
    """
    if locator.startswith("name:"):
        search_criteria = "name"
        _, locator = locator.split(":", 1)
    elif locator.startswith(("class_name:", "class:")):
        search_criteria = "class_name"
        _, locator = locator.split(":", 1)
    elif locator.startswith(("control_type:", "type:")):
        search_criteria = "control_type"
        _, locator = locator.split(":", 1)
    elif locator.startswith(("automation_id:", "id:")):
        search_criteria = "automation_id"
        _, locator = locator.split(":", 1)
    elif locator.startswith("partial name:"):
        search_criteria = "partial name"
        _, locator = locator.split(":", 1)
    elif locator.startswith("regexp:"):
        search_criteria = "regexp"
        _, locator = locator.split(":", 1)
    else:
        search_criteria = "any"

        return search_criteria, locator


def locator_to_rectangle(locator: str) -> Region:
    """ Convert a locator to a rectangle for clicking or other coordinate-dependent purposes."""
    if locator.startswith("alias:"):
        # FIXME: convert alias to actual image

        template = convert_locator_to_template(locator)
        return Images().find_and_validate_template_on_screen(template)[0]
    elif locator.startswith("coordinates"):
        locator_content = locator[len("coordinates:") :]
        x, y = map(lambda x: float(x), locator_content.split(","))
        return Region(x, y, x, y)
    else:
        raise ValueError("Unsupported locator strategy")

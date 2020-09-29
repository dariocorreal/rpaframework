def determine_search_criteria(self, locator: str) -> Any:
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

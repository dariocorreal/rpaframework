import json
import os
import re
from abc import ABCMeta
from datetime import time
from pathlib import Path
from typing import Any

from RPA.Desktop.new_implementations.shared_abc import SharedAbc
from RPA.core.helpers import clean_filename, delay
from robot.api.deco import keyword

from .locator_helpers import determine_search_criteria


class MenuItemNotFoundError(Exception):
    """Raised when expected menu item is not found"""


class ElementNotFoundError(Exception):
    """Raised when expected element is not found"""


def write_element_info_as_json(
    elements: Any, filename: str, path: str = "output/json"
) -> None:
    """Write list of elements into json file

    :param elements: list of elements to write
    :param filename: output file name
    :param path: output directory, defaults to "output/json"
    """
    elements = elements if isinstance(elements, list) else [elements]
    filename = Path(f"{path}/{filename}.json")
    os.makedirs(filename.parent, exist_ok=True)
    with open(filename, "w") as outfile:
        json.dump(elements, outfile, indent=4, sort_keys=True)


class Elements(SharedAbc, metaclass=ABCMeta):
    def get_text(self, locator: str) -> dict:
        """Get text from element

        :param locator: element locator

        Example:

        .. code-block:: robotframework

            Open Using Run Dialog  calc     Calculator
            Type Into    CalculatorResults   11
            Type Into    CalculatorResults   55
            &{val}       Get Text   CalculatorResults

        """
        elements, _ = self.find_element(locator)
        element_text = {}
        if elements and len(elements) == 1:
            ctrl = elements[0]["control"]
            element_text["value"] = (
                str(ctrl.get_value()) if hasattr(ctrl, "get_value") else None
            )
            element_text["children_texts"] = (
                "".join(ctrl.children_texts())
                if hasattr(ctrl, "children_texts")
                else None
            )
            legacy = (
                ctrl.legacy_properties() if hasattr(ctrl, "legacy_properties") else None
            )
            element_text["legacy_value"] = str(legacy["Value"]) if legacy else None
            element_text["legacy_name"] = str(legacy["Name"]) if legacy else None
        return element_text

    @keyword
    def get_element(self, locator: str, screenshot: bool = False) -> Any:
        """Get element by locator.

        :param locator: name of the locator
        :param screenshot: takes element screenshot if True, defaults to False
        :return: element if element was identified, else False

        Example:

        .. code-block:: robotframework

            ${element}  Get Element  CalculatorResults
            ${element}  Get Element  Result      screenshot=True

        """
        self.logger.info("Get element: %s", locator)
        self.open_dialog(self.window_title)
        self.dlg.wait("exists enabled visible ready")

        search_criteria, locator = determine_search_criteria(locator)
        matching_elements, locators = self.find_element(locator, search_criteria)

        locators = sorted(set(locators))
        if locator in locators:
            locators.remove(locator)
        locators_string = "\n\t- ".join(locators)

        if len(matching_elements) == 0:
            self.logger.info(
                "Locator '%s' using search criteria '%s' not found in '%s'.\n"
                "Maybe one of these would be better?\n%s\n",
                locator,
                search_criteria,
                self.window_title,
                locators_string,
            )
        elif len(matching_elements) == 1:
            element = matching_elements[0]
            if screenshot:
                self.screenshot(f"locator_{locator}", element=element)
            for key in element.keys():
                self.logger.debug("%s=%s", key, element[key])
            return element
        else:
            # TODO. return more valuable information about what should
            # be matching element ?
            self.logger.info(
                "Locator '%s' matched multiple elements in '%s'. "
                "Maybe one of these would be better?\n%s\n",
                locator,
                self.window_title,
                locators_string,
            )
        return False

    def get_element_rich_text(self, locator: str) -> Any:
        """Get value of element `rich text` attribute.

        :param locator: element locator
        :return: `rich_text` value if found, else False

        Example:

        .. code-block:: robotframework

            ${text}  Get Element Rich Text  CalculatorResults

        """
        element = self.get_element(locator)
        if element is not False and "rich_text" in element:
            return element["rich_text"]
        elif element is False:
            self.logger.info("Did not find element with locator: %s", locator)
            return False
        else:
            self.logger.info(
                "Element for locator %s does not have 'rich_text' attribute", locator
            )
            return False

    def get_element_rectangle(self, locator: str, as_dict: bool = False) -> Any:
        # pylint: disable=C0301
        """Get value of element `rectangle` attribute.

        :param locator: element locator
        :param as_dict: return values in a dictionary, default `False`
        :return: (left, top, right, bottom) values if found, else False

        Example:

        .. code-block:: robotframework

            ${left}  ${top}  ${right}  ${bottom}=  Get Element Rectangle  CalculatorResults
            &{coords}  Get Element Rectangle  CalculatorResults  as_dict=True
            Log  top=${coords.top} left=${coords.left}

        """  # noqa: E501
        rectangle = self._get_element_attribute(locator, "rectangle")
        left, top, right, bottom = self._get_element_coordinates(rectangle)
        if as_dict:
            return {"left": left, "top": top, "right": right, "bottom": bottom}
        return left, top, right, bottom

    def _get_element_attribute(self, locator: str, attribute: str) -> Any:
        element = self.get_element(locator)
        if element is not False and attribute in element:
            return element[attribute]
        elif element is False:
            self.logger.info("Did not find element with locator %s", locator)
            return False
        else:
            self.logger.info(
                "Element for locator %s does not have 'visible' attribute", locator
            )
            return False

    def is_element_visible(self, locator: str) -> bool:
        """Is element visible.

        :param locator: element locator
        :return: True if visible, else False

        Example:

        .. code-block:: robotframework

            ${res}=   Is Element Visible  CalculatorResults

        """
        visible = self._get_element_attribute(locator, "visible")
        return bool(visible)

    def is_element_enabled(self, locator: str) -> bool:
        """Is element enabled.

        :param locator: element locator
        :return: True if enabled, else False

        Example:

        .. code-block:: robotframework

            ${res}=   Is Element Enabled  CalculatorResults

        """
        enabled = self._get_element_attribute(locator, "enabled")
        return bool(enabled)

    def menu_select(self, menuitem: str) -> None:
        """Select item from menu

        :param menuitem: name of the menu item

        Example:

        .. code-block:: robotframework

            Open Using Run Dialog   notepad     Untitled - Notepad
            Menu Select             File->Print

        """
        self.logger.info("Menu select: %s", menuitem)
        if self.dlg is None:
            raise ValueError("No dialog open")
        try:
            self.dlg.menu_select(menuitem)
        except AttributeError as e:
            raise MenuItemNotFoundError(
                "Unable to access menu item '%s'" % menuitem
            ) from e

    @keyword
    def wait_for_element(
        self,
        locator: str,
        search_criteria: str = None,
        timeout: float = 30.0,
        interval: float = 2.0,
    ) -> Any:
        """Wait for element to appear into the window.

        Can return 1 or more elements matching locator, or raises
        `ElementNotFoundError` if element is not found within timeout.

        :param locator: name of the locator
        :param search_criteria: criteria by which element is matched
        :param timeout: defines how long to wait for element to appear,
         defaults to 30.0 seconds
        :param interval: how often to poll for element,
         defaults to 2.0 seconds (minimum is 0.5 seconds)

        Example:

        .. code-block:: robotframework

            @{elements}  Wait For Element  CalculatorResults
            @{elements}  Wait For Element  Results   timeout=10  interval=1.5

        """
        end_time = time.time() + float(timeout)
        interval = max([0.5, interval])
        elements = None
        while time.time() < end_time:
            elements, _ = self.find_element(locator, search_criteria)
            if len(elements) > 1:
                break
            if interval >= timeout:
                self.logger.info(
                    "Wait For Element: interval has been set longer than timeout - "
                    "executing one cycle."
                )
                break
            if time.time() >= end_time:
                break
            time.sleep(interval)
        if elements:
            return elements
        raise ElementNotFoundError

    def find_element(self, locator: str, search_criteria: str = None) -> Any:
        """Find element from window by locator and criteria.

        :param locator: name of the locator
        :param search_criteria: criteria by which element is matched
        :return: list of matching elements and locators that were found on the window

        Example:

        .. code-block:: robotframework

            @{elements}   Find Element   CalculatorResults
            Log Many  ${elements[0]}     # list of matching elements
            Log Many  ${elements[1]}     # list of all available locators

        """
        search_locator = locator
        if search_criteria is None:
            search_criteria, search_locator = determine_search_criteria(locator)

        controls, elements = self.get_window_elements()
        self.logger.info(
            "Find element: (locator: %s, criteria: %s)",
            locator,
            search_criteria,
        )

        matching_elements, locators = [], []
        for ctrl, element in zip(controls, elements):
            if self.is_element_matching(element, search_locator, search_criteria):
                element["control"] = ctrl
                matching_elements.append(element)
            if search_criteria == "any" and "name" in element:
                locators.append(element["name"])
            elif search_criteria and search_criteria in element:
                locators.append(element[search_criteria])

        return matching_elements, locators

    # TODO. supporting multiple search criterias at same time to identify ONE element
    def _is_element_matching(
        self, itemdict: dict, locator: str, criteria: str, wildcard: bool = False
    ) -> bool:
        if criteria == "regexp":
            name_search = re.search(locator, itemdict["name"])
            class_search = re.search(locator, itemdict["class_name"])
            type_search = re.search(locator, itemdict["control_type"])
            id_search = re.search(locator, itemdict["automation_id"])
            return name_search or class_search or type_search or id_search
        elif criteria != "any" and criteria in itemdict:
            if (wildcard and locator in itemdict[criteria]) or (
                locator == itemdict[criteria]
            ):
                return True
        elif criteria == "any":
            name_search = self.is_element_matching(itemdict, locator, "name")
            class_search = self.is_element_matching(itemdict, locator, "class_name")
            type_search = self.is_element_matching(itemdict, locator, "control_type")
            id_search = self.is_element_matching(itemdict, locator, "automation_id")
            if name_search or class_search or type_search or id_search:
                return True
        elif criteria == "partial name":
            return self.is_element_matching(itemdict, locator, "name", True)
        return False

    # TODO. supporting multiple search criterias at same time to identify ONE element
    def is_element_matching(
        self, itemdict: dict, locator: str, criteria: str, wildcard: bool = False
    ) -> bool:
        """Is element matching. Check if locator is found in `any` field
        or `criteria` field in the window items.

        :param itemDict: dictionary of element items
        :param locator: name of the locator
        :param criteria: criteria on which to match element
        :param wildcard: whether to do reg exp match or not, default False
        :return: True if element is matching locator and criteria, False if not
        """
        return self._is_element_matching(itemdict, locator, criteria, wildcard)

    def get_element_center(self, element: dict) -> Any:
        """Get element center coordinates

        :param element: dictionary of element items
        :return: coordinates, x and y

        Example:

        .. code-block:: robotframework

            @{element}   Find Element  CalculatorResults
            ${x}  ${y}=  Get Element Center  ${elements[0][0]}

        """
        return self.calculate_rectangle_center(element["rectangle"])

    def _get_element_coordinates(self, rectangle: Any) -> Any:
        """Get element coordinates from pywinauto object.

        :param rectangle: item containing rectangle information
        :return: coordinates: left, top, right, bottom
        """
        self.logger.debug(
            "Get element coordinates from rectangle: %s of type %s",
            rectangle,
            type(rectangle),
        )
        left = 0
        top = 0
        right = 0
        bottom = 0
        if isinstance(rectangle, pywinauto.win32structures.RECT):
            left = rectangle.left
            top = rectangle.top
            right = rectangle.right
            bottom = rectangle.bottom
        elif isinstance(rectangle, dict):
            left = rectangle.left
            top = rectangle.top
            right = rectangle.right
            bottom = rectangle.bottom
        else:
            left, top, right, bottom = map(
                int,
                re.match(
                    r"\(L(\d+).*T(\d+).*R(\d+).*B(\d+)\)", str(rectangle)
                ).groups(),
            )
        return left, top, right, bottom

    def get_window_elements(
        self,
        screenshot: bool = False,
        element_json: bool = False,
        outline: bool = False,
    ) -> Any:
        # pylint: disable=C0301
        """Get element information about all window dialog controls
        and their descendants.

        :param screenshot: save element screenshot if True, defaults to False
        :param element_json: save element json if True, defaults to False
        :param outline: highlight elements if True, defaults to False
        :return: all controls and all elements

        Example:

        .. code-block:: robotframework

            @{elements}   Get Window Elements
            Log Many      ${elements[0]}     # list of all available locators
            Log Many      ${elements[1]}     # list of matching elements
            @{elements}   Get Window Elements  screenshot=True  element_json=True  outline=True

        """  # noqa: E501
        if self.dlg is None:
            raise ValueError("No dialog open")

        ctrls = [self.dlg]
        if hasattr(self.dlg, "descendants"):
            ctrls += self.dlg.descendants()

        elements, controls = [], []
        for _, ctrl in enumerate(ctrls):
            if not hasattr(ctrl, "element_info"):
                continue

            filename = clean_filename(
                f"locator_{self.windowtitle}_ctrl_{ctrl.element_info.name}"
            )

            if screenshot and len(ctrl.element_info.name) > 0:
                self.screenshot(filename, ctrl=ctrl, overwrite=True)
            if outline:
                ctrl.draw_outline(colour="red", thickness=4)
                delay(0.2)
                ctrl.draw_outline(colour=0x000000, thickness=4)

            element = self._parse_element_attributes(element=ctrl)
            if element_json:
                write_element_info_as_json(element, filename)

            controls.append(ctrl)
            elements.append(element)

        if element_json:
            write_element_info_as_json(
                elements, clean_filename(f"locator_{self.windowtitle}_all_elements")
            )

        return controls, elements

    def _parse_element_attributes(self, element: dict) -> Optional[dict]:
        """Return filtered element dictionary for an element.

        :param element: should contain `element_info` attribute
        :return: dictionary containing element attributes
        """
        if element is None and "element_info" not in element:
            self.logger.warning(
                "%s is none or does not have element_info attribute", element
            )
            return None

        attributes = [
            "automation_id",
            # "children",
            "class_name",
            "control_id",
            "control_type",
            # "descendants",
            # "dump_window",
            # "element"
            "enabled",
            # "filter_with_depth",
            # "framework_id",
            # "from_point",
            "handle",
            # "has_depth",
            # "iter_children",
            # "iter_descendants",
            "name",
            # "parent",
            "process_id",
            "rectangle",
            "rich_text",
            "runtime_id",
            # "set_cache_strategy",
            # "top_from_point",
            "visible",
        ]

        element_dict = {}
        # self.element_info = backend.registry.backends[_backend].element_info_class()
        element_info = element.element_info
        # self.logger.debug(element_info)
        for attr in attributes:
            if hasattr(element_info, attr):
                attr_value = getattr(element_info, attr)
                try:
                    element_dict[attr] = (
                        attr_value() if callable(attr_value) else str(attr_value)
                    )
                except TypeError:
                    pass
            else:
                self.logger.warning("did not have attr %s", attr)
        return element_dict

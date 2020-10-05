from abc import ABCMeta
from typing import Tuple
import platform

from RPA.Desktop.new_implementations.locator_helpers import locator_to_rectangle
from RPA.Desktop.new_implementations.types import MouseAction
from robot.api.deco import keyword
import pynput
from pynput.mouse import Button

from RPA.core.helpers import delay
from RPA.Desktop.new_implementations.shared_abc import SharedAbc

if platform.system() == "Windows":
    import ctypes

    PROCESS_PER_MONITOR_DPI_AWARE = 2
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)


class Mouse(SharedAbc, metaclass=ABCMeta):
    @keyword
    def mouse_click(
        self,
        locator: str = None,
        off_x: int = 0,
        off_y: int = 0,
        click_type: MouseAction = MouseAction.click,
    ) -> None:
        # pylint: disable=C0301
        """Mouse click `locator`, `coordinates`, or `image`

        When using method `locator`,`image` or `ocr` mouse is clicked by default at
        center coordinates.

        Click types are:

        - `click` normal left click
        - `hold` left click without releasing
        - `right_click`
        - `right_hold`
        - `double_click`
        - `triple_click`

        :param locator: element locator
        :param off_x: offset x (used for locator and image clicks)
        :param off_y: offset y (used for locator and image clicks)
        :param click_type: type of mouse click

        Example:

        .. code-block:: robotframework

            Mouse Click  method=coordinates  100   100
            Mouse Click  CalculatorResults
            Mouse Click  method=image  image=myimage.png  off_x=10  off_y=10  ctype=right
            Mouse Click  method=image  image=myimage.png  tolerance=0.8

        """  # noqa: E501
        self.logger.info(f"Mouse click: {locator}")

        x, y = locator_to_rectangle(locator).center().as_tuple
        self._click(x + off_x, y + off_y, click_type)

    def mouse_click_image(
        self,
        image_locator: str,
        off_x: int = 0,
        off_y: int = 0,
        mouse_action: MouseAction = MouseAction.click,
        **kwargs,
    ) -> None:
        """Click at template image on desktop

        :param image_locator: image to click on desktop
        :param off_x: horizontal offset from top left corner to click on
        :param off_y: vertical offset from top left corner to click on
        :param mouse_action: type of mouse action
        :param **kwargs: these keyword arguments can be used to pass arguments
         to underlying `Images` library to finetune image template matching,
         for example. `tolerance=0.5` would adjust image tolerance for the image
         matching

        Example:

        .. code-block:: robotframework

            Mouse Click  image=myimage.png  off_x=10  off_y=10  ctype=right
            Mouse Click  image=myimage.png  tolerance=0.8

        """
        rect = locator_to_rectangle(image_locator)
        x, y = rect.center().as_tuple()
        self._click(x + off_x, y + off_y, mouse_action)

    def _click(
        self, x: int = None, y: int = None, click_type: MouseAction = MouseAction.click
    ) -> None:
        """Execute MouseAction on coordinates x and y. For internal use.

        Default click type is `click` meaning `left`

        :param x: horizontal coordinate for click, defaults to None
        :param y: vertical coordinate for click, defaults to None
        :param click_type: default to click, any of MouseAction
        :raises ValueError: if coordinates are not valid

        Example:

        .. code-block:: robotframework

            Click Type  x=450  y=100
            Click Type  x=450  y=100  click_type=right
            Click Type  x=450  y=100  click_type=double

        """
        self.logger.info("Click type '%s' at (%s, %s)", click_type, x, y)
        if x is None or y is None:
            raise ValueError(f"Coordinates weren't provided. Got ({x}, {y})")
        if x < 0 or y < 0:
            raise ValueError(f"Can't click on given coordinates: ({x}, {y})")
        mouse = pynput.mouse.Controller()
        mouse.position = (x, y)
        if click_type is MouseAction.click:
            mouse.click(Button.left)
        if click_type is MouseAction.hold:
            mouse.press(Button.left)
        elif click_type is MouseAction.double_click:
            mouse.click(Button.left, 2)
        elif click_type is MouseAction.right_click:
            mouse.click(Button.right)
        else:
            # FIXME: mypy should handle enum exhaustivity validation
            raise ValueError(f"Unsupported MouseAction '{click_type}'")

    def drag_and_drop(
        self,
        src_locator: str,
        target_locator: str,
        drop_delay: float = 2.0,
    ) -> None:
        # pylint: disable=C0301
        """Drag from source and drop on target

        Please note that if CTRL is not pressed down during drag and drop then
        operation is MOVE operation, on CTRL down the operation is COPY operation.

        There will be also overwrite notification if dropping over existing files.

        :param src_locator: elements to move
        :param drop_delay: how many seconds to wait until releasing mouse drop,
         default 2.0
        :raises ValueError: on validation errors

        Example:

        .. code-block:: robotframework

            ${app1}=        Open Using Run Dialog    explorer.exe{VK_SPACE}C:\\workfiles\\movethese   movethese
            ${app2}=        Open Using Run Dialog    wordpad.exe   Document - WordPad
            Drag And Drop   ${app1}   ${app2}   regexp:testfile_\\d.txt  name:Rich Text Window   handle_ctrl_key=${True}
            Drag And Drop   ${app1}   ${app1}   regexp:testfile_\\d.txt  name:subdir  handle_ctrl_key=${True}

        """  # noqa : E501

        source_x, source_y = locator_to_rectangle(src_locator).center.as_tuple()
        target_x, target_y = locator_to_rectangle(target_locator).center.as_tuple()

        self.logger.info(
            "Dragging from (%d,%d) to (%d,%d)",
            source_x,
            source_y,
            target_x,
            target_y,
        )

        self.mouse_move(source_x, source_y)
        self.mouse_down()
        delay(0.5)
        self.mouse_move(target_x, target_y)
        self.logger.debug("Cursor position: %s", self.mouse_position())
        delay(drop_delay)
        self.mouse_up()

    @keyword
    def mouse_move(self, source_x: float, source_y: float):
        mouse = pynput.mouse.Controller()
        mouse.position = (source_x, source_y)

    @keyword
    def mouse_down(self, key: Button):
        mouse = pynput.mouse.Controller()
        mouse.press(key)

    @keyword
    def mouse_up(self, key: Button):
        mouse = pynput.mouse.Controller()
        mouse.release(key)

    @keyword
    def mouse_position(self) -> Tuple[float, float]:
        mouse = pynput.mouse.Controller()
        return mouse.position

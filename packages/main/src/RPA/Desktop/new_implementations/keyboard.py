from abc import ABCMeta

from pynput import keyboard
from robot.api.deco import keyword

from RPA.Desktop.new_implementations.shared_abc import SharedAbc


class Keyboard(SharedAbc, metaclass=ABCMeta):
    def type_into(self, locator: str, keys: str, empty_field: bool = False) -> None:
        """Click element matching locator and then type keys.

        :param locator: element locator
        :param keys:    list of keys to type

        Example:

        .. code-block:: robotframework

            Open Executable  calc.exe  Calculator
            Type Into        CalculatorResults  11
            Type Into        CalculatorResults  22  empty_field=True

        """
        self.mouse_click(locator)
        if empty_field:
            # FIXME: doesn't even work on windows, and especially not macOS
            self.press_keys("ctrl+a, DEL")
        self.type_keys(keys)

    @keyword
    def type_keys(self, keys: str) -> None:
        """Type string.

        :param keys: string representing characters to type

        Example:

        .. code-block:: robotframework

            Open Executable  notepad.exe  Untitled - Notepad
            Type Keys   My text

        """
        self.logger.info("Type keys: %s", keys)
        kb = keyboard.Controller()
        kb.type(keys)

    def _send_keys(self, keys: str):
        for key in keys.split(","):
            key_lowered = key.lower().strip()
            try:
                kb = keyboard.Controller()
                kb.press(key_lowered)
            except ValueError as e:
                self.logger.debug(e)
                self.logger.error(
                    f"Key '{key}' couldn't be converted to a valid keycode"
                )

    @keyword
    def press_keys(self, keys: str) -> None:
        """Send list of keys into active window.

        :param keys: list of keys to send

        Example:

        .. code-block:: robotframework

            Open Executable  calc.exe  Calculator
            Send Keys        2, +, 3, =

        """
        self.logger.info("Send keys: %s", keys)
        self._send_keys(keys)

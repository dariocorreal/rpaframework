from typing import Union
from pynput.keyboard import Controller, Key, KeyCode
from RPA.Desktop.keywords import LibraryContext, keyword


def to_key(key: str) -> Union[Key, KeyCode]:
    """Convert key string to correct enum value."""
    if isinstance(key, (Key, KeyCode)):
        return key

    value = str(key).lower().strip()

    # Check for modifier or function key, e.g. ctrl or f4
    try:
        return Key[value]
    except KeyError:
        pass

    # Check for individual character
    if len(value) == 1:
        try:
            return KeyCode.from_char(value)
        except ValueError:
            pass

    raise ValueError("Invalid key: {key}")


class KeyboardKeywords(LibraryContext):
    """Keywords for sending inputs through an (emulated) keyboard."""

    def __init__(self, ctx):
        super().__init__(ctx)
        self._keyboard = Controller()

    @keyword
    def type_text(self, text: str, *modifiers: str) -> None:
        """Type text one letter at a time."""
        keys = [to_key(key) for key in modifiers]
        self.logger.info("Typing text: %s", text)

        with self._keyboard.pressed(*keys):
            self._keyboard.type(text)

    @keyword
    def press_keys(self, *keys: str) -> None:
        """Press multiple keys down simultaneously."""
        keys = [to_key(key) for key in keys]
        self.logger.info("Pressing keys: %s", ", ".join(str(key) for key in keys))

        for key in keys:
            self._keyboard.press(key)

        for key in reversed(keys):
            self._keyboard.release(key)

    @keyword
    def type_text_into(self, locator: str, text: str, clear: bool = False) -> None:
        """Type text at the position indicated by given locator."""
        self.ctx.click(locator)

        if clear:
            self.press_keys("ctrl", "a")
            self.press_keys("del")

        self.type_text(text)

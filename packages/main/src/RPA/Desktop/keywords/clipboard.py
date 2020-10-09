import pyperclip
from RPA.Desktop.keywords import LibraryContext, keyword


class ClipboardKeywords(LibraryContext):
    """Keywords for interacting with the system clipboard."""

    @keyword
    def copy_to_clipboard(self, locator):
        """Read value to system clipboard from given element."""
        self.ctx.click(locator, "triple click")
        self.ctx.press_keys("ctrl", "c")
        return self.get_clipboard_value()

    @keyword
    def paste_from_clipboard(self, locator):
        """Paste value from system clipboard into given element."""
        match = self.find_element(locator)
        text = pyperclip.paste()
        self.ctx.click(match)
        self.ctx.type_text(text)

    @keyword
    def clear_clipboard(self):
        """Clear the system clipboard."""
        pyperclip.copy("")

    @keyword
    def get_clipboard_value(self):
        """Read current value from system clipboard."""
        return pyperclip.paste()

    @keyword
    def set_clipboard_value(self, text):
        """Write given value to system clipboard."""
        pyperclip.copy(text)

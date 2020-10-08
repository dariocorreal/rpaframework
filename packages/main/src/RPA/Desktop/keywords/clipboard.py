import pyperclip
from RPA.Desktop.keywords import LibraryContext


class ClipboardKeywords(LibraryContext):
    """Keywords for interacting with the system clipboard."""

    # TODO: Add keywords for copying/pasting to GUI elements

    def copy_to_clipboard(self, text):
        pyperclip.copy(text)

    def paste_from_clipboard(self):
        return pyperclip.paste()

    def clear_clipboard(self):
        pyperclip.copy("")

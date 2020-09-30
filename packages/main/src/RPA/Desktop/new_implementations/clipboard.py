# pylint: disable=c-extension-no-member
import platform
from abc import ABCMeta, ABC, abstractmethod

if platform.system() == "Windows":
    import win32clipboard
else:
    import clipboard


class _AbstractClipboard(ABC):
    @abstractmethod
    def copy_to_clipboard(self, text):
        """Copy text to clipboard

        :param text: to copy
        """
        ...

    @abstractmethod
    def paste_from_clipboard(self):
        """Paste text from clipboard

        :return: text
        """
        ...

    @abstractmethod
    def clear_clipboard(self):
        """Clear clipboard contents"""
        ...


class _WindowsClipboard(_AbstractClipboard):
    """RPA Framework library for cross platform clipboard management.
    Will use `win32` package on Windows and `clipboard` package on Linux and Mac.
    """

    def copy_to_clipboard(self, text):
        self.logger.debug("copy_to_clipboard")
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()

    def paste_from_clipboard(self):
        self.logger.debug("paste_from_clipboard")
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
            text = win32clipboard.GetClipboardData()
        else:
            text = None
        win32clipboard.CloseClipboard()
        return text

    def clear_clipboard(self):
        self.logger.debug("clear_clipboard")
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()


class _UnixClipboard(_AbstractClipboard):
    """RPA Framework library for cross platform clipboard management.

    Will use `win32` package on Windows and `clipboard` package on Linux and Mac.
    """

    def copy_to_clipboard(self, text):
        self.logger.debug("copy_to_clipboard")
        clipboard.copy(text)

    def paste_from_clipboard(self):
        self.logger.debug("paste_from_clipboard")
        return clipboard.paste()

    def clear_clipboard(self):
        self.logger.debug("clear_clipboard")
        clipboard.copy("")


if platform.system() == "Windows":
    Clipboard = _WindowsClipboard
else:
    Clipboard = _UnixClipboard

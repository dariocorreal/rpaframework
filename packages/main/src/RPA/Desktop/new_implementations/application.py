import os
import platform
import subprocess
from abc import ABCMeta

from RPA.Desktop.new_implementations.shared_abc import SharedAbc
from robot.api.deco import keyword


class ApplicationManager(SharedAbc, metaclass=ABCMeta):
    def quit_application(self, app_id: str = None, send_keys: bool = False) -> None:
        raise NotImplementedError("Quit Application is not yet implemented")

    @keyword
    def open_application_by_path(self, path) -> subprocess.Popen:
        """Open application by path.

        Example:
        .. code-block:: robotframework

            ${app}    Open Application   /path/to/myfile.exe

        """
        self.logger.info("Open file: %s", path)
        if platform.system() == "Windows":
            if not path.endswith(".exe"):
                raise ValueError(
                    "path argument needs to be path to a launchable application"
                )
            return subprocess.Popen([path])
        elif platform.system() == "Darwin":
            if not path.endswith(".app"):
                raise ValueError(
                    "path argument needs to be path to a launchable application"
                )
            return subprocess.Popen(["open", path])
        else:
            if not os.access(path, os.X_OK):
                raise ValueError(
                    "path argument needs to be path to a launchable application"
                )
            return subprocess.Popen(["xdg-open", path])

    @keyword
    def open_file(self, filename: str) -> subprocess.Popen:
        """Open associated application when opening file

        :param filename: path to file
        :return: subprocess.Popen object representing the opened application

        Example:

        .. code-block:: robotframework

            ${app1}    Open File   /path/to/myfile.txt

        """
        self.logger.info("Open file: %s", filename)
        if platform.system() == "Windows":
            return subprocess.Popen([filename])
        elif platform.system() == "Darwin":
            return subprocess.Popen(["open", filename])
        else:
            return subprocess.Popen(["xdg-open", filename])

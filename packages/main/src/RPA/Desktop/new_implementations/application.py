import os
import platform
import subprocess
from abc import ABCMeta
from typing import Any, Optional

from RPA.Desktop.new_implementations.shared_abc import SharedAbc
from RPA.core.decorators import operating_system_required
from RPA.core.helpers import delay
from robot.api.deco import keyword

SUPPORTED_WINDOWS_BACKENDS = ["uia", "win32"]

if platform.system() == "Windows":
    import win32gui
    import pywinauto


class ApplicationManager(SharedAbc, metaclass=ABCMeta):
    def validate_backend(self, backend: Optional[str] = None) -> str:
        """ Set interaction backend """
        if platform.system() == "windows":
            return self._validate_windows_backend(backend)
        else:
            # FIXME: Since logger is set in a super class this is very bug prone
            self.logger.warning("Non-windows backends don't exist yet")
            # raise NotImplementedError("Set Backend not yet implemented for non-windows")

    def _add_app_instance(
        self,
        app: Any = None,
        dialog: bool = True,
        params: dict = None,
    ):
        """ Add an App to list of open apps """
        if platform.system() == "windows":
            return self._windows_add_app_instance(app, dialog, params)

    def _validate_windows_backend(self, backend: Optional[str] = "uia") -> str:
        """Set Windows backend which is used to interact with Windows
        applications

        Allowed values defined by `SUPPORTED_BACKENDS`

        :param backend: name of the backend to use

        Example:

        .. code-block:: robotframework

            Set Windows Backend   uia
            Open Executable   calc.exe  Calculator
            Set Windows Backend   win32
            Open Executable   calc.exe  Calculator

        """
        if backend and backend.lower() in SUPPORTED_WINDOWS_BACKENDS:
            return backend.lower()
        else:
            raise ValueError("Unsupported Windows backend: %s" % backend)

    def _windows_add_app_instance(
        self,
        app: Any = None,
        dialog: bool = True,
        params: dict = None,
    ) -> Optional[int]:
        params = params or {}
        self._app_instance_id += 1
        process_id = None
        handle = None
        if app:
            self.app = app
            if hasattr(app, "process"):
                process_id = app.process
                handle = win32gui.GetForegroundWindow()

            default_params = {
                "app": app,
                "id": self._app_instance_id,
                "dialog": dialog,
                "process_id": process_id,
                "handle": handle,
                "dispatched": False,
            }

            self._apps[self._app_instance_id] = {**default_params, **params}

            self.logger.debug(
                "Added app instance %s: %s",
                self._app_instance_id,
                self._apps[self._app_instance_id],
            )
            self._active_app_instance = self._app_instance_id
            return self._active_app_instance

    @keyword
    def open_application(self):
        # TODO: implement behaviour here. Windows specifically has a ton of different strategies to support
        pass

    @keyword
    def switch_to_application(self, app_id: int) -> None:
        """Switch to application by id.

        :param app_id: application's id
        :raises ValueError: if application is not found by given id

        Example:

        .. code-block:: robotframework

            ${app1}    Open Application   Excel
            ${app2}    Open Application   Word
            Switch To Application   ${app1}

        """
        if app_id and app_id in self._apps.keys():
            app = self.get_app(app_id)
            self._active_app_instance = app_id
            self.app = app["app"]
            if "windowtitle" in app:
                self.open_dialog(app["windowtitle"], existing_app=True)
                delay(0.5)
                self.restore_dialog(app["windowtitle"])
        else:
            raise ValueError(f"No open application with id '{app_id}'")

    def get_open_applications(self):
        """Get list of all open applications

        Returns a dictionary

        Example:

        .. code-block:: robotframework

            ${app1}    Open Application   Excel
            ${app2}    Open Executable    calc.exe  Calculator
            ${app3}    Open File          /path/to/myfile.txt
            &{apps}    Get Open Applications

        """
        return self._apps

    def get_app(self, app_id: int = None) -> Any:
        """Get application object by id

        By default returns active_application application object.

        :param app_id: id of the application to get, defaults to None
        :return: application object

        Example:

        .. code-block:: robotframework

            ${app1}        Open Application   Excel
            &{appdetails}  Get App   ${app1}

        """
        if app_id is None and self._active_app_instance != -1:
            return self._apps[self._active_app_instance]
        else:
            return self._apps[app_id]

    def close_all_applications(self) -> None:
        """Close all applications

        Example:

        .. code-block:: robotframework

            Open Application   Excel
            Open Application   Word
            Open Executable    notepad.exe   Untitled - Notepad
            Close All Applications

        """
        self.logger.info("Closing all applications")
        self.logger.debug("Applications in memory: %d", len(self._apps))
        for aid in list(self._apps):
            self.quit_application(aid)
            del self._apps[aid]

    @keyword
    def quit_application(self, app_id: str = None, send_keys: bool = False) -> None:
        """Quit an application by application id or
        active application if `app_id` is None.

        :param app_id: application_id, defaults to None

        Example:

        .. code-block:: robotframework

            ${app1}   Open Application   Excel
            ${app2}   Open Application   Word
            Quit Application  ${app1}

        """
        app = self.get_app(app_id)
        self.logger.info("Quit application: %s (%s)", app_id, app)
        if send_keys:
            self.switch_to_application(app_id)
            self.send_keys("%{F4}")
        else:
            if app["dispatched"]:
                app["app"].Quit()
            else:
                if "process" in app and app["process"] > 0:
                    # pylint: disable=E1101
                    self.kill_process_by_pid(app["process"])
                else:
                    app["app"].kill()
        self._active_app_instance = -1

    # TODO. How to manage app launched by open_file
    def open_file(self, filename: str) -> bool:
        """Open associated application when opening file

        :param filename: path to file
        :return: True if application is opened, False if not

        Example:

        .. code-block:: robotframework

            ${app1}    Open File   /path/to/myfile.txt

        """
        # FIXME: this never actually returns False if app failed to open.
        self.logger.info("Open file: %s", filename)
        if platform.system() == "Windows":
            # pylint: disable=no-member
            os.startfile(filename)
            return True
        elif platform.system() == "Darwin":
            subprocess.call(["open", filename])
            return True
        else:
            subprocess.call(["xdg-open", filename])
            return True
        return False

    @operating_system_required(["Windows"])
    def open_application(self, application: str) -> int:
        """Open application by dispatch method

        This keyword is used to launch Microsoft applications like
        Excel, Word, Outlook and Powerpoint.

        :param application: name of the application as `str`
        :return: application instance id

        Example:

        .. code-block:: robotframework

            ${app1}    Open Application   Excel
            ${app2}    Open Application   Word

        """
        self.logger.info("Open application: %s", application)
        app = win32com.client.gencache.EnsureDispatch(f"{application}.Application")
        app.Visible = True
        # show eg. file overwrite warning or not
        if hasattr(self.app, "DisplayAlerts"):
            app.DisplayAlerts = False
        params = {
            "dispatched": True,
            "startkeyword": "Open Application",
        }
        return self.add_app_instance(app, dialog=False, params=params)

    @operating_system_required(["Windows"])
    def open_executable(
        self,
        executable: str,
        windowtitle: str,
        backend: str = None,
        work_dir: str = None,
    ) -> int:
        """Open Windows executable. Window title name is required
        to get handle on the application.

        :param executable: name of the executable
        :param windowtitle: name of the window
        :param backend: set Windows backend, default None means using
         library default value
        :param work_dir: path to working directory, default None
        :return: application instance id

        Example:

        .. code-block:: robotframework

            ${app1}    Open Executable   calc.exe  Calculator

        """
        self.logger.info("Opening executable: %s - window: %s", executable, windowtitle)
        if backend:
            self._backend = self.validate_backend(backend)
        params = {
            "executable": executable,
            "windowtitle": windowtitle,
            "startkeyword": "Open Executable",
        }
        self.window_title = windowtitle
        app = pywinauto.Application(backend=self._backend).start(
            cmd_line=executable, work_dir=work_dir
        )

        return self.add_app_instance(app, dialog=False, params=params)

    @operating_system_required(["Windows"])
    def open_using_run_dialog(self, executable: str, windowtitle: str) -> int:
        """Open application using Windows run dialog.
        Window title name is required to get handle on the application.

        :param executable: name of the executable
        :param windowtitle: name of the window
        :return: application instance id

        Example:

        .. code-block:: robotframework

            ${app1}    Open Using Run Dialog  notepad  Untitled - Notepad

        """
        self.send_keys("{VK_LWIN down}r{VK_LWIN up}")
        delay(1)

        self.send_keys_to_input(executable, send_delay=0.2, enter_delay=0.5)

        app_instance = self.open_dialog(windowtitle)
        self._apps[app_instance]["windowtitle"] = windowtitle
        self._apps[app_instance]["executable"] = executable
        self._apps[app_instance]["startkeyword"] = "Open Using Run Dialog"
        return app_instance

    @operating_system_required(["Windows"])
    def open_from_search(self, executable: str, windowtitle: str) -> int:
        """Open application using Windows search dialog.
        Window title name is required to get handle on the application.

        :param executable: name of the executable
        :param windowtitle: name of the window
        :return: application instance id

        Example:

        .. code-block:: robotframework

            ${app1}    Open From Search  calculator  Calculator

        """
        self.logger.info("Run from start menu: %s", executable)
        self.send_keys("{LWIN}")
        delay(1)

        self.send_keys_to_input(executable)

        app_instance = self.open_dialog(windowtitle)
        self._apps[app_instance]["windowtitle"] = windowtitle
        self._apps[app_instance]["executable"] = executable
        self._apps[app_instance]["startkeyword"] = "Open From Search"
        return app_instance

    @property
    def get_window_list(self):
        """Get list of open windows

        Window dictionaries contain:

        - title
        - pid
        - handle

        :return: list of window dictionaries

        Example:

        .. code-block:: robotframework

            @{windows}    Get Window List
            FOR  ${window}  IN  @{windows}
                Log Many  ${window}
            END
        """
        windows = pywinauto.Desktop(backend=self._backend).windows()
        window_list = []
        for w in windows:
            window_list.append(
                {"title": w.window_text(), "pid": w.process_id(), "handle": w.handle}
            )
        return window_list

import platform
from typing import Any, Optional

from RPA.core.helpers import delay

SUPPORTED_WINDOWS_BACKENDS = ["uia", "win32"]

if platform.system() == "Windows":
    import ctypes
    import win32api
    import win32gui


class ApplicationManager:
    def __init__(self):
        self._apps = {}
        self._app_instance_id = 0
        self._active_app_instance = -1
        self.app = None
        self.dlg = None
        self.windowtitle = None
        self.set_backend()

    def set_backend(self, backend: Optional[str] = None):
        """ Set interaction backend """
        if platform.system() == "windows":
            return self._set_windows_backend(backend)
        else:
            # FIXME: Since logger is set in a super class this is very bug prone
            self.logger.warn("Non-windows backends don't exist yet")
            # raise NotImplementedError("Set Backend not yet implemented for non-windows")

    def add_app_instance(
        self,
        app: Any = None,
        dialog: bool = True,
        params: dict = None,
    ):
        """ Add an App to list of open apps """
        if platform.system() == "windows":
            return self._windows_add_app_instance(app, dialog, params)

    def _set_windows_backend(self, backend: Optional[str] = "uia") -> None:
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
            self._backend = backend.lower()
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

    def open_application(self):
        # TODO: implement behaviour here. Windows specifically has a ton of different strategies to support
        pass

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

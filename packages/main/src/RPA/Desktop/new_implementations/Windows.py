import platform

if platform.system() == "Windows":
    import ctypes
    import win32api
    import win32com.client
    import win32con
    import win32security
    import pywinauto
    import win32gui


SUPPORTED_BACKENDS = ["uia", "win32"]

""" Windows only implementations and helpers """


def set_windows_backend(self, backend: str) -> None:
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
    if backend and backend.lower() in SUPPORTED_BACKENDS:
        self._backend = backend.lower()
    else:
        raise ValueError("Unsupported Windows backend: %s" % backend)


def _add_app_instance(
    instance: DesktopBase,
    app: Any = None,
    dialog: bool = True,
    params: dict = None,
) -> Optional[int]:
    params = params or {}
    instance._app_instance_id += 1
    process_id = None
    handle = None
    if app:
        self.app = app
        if hasattr(app, "process"):
            process_id = app.process
            handle = win32gui.GetForegroundWindow()

        default_params = {
            "app": app,
            "id": instance._app_instance_id,
            "dialog": dialog,
            "process_id": process_id,
            "handle": handle,
            "dispatched": False,
        }

        instance._apps[instance._app_instance_id] = {**default_params, **params}

        instance.logger.debug(
            "Added app instance %s: %s",
            instance._app_instance_id,
            instance._apps[instance._app_instance_id],
        )
        instance._active_app_instance = instance._app_instance_id
        return instance._active_app_instance


def log_in(self, username: str, password: str, domain: str = ".") -> str:
    """Log into Windows `domain` with `username` and `password`.

    :param username: name of the user
    :param password: password of the user
    :param domain: windows domain for the user, defaults to "."
    :return: handle

    Example:

    .. code-block:: robotframework

        Log In  username=myname  password=mypassword  domain=company
    """
    return win32security.LogonUser(
        username,
        domain,
        password,
        win32con.LOGON32_LOGON_INTERACTIVE,
        win32con.LOGON32_PROVIDER_DEFAULT,
    )


class OpenApplicationStrategies:
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
        return self._add_app_instance(app, dialog=False, params=params)

    # TODO. How to manage app launched by open_file
    def open_file(self, filename: str) -> bool:
        """Open associated application when opening file

        :param filename: path to file
        :return: True if application is opened, False if not

        Example:

        .. code-block:: robotframework

            ${app1}    Open File   /path/to/myfile.txt

        """
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
            self.set_windows_backend(backend)
        params = {
            "executable": executable,
            "windowtitle": windowtitle,
            "startkeyword": "Open Executable",
        }
        self.windowtitle = windowtitle
        app = pywinauto.Application(backend=self._backend).start(
            cmd_line=executable, work_dir=work_dir
        )

        return self._add_app_instance(app, dialog=False, params=params)

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

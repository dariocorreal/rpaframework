import subprocess
from pathlib import Path
from typing import List
from RPA.Desktop import utils
from RPA.Desktop.keywords import LibraryContext, keyword


class App:
    """Container for launched application."""

    def __init__(self, name: str, args: List[str], shell: bool = False):
        self._name = name
        self._args = args
        self._shell = shell
        self._proc = None

    def __str__(self):
        return 'App("{name}", pid:{pid})'.format(name=self._name, pid=self.pid)

    @property
    def is_running(self):
        if not self._proc:
            return False

        return self._proc.poll() is None

    @property
    def pid(self):
        return self._proc.pid if self._proc else None

    def start(self):
        if self._proc:
            raise RuntimeError("Application already started")

        self._proc = subprocess.Popen(self._args, shell=self._shell)

    def stop(self):
        if self._proc:
            self._proc.terminate()

    def wait(self, timeout=30):
        if not self._proc:
            raise RuntimeError("Application not started")

        self._proc.communicate(timeout=int(timeout))


class ApplicationKeywords(LibraryContext):
    """Keywords for starting and stopping applications."""

    def __init__(self, ctx):
        super().__init__(ctx)
        self._apps = []

    def _create_app(self, name: str, args: List[str], shell: bool = False):
        app = App(name, args, shell)
        app.start()

        self._apps.append(app)
        return app

    @keyword
    def open_application(self, name_or_path: str, *args) -> App:
        """Start a given application by name (if in PATH),
        or by path to executable.
        """
        name = Path(name_or_path).name
        return self._create_app(name, [name_or_path] + list(args))

    @keyword
    def open_file(self, path: str) -> App:
        """Open a file with the default application."""
        name = Path(path).name

        if utils.is_windows():
            return self._create_app(name, ["start", "/WAIT"], shell=True)
        elif utils.is_macos():
            return self._create_app(name, ["open", "-W", path])
        else:
            # TODO: xdg-open quits immediately after child process has started,
            # figure out default application some other way and launch directly.
            return self._create_app(name, ["xdg-open", path])

    @keyword
    def close_application(self, app: App) -> None:
        """Close given application."""
        if app.is_running:
            app.close()

    @keyword
    def close_all_applications(self) -> None:
        """Close all opened applications."""
        for app in self._apps:
            if app.is_running:
                app.close()

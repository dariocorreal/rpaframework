import logging
from abc import abstractmethod, ABC
from typing import Any, Optional

from RPA.Desktop.new_implementations.types import MouseAction


class SharedAbc(ABC):
    """Abstract class for sharing methods between the modules in
    new_implementations when inherited to desktop_base
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._apps = {}
        self._app_instance_id = 0
        self._active_app_instance = -1
        self.app = None
        self.dlg = None
        self.window_title: Optional[str] = None
        self._backend = self.validate_backend()

    @property
    @abstractmethod
    def get_window_list(self):
        ...

    @abstractmethod
    def validate_backend(self, backend: Optional[str] = None) -> str:
        ...

    @abstractmethod
    def press_keys(self, keys: str) -> None:
        ...

    @abstractmethod
    def _add_app_instance(
        self, app: Any = None, dialog: bool = True, params: dict = None
    ):
        ...

    @abstractmethod
    def switch_to_application(self, app_id: int) -> None:
        ...

    @abstractmethod
    def _get_element_coordinates(self, rectangle: Any) -> Any:
        ...

    @abstractmethod
    def restore_dialog(self, windowtitle: str = None) -> None:
        ...

    @abstractmethod
    def open_dialog(
        self,
        windowtitle: str = None,
        highlight: bool = False,
        timeout: int = 10,
        existing_app: bool = False,
    ) -> Any:
        ...

    @abstractmethod
    def connect_by_handle(self, param, existing_app):
        ...

    @abstractmethod
    def kill_process_by_pid(self, pid: int) -> None:
        ...

    @abstractmethod
    def find_element(self, locator: str, search_criteria: str = None) -> Any:
        ...

    @abstractmethod
    def get_app(self, app_id: int = None) -> Any:
        ...

    @abstractmethod
    def screenshot(
        self,
        filename: str,
        element: dict = None,
        ctrl: Any = None,
        desktop: bool = False,
        overwrite: bool = False,
    ) -> None:
        ...

    @abstractmethod
    def mouse_click(
        self,
        locator: str = None,
        off_x: int = 0,
        off_y: int = 0,
        click_type: MouseAction = MouseAction.click,
    ) -> None:
        ...

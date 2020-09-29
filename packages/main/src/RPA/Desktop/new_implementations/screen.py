import os
from datetime import time
from pathlib import Path
from typing import Any, Union, Tuple

from RPA.Images import Images
from RPA.core.helpers import clean_filename
from robot.libraries.BuiltIn import RobotNotRunningError, BuiltIn


class Screen:
    def get_dialog_rectangle(
        self, ctrl: Any = None, as_dict: bool = False
    ) -> Union[dict, Tuple[int, int, int, int]]:
        """Get dialog rectangle coordinates

        If `ctrl` is None then get coordinates from `dialog`
        :param ctrl: name of the window control object, defaults to None
        :return: coordinates: left, top, right, bottom

        Example:

        .. code-block:: robotframework

            ${left}  ${top}  ${right}  ${bottom}=  Get Dialog Rectangle
            &{coords}  Get Dialog Rectangle  as_dict=True
            Log  top=${coords.top} left=${coords.left}

        """
        if ctrl:
            rect = ctrl.element_info.rectangle
        elif self.dlg:
            rect = self.dlg.element_info.rectangle
        else:
            raise ValueError("No dialog open")

        if as_dict:
            return {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
            }
        else:
            return rect.left, rect.top, rect.right, rect.bottom

    def screenshot(
        self,
        filename: str,
        element: dict = None,
        ctrl: Any = None,
        desktop: bool = False,
        overwrite: bool = False,
    ) -> None:
        """Save screenshot into filename.

        :param filename: name of the file
        :param element: take element screenshot, defaults to None
        :param ctrl: take control screenshot, defaults to None
        :param desktop: take desktop screenshot if True, defaults to False
        :param overwrite: file is overwritten if True, defaults to False

        Example:

        .. code-block:: robotframework

            @{element}   Find Element  CalculatorResults
            Screenshot   element.png   ${elements[0][0]}
            Screenshot   desktop.png   desktop=True
            Screenshot   desktop.png   desktop=True  overwrite=True

        """
        if desktop:
            region = None
        elif element:
            region = self._get_element_coordinates(element["rectangle"])
        elif ctrl:
            region = self.get_dialog_rectangle(ctrl)
        else:
            region = self.get_dialog_rectangle()

        if region:
            left, top, right, bottom = region
            if right - left == 0 or bottom - top == 0:
                self.logger.info(
                    "Unable to take screenshot, because regions was: %s", region
                )
                return
        try:
            output_dir = BuiltIn().get_variable_value("${OUTPUT_DIR}")
        except (ModuleNotFoundError, RobotNotRunningError):
            output_dir = Path.cwd()

        filename = Path(output_dir, "images", clean_filename(filename))
        os.makedirs(filename.parent, exist_ok=overwrite)
        Images().take_screenshot(filename=filename, region=region)

        self.logger.info("Saved screenshot as '%s'", filename)

    def restore_dialog(self, windowtitle: str = None) -> None:
        """Restore window by its title

        :param windowtitle: name of the window, default `None` means that
         active window is going to be restored

        Example:

        .. code-block:: robotframework

            Open Using Run Dialog  notepad  Untitled - Notepad
            Minimize Dialog
            Sleep             1s
            Restore Dialog
            Sleep             1s
            Restore Dialog    Untitled - Notepad

        """
        windowtitle = (
            windowtitle or self._apps[self._active_app_instance]["windowtitle"]
        )
        self.logger.info("Restore dialog: %s", windowtitle)
        app = pywinauto.Application().connect(title_re=".*%s" % windowtitle)
        try:
            app.window().restore()
        except pywinauto.findwindows.ElementAmbiguousError as e:
            self.logger.info("Could not restore dialog, %s", str(e))
        finally:
            if "handle" in self._apps[self._active_app_instance]:
                app = pywinauto.Application().connect(
                    handle=self._apps[self._active_app_instance]["handle"]
                )
                app.window().restore()

    def open_dialog(
        self,
        windowtitle: str = None,
        highlight: bool = False,
        timeout: int = 10,
        existing_app: bool = False,
    ) -> Any:
        """Open window by its title.

        :param windowtitle: name of the window, defaults to active window if None
        :param highlight: draw outline for window if True, defaults to False
        :param timeout: time to wait for dialog to appear

        Example:

        .. code-block:: robotframework

            Open Dialog       Untitled - Notepad
            Open Dialog       Untitled - Notepad   highlight=True   timeout=5

        """
        self.logger.info("Open dialog: '%s', '%s'", windowtitle, highlight)

        if windowtitle:
            self.windowtitle = windowtitle

        app_instance = None
        end_time = time.time() + float(timeout)
        while time.time() < end_time and app_instance is None:
            for window in self.get_window_list():
                if window["title"] == self.windowtitle:
                    app_instance = self.connect_by_handle(
                        window["handle"], existing_app=existing_app
                    )
            time.sleep(0.1)

        if self.dlg is None:
            raise ValueError("No window with title '{}'".format(self.windowtitle))

        if highlight:
            self.dlg.draw_outline()

        return app_instance

    def minimize_dialog(self, windowtitle: str = None) -> None:
        """Minimize window by its title

        :param windowtitle: name of the window, default `None` means that
         active window is going to be minimized

        Example:

        .. code-block:: robotframework

            Open Using Run Dialog  calc     Calculator
            Open Using Run Dialog  notepad  Untitled - Notepad
            Minimize Dialog    # Current window (Notepad)
            Minimize Dialog    Calculator

        """
        windowtitle = (
            windowtitle or self._apps[self._active_app_instance]["windowtitle"]
        )
        self.logger.info("Minimize dialog: %s", windowtitle)
        self.dlg = pywinauto.Desktop(backend=self._backend)[windowtitle]
        self.dlg.minimize()

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

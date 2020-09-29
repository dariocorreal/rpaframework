class DragAndDrop:
    def _validate_target(self, target: dict, target_locator: str) -> Any:
        target_x = target_y = 0
        if target_locator is not None:
            self.switch_to_application(target["id"])
            target_elements, _ = self.find_element(target_locator)
            if len(target_elements) == 0:
                raise ValueError(
                    ("Target element was not found by locator '%s'", target_locator)
                )
            elif len(target_elements) > 1:
                raise ValueError(
                    (
                        "Target element matched more than 1 element (%d) "
                        "by locator '%s'",
                        len(target_elements),
                        target_locator,
                    )
                )
            target_x, target_y = self.calculate_rectangle_center(
                target_elements[0]["rectangle"]
            )
        else:
            target_x, target_y = self.calculate_rectangle_center(
                target["dlg"].rectangle()
            )
        return target_x, target_y

    def _select_elements_for_drag(self, src: dict, src_locator: str) -> Any:
        self.switch_to_application(src["id"])
        source_elements, _ = self.find_element(src_locator)
        if len(source_elements) == 0:
            raise ValueError(
                ("Source elements where not found by locator '%s'", src_locator)
            )
        selections = []
        source_min_left = 99999
        source_max_right = -1
        source_min_top = 99999
        source_max_bottom = -1
        for elem in source_elements:
            left, top, right, bottom = self._get_element_coordinates(elem["rectangle"])
            if left < source_min_left:
                source_min_left = left
            if right > source_max_right:
                source_max_right = right
            if top < source_min_top:
                source_min_top = top
            if bottom > source_max_bottom:
                source_max_bottom = bottom
            mid_x = int((right - left) / 2) + left
            mid_y = int((bottom - top) / 2) + top
            selections.append((mid_x, mid_y))
        source_x = int((source_max_right - source_min_left) / 2) + source_min_left
        source_y = int((source_max_bottom - source_min_top) / 2) + source_min_top
        return selections, source_x, source_y

    def drag_and_drop(
        self,
        src: Any,
        target: Any,
        src_locator: str,
        target_locator: str = None,
        handle_ctrl_key: bool = False,
        drop_delay: float = 2.0,
    ) -> None:
        # pylint: disable=C0301
        """Drag elements from source and drop them on target.

        Please note that if CTRL is not pressed down during drag and drop then
        operation is MOVE operation, on CTRL down the operation is COPY operation.

        There will be also overwrite notification if dropping over existing files.

        :param src: application object or instance id
        :param target: application object or instance id
        :param src_locator: elements to move
        :param handle_ctrl_key: True if keyword should press CTRL down dragging
        :param drop_delay: how many seconds to wait until releasing mouse drop,
         default 2.0
        :raises ValueError: on validation errors

        Example:

        .. code-block:: robotframework

            ${app1}=        Open Using Run Dialog    explorer.exe{VK_SPACE}C:\\workfiles\\movethese   movethese
            ${app2}=        Open Using Run Dialog    wordpad.exe   Document - WordPad
            Drag And Drop   ${app1}   ${app2}   regexp:testfile_\\d.txt  name:Rich Text Window   handle_ctrl_key=${True}
            Drag And Drop   ${app1}   ${app1}   regexp:testfile_\\d.txt  name:subdir  handle_ctrl_key=${True}

        """  # noqa : E501
        if isinstance(src, int):
            src = self.get_app(src)
        if isinstance(target, int):
            target = self.get_app(target)

        single_application = src["app"] == target["app"]
        selections, source_x, source_y = self._select_elements_for_drag(
            src, src_locator
        )
        target_x, target_y = self._validate_target(target, target_locator)

        self.logger.info(
            "Dragging %d elements from (%d,%d) to (%d,%d)",
            len(selections),
            source_x,
            source_y,
            target_x,
            target_y,
        )

        try:
            if handle_ctrl_key:
                self.send_keys("{VK_LCONTROL down}")
                delay(0.2)

            # Select elements by mouse clicking
            if not single_application:
                self.restore_dialog(src["windowtitle"])
            for idx, selection in enumerate(selections):
                self.logger.debug("Selecting item %d by mouse_click", idx)
                self.logger.debug(selection)
                # pywinauto.mouse.click(coords=(selection[0]+5, selection[1]+5))
                self.mouse_click_coords(selection[0] + 5, selection[1] + 5)

            # Start drag from the last item
            pywinauto.mouse.press(coords=(source_x, source_y))
            delay(0.5)
            if not single_application:
                self.restore_dialog(target["windowtitle"])
            pywinauto.mouse.move(coords=(target_x, target_y))

            self.logger.debug("Cursor position: %s", win32api.GetCursorPos())
            delay(drop_delay)
            self.mouse_click_coords(target_x, target_y)
            pywinauto.mouse.click(coords=(target_x, target_y))

            # if action_required:
            self.send_keys("{ENTER}")
            if handle_ctrl_key:
                self.send_keys("{VK_LCONTROL up}")
                delay(0.5)
            # Deselect elements by mouse clicking
            for selection in selections:
                self.logger.debug("Deselecting item by mouse_click")
                self.mouse_click_coords(selection[0] + 5, selection[1] + 5)
        finally:
            self.send_keys("{VK_LCONTROL up}")

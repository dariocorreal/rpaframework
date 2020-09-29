class Keyboard:
    def type_keys(self, keys: str) -> None:
        """Type keys into active window element.

        :param keys: list of keys to type

        Example:

        .. code-block:: robotframework

            Open Executable  notepad.exe  Untitled - Notepad
            Type Keys   My text

        """
        self.logger.info("Type keys: %s", keys)
        if self.dlg is None:
            raise ValueError("No dialog open")
        self.dlg.type_keys(keys)

    def type_into(self, locator: str, keys: str, empty_field: bool = False) -> None:
        """Type keys into element matched by given locator.

        :param locator: element locator
        :param keys:    list of keys to type

        Example:

        .. code-block:: robotframework

            Open Executable  calc.exe  Calculator
            Type Into        CalculatorResults  11
            Type Into        CalculatorResults  22  empty_field=True

        """
        elements, _ = self.find_element(locator)
        if elements and len(elements) == 1:
            ctrl = elements[0]["control"]
            if empty_field:
                ctrl.type_keys("{VK_LBUTTON down}{VK_CLEAR}{VK_LBUTTON up}")
            ctrl.type_keys(keys)
        else:
            raise ValueError(f"Could not find unique element for '{locator}'")

    def send_keys(self, keys: str) -> None:
        """Send keys into active windows.

        :param keys: list of keys to send

        Example:

        .. code-block:: robotframework

            Open Executable  calc.exe  Calculator
            Send Keys        2{+}3=

        """
        self.logger.info("Send keys: %s", keys)
        pywinauto.keyboard.send_keys(keys)

    def get_spaced_string(self, text):
        """Replace spaces in a text with `pywinauto.keyboard`
        space characters `{VK_SPACE}`

        :param text: replace spaces in this string

        Example:

        .. code-block:: robotframework

            ${txt}    Get Spaced String   My name is Bond
            # ${txt} = My{VK_SPACE}name{VK_SPACE}is{VK_SPACE}Bond

        """
        return text.replace(" ", "{VK_SPACE}")

    def send_keys_to_input(
        self,
        keys_to_type: str,
        with_enter: bool = True,
        send_delay: float = 0.5,
        enter_delay: float = 1.5,
    ) -> None:
        """Send keys to windows and add ENTER if `with_enter` is True

        At the end of send_keys there is by default 0.5 second delay.
        At the end of ENTER there is by default 1.5 second delay.

        :param keys_to_type: keys to type into Windows
        :param with_enter: send ENTER if `with_enter` is True
        :param send_delay: delay after send_keys
        :param enter_delay: delay after ENTER

        Example:

        .. code-block:: robotframework

            ${txt}    Get Spaced String   My name is Bond, James Bond
            Send Keys To Input  ${txt}    with_enter=False
            Send Keys To Input  {ENTER}THE   send_delay=5.0  with_enter=False
            Send Keys To Input  {VK_SPACE}-{VK_SPACE}END   enter_delay=5.0

        """
        # Set keyboard layout for Windows platform
        if platform.system() == "Windows":
            win32api.LoadKeyboardLayout("00000409", 1)

        self.send_keys(keys_to_type)
        delay(send_delay)
        if with_enter:
            self.send_keys("{ENTER}")
            delay(enter_delay)

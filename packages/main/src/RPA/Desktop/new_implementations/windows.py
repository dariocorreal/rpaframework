import platform

from RPA.core.helpers import delay

if platform.system() == "Windows":
    import win32com.client
    import win32con
    import win32security
    import pywinauto

""" Windows only implementations and helpers """


def log_in(username: str, password: str, domain: str = ".") -> str:
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

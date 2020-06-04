import logging
from urllib.parse import urlparse
from typing import Any

from RequestsLibrary import RequestsLibrary
from RPA.FileSystem import FileSystem


class HTTP(RequestsLibrary):
    """RPA Framework HTTP library that wraps
    _RequestsLibrary_ functionality.
    """

    def __init__(self, *args, **kwargs) -> None:
        RequestsLibrary.__init__(self, *args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.fs = FileSystem()
        self.session_alias_prefix = "rpasession_alias."
        self.current_session_alias = None

    def http_get(
        self,
        url: str,
        target_file: str = None,
        binary: bool = True,
        verify: bool = True,
        force_new_session: bool = False,
        overwrite: bool = False,
    ) -> dict:
        """
        A helper method for `Get Request` that will create a session, perform GET
        request, and store the target file, if set by the `target_file` parameter.

        The old session will be used if thr URL scheme and the host are the same as
        previously, e.g., 'https://www.google.fi' part of the URL.

        :param url: target URL for GET request
        :param target_file: filepath to save request content, default `None`
        :param binary: if `True`, file is saved as binary, default `True`
        :param verify: if SSL verification should be done, default `True`
        :param force_new_session: if new HTTP session should be created, default `False`
        :param overwrite: used together with `target_file`, if `True` will
            overwrite the target file
        :return: request response
        """
        uc = urlparse(url)

        http_host = f"{uc.scheme}://{uc.netloc}"
        request_alias = f"{self.session_alias_prefix}{uc.scheme}{uc.netloc}"
        url_path = url.replace(http_host, "")
        if force_new_session or not self.session_exists(request_alias):
            self.logger.info("Creating a new HTTP session")
            self.create_session(request_alias, http_host, verify=verify)
        else:
            self.logger.info("Using already existing HTTP session")
        self.current_session_alias = request_alias
        response = self.get_request(request_alias, url_path)
        if target_file is not None:
            self._create_or_overwrite_target_file(
                target_file, response.content, binary, overwrite
            )
        return response

    def _create_or_overwrite_target_file(
        self, target_file: str, content: Any, binary: bool, overwrite: bool,
    ) -> None:
        if binary:
            self.fs.create_binary_file(target_file, content, overwrite)
        else:
            self.fs.create_file(target_file, content, overwrite)

    def get_current_session_alias(self) -> str:
        """Get request session alias that was used with the `HTTP Get` keyword.

        :return: name of session alias
        """
        return self.current_session_alias

    def download(
        self,
        url: str,
        target_file: str = None,
        binary: bool = True,
        verify: bool = True,
        force_new_session: bool = False,
        overwrite: bool = False,
    ) -> dict:
        """An alias for the `HTTP Get` keyword.

        The difference in use is that the URL is always downloaded based on
        the URL path (even without `target_file`). If there is a filename
        in the path, then that is used as `target_file` to save to. By default,
        the filename will be `downloaded.html`.
        """
        response = self.http_get(
            url, target_file, binary, verify, force_new_session, overwrite
        )
        if target_file is None:
            uc = urlparse(url)
            target = uc.path.rsplit("/", 1)[-1]
            if not target:
                target = "downloaded.html"

            self._create_or_overwrite_target_file(
                target, response.content, binary, overwrite
            )
        return response

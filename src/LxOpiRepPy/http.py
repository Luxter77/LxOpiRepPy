from typing import Any, Callable, Optional

import requests as re
from fake_useragent import UserAgent
from stem import Signal
from stem.control import Controller

from .logging import log

class AnonimousEngine:
    """
    Stubborn and anonymous requests engine using Tor for anonymity.

    Attributes:
        s_conf (str): Configuration for the Tor SOCKS proxy.
        controller: Stem Controller for interacting with Tor.
        session (requests.Session): HTTP session for making requests.
        eip (Optional[Exception]): Exception encountered during IP retrieval.
        cip (str): Current external IP address.

    Methods:
        __init__(password: str = "password", s_conf: str = "socks5://localhost:9050"):
            Initializes the AnonimousEngine with default or provided settings.

        get_new_ip() -> None:
            Gets a new IP address by signaling Tor to create a new circuit and checks its reliability.

        check_ip() -> bool:
            Checks the reliability of the current IP address.

        get(url: str, *args, **kwargs) -> requests.Response:
            Sends a GET request to the specified URL using the configured session.

        post(url: str, *args, **kwargs) -> requests.Response:
            Sends a POST request to the specified URL using the configured session.

        _retry_loop(func: Callable[[Any], requests.Response], *args, **kwargs) -> requests.Response:
            Internal method implementing a retry loop for request execution in case of exceptions.
    """
    def __init__(self,
                 password: str = "password",
                 s_conf:   str = "socks5://localhost:9050"):
        """
        Initializes the AnonimousEngine with the provided password and Tor SOCKS proxy configuration.

        Args:
            password (str): Password for authenticating with the Tor controller. Defaults to "password".
            s_conf (str): Configuration for the Tor SOCKS proxy. Defaults to "socks5://localhost:9050".
        """
        self.s_conf = {"http": s_conf, "https": s_conf}

        self.controller = Controller.from_port()
        self.controller.authenticate(password=password)

        self.session: re.Session      = None
        self.eip: Optional[Exception] = None
        self.cip: str                 = ""

        self.get_new_ip()

    def get_new_ip(self) -> None:
        """
        Gets a new IP address by signaling Tor to create a new circuit and checks its reliability.
        """
        bad = True
        while bad:
            # "signal NEWNYM" will make Tor switch to clean circuits
            # so new application requests don't share any circuits with old ones.
            # this effectively resets the external IP
            self.controller.signal(Signal.NEWNYM) # pylint: disable=no-member
            self.session = re.Session()
            self.session.proxies = self.s_conf
            self.session.headers.update({"User-Agent": UserAgent().random})
            bad = self.check_ip()

    def check_ip(self) -> bool:
        """
        Checks the reliability of the current IP address.

        Returns:
            bool: True if the IP is unreliable, False otherwise.
        """
        # check the output node's reliability
        # (some output nodes are evil and should not be used).
        # I considere a node evil if it messes with HTTPs conecctions, whitch is unacceptable.

        try:
            self.cip, self.eip = str(self.session.get("https://api.ipify.org/?format=json").json()["ip"]), None
        except (re.exceptions.RequestException, re.exceptions.Timeout) as e:
            self.cip, self.eip = Exception('IP_NOT_KNOWN'), e
            log(f"DBG_:  [ AnonimousEngine {id(self)} ]: " + repr(e))
            return True

        if "DOCTYPE" in str(self.cip):
            log(f"DBG_: [ AnonimousEngine {id(self)} ]: NEW EXTERNAL IP‽")
        else:
            log(f"DBG_: [ AnonimousEngine {id(self)} ]: NEW EXTERNAL IP! [ {self.cip} ]")
        return False

    def get(self, url: str, *args, **kwargs) -> re.Response:
        """
        Sends a GET request to the specified URL using the configured session.

        Args:
            url (str): The URL to send the GET request to.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            requests.Response: The response object from the GET request.
        """
        return self._retry_loop(self.session.get, *args, url=url, **kwargs)

    def post(self, url: str, *args, **kwargs) -> re.Response:
        """
        Sends a POST request to the specified URL using the configured session.

        Args:
            url (str): The URL to send the POST request to.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            requests.Response: The response object from the POST request.
        """
        return self._retry_loop(self.session.post, *args, url=url, **kwargs)

    def _retry_loop(self, func: Callable[[Any], re.Response], *args, **kwargs) -> re.Response:
        """
        Internal method implementing a retry loop for request execution in case of exceptions.

        Args:
            func (Callable[[Any], requests.Response]): Function to execute.
            *args: Variable length argument list to be passed to func.
            **kwargs: Arbitrary keyword arguments to be passed to func.

        Returns:
            requests.Response: The response object from the executed function.
        """
        j = None
        while j is None:
            try:
                j: re.Response = func(*args, **kwargs)
            except (re.exceptions.RequestException, re.exceptions.Timeout) as e:
                log(f"DBG_: [ AnonimousEngine {id(self)} ]: {repr(e)}")
                self.get_new_ip()
                j = None
        return j

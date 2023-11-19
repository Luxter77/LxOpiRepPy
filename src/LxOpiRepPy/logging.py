import logging
import sys

from pprint import pformat
from typing import Any

from tqdm.auto import tqdm # pylint: disable=import-error # bug

# COLORS!
try:
    import colorama as col

    # see https://github.com/tartley/col/issues/21
    # breaks some windows systems but fixes other windows systems
    col.deinit()
    col.init(strip=False)

    COL_IMPORTED = True
except ImportError:
    COL_IMPORTED = False

def log(obj: Any):
    """
    Formats and logs the given object with color-coded prefixes indicating log levels.

    Args:
    - obj (object): The object to be logged.

    The function uses the `pformat` method from the `pprint` module to format the object.
    The formatted output is color-coded based on predefined prefixes in the string representation
    of the object. These prefixes are used to identify different log levels and apply corresponding colors:

    - 'DBG_' (Debug): Logs the object with a light black foreground and black background.
    - 'INFO' (Informational): Logs the object with a white foreground and black background.
    - 'WARN' (Warning): Logs the object with a yellow foreground and black background.
    - 'ERR_' (Error): Logs the object with a red foreground and black background.
    - 'FATA' (Fatal): Logs the object with a black foreground and red background.

    If the object's string representation doesn't match any of these prefixes, it defaults to INFO level logging.

    Note:
    - The function relies on the 'colorama' library for terminal coloring.
    - Different log levels are represented by different colors for better visibility and distinction.
    - In case 'colorama' is not installed or fails to initialize, logging will occur without color formatting.

    Example:
    >>> log("INFO: This is an informational message.")
    >>> log("ERR_: This is an error message.")
    >>> log("Custom log message.")
    """
    out = pformat(obj, indent=4, width=sys.maxsize)

    s = out[:4].upper()

    pre = ""

    if   s == 'DBG_':
        if COL_IMPORTED: pre = col.Fore.LIGHTBLACK_EX + col.Back.BLACK
        logging.log(logging.DEBUG, pre + out)
    elif s == 'INFO':
        if COL_IMPORTED: pre = col.Fore.WHITE + col.Back.BLACK
        logging.log(logging.INFO,  pre + out)
    elif s == 'WARN':
        if COL_IMPORTED: pre = col.Fore.YELLOW + col.Back.BLACK
        logging.log(logging.WARN,  pre + out)
    elif s == 'ERR_':
        if COL_IMPORTED: pre = col.Fore.RED + col.Back.BLACK
        logging.log(logging.ERROR, pre + out)
    elif s == 'FATA':
        if COL_IMPORTED: pre = col.Fore.BLACK + col.Back.RED
        logging.log(logging.FATAL, pre + out)
    else:
        if COL_IMPORTED: pre = col.Fore.WHITE + col.Back.BLACK
        logging.log(logging.INFO,  pre + out)

class TqdmLoggingHandler(logging.Handler):
    """Custom logging handler that redirects log messages to tqdm progress bar.

    This class extends the logging.Handler class to redirect log messages to a tqdm progress bar.
    It is specifically designed to integrate logging output with tqdm's progress bar display.

    Attributes:
        level (int): The logging level for the handler (default is logging.INFO).
    
    Methods:
        emit(record): Overrides the base class's emit method to redirect log messages to tqdm.

    Usage:
        To use this handler, create an instance of TqdmLoggingHandler and add it to the logger:
        ```
        import logging
        from tqdm.auto import tqdm

        logger = logging.getLogger(__name__)
        handler = TqdmLoggingHandler()
        logger.addHandler(handler)
        ```
    """
    def __init__(self, level=logging.INFO):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except Exception: # pylint: disable=broad-exception-caught
            self.handleError(record)

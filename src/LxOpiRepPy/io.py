import base64
import dataclasses
import datetime as dt
import json
import os
from decimal import Decimal
from pprint import pformat
from typing import Any, Generator, Optional, Union

def or_none(o: Optional[object]) -> Optional[object]:
    """return o if o else None"""
    return o if o else None

def clean(o: Any) -> Union[int, float, bool, dict, list]:
    """
    Cleans the input object by converting it into a simplified form
    containing only primitive data types (int, float, bool), dictionaries, and lists.

    Args:
        - o (Any): The input object to be cleaned.

    Returns:
        - Union[int, float, bool, dict, list]: The cleaned object represented in a simplified form.

    Note:
        - For input types like Generator, list, tuple: Converts to a list of cleaned elements.
        - For dataclasses: Converts to a dictionary and cleans the contents.
        - For dictionaries: Recursively cleans keys and values.
        - For int, float, bool, or None: Returns the same value.
        - For other types: Converts to a string representation.
    """
    if isinstance(o, (Generator, list, tuple)):
        return list(clean(x) for x in o)
    if dataclasses.is_dataclass(o):
        return clean(dataclasses.asdict(o))
    if isinstance(o, dict):
        return {(clean(k), clean(v)) for k, v in o.items()}
    if isinstance(o, (int, float, bool)) or (o is None):
        return o
    return str(o)

def win_slug(fname: Union[str, os.PathLike], rep: str = '_') -> str:
    """
    Generates a Windows-compatible slug from the provided path by replacing
    characters that are not valid in Windows filenames with a specified
    replacement character.

    Args:
        - path (Union[str, os.PathLike]): The input path for which a slug is generated.
        - rep (str): The replacement character for invalid characters in the path.
                    Default is "_".

    Returns:
        - str: A Windows-compatible slug derived from the input path.

    Raises:
        - TypeError: If the provided path is not a string or a path-like object.

    Note:
        The function replaces characters not allowed in Windows filenames 
        ('<', '>', ':', '"', '/', '|', '?', '\\', '*', etc) with the specified
        replacement character.
    """
    return(''.join((char if char.lower() in '-_.() abcdefghijklmnopqrstuvwxyz0123456789' else rep) for char in fname))

class JsonEncoder(json.JSONEncoder):
    """
    Custom JSON Encoder for handling specific data types during JSON serialization.

    Methods:
        - default(o): Overrides the default method of `json.JSONEncoder` to handle encoding
        for specific data types:
            - set: Converts sets to lists for JSON serialization.
            - Exception: Formats exceptions using `pprint.pformat` for better readability.
            - dt.datetime, dt.date: Converts datetime objects to ISO 8601 format strings.
            - Decimal: Converts Decimal objects to float for JSON serialization.
            - bytes: Encodes bytes to Base64 strings for JSON serialization.
            - Dataclasses: Converts dataclass instances to dictionaries using `dataclasses.asdict`.

    Usage:
        Instantiate this class and pass it to the `json.dump` or `json.dumps` method
        as the `cls` argument to customize JSON serialization for specific data types.

    Example:
        ```python
        custom_encoder = JsonEncoder()
        json_str = json.dumps(data, cls=custom_encoder)
        ```
    """
    def default(self, o):
        """
        Overrides the default method of `json.JSONEncoder` to handle encoding
        for specific data types during JSON serialization.

        Args:
            - o: The object to be serialized to JSON.

        Returns:
            - Serialized JSON-compatible representations of specific data types.

        Raises:
            - No specific exceptions raised by this method.

        Notes:
            This method handles encoding for various data types such as set, Exception,
            datetime objects, Decimal, bytes, and dataclasses, converting them into
            JSON-serializable representations.
        """
        if isinstance(o, set):
            return list(o)
        if isinstance(o, Exception):
            return pformat(o)
        if isinstance(o, dt.datetime):
            return o.isoformat()
        if isinstance(o, dt.date):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, bytes):
            return base64.b64encode(o).decode('utf-8')
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return json.JSONEncoder.default(self, o)

class LastTimeGetter:
    """
    A class to manage the retrieval and storage of the last recorded time.

    Attributes:
        - fname (Union[os.PathLike, str]): The file path or file name (default: 'last_time.json').
        - fname_bkp (str): The backup file name created based on 'fname'.
        - last_time (dt.datetime): The last recorded time.

    Methods:
        - __init__(self, fname: Union[os.PathLike, str] = 'last_time.json'): Initializes the LastTimeGetter instance.
        - get(self) -> dt.datetime: Retrieves the last recorded time from the specified file.
        - set(self, time: dt.datetime = None): Sets the last recorded time and updates the file accordingly.
    """
    def __init__(self, fname: Union[os.PathLike, str] = 'last_time.json'):
        """
        Initializes the LastTimeGetter instance.

        Args:
            - fname (Union[os.PathLike, str]): The file path or file name (default: 'last_time.json').
        """
        self.fname = fname

        n = fname.split('.')
        self.fname_bkp = '.'.join(n[:-1]) + '_bkp.' + n[-1] # last_time_bkp.json

        self.last_time = None
        self.get()

    def get(self) -> dt.datetime:
        """
        Retrieve the last accessed time.

        Retrieves the last accessed time from the specified file.
        If the file does not exist or encounters a JSON decoding error, it defaults to the current time.

        Returns:
            - dt.datetime: The last accessed time.
        """
        try:
            self._get(self.fname)
        except (json.JSONDecodeError, FileNotFoundError):
            try:
                self._get(self.fname_bkp)
            except (json.JSONDecodeError, FileNotFoundError):
                self.last_time = dt.datetime.now()
        return self.last_time

    def _get(self, fdir: Union[os.PathLike, str]):
        with open(fdir, 'r', encoding='utf-8') as file:
            self.last_time = dt.datetime.fromisoformat(json.load(file))

    def set(self, time: dt.datetime = None):
        """
        Set the last accessed time.

        Sets the last accessed time to the provided time or the current time if not specified.
        Updates both the primary and backup files with the new last accessed time.

        Args:
            - time (dt.datetime, optional): The time to set as the last accessed time. Defaults to None.
        """
        if time is None:
            self.last_time = dt.datetime.now()
        with open(self.fname, 'w', encoding='utf-8') as file:
            json.dump(self.last_time.isoformat(), file)
        with open(self.fname_bkp, 'w', encoding='utf-8') as bkp:
            json.dump(self.last_time.isoformat(), bkp)

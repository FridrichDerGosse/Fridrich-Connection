"""
deamons/connection/communication/_protocol.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import TypedDict
from json import loads, dumps
import socket


##################################################
#                     Code                       #
##################################################

class HeaderDict(TypedDict):
    time: float
    data: dict[str | int | float | bool | None, any]


class MessageToLongError(Exception):
    ...

class _Protocol:
    """
    Encapsulate, decapsulate the protocol
    """
    __max_size: int
    __encoding: str

    def __init__(self) -> None:
        self.max_size = 4

    @property
    def max_size(self) -> int:
        """
        Returns the number of bytes that are used to communicate the message length
        """
        return self.__max_size

    @max_size.setter
    def max_size(self, value: int) -> None:
        """
        Set max message size

        :param value: Number of bites to communicate max_size
        """
        self.__max_size = 2 ** (value * 8)


    def encapsulate(self, message: dict[str | int | float | bool | None, any]) -> tuple(bytes, bytes):
        """
        Add additional information
        :param message: Raw message
        :return: Encapsulated message
        """
        additional_information: HeaderDict = {
            "time": datetime.now().timestamp(),
            "data": message
        }

        message_str: str = dumps(additional_information)

        if len(message_str) > self.max_size:
            raise MessageToLongError(f"With a size of {message_str} the message is to long!")

        "a".encode()


        return ""


Protocol = _Protocol()

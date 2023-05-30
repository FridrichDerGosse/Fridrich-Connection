"""
deamons/connection/protocol/_fdc_protocol.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import Literal
from datetime import datetime
from json import loads, dumps

from ._protocol_types import BulkDict, MessageDict, KINDS
from ._fcm_subprotocol import FCMP

##################################################
#                     Code                       #
##################################################


class MessageToLongError(Exception):
    ...


class FDCP:
    """
    Fridrich-Default-Communication-Protocol
    Protocol for send and response bulks

    Comes with FCMP by default
    """
    __max_bytes: int
    __max_size: int
    __even: bool

    __sub_range: range
    __sub_count: int

    __id_range: range
    __id_count: int

    __send_bulk: list[MessageDict]
    __resp_bulk: list[MessageDict]

    __fcmp: FCMP

    def __init__(
            self,
            max_size: int = 4,
            even: bool | None = False,
            id_range: range = range(100, 999)
    ) -> None:
        """
        Create protocol
        :param max_size: Num of bytes for length
        :param even: Whether the even or the odd numbers should be taken for the ids
        :param id_range: Numrange for message id (0 - 1000 is reserved)
        """
        self.max_size = max_size
        self.__even = even
        self.__id_range = id_range

        self.__id_count = self.__id_range.start + (1 if even else 0)
        self.__send_bulk = []
        self.__resp_bulk = []

        self.__fcmp = FCMP(self)

    @property
    def fcmp(self) -> FCMP:
        """
        Return FCM-Protocol
        :return: Protocol instance
        """
        return self.__fcmp

    @property
    def max_size(self) -> int:
        """
        :return: The number of bytes that are used to communicate
        """
        return self.__max_size

    @property
    def max_bytes(self) -> int:
        """
        :return: The number of bytes that are used to communicate the message length
        """
        return self.__max_bytes

    @max_size.setter
    def max_size(self, value: int) -> None:
        """
        Set max message size
        :param value: Number of bytes to communicate max_size
        """
        self.__max_bytes = value
        self.__max_size = 2 ** (value * 8)

    def _encapsulate(
            self,
            message: dict[str | int | float | bool | None, any] | list[MessageDict],
            kind: KINDS | Literal["single_send", "single_resp"],
            _id: int | None = None
    ) -> None | str:
        """
        Encapsulate message
        :param message: The message itself
        :param kind: What kind of message it is
        :param _id: Specify id
        :return: Depens on kind
        """
        # Choose what id to use
        info_id: int
        match kind:
            case "single_send" | "send":
                info_id = self.__id_count
            case _:
                info_id = _id

        # Base encapsulation
        additional_information: MessageDict | BulkDict = {
            "id": info_id,
            "time": datetime.now().timestamp(),
            "data": [message]
        }

        # Additional encapsulation
        match kind:
            case "send" | "resp":
                additional_information: BulkDict = additional_information
                additional_information["kind"] = kind

        # Increase ids
        match kind:
            case "single_send" | "send":
                self.__id_count += 2
                if self.__id_count >= self.__id_range.stop:
                    self.__id_count = self.__id_range.start + (1 if self.__even else 0)

        # Return | save result
        match kind:
            case "single_send":
                self.__send_bulk.append(additional_information)

            case "single_response":
                self.__resp_bulk.append(additional_information)

            case "send" | "resp" | "sub":
                message_str: str = dumps(additional_information)

                if len(message_str) > self.max_size:
                    raise MessageToLongError(f"With a size of {message_str} the message is to long!")

                length: str = len(message_str).to_bytes(length=self.__max_size, byteorder="big", signed=False).hex()
                return length + message_str

        return None

    def send_start(self) -> None:
        """
        Start a bulk send encapsulation message queue
        """
        self.__send_bulk = []

    def send_add(self, message: dict[str | int | float | bool | None, any]) -> None:
        """
        Add a send message to the bulk queue
        :param message: Message to add
        """
        self._encapsulate(message, kind="single_send")

    def send_get(self, restart: bool = True) -> str:
        """
        Get the whole encapsulated bulk send message queue
        :param restart: Whether the send queue should be reseted
        :return: String to send
        """
        try:
            return self._encapsulate(self.__send_bulk, kind="send")
        finally:
            if restart:
                self.send_start()

    def response_start(self) -> None:
        """
        Start a bulk response encapsulation message queue
        """
        self.__resp_bulk = []

    def response_add(self, message: dict[str | int | float | bool | None, any]) -> None:
        """
        Add a response message to the bulk queue
        :param message:
        :return:
        """
        self._encapsulate(message, kind="single_resp")

    def response_get(self, restart: bool = True) -> str:
        """
        Get the whole encapsulated bulk response message queue
        :param restart: Whether the response queue should be reseted
        :return: String to send
        """
        try:
            return self._encapsulate(self.__resp_bulk, kind="resp")
        finally:
            if restart:
                self.response_start()

    def sub_protocol(
            self,
            message: dict[str | int | float | bool | None, any],
            _id: int,
            kind: KINDS
    ) -> str:
        """
        Encapsulation for sub-protocols
        :param message: Data of the message
        :param _id: The ID to use
        :param kind: Protocol type
        :return: The encapsulated message string
        """
        return self._encapsulate(message, kind=kind, _id=_id)

    def decapsulate(self, messages: bytes) -> BulkDict:
        """
        Decode and convert to dict
        :param messages: Raw bytes without length header
        :return: Dictonary with data
        """
        return loads(messages.decode())
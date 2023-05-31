"""
deamons/connection/protocol/_protocol.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from datetime import datetime
from typing import get_args
from json import dumps

from ._types import BulkDict, MessageDict, KINDS, DIRECTIONS, DATAUNIT


##################################################
#                     Code                       #
##################################################


class MessageToLongError(Exception):
    ...


class Protocol:
    """
    Default protocol for all kinds and directions of messages
    """
    max_bytes: int = 4
    max_size: int = 4294967296

    __bulks: dict[DIRECTIONS, list[MessageDict]]
    __kind: KINDS

    _id_range: range
    _id_count: int

    def __init__(
            self,
            kind: KINDS,
            id_range: range = range(100, 999)
    ) -> None:
        """
        Configure protocol and id system
        :param kind: Specify kind of this protocol
        :param id_range: Numrange for message id (0 - 1000 is reserved)
        """
        self.__kind = kind

        self.__id_range = id_range
        self._id_count = id_range.start

        self.__bulks = {}
        for direction in get_args(DIRECTIONS):
            self.__bulks[direction] = []

    @classmethod
    def set_max_bytes(cls, value: int) -> None:
        """
        Set the bytes to communicate the maximum length for all protocols
        :param value: New value to set
        """
        cls.max_bytes = value
        cls.max_size = 2 ** (value * 8)

    @property
    def id_count(self) -> int:
        """
        :return: Current id count
        """
        return self._id_count

    def _encapsulate(
            self,
            message: DATAUNIT | list[MessageDict],
            direction: DIRECTIONS,
            single: bool | None = True,
            id_: int | None = None
    ) -> None | str:
        """
        Encapsulate message
        :param message: The message itself
        :param direction: Specify the message direction
        :param single: Whether it's a single message that should be added to the queue or the whole queue request
        :param id_: When no new ID should be used (when direction is response)
        :return: Depends on single
        :raises MessageToLongError: If message is to long to communicate length
        """
        # Base encapsulation
        additional_information: MessageDict | BulkDict = {
            "time": datetime.now().timestamp(),
            "data": message
        }

        # Additional encapsulation
        if single:
            additional_information: MessageDict
            additional_information["id"] = id_ if id_ is not None else self._id_count
        else:
            additional_information: BulkDict
            additional_information["direction"] = direction
            additional_information["kind"] = self.__kind

        # Increase id
        if not id_:
            self._id_count += 1
            if self._id_count >= self._id_range.stop:
                self._id_count = self._id_range.start

        # Return | Save in bulk
        if single:
            self.__bulks[direction].append(additional_information)
        else:
            message_str: str = dumps(additional_information)

            if len(message_str) > self.__class__.max_size:
                raise MessageToLongError(f"With a size of {message_str} the message is to long!")

            return message_str
        return None

    def request_start(self) -> None:
        """
        Start a bulk request message queue
        """
        self.__bulks["request"] = []

    def request_add(self, message: DATAUNIT) -> None:
        """
        Add a message to the request bulk queue
        :param message: Message to add
        """
        self._encapsulate(message, direction="request")

    def request_get(self, restart: bool = True) -> str | None:
        """
        Get the whole request message queue
        :param restart: Whether the request queue should be reseted
        :return: String to send
        """
        try:
            if self.__bulks["request"]:
                return self._encapsulate(self.__bulks["request"], direction="request", single=False)
            return None
        finally:
            if restart:
                self.request_start()

    def response_start(self) -> None:
        """
        Start a bulk response message queue
        """
        self.__bulks["response"] = []

    def response_add(self, message: DATAUNIT, id_: int) -> None:
        """
        Add a message to the response bulk queue
        :param message: Message to add
        :param id_: ID the response is marked with
        """
        self._encapsulate(message, direction="response", id_=id_)

    def response_get(self, restart: bool = True) -> str | None:
        """
        Get the whole response message queue
        :param restart: Whether the response queue should be reseted
        :return: String to send
        """
        try:
            if self.__bulks["response"]:
                return self._encapsulate(self.__bulks["response"], direction="response", single=False)
            return None
        finally:
            if restart:
                self.response_start()

    def process_response(self, message: BulkDict) -> None:
        """
        Every protocol should overwrite this function to process incomming responses
        """
        ...

    def process_request(self, message: BulkDict) -> str | None:
        """
        Every protocol should overwrite this function to process incomming requests
        """
        ...

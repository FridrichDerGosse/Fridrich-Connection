"""
fridex/connection/protocol/_connection.py

Project: Fridrich-Connection
Created: 13.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import TypedDict, Literal, Callable, Any

from ._types import BulkDict, MessageDict
from ._protocol import Protocol


##################################################
#                     Code                       #
##################################################

class ControlData(TypedDict):
    type: Literal["ping", "alive"]


class ControlProtocol:
    """
    Protocol for connection control
    """
    __protocol: Protocol

    PING_CALLBACK_TYPE = Callable[[], Any]

    __ping_callback: PING_CALLBACK_TYPE

    def __init__(
            self,
            id_range: range,
            ping_callback: PING_CALLBACK_TYPE
    ) -> None:
        """
        Create control protocol
        :param id_range: ID range to use for this subprotocol
        :param ping_callback: Callback when ping response is received
        """
        self.__protocol = Protocol("con", id_range)
        self.__ping_callback = ping_callback

    def __response(self, data: ControlData, id_: int) -> str:
        """
        General response encapsulation
        :param data: Response dictonary
        :param id_: ID of the conversation
        :return: Raw string to send
        """
        self.__protocol.response_add(data, id_)
        return self.__protocol.response_get()

    def __request(self, data: ControlData) -> str:
        """
        General request encapsulation
        :param data: Dictonary to encapsulate
        :return: Raw string to send
        """
        self.__protocol.request_add(data)
        return self.__protocol.request_get()

    def request_ping(self) -> str:
        """
        Request ping eachother
        :return: Ping string to send
        """
        return self.__request({"type": "ping"})

    def _response_ping(self, id_: int) -> str:
        """
        Confirm ping request
        :param id_: ID of the conversation
        :return: Confirm message
        """
        return self.__response({"type": "ping"}, id_)

    def request_alive(self) -> str:
        """
        Provide alive message
        :return: String to send
        """
        return self.__request({"type": "alive"})

    def process_response(self, message: BulkDict) -> None:
        """
        Process incoming control responses
        :param message: Response message
        """
        submessage: MessageDict = message["data"][0]
        match submessage["data"]["type"]:
            case "ping":
                self.__ping_callback()

    def process_request(self, message: BulkDict) -> str | None:
        """
        Process incoming control requests
        :param message: Request message
        :return: Response message
        """
        submessage: MessageDict = message["data"][0]
        id_: int = submessage["id"]

        match submessage["data"]["type"]:
            case "ping":
                return self._response_ping(id_)
            case "alive":
                self.__ping_callback()

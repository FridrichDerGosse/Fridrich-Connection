"""
deamons/connection/protocol/_control.py

Project: Fridrich-Connection
Created: 30.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import TypedDict, Any, Callable

from ._types import BulkDict, MessageDict
from ._protocol import Protocol

from ..encryption import CRYPTION_METHODS


##################################################
#                     Code                       #
##################################################

class ControlData(TypedDict):
    type: str
    value: Any


class ControlProtocol:
    """
    Protocol for connection control
    """
    __protocol: Protocol

    NEW_KEY_CALLBACK_TYPE = Callable[[], str]
    SET_KEY_CALLBACK_TYPE = Callable[[str], Any]
    PING_CALLBACK_TYPE = Callable[[], Any]
    MAX_BYTES_CALLBACK_TYPE = Callable[[int], Any]
    CRYPTION_CALLBACK_TYPE = Callable[[str], tuple[NEW_KEY_CALLBACK_TYPE, SET_KEY_CALLBACK_TYPE]]

    __new_key_callback: NEW_KEY_CALLBACK_TYPE
    __set_key_callback: SET_KEY_CALLBACK_TYPE
    __ping_callback: PING_CALLBACK_TYPE
    __max_bytes_callback: MAX_BYTES_CALLBACK_TYPE
    __cryption_callback: CRYPTION_CALLBACK_TYPE

    def __init__(
            self,
            id_range: range,
            new_key_callback: NEW_KEY_CALLBACK_TYPE,
            set_key_callback: SET_KEY_CALLBACK_TYPE,
            ping_callback: PING_CALLBACK_TYPE,
            max_bytes_callback: MAX_BYTES_CALLBACK_TYPE,
            cryption_callback: CRYPTION_CALLBACK_TYPE
    ) -> None:
        """
        Create control protocol
        :param id_range: ID range to use for this subprotocol
        :param new_key_callback: Callback to generate a new key and get it
        :param set_key_callback: Callback when a new key is received
        :param ping_callback: Callback when ping response is received
        :param max_bytes_callback: Callback to set new max bytes
        :param cryption_callback: Callback to set new encryption,
        Should return new ney_key_callback, set_key_callback
        """
        self.__protocol = Protocol("con", id_range)
        self.__new_key_callback = new_key_callback
        self.__ping_callback = ping_callback
        self.__set_key_callback = set_key_callback
        self.__max_bytes_callback = max_bytes_callback
        self.__cryption_callback = cryption_callback

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

    def request_key_exchange(self) -> str:
        """
        Request exchanging encryption keys
        :return: Raw string to send
        """
        return self.__request({"type": "key", "value": self.__new_key_callback()})

    def _response_key_exchange(self, id_: int) -> str:
        """
        Also send back a new key
        :param id_: ID of the conversation
        :return: Confirm message
        """
        return self.__response({"type": "key", "value": self.__new_key_callback()}, id_)

    def request_ping(self) -> str:
        """
        Request ping eachother
        :return: Ping string to send
        """
        return self.__request({"type": "ping", "value": None})

    def _response_ping(self, id_: int) -> str:
        """
        Confirm ping request
        :param id_: ID of the conversation
        :return: Confirm message
        """
        return self.__response({"type": "ping", "value": None}, id_)

    def request_max_bytes(self, num: int) -> str:
        """
        Redefine number of bytes to communicate length
        :param num: Number of bytes
        :return: String to send
        """
        return self.__request({"type": "max_bytes", "value": num})

    def request_crpytion(self, new_cryption: CRYPTION_METHODS) -> str:
        """
        Request to change the encryption
        :param new_cryption: New encryption to use
        :return: String to send
        """
        return self.__request({"type": "cryption", "value": new_cryption})

    def process_response(self, message: BulkDict) -> None:
        """
        Process incoming control responses
        :param message: Response message
        """
        submessage: MessageDict = message["data"][0]
        match submessage["data"]["type"]:
            case "ping":
                self.__ping_callback()
            case "key":
                self.__set_key_callback(submessage["data"]["value"])

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
            case "key":
                self.__set_key_callback(submessage["data"]["value"])
                return self._response_key_exchange(id_)
            case "max_bytes":
                self.__max_bytes_callback(submessage["data"]["value"])
            case "cryption":
                self.__new_key_callback, self.__set_key_callback = \
                    self.__cryption_callback(submessage["data"]["value"])

        return None

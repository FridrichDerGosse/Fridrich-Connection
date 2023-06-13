"""
deamons/connection/protocol/_control.py

Project: Fridrich-Connection
Created: 30.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import TypedDict, Any, Callable, Literal

from ._types import BulkDict, MessageDict
from ._protocol import Protocol

from ..encryption import CRYPTION_METHODS


##################################################
#                     Code                       #
##################################################

class CommunicationData(TypedDict):
    type: Literal["key", "max_bytes", "cryption", "state"]
    value: Any


class CommunicationProtocol:
    """
    Protocol for connection changes
    All Messages are sent in "MasterSlave"-Mode
    """
    __protocol: Protocol

    NEW_KEY_CALLBACK_TYPE = Callable[[], str]
    SET_KEY_CALLBACK_TYPE = Callable[[str], Any]
    CONTROL_CALLBACK = Callable[[], Any]
    MAX_BYTES_CALLBACK_TYPE = Callable[[int], Any]
    CRYPTION_REQ_CALLBACK_TYPE = Callable[[str, str], tuple[NEW_KEY_CALLBACK_TYPE, SET_KEY_CALLBACK_TYPE]]
    CRYPTION_RES_CALLBACK_TYPE = Callable[[str], tuple[NEW_KEY_CALLBACK_TYPE, SET_KEY_CALLBACK_TYPE]]
    PAUSE_CONNECTION_CALLBACK_TYPE = Callable[[], Any]
    RESUME_CONNECTION_CALLBACK_TYPE = Callable[[], Any]

    __new_key_callback: NEW_KEY_CALLBACK_TYPE
    __set_key_callback: SET_KEY_CALLBACK_TYPE
    __control_callback: CONTROL_CALLBACK
    __max_bytes_callback: MAX_BYTES_CALLBACK_TYPE
    __cryption_req_callback: CRYPTION_REQ_CALLBACK_TYPE
    __cryption_res_callback: CRYPTION_RES_CALLBACK_TYPE
    __pause_connection_callback: PAUSE_CONNECTION_CALLBACK_TYPE
    __resume_connection_callback: RESUME_CONNECTION_CALLBACK_TYPE

    def __init__(
            self,
            id_range: range,
            new_key_callback: NEW_KEY_CALLBACK_TYPE,
            set_key_callback: SET_KEY_CALLBACK_TYPE,
            control_callback: CONTROL_CALLBACK,
            max_bytes_callback: MAX_BYTES_CALLBACK_TYPE,
            cryption_req_callback: CRYPTION_REQ_CALLBACK_TYPE,
            cryption_res_callback: CRYPTION_RES_CALLBACK_TYPE,
            pause_connection_callback: PAUSE_CONNECTION_CALLBACK_TYPE,
            resume_connection_callback: RESUME_CONNECTION_CALLBACK_TYPE
    ) -> None:
        """
        Create communication protocol
        :param id_range: ID range to use for this subprotocol
        :param new_key_callback: Callback to generate a new key and get it
        :param set_key_callback: Callback when a new key is received
        :param control_callback: Callback when control response is received that requires pausing the connection
        :param max_bytes_callback: Callback to set new max bytes
        :param cryption_req_callback: Callback to set new encryption with key.
        :param cryption_res_callback: Callback to confirm cryption change and set key
        :param pause_connection_callback: Callback to pause connection if requested
        :param resume_connection_callback: Callback to resume connection if requested
        """
        self.__protocol = Protocol("com", id_range)
        self.__new_key_callback = new_key_callback
        self.__set_key_callback = set_key_callback
        self.__control_callback = control_callback
        self.__max_bytes_callback = max_bytes_callback
        self.__cryption_req_callback = cryption_req_callback
        self.__cryption_res_callback = cryption_res_callback
        self.__pause_connection_callback = pause_connection_callback
        self.__resume_connection_callback = resume_connection_callback

    def __response(self, data: CommunicationData, id_: int) -> str:
        """
        General response encapsulation
        :param data: Response dictonary
        :param id_: ID of the conversation
        :return: Raw string to send
        """
        self.__protocol.response_add(data, id_)
        return self.__protocol.response_get()

    def __request(self, data: CommunicationData) -> str:
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

    def request_max_bytes(self, num: int) -> str:
        """
        Redefine number of bytes to communicate length
        :param num: Number of bytes
        :return: String to send
        """
        self.__protocol.set_max_bytes(num)
        return self.__request({"type": "max_bytes", "value": num})

    def request_crpytion(self, new_cryption: CRYPTION_METHODS, new_key: str | None = None) -> str:
        """
        Request to change the encryption
        :param new_cryption: New encryption to use
        :param new_key: Key for the new encryption
        :return: String to send
        """
        return self.__request({"type": "cryption", "value": {"name": new_cryption, "key": new_key}})

    def _response_cryption(self, id_: int) -> str:
        """
        Response to cryption change with a key
        :param id_: ID of the conversation
        :return: String to send
        """
        return self.__response({"type": "cryption", "value": self.__new_key_callback()}, id_)

    def request_pause(self) -> str:
        """
        Request to pause connection
        :return: String to send
        """
        return self.__request({"type": "state", "value": "pause"})

    def _response_pause(self, id_: int) -> str:
        """
        Respone to pause connection request
        :param id_: ID of the conversation
        :return: String to send
        """
        return self.__response({"type": "state", "value": "pause"}, id_)

    def request_resume(self) -> str:
        """
        Request to resume connection
        :return: String to send
        """
        return self.__request({"type": "state", "value": "resume"})

    def _response_resume(self, id_: int) -> str:
        """
        Respone to resume connection request
        :param id_: ID of the conversation
        :return: String to send
        """
        return self.__response({"type": "state", "value": "resume"}, id_)

    def process_response(self, message: BulkDict) -> None:
        """
        Process incoming communication responses
        :param message: Response message
        """
        submessage: MessageDict = message["data"][0]
        match submessage["data"]["type"]:
            case "key":
                self.__set_key_callback(submessage["data"]["value"])
                self.__control_callback()
            case "cryption":
                self.__new_key_callback, self.__set_key_callback = \
                    self.__cryption_res_callback(submessage["data"]["value"])
                self.__control_callback()
            case "state":
                self.__control_callback()

    def process_request(self, message: BulkDict) -> str | None:
        """
        Process incoming communication requests
        :param message: Request message
        :return: Response message
        """
        submessage: MessageDict = message["data"][0]
        id_: int = submessage["id"]

        match submessage["data"]["type"]:
            case "key":
                self.__set_key_callback(submessage["data"]["value"])
                return self._response_key_exchange(id_)

            case "max_bytes":
                self.__max_bytes_callback(submessage["data"]["value"])

            case "cryption":
                self.__new_key_callback, self.__set_key_callback = \
                    self.__cryption_req_callback(submessage["data"]["value"]["name"],
                                                 submessage["data"]["value"]["key"])
                return self._response_cryption(id_)

            case "state":
                match submessage["data"]["value"]:
                    case "pause":
                        self.__pause_connection_callback()
                        return self._response_pause(id_)
                    case "resume":
                        self.__resume_connection_callback()
                        return self._response_resume(id_)

        return None

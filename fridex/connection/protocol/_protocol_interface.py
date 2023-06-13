"""
deamons/connection/protocol/_protocol_interface.py

Project: Fridrich-Connection
Created: 31.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from concurrent.futures import ThreadPoolExecutor
from json import loads

from ._subscription import SubscriptionProtocol
from ._communication import CommunicationProtocol
from ._control import ControlProtocol
from ._data import DataProtocol
from ._types import BulkDict
from ._cache import Cache


##################################################
#                     Code                       #
##################################################


class ProtocolInterface:
    """
    Interface to access all protocols
    """
    __cache: Cache
    __data: DataProtocol
    __control: ControlProtocol
    __communication: CommunicationProtocol
    __subscription: SubscriptionProtocol

    REQUEST_CALLBACK_TYPE = DataProtocol.REQUEST_CALLBACK_TYPE
    REWORK_CALLBACK_TYPE = DataProtocol.REWORK_CALLBACK_TYPE
    ADD_RELATED_SUB_CALLBACK_TYPE = SubscriptionProtocol.ADD_RELATED_SUB_CALLBACK_TYPE | None
    DELETE_RELATED_SUB_CALLBACK_TYPE = SubscriptionProtocol.DELETE_RELATED_SUB_CALLBACK_TYPE | None

    def __init__(
            self,
            data_callback: DataProtocol.REQUEST_CALLBACK_TYPE,
            rework_callback: DataProtocol.REWORK_CALLBACK_TYPE,
            new_key_callback: CommunicationProtocol.NEW_KEY_CALLBACK_TYPE,
            set_key_callback: CommunicationProtocol.SET_KEY_CALLBACK_TYPE,
            control_callback: CommunicationProtocol.CONTROL_CALLBACK,
            ping_callback: ControlProtocol.PING_CALLBACK_TYPE,
            max_bytes_callback: CommunicationProtocol.MAX_BYTES_CALLBACK_TYPE,
            cryption_req_callback: CommunicationProtocol.CRYPTION_REQ_CALLBACK_TYPE,
            cryption_res_callback: CommunicationProtocol.CRYPTION_RES_CALLBACK_TYPE,
            pause_connection_callback: CommunicationProtocol.PAUSE_CONNECTION_CALLBACK_TYPE,
            resume_connection_callback: CommunicationProtocol.RESUME_CONNECTION_CALLBACK_TYPE,
            thread_pool: ThreadPoolExecutor,
            add_related_sub_callback: SubscriptionProtocol.ADD_RELATED_SUB_CALLBACK_TYPE | None = None,
            delete_related_sub_callback: SubscriptionProtocol.DELETE_RELATED_SUB_CALLBACK_TYPE | None = None,
            send_sub_callback: SubscriptionProtocol.SEND_SUB_CALLBACK_TYPE | None = None,
            max_bytes: int = 4
    ) -> None:
        """
        Create all protocols
        :param data_callback: Callback to get information for requests
        :param rework_callback: Callback to rework data result before setting to future
        :param new_key_callback: Callback to generate a new key and get it
        :param set_key_callback: Callback when a new key is received
        :param control_callback: Callback when control response is received that requires pausing the connection
        :param ping_callback: Callback when ping response is received
        :param max_bytes_callback: Callback to set new max bytes
        :param cryption_req_callback: Callback to set new encryption with key.
        :param cryption_res_callback: Callback to confirm cryption change and set key
        :param pause_connection_callback: Callback to pause connection if requested
        :param resume_connection_callback: Callback to resume connection if requested
        :param thread_pool: ThreadPool to execute callbacks
        :param add_related_sub_callback: Callback when an add subscription request comes in
        :param delete_related_sub_callback: Callback when a delete subscription request comes in
        :param send_sub_callback: Callback to send subscription data
        :param max_bytes: Number of bytes to communicate length
        """
        DataProtocol.set_max_bytes(max_bytes)

        self.__cache = Cache()

        self.__data = DataProtocol(range(0, 999), request_callback=data_callback,
                                   rework_callback=rework_callback, cache=self.__cache)
        self.__control = ControlProtocol(range(1000, 1999), ping_callback)
        self.__communication = CommunicationProtocol(range(2000, 2999), new_key_callback, set_key_callback,
                                                     control_callback, max_bytes_callback,
                                                     cryption_req_callback, cryption_res_callback,
                                                     pause_connection_callback, resume_connection_callback)
        self.__subscription = SubscriptionProtocol(range(3000, 3999), thread_pool,
                                                   add_related_sub_callback, delete_related_sub_callback,
                                                   send_sub_callback, cache=self.__cache)

    def decapsulate(self, messages: bytes) -> BulkDict:  # noqa
        """
        Decode and convert to dict
        :param messages: Raw bytes without length header
        :return: Dictonary with data
        """
        return loads(messages.decode("UTF-8"))

    @property
    def data(self) -> DataProtocol:
        """
        :return: DataProtocol instance
        """
        return self.__data

    @property
    def control(self) -> ControlProtocol:
        """
        :return: ControlProtocol instance
        """
        return self.__control

    @property
    def communication(self) -> CommunicationProtocol:
        """
        :return: CommunicationProtocol instance
        """
        return self.__communication

    @property
    def subscription(self) -> SubscriptionProtocol:
        """
        :return: SubscriptionProtocol instance
        """
        return self.__subscription

"""
deamons/connection/protocol/_data.py

Project: Fridrich-Connection
Created: 31.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from concurrent.futures import Future
from json import loads
from typing import Callable

from ._types import BulkDict, DATAUNIT
from ._protocol import Protocol
from ._cache import Cache


##################################################
#                     Code                       #
##################################################

class DataProtocol(Protocol):
    """
    Protocol for custom traffic
    """
    __cache: Cache | None

    REQUEST_CALLBACK_TYPE = Callable[[DATAUNIT], DATAUNIT]
    REWORK_CALLBACK_TYPE = Callable[[DATAUNIT], DATAUNIT]

    __request_callback: REQUEST_CALLBACK_TYPE
    __rework_callback: REWORK_CALLBACK_TYPE

    __send_futures: dict[int, Future]

    def __init__(
            self,
            id_range: range,
            request_callback: REQUEST_CALLBACK_TYPE,
            rework_callback: REWORK_CALLBACK_TYPE,
            cache: Cache | None = None
    ) -> None:
        """
        Create data protocol
        :param id_range: ID range to use for this subprotocol
        :param request_callback: Callback to get information for requests
        :param rework_callback: Callback to rework result before setting to future
        :param cache: Optional cache
        """
        super().__init__("data", id_range)
        self.__request_callback = request_callback
        self.__rework_callback = rework_callback
        self.__cache = cache

        self.__send_futures = {}

    def request_add(self, message: DATAUNIT) -> Future:
        """
        Add a message to the request bulk queue
        :param message: Message to add
        :return: Future instance to receive the result
        """
        future: Future = Future()

        if self.__cache:
            value = self.__cache.get(message)
            if value:
                future.set_result(value)
                return future

        super().request_add(message)

        self.__send_futures[self._id_count-1] = future
        return future

    def process_response(self, message: BulkDict) -> None:
        """
        Supply Futures results with response data
        :param message: Response message
        """
        for submessage in message["data"]:
            value: DATAUNIT = self.__rework_callback(loads(submessage["data"]))
            self.__send_futures[submessage["id"]].set_result(value)
            self.__send_futures.pop(submessage["id"])

    def process_request(self, message: BulkDict) -> str:
        """
        Process data request and get all required information
        :param message: Request message
        :return: Response message with all information
        """
        self.response_start()

        for sub_req in message["data"]:
            self.response_add(self.__request_callback(sub_req["data"]), id_=sub_req["id"])

        return self.response_get()

"""
deamons/connection/protocol/_subscription.py

Project: Fridrich-Connection
Created: 26.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable, Any, TypedDict, Literal, Type, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor

from ._protocol import Protocol
from ._types import BulkDict, DATAUNIT

if TYPE_CHECKING:
    from ._cache import Cache


##################################################
#                     Code                       #
##################################################

class SubscriptionRequest(TypedDict):
    action: Literal["add", "delete"]
    value: Type[DATAUNIT] | int


CALLBACK_TYPE = Callable[[DATAUNIT], Any]


class SubscriptionSave(TypedDict):
    callback: CALLBACK_TYPE
    req_dict: Type[DATAUNIT]


class SubscriptionProtocol:
    """
    Protocol for subscriptions
    """
    __protocol: Protocol
    __cache: Cache | None

    __thread_pool: ThreadPoolExecutor
    __subscriptions: dict[int, SubscriptionSave]

    ADD_RELATED_SUB_CALLBACK_TYPE = Callable[[int, DATAUNIT], Any]
    DELETE_RELATED_SUB_CALLBACK_TYPE = Callable[[int], Any]

    __add_related_sub_callback: ADD_RELATED_SUB_CALLBACK_TYPE
    __delete_related_sub_callback: DELETE_RELATED_SUB_CALLBACK_TYPE

    def __init__(
            self,
            id_range: range,
            thread_pool: ThreadPoolExecutor,
            add_related_sub_callback: ADD_RELATED_SUB_CALLBACK_TYPE,
            delete_related_sub_callback: DELETE_RELATED_SUB_CALLBACK_TYPE,
            cache: Cache | None = None
    ) -> None:
        """
        Create subscription protocol
        :param id_range: ID range to use for this subprotocol
        :param thread_pool: ThreadPool to execute callbacks
        :param add_related_sub_callback: Callback when an add subscription request comes in
        :param delete_related_sub_callback: Callback when a delete subscription request comes in
        :param cache: Optional cache
        """
        self.__protocol = Protocol("sub", id_range)

        self.__thread_pool = thread_pool
        self.__add_related_sub_callback = add_related_sub_callback
        self.__delete_related_sub_callback = delete_related_sub_callback
        self.__cache = cache

    def __response(
            self,
            data: DATAUNIT,
            inner_id: int
    ) -> str:
        """
        General response encapsulation
        :param data: Response dictonary
        :param inner_id: ID of the conversation
        :return: Raw string to send
        """
        self.__protocol.response_add(data, inner_id)
        return self.__protocol.response_get()

    def __request(self, data: SubscriptionRequest) -> str:
        """
        General request encapsulation
        :param data: Subscription request
        :return: Request string to send
        """
        self.__protocol.request_add(data)
        return self.__protocol.request_get()

    def add_subscription(
            self,
            callback: CALLBACK_TYPE,
            request_dict: dict[str | int | float | bool | None, any]
    ) -> tuple[int, str]:
        """
        Add a new subscription
        :param callback: Callback when value is updated
        :param request_dict: Same dictonary as a normal request to use
        :return: Subscription ID and String to send
        """
        message: str = self.__request({"action": "add", "value": request_dict})
        self.__subscriptions[self.__protocol.id_count] = {"callback": callback, "req_dict": request_dict}

        return self.__protocol.id_count, message

    def remove_subscription(
            self,
            subscription_id: int
    ) -> str:
        """
        Remove a subscription
        :param subscription_id: ID of the subscription
        """
        self.__subscriptions.pop(subscription_id)
        return self.__request({"action": "delete", "value": subscription_id})

    def response_subscription(
            self,
            id_: int,
            value: dict[str | int | float | bool | None, any]
    ) -> str:
        """
        Respone to a subscription (update value)
        :param id_: ID of the subscription
        :param value: New value
        :return: Response string to send
        """
        return self.__response(value, id_)

    def process_response(self, message: BulkDict) -> None:
        """
        These responses are coming without a request
        :param message: Response message
        """
        submessage = message["data"][0]
        if self.__cache:
            self.__cache.set(self.__subscriptions[submessage["id"]]["req_dict"], submessage["data"])
        self.__thread_pool.submit(self.__subscriptions[submessage["id"]]["callback"], submessage["data"])

    def process_request(self, message: BulkDict) -> None:
        """
        Process requests for new subscription management
        Subscription requests do not get an immidiate response
        :param message: Request message
        """
        submessage = message["data"][0]
        match submessage["data"]["action"]:
            case "add":
                self.__add_related_sub_callback(submessage["id"], submessage["data"]["value"])
            case "delete":
                self.__delete_related_sub_callback(submessage["data"]["value"])

"""
deamons/connection/communication/_client_connection.py

Project: Fridrich-Connection
Created: 26.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import Callable, Any
import socket

from ._base_connection import BaseConnection, BulkDict
from ..protocol import SubscriptionProtocol


##################################################
#                     Code                       #
##################################################

class ClientConnection(BaseConnection):
    """
    Connection from the client to the server
    """
    __sub_protocol: SubscriptionProtocol

    __subscriptions: dict[int, Callable[[Any], Any]]

    def __init__(self, ip: str, port: int) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        super().__init__(conn=sock, recv_callback=self.__subscription_check)

    def add_subscription(
            self,
            callback: Callable[[Any], Any],
            initial_call: bool | None = True
    ) -> None:
        ...

    def __subscription_check(self, data: BulkDict) -> None:
        if data["kind"] == "sub":
            self.__subscriptions[data["id"]](data["data"])

    def delete_subscription(self) -> None:
        ...

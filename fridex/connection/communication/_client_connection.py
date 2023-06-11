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

from ._base_connection import BaseConnection
from ..protocol import ProtocolInterface


##################################################
#                     Code                       #
##################################################

class ClientConnection(BaseConnection):
    """
    Connection from the client to the server
    """
    def __init__(
            self,
            ip: str,
            port: int,
            request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE,
    ) -> None:
        """
        Connect to server
        :param ip: IP of the server
        :param port: Port to connect
        :param request_callback: Callback to get information for data requests
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        super().__init__(conn=sock, request_callback=request_callback)

        self._state = "open"
        self.send_key_exchange()
        self.send_key_exchange()

    def add_subscription(
            self,
            callback: Callable[[Any], Any],
            request_dict: dict[str | int | float | bool | None, any]
    ) -> int:
        """
        Send add subscription request
        :param callback: Callback when value is updated
        :param request_dict: Same dictonary as a normal request to use
        :return: ID of the subscripton
        """
        sub_id, message = self._protocol.subscription.add_subscription(callback, request_dict)
        self.send(message)

        return sub_id

    def delete_subscription(self, sub_id: int) -> None:
        """
        Send subscription delete request
        :param sub_id: ID of the subscription
        """
        self.send(self._protocol.subscription.remove_subscription(sub_id))

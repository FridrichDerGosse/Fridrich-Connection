"""
deamons/connection/communication/_server_connection.py

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

class ServerConnection(BaseConnection):
    """
    Connection from the server to the client
    """
    def __init__(
            self,
            conn: socket.socket,
            request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE,
            add_sub_callback: ProtocolInterface.ADD_RELATED_SUB_CALLBACK_TYPE,
            del_sub_callback: ProtocolInterface.DELETE_RELATED_SUB_CALLBACK_TYPE,
    ) -> None:
        """
        Create connection
        :param conn: Socket
        :param request_callback: Callback to get information for data requests
        :param add_sub_callback: Callback when an add subscription request comes in
        :param del_sub_callback: Callback when a delete subscription request comes in
        """
        super().__init__(conn,
                         request_callback=request_callback,
                         add_sub_callback=add_sub_callback,
                         del_sub_callback=del_sub_callback)

"""
deamons/connection/communication/_server_connection.py

Project: Fridrich-Connection
Created: 26.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

import socket

from ..protocol import ProtocolInterface, DATAUNIT
from ._base_connection import BaseConnection


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
            rework_callback: ProtocolInterface.REWORK_CALLBACK_TYPE,
            add_sub_callback: ProtocolInterface.ADD_RELATED_SUB_CALLBACK_TYPE,
            del_sub_callback: ProtocolInterface.DELETE_RELATED_SUB_CALLBACK_TYPE,
    ) -> None:
        """
        Create connection
        :param conn: Socket
        :param request_callback: Callback to get information for data requests
        :param rework_callback: Callback to rework result before setting to future
        :param add_sub_callback: Callback when an add subscription request comes in
        :param del_sub_callback: Callback when a delete subscription request comes in
        """
        super().__init__(conn,
                         request_callback=request_callback,
                         rework_callback=rework_callback,
                         add_sub_callback=add_sub_callback,
                         del_sub_callback=del_sub_callback)

    def provide_data(self, req_dict: DATAUNIT, value: DATAUNIT) -> None:
        """
        Check if data is needed in a subscription
        :param req_dict: Same dictonary as a normal request to use
        :param value: New value
        """
        self._protocol.subscription.provide_data(req_dict, value)

"""
fridex/connection/communication/_client_handler.py

Project: Fridrich-Connection
Created: 12.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from concurrent.futures import ThreadPoolExecutor
from time import sleep
import socket

from ..protocol import ProtocolInterface, DATAUNIT
from ._server_connection import ServerConnection


##################################################
#                     Code                       #
##################################################

class ClientHandler(socket.socket):
    """
    Serverside ClientHandler
    """
    __clients: list[ServerConnection]

    __request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE
    __rework_callback: ProtocolInterface.REWORK_CALLBACK_TYPE
    __add_sub_callback: ProtocolInterface.ADD_RELATED_SUB_CALLBACK_TYPE
    __del_sub_callback: ProtocolInterface.DELETE_RELATED_SUB_CALLBACK_TYPE

    def __init__(
            self,
            request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE,
            rework_callback: ProtocolInterface.REWORK_CALLBACK_TYPE,
            add_sub_callback: ProtocolInterface.ADD_RELATED_SUB_CALLBACK_TYPE,
            del_sub_callback: ProtocolInterface.DELETE_RELATED_SUB_CALLBACK_TYPE,
            port: int | None = 4205,
    ) -> None:
        """
        Create server with client accept handler
        :param request_callback: Callback to get information for data requests
        :param add_sub_callback: Callback when an add subscription request comes in
        :param del_sub_callback: Callback when a delete subscription request comes in
        :param port: Port to open the server on
        """
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(("0.0.0.0", port))
        self.listen()

        self.__request_callback = request_callback
        self.__rework_callback = rework_callback
        self.__add_sub_callback = add_sub_callback
        self.__del_sub_callback = del_sub_callback

        self.__clients = []
        self.__threadpool = ThreadPoolExecutor(max_workers=1)

        self.__threadpool.submit(self.__accept_clients)

    __threadpool: ThreadPoolExecutor

    def __accept_clients(self) -> None:
        """
        Loop accept client connections
        """
        while True:
            sock, address = self.accept()

            self.__clients.append(ServerConnection(sock,
                                                   request_callback=self.__request_callback,
                                                   rework_callback=self.__rework_callback,
                                                   add_sub_callback=self.__add_sub_callback,
                                                   del_sub_callback=self.__del_sub_callback))
            sleep(0.1)

    def provide_data(self, req_dict: DATAUNIT, value: DATAUNIT) -> None:
        """
        Provide data for subscription to all clients
        :param req_dict: Same dictonary as a normal request to use
        :param value: New value
        """
        for client in self.__clients:
            client.provide_data(req_dict, value)


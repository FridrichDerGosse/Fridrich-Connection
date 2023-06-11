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

from ._server_connection import ServerConnection
from ..protocol import ProtocolInterface


##################################################
#                     Code                       #
##################################################

class ClientHandler(socket.socket):
    """
    Serverside ClientHandler
    """
    __clients: list[ServerConnection]

    __request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE
    __add_sub_callback: ProtocolInterface.ADD_RELATED_SUB_CALLBACK_TYPE
    __del_sub_callback: ProtocolInterface.DELETE_RELATED_SUB_CALLBACK_TYPE

    def __init__(
            self,
            request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE,
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
            print("NEW CLIENT:", address)

            self.__clients.append(ServerConnection(sock,
                                                   request_callback=self.__request_callback,
                                                   add_sub_callback=self.__add_sub_callback,
                                                   del_sub_callback=self.__del_sub_callback))
            sleep(0.1)

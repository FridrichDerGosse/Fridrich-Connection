"""
deamons/connection/communication/_base_connection.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime, timedelta
from typing import Callable, Any
import socket

from ..protocol import BulkDict


##################################################
#                     Code                       #
##################################################

class BaseConnection:
    """
    This represents a connection between server and client
    """
    __socket: socket.socket
    __recv_callback: Callable[[BulkDict], Any]
    __start_time: datetime
    __lease_time: datetime

    _thread_pool: ThreadPoolExecutor

    _recv_data: list[BulkDict]
    _send_data: list[tuple[str]]

    def __init__(
            self,
            conn: socket.socket,
            recv_callback: Callable[[BulkDict], Any],
            timeout: int = 10
    ) -> None:
        self.__socket = conn
        self.__recv_callback = recv_callback

        self.__start_time = datetime.now()
        self.__lease_time = self.__start_time + timedelta(seconds=timeout)

        self._recv_data = []
        self._send_data = []

        self._thread_pool = ThreadPoolExecutor(max_workers=1)
        self._thread_pool.submit(self.__loop)

    def __loop(self) -> None:
        for send in self._send_data:
            ...

    def send(self, message: bytes, _id: int) -> Future:
        future: Future = Future()
        return future


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
from typing import Callable, Any, Literal
from datetime import datetime, timedelta
from time import sleep
import socket

from ..protocol import BulkDict, FDCP
from ..encryption import CryptionService, CryptionMethod


##################################################
#                     Code                       #
##################################################

class BaseConnection:
    """
    This represents a connection between server and client
    """
    __socket: socket.socket
    __recv_callback: Callable[[BulkDict], Any]
    __timeout: int
    __start_time: datetime
    __lease_time: datetime

    _thread_pool: ThreadPoolExecutor

    _fdcp: FDCP
    _cryption: CryptionMethod

    _send_data: list[str]
    __send_futures: dict[int, Future]

    __STATES = Literal["init", "open", "closed", "all"]
    __state: __STATES | Literal["all"]
    __state_callbacks: dict[int, tuple[__STATES, Callable[[], Any]]]

    def __init__(
            self,
            conn: socket.socket,
            recv_callback: Callable[[BulkDict], Any],
            even_ids: bool | None = False,
            timeout: int = 10
    ) -> None:
        """
        Create connection
        :param conn: Socket
        :param recv_callback: Callback when something is reveived
        :param even_ids: Whether the even or the odd numbers should be taken for the ids
        :param timeout: Connection leasetime if no response on ping (min 2)
        """
        if timeout < 2:
            timeout = 2
        self.__timeout = timeout

        self.__socket = conn
        self.__socket.settimeout(0.1)
        self.__recv_callback = recv_callback

        self.__start_time = datetime.now()
        self.__lease_time = self.__start_time + timedelta(seconds=self.__timeout)

        self.__state = "init"

        self._send_data = []
        self.__send_futures = {}

        self._fdcp = FDCP(even=even_ids)
        self._cryption = CryptionService.new_cryption()

        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._thread_pool.submit(self.__loop)

    def __loop(self) -> None:
        while True:
            if self.__state == "open":
                if datetime.now() > self.__lease_time - timedelta(seconds=2):
                    self._send_data.append(self._fdcp.fcmp.ping())

            for send in self._send_data:
                self._cryption.encrypt(send)

            # RECV Decrypt

            sleep(0.05)

    def send(self, message: str, _id: int) -> Future:
        """
        Send a message
        :param message: Raw string message
        :param _id: ID of the conversation
        :return: Future for the response
        """
        if self._state == "open":
            future: Future = Future()

            self.__send_futures[_id] = future
            self._send_data.append(message)

            return future
        raise ConnectionError("Connection is not in state 'open'.")

    @property
    def state(self) -> Literal["init", "open", "closed"]:
        """
        :return: Current connection state
        """
        return self.__state

    @property
    def _state(self) -> Literal["init", "open", "closed"]:
        """
        :return: Current connection stat
        """
        return self.state

    @_state.setter
    def _state(self, value: __STATES) -> None:
        """
        Set current state and go through callbacks
        :param value: Value to set to
        """
        self.__state = value

        for cb_id, (state, callback) in self.__state_callbacks.items():
            if state == self.__state:
                callback()

        if self.__state == "open":
            self.__lease_time = datetime.now() + timedelta(seconds=self.__timeout)

    def join_state(self, state: __STATES, _time_delta: float | None = 0.1) -> None:
        """
        Wait until certain state is reached
        :param state: State to wait for
        :param _time_delta: Time interval for checking
        """
        while self._state != state:
            sleep(_time_delta)

    def callback_state(self, state: __STATES | Literal["all"], callback: Callable[[], Any]) -> int:
        """
        Get a callback when certain state is reached
        :param state: On what state
        :param callback: Function to call
        :return: Callback ID
        """
        num: int = max(self.__state_callbacks.keys()) if self.__state_callbacks else 0
        self.__state_callbacks[num] = (state, callback)
        return num

    def remove_callback_state(self, callback_id: int) -> None:
        """
        Remove certain state callback
        :param callback_id: ID of the callback
        """
        self.__state_callbacks.pop(callback_id)

    def remove_all_callbacks(self) -> None:
        """
        Removes all current callbacks
        """
        self.__state_callbacks = {}

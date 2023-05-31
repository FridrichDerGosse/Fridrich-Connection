"""
deamons/connection/communication/_base_connection.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Literal
from datetime import datetime, timedelta
from time import sleep
import socket

from ..protocol import BulkDict, Protocol
from ..encryption import CryptionService, CryptionMethod


##################################################
#                     Code                       #
##################################################

class BaseConnection:
    """
    This represents a connection between server and client
    """
    __socket: socket.socket
    __timeout: int
    __start_time: datetime
    __lease_time: datetime

    _thread_pool: ThreadPoolExecutor

    _fdcp: Protocol
    _cryption: CryptionMethod

    _send_data: list[str]

    __STATES = Literal["init", "open", "closed", "all"]
    __state: __STATES | Literal["all"]
    __state_callbacks: dict[int, tuple[__STATES, Callable[[], Any]]]

    def __init__(
            self,
            conn: socket.socket,
            request_callback: Protocol.REQUEST_CALLBACK_TYPE,
            even_ids: bool | None = False,
            timeout: int = 10,
            packet_size: int = 32,
    ) -> None:
        """
        Create connection
        :param conn: Socket
        :param request_callback: Callback to get information for requests
        :param even_ids: Whether the even or the odd numbers should be taken for the ids
        :param timeout: Connection leasetime if no response on ping (min 2)
        """
        if timeout < 2:
            timeout = 2
        self.__timeout = timeout

        self.__packet_size = packet_size

        self.__socket = conn
        self.__socket.settimeout(0.1)

        self.__start_time = datetime.now()
        self.__lease_time = self.__start_time + timedelta(seconds=self.__timeout)

        self.__state = "init"

        self._send_data = []

        self._fdcp = Protocol(request_callback=request_callback)
        self._cryption = CryptionService.new_cryption()

        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._thread_pool.submit(self.__loop)

    def __loop(self) -> None:
        while True:
            if self.__state == "open":
                if datetime.now() > self.__lease_time - timedelta(seconds=2):
                    self._send_data.append(self._fdcp.fcmp.ping())

            # Sending
            for send in self._send_data:
                size_send: bytes = len(send).to_bytes(length=self._fdcp.max_bytes, byteorder="big")

                self.__socket.send(self._cryption.encrypt(size_send + send.encode("UTF-8")))

            # Receiving
            encrypted_buffer: bytes = bytes()
            while True:
                recv: bytes = self.__socket.recv(__bufsize=self.__packet_size)
                if not recv:
                    break
                encrypted_buffer += recv

            message_buffer: bytes = self._cryption.decrypt(encrypted_buffer)
            recv_messages: list[BulkDict] = []

            while message_buffer != b'':
                size_recv: int = int.from_bytes(bytes=message_buffer[:self._fdcp.max_bytes], byteorder="big")

                message_bytes = message_buffer[self._fdcp.max_bytes:self._fdcp.max_bytes+size_recv]
                recv_messages.append(self._fdcp.decapsulate(message_bytes))

                message_buffer = message_buffer[self._fdcp.max_bytes+size_recv:]

            for message in recv_messages:
                match message["kind"]:
                    case "send":
                        self._fdcp.process_request(message)

                    case "resp":
                        self._fdcp.process_response(message)

                    case "fssp":
                        ...
                    case "fcmp":
                        ...

            sleep(0.05)

    def send(self, message: str) -> None:
        """
        Send a message
        :param message: Raw string message
        """
        if self._state == "open":
            self._send_data.append(message)

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

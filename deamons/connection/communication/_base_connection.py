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
import select
import sys

from ..protocol import BulkDict, ProtocolInterface, Protocol
from ..encryption import CryptionService, CryptionMethod
from ..protocol import ControlProtocol


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

    _protocol: ProtocolInterface
    _cryption: CryptionMethod

    _send_data: list[str]
    __send_key: str | None

    __STATES = Literal["init", "open", "key_exchange", "closed"]
    __state: __STATES | Literal["all"]
    __state_callbacks: dict[int, tuple[__STATES, Callable[[], Any]]]

    def __init__(
            self,
            conn: socket.socket,
            request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE,
            add_sub_callback: ProtocolInterface.ADD_RELATED_SUB_CALLBACK_TYPE | None = None,
            del_sub_callback: ProtocolInterface.DELETE_RELATED_SUB_CALLBACK_TYPE | None = None,
            timeout: int = 10,
            packet_size: int = 32,
    ) -> None:
        """
        Create connection
        :param conn: Socket
        :param request_callback: Callback to get information for requests
        :param add_sub_callback: Callback when an add subscription request comes in
        :param del_sub_callback: Callback when a delete subscription request comes in
        :param timeout: Connection leasetime if no response on ping
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
        self.__state_callbacks = {}

        self._send_data = []
        self.__send_key = None

        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._cryption = CryptionService.new_cryption()

        self._protocol = ProtocolInterface(
            data_callback=request_callback,
            new_key_callback=self._cryption.new_key,
            set_key_callback=self._cryption.set_key,
            ping_callback=self.__ping_confirm,
            max_bytes_callback=Protocol.set_max_bytes,
            cryption_callback=self.__update_encryption,
            thread_pool=self._thread_pool,
            add_related_sub_callback=add_sub_callback,
            delete_related_sub_callback=del_sub_callback
        )

        self._thread_pool.submit(self.__loop)

    def key_exchange_confirm(self, key: str) -> None:
        if self.__state == "key_exchange":
            self._cryption.set_key(key)


    def __ping_confirm(self) -> None:
        """
        Callback when ping request gets a response
        """
        self.__lease_time = datetime.now() + timedelta(seconds=self.__timeout)

    def __update_encryption(
            self,
            encryption: Literal["private_public"]
    ) -> tuple[ControlProtocol.NEW_KEY_CALLBACK_TYPE, ControlProtocol.SET_KEY_CALLBACK_TYPE]:
        """
        Callback when a new cryption should be set
        :param encryption: Encryption type string
        :return: New cryption callbacks for ControlProtocol
        """
        self._cryption = CryptionService.new_cryption(encryption)
        return self._cryption.new_key, self._cryption.set_key

    def __loop(self) -> None:
        pinged: bool = False

        while True:
            if self.__state == "open":
                # Request ping
                if not pinged and datetime.now() > self.__lease_time:
                    self._send_data.append(self._protocol.control.request_ping())
                    pinged = True

                if pinged and self.__lease_time > datetime.now():
                    pinged = False

                # Close connection if leased
                if datetime.now() > self.__lease_time + timedelta(seconds=2) and pinged:
                    print("CLOSE")
                    self.__socket.close()
                    return

            # Sending
            to_send: list[str] = []
            if self.__state == "key_exchange":
                to_send = [self.__send_key]
                self.__send_key = None
            else:
                to_send = self._send_data
                self._send_data = []

            for send in to_send:
                print("SEND", send)
                size_send: bytes = len(send).to_bytes(length=Protocol.max_bytes, byteorder="big")
                self.__socket.send(self._cryption.encrypt(size_send + send.encode("UTF-8")))

            # Receiving
            encrypted_buffer: bytes = bytes()
            while True:
                ready_to_read, _, _ = select.select([self.__socket], [], [], 0)
                if ready_to_read:
                    recv: bytes = self.__socket.recv(self.__packet_size)
                    if not recv:
                        break
                    encrypted_buffer += recv
                else:
                    break

            message_buffer: bytes = self._cryption.decrypt(encrypted_buffer)
            recv_messages: list[BulkDict] = []

            while message_buffer != b'':
                print("WORKING", message_buffer)
                size_recv: int = int.from_bytes(bytes=message_buffer[:Protocol.max_bytes], byteorder="big")

                message_bytes = message_buffer[Protocol.max_bytes:Protocol.max_bytes + size_recv]
                recv_messages.append(self._protocol.decapsulate(message_bytes))

                message_buffer = message_buffer[Protocol.max_bytes + size_recv:]

            for message in recv_messages:
                match message["direction"]:
                    case "request":
                        match message["kind"]:
                            case "data":
                                self._send_data.append(self._protocol.data.process_request(message))
                            case "sub":
                                self._protocol.subscription.process_request(message)
                            case "con":
                                con_res = self._protocol.control.process_request(message)
                                if con_res:
                                    self._send_data.append(con_res)

                    case "response":
                        match message["kind"]:
                            case "data":
                                self._protocol.data.process_response(message)
                            case "sub":
                                self._protocol.subscription.process_response(message)
                            case "con":
                                self._protocol.control.process_response(message)

            sleep(0.05)

    def close(self) -> None:
        """
        Close connection
        """
        self.__state = "closed"
        self._thread_pool.shutdown(wait=False, cancel_futures=True)
        self.__socket.close()

    def send(self, message: str) -> None:
        """
        Send a message
        :param message: Raw string message
        """
        if self.__state == "open":
            self._send_data.append(message)
            return

        raise ConnectionError("Connection is not in state 'open'.")

    def send_key_exchange(self, message: str) -> None:
        """
        Send key exchange message
        :param message: Key exchange message
        """
        self.__send_key = message
        self.__state = "key_exchange"

    @property
    def state(self) -> Literal["init", "open", "closed"]:
        """
        :return: Current connection state
        """
        return self.__state

    def _set_state(self, value: __STATES) -> None:
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
        while self.__state != state:
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

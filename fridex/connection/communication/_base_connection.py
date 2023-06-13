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
from time import sleep, time
import socket
import select

from ..encryption import CryptionService, CryptionMethod, CRYPTION_METHODS
from ..protocol import BulkDict, ProtocolInterface, Protocol
from ..protocol import CommunicationProtocol


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
    _new_cryption: CryptionMethod | None

    _send_data: list[str]
    _send_communication: list[Literal["key"] | CRYPTION_METHODS]
    _respond_communication: str | None

    __STATES = Literal["open", "paused", "prewait", "waiting", "afterwait", "closed"]
    __state: __STATES | Literal["all"]
    __state_callbacks: dict[int, tuple[__STATES, Callable[[], Any]]]

    def __init__(
            self,
            conn: socket.socket,
            request_callback: ProtocolInterface.REQUEST_CALLBACK_TYPE,
            rework_callback: ProtocolInterface.REWORK_CALLBACK_TYPE,
            add_sub_callback: ProtocolInterface.ADD_RELATED_SUB_CALLBACK_TYPE | None = None,
            del_sub_callback: ProtocolInterface.DELETE_RELATED_SUB_CALLBACK_TYPE | None = None,
            timeout: int = 10,
            packet_size: int = 1,
    ) -> None:
        """
        Create connection
        :param conn: Socket
        :param request_callback: Callback to get information for data requests
        :param rework_callback: Callback to rework result before setting to future
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

        self.__state = "open"
        self.__state_callbacks = {}

        self._send_data = []
        self._send_communication = []
        self._respond_communication = None

        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._cryption = CryptionService.new_cryption()
        self._new_cryption = None

        self._protocol = ProtocolInterface(
            data_callback=request_callback,
            rework_callback=rework_callback,
            new_key_callback=self._cryption.new_key,
            set_key_callback=self._cryption.set_key,
            control_callback=self.__confirm_control,
            ping_callback=self.__ping_confirm,
            max_bytes_callback=Protocol.set_max_bytes,
            cryption_req_callback=self.__cryption_request,
            cryption_res_callback=self.__cryption_confirm,
            pause_connection_callback=lambda: self._set_state("paused"),
            resume_connection_callback=lambda: self._set_state("open"),
            thread_pool=self._thread_pool,
            add_related_sub_callback=add_sub_callback,
            delete_related_sub_callback=del_sub_callback,
            send_sub_callback=self.send
        )

        self._thread_pool.submit(self.__loop)

    def __confirm_control(self) -> None:
        """
        Confirm control message that requires pausing the connection
        """
        if self.__state == "afterwait":
            self._set_state("open")
        else:
            self._set_state("prewait")

    def __cryption_request(
            self,
            encryption: CRYPTION_METHODS,
            key: str
    ) -> tuple[CommunicationProtocol.NEW_KEY_CALLBACK_TYPE, CommunicationProtocol.SET_KEY_CALLBACK_TYPE]:
        """
        Callback when cryption exchange is requested
        :param encryption: New encryption type string
        :param key: New key
        :return: New cryption callbacks for ControlProtocol
        """
        self._cryption = CryptionService.new_cryption(encryption)
        self._cryption.set_key(key)
        return self._cryption.new_key, self._cryption.set_key

    def __cryption_confirm(self, key: str) -> tuple[CommunicationProtocol.NEW_KEY_CALLBACK_TYPE, CommunicationProtocol.SET_KEY_CALLBACK_TYPE]:
        """
        Callback when cryption exchange was successful
        :param key: New key
        :return: New cryption callbacks for ControlProtocol
        """
        self._cryption.set_key(key)

        return self._cryption.new_key, self._cryption.set_key

    def __ping_confirm(self) -> None:
        """
        Callback when ping request gets a response
        """
        self.__lease_time = datetime.now() + timedelta(seconds=self.__timeout)

    def __loop(self) -> None:
        next_alive: datetime = datetime.now()

        while True:
            if self.__state == "open":
                # Request ping
                if datetime.now() > next_alive:
                    self._send_data.append(self._protocol.control.request_alive())
                    next_alive = datetime.now() + timedelta(seconds=self.__timeout)

                # Close connection if leased
                if datetime.now() > self.__lease_time + timedelta(seconds=2):
                    self.__socket.close()
                    return

            # Sending
            to_send: list[str] = []

            # Pause other side
            if self.__state == "open" and self._send_communication:
                self._set_state("waiting")
                to_send = [self._protocol.communication.request_pause()]

            if self.__state == "prewait" and not self._send_communication:
                self._set_state("afterwait")
                to_send = [self._protocol.communication.request_resume()]

            # Choose what to send
            match self.__state:
                case "prewait":
                    send = self._send_communication.pop(0)
                    match send:
                        case "key":
                            to_send = [self._protocol.communication.request_key_exchange()]

                        case "private_public" | "fernet":
                            self._new_cryption = CryptionService.new_cryption(send)
                            to_send = [
                                self._protocol.communication.request_crpytion(
                                    send,
                                    self._new_cryption.new_key()
                                )
                            ]
                    self._set_state("waiting")

                case "waiting" | "afterwait":
                    ...

                case "paused" | "open":
                    if self._respond_communication:
                        to_send.append(self._respond_communication)
                        self._respond_communication = None

                    if self.__state == "open":
                        to_send += self._send_data.copy()
                        self._send_data = []

            # Sending
            for send in to_send:
                size_send: bytes = len(send).to_bytes(length=Protocol.max_bytes, byteorder="big")
                self.__socket.send(self._cryption.encrypt(size_send + send.encode("UTF-8")))

            if self._new_cryption:
                self._cryption = self._new_cryption
                self._new_cryption = None

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

            # Work out inividual messages
            t1 = time()
            message_buffer: bytes = self._cryption.decrypt(encrypted_buffer)
            recv_messages: list[BulkDict] = []

            while message_buffer != b'':
                size_recv: int = int.from_bytes(bytes=message_buffer[:Protocol.max_bytes], byteorder="big")

                message_bytes = message_buffer[Protocol.max_bytes:Protocol.max_bytes + size_recv]
                recv_messages.append(self._protocol.decapsulate(message_bytes))

                message_buffer = message_buffer[Protocol.max_bytes + size_recv:]

            # Process received messages
            for message in recv_messages:
                match message["direction"]:
                    case "request":
                        match message["kind"]:
                            case "data":
                                self._send_data.append(self._protocol.data.process_request(message))
                            case "sub":
                                self._protocol.subscription.process_request(message)
                            case "com":
                                self._respond_communication = self._protocol.communication.process_request(message)
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
                            case "com":
                                self._protocol.communication.process_response(message)

            sleep(0.05)

    def close(self) -> None:
        """
        Close connection
        """
        self._set_state("closed")
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

    def send_key_exchange(self) -> None:
        """
        Send key exchange message
        """
        self._send_communication.append("key")

    def send_cryption_change(self, cryption: CRYPTION_METHODS) -> None:
        """
        Send cryption change message
        """
        self._send_communication.append(cryption)

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
            self.__lease_time = datetime.now() + timedelta(seconds=self.__timeout+1)

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

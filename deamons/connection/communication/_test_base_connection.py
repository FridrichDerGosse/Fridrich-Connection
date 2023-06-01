"""
deamons/connection/communication/_base_connection_test.py

Project: Fridrich-Connection
Created: 01.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################


from concurrent.futures import Future
from typing import Literal
from json import dumps
from time import sleep
import unittest
import socket

from ._base_connection import BaseConnection, ProtocolInterface


##################################################
#                     Code                       #
##################################################

server: socket.socket | None = None


def get_socket_pair(
        port: int = 12345
) -> tuple[socket.socket, socket.socket, socket.socket]:
    """
    Get a connected socket pair
    :param port: Port to use
    :return: Server, ServerConnection, Client
    """
    global server
    if server is None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", 12345))
        server.listen()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", port))

    sock, add = server.accept()
    return server, sock, client


class BaseConnectionModified(BaseConnection):
    def set_state(self, state: Literal["init", "open", "closed"]) -> None:
        self._set_state(state)

    @property
    def protocol(self) -> ProtocolInterface:
        return self._protocol


class BaseConnectionTest(unittest.TestCase):
    """
    Test BaseConnection
    """
    server: socket.socket
    client_handler: socket.socket
    client: socket.socket

    conn_server: BaseConnectionModified
    conn_client: BaseConnectionModified

    def setUp(self) -> None:
        """
        Setup connections and BaseConnections
        """
        self.server, self.client_handler, self.client = get_socket_pair()

        self.conn_server = BaseConnectionModified(self.client_handler, request_callback=lambda a: a, timeout=1)
        self.conn_client = BaseConnectionModified(self.client, request_callback=lambda a: a, timeout=1)
        self.conn_server.set_state("open")
        self.conn_client.set_state("open")

    def test_unencrypted_data(self) -> None:
        """
        Test basic unencrypted data traffic
        """

        f_client: list[tuple[Future, int]] = []
        f_server: list[tuple[Future, int]] = []

        for i in range(10):
            self.conn_client.protocol.data.request_start()
            f_client.append((self.conn_client.protocol.data.request_add(dumps({"test": i})), i))
            self.conn_client.send(self.conn_client.protocol.data.request_get())

        for i in range(10):
            self.conn_server.protocol.data.request_start()
            f_server.append((self.conn_server.protocol.data.request_add(dumps({"test": i})), i))
            self.conn_server.send(self.conn_server.protocol.data.request_get())

        for f, num in f_client + f_server:
            self.assertEqual(f.result()["test"], num)

    def test_encrypted_data(self) -> None:
        """
        Test encrypted data protocol traffic
        """
        self.conn_client.send(self.conn_client.protocol.control.request_key_exchange())

        for i in range(50):
            sleep(0.1)

    def tearDown(self) -> None:
        """
        Clearup after each test
        """
        self.conn_client.close()
        self.conn_server.close()

        del self.client, self.client_handler, self.conn_server, self.conn_client

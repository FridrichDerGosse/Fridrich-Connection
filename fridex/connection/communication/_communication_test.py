"""
fridex/connection/communication/_communication_test.py

Project: Fridrich-Connection
Created: 13.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

import unittest

from ._client_connection import ClientConnection
from ._client_handler import ClientHandler


##################################################
#                     Code                       #
##################################################

class CommunicationTest(unittest.TestCase):
    """
    Basic client - server communication test
    """
    __client: ClientConnection
    __server: ClientHandler

    def setUp(self) -> None:
        """
        Setup client and server
        """
        self.__client = ClientConnection("127.0.0.1", 4205, lambda a: a)
        # self.__server = ClientHandler(lambda a: a)

    def tearDown(self) -> None:
        """
        Delete client and server
        """

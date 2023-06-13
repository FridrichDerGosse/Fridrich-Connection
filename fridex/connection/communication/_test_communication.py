"""
fridex/connection/communication/_test_communication.py

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

    def tearDown(self) -> None:
        """
        Delete client and server
        """

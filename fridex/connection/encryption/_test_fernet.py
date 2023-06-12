"""
fridex/connection/encryption/_test_fernet.py

Project: Fridrich-Connection
Created: 12.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from ._supertest_cryption import CryptionTest


##################################################
#                     Code                       #
##################################################

class FernetTest(CryptionTest):
    """
    Test Fernet encryption
    """
    _cryption = "fernet"

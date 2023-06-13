"""
deamons/connection/encryption/_cryption.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import Literal

from ._private_public import PrivatePublicCryption
from ._cryption_method import CryptionMethod
from ._fernet import FernetCryption

##################################################
#                     Code                       #
##################################################

CRYPTION_METHODS = Literal["private_public", "fernet"]


class CryptionService:
    """
    Encrypt and decrypt messages with different encryptions
    """

    @staticmethod
    def new_cryption(method: CRYPTION_METHODS = "private_public") -> CryptionMethod:
        match method:
            case "private_public":
                return PrivatePublicCryption()
            case "fernet":
                return FernetCryption()

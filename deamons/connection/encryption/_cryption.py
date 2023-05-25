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


##################################################
#                     Code                       #
##################################################

class CryptionService:
    """
    Encrypt and decrypt messages with different encryptions
    """

    @staticmethod
    def new_cryption(method: Literal["private_public"] = "private_public") -> CryptionMethod:
        match method:
            case "private_public":
                return PrivatePublicCryption()



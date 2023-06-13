"""
deamons/connection/encryption/_cryption_method.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################


##################################################
#                     Code                       #
##################################################

class CryptionMethod:
    """
    Every cryptionmethod should inherit from this and overwrite all functions
    """
    def encrypt(self, message: bytes) -> bytes:
        """
        Encrypt messages
        :param message: Raw message
        :return: Encrypted message
        """
        ...

    def decrypt(self, message: bytes) -> bytes:
        """
        Decrypte messages
        :param message: Encrypted message
        :return: Raw message
        """

    def get_key(self) -> str:
        """
        Get the main/public key to share with the other site
        :return: Key
        """
        ...

    def set_key(self, key: str) -> None:
        """
        Set the main/public key
        """
        ...

    def new_key(self) -> str:
        """
        Generate a new key and return public key
        """
        ...

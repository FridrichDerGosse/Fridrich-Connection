"""
fridex/connection/encryption/_fernet.py

Project: Fridrich-Connection
Created: 12.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from cryptography.fernet import Fernet

from ._cryption_method import CryptionMethod


##################################################
#                     Code                       #
##################################################

class FernetCryption(CryptionMethod):
    """
    Simple fernet encryption
    """
    __own_cryption: Fernet | None
    __foreign_cryption: Fernet | None

    __own_key: bytes | None
    __foreign_key: bytes | None

    def __init__(self) -> None:
        """
        Create FernetCryption
        """
        self.__own_cryption = None
        self.__foreign_cryption = None
        self.__own_key = None
        self.__foreign_key = None

    def encrypt(self, message: bytes) -> bytes:
        if self.__foreign_cryption:
            return self.__foreign_cryption.encrypt(message)
        return message

    def decrypt(self, message: bytes) -> bytes:
        if self.__own_cryption:
            return self.__own_cryption.decrypt(message)
        return message

    def get_key(self) -> str:
        if not self.__own_key:
            self.new_key()
        return self.__own_key.decode()

    def set_key(self, key: str) -> None:
        self.__foreign_key = key.encode()
        self.__foreign_cryption = Fernet(self.__foreign_key)

    def new_key(self) -> str:
        self.__own_key = Fernet.generate_key()
        self.__own_cryption = Fernet(self.__own_key)
        return self.__own_key.decode()


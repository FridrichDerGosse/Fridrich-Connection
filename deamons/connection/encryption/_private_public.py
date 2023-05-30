"""
deamons/connection/encryption/_private_public.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

from ._cryption_method import CryptionMethod


##################################################
#                     Code                       #
##################################################

class PrivatePublicCryption(CryptionMethod):
    """
    A high security private-public-keypair encryption
    """

    __own_private_key: rsa.RSAPrivateKey
    __own_public_key: rsa.RSAPublicKey
    __foreign_public_key: rsa.RSAPublicKey | None
    __public_str: str

    def __init__(self) -> None:
        """
        Create public-private cryption model
        """
        self.new_key()
        self.__foreign_public_key = None

    def encrypt(self, message: str) -> bytes:
        if self.__foreign_public_key:
            return self.__foreign_public_key.encrypt(
                message.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        else:
            return message.encode()

    def decrypt(self, message: bytes) -> str:
        return self.__own_private_key.decrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ).decode()

    def get_key(self) -> str:
        return self.__public_str

    def set_key(self, key: str) -> None:
        self.__foreign_public_key = serialization.load_pem_public_key(
            data=key.encode(),
            backend=default_backend()
        )

    def new_key(self) -> None:
        self.__own_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.__own_public_key = self.__own_private_key.public_key()

        self.__public_str = self.__own_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

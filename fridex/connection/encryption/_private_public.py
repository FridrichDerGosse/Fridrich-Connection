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

    __own_private_key: rsa.RSAPrivateKey | None
    __own_public_key: rsa.RSAPublicKey | None
    __foreign_public_key: rsa.RSAPublicKey | None
    __public_str: str | None

    __key_size: int

    def __init__(self) -> None:
        """
        Create public-private cryption model
        """
        self.__foreign_public_key = None
        self.__own_private_key = None
        self.__own_public_key = None
        self.__public_str = None
        self.__key_size = (256 + 66) * 8

    def encrypt(self, message: bytes) -> bytes:
        if self.__foreign_public_key is not None:
            size: int = (self.__foreign_public_key.key_size // 8) - 66
            splits: list[bytes] = [message[i:i + size] for i in range(0, len(message), size)]
            encrypted_result: bytes = b''

            for split in splits:
                encrypted_result += self.__foreign_public_key.encrypt(
                    split,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )

        else:
            encrypted_result = message

        return encrypted_result

    def decrypt(self, message: bytes) -> bytes:
        decrypted_result: bytes = b""

        if self.__own_public_key is not None:

            size: int = (self.__own_private_key.key_size // 8)
            splits: list[bytes] = [message[i:i+size] for i in range(0, len(message), size)]
            for split in splits:
                decrypted_result += self.__own_private_key.decrypt(
                    split,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
        else:
            decrypted_result = message

        return decrypted_result

    def get_key(self) -> str:
        if not self.__public_str:
            self.new_key()
        return self.__public_str

    def set_key(self, key: str) -> None:
        self.__foreign_public_key = serialization.load_pem_public_key(
            data=key.encode("ASCII"),
            backend=default_backend()
        )

    def new_key(self) -> str:
        self.__own_private_key = rsa.generate_private_key(public_exponent=65537, key_size=self.__key_size)
        self.__own_public_key = self.__own_private_key.public_key()

        self.__public_str = self.__own_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("ASCII")

        return self.get_key()

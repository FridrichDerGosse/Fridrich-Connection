"""
fridex/connection/encryption/_test_cryption.py

Project: Fridrich-Connection
Created: 12.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from string import printable
import unittest

from ._cryption_method import CryptionMethod
from ._cryption import CryptionService, CRYPTION_METHODS


##################################################
#                     Code                       #
##################################################

class CryptionTest(unittest.TestCase):
    """
    Test encryption
    """
    _cryption: CRYPTION_METHODS

    _left: CryptionMethod
    _right: CryptionMethod

    _raw_left = printable.encode()
    _raw_right = _raw_left[::-1]

    _encrypted_left: bytes
    _encrypted_right: bytes

    _decrypted_left: bytes
    _decrypted_right: bytes

    def setUp(self) -> None:
        """
        Create new cryptions
        """
        self._left = CryptionService.new_cryption(self._cryption)
        self._right = CryptionService.new_cryption(self._cryption)

    def dual_side_exchange(self) -> None:
        """
        Basic exchange in each side
        """
        self._encrypted_left = self._left.encrypt(self._raw_left)
        self._decrypted_left = self._right.decrypt(self._encrypted_left)

        self._encrypted_right = self._right.encrypt(self._raw_right)
        self._decrypted_right = self._left.decrypt(self._encrypted_right)

        self.assertEqual(self._raw_left, self._decrypted_left)
        self.assertEqual(self._raw_right, self._decrypted_right)

        print(self._encrypted_left, "\n", self._encrypted_right)

    def test_no_keys(self) -> None:
        """
        Test cryption without any keys set
        """
        self.dual_side_exchange()
        self.assertEqual(self._raw_left, self._encrypted_left)
        self.assertEqual(self._raw_right, self._encrypted_right)

    def test_keys(self) -> None:
        """
        Test cryption with both keys generated
        """
        self._left.set_key(self._right.get_key())
        self._right.set_key(self._left.get_key())
        self.dual_side_exchange()

        self.assertNotEqual(self._raw_left, self._encrypted_left)
        self.assertNotEqual(self._raw_right, self._encrypted_right)
        self.assertNotEqual(self._left.get_key(), self._right.get_key())

    def tearDown(self) -> None:
        """
        Cleanup used cryption_methods
        """
        del self._right
        del self._left

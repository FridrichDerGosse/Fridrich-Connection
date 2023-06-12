"""
fridex/connection/encryption/_test_private_public.py

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

class PrivatePublicTest(CryptionTest):
    """
    Test PrivatePublic encryption
    """
    _cryption = "private_public"

    def test_left_key(self) -> None:
        """
        Test cryption with only left key generated
        """
        self._right.set_key(self._left.get_key())
        self.dual_side_exchange()

        self.assertEqual(self._raw_left, self._encrypted_left)
        self.assertNotEqual(self._raw_right, self._encrypted_right)

    def test_right_key(self) -> None:
        """
        Test cryption with only __right generated
        """
        self._left.set_key(self._right.get_key())
        self.dual_side_exchange()

        self.assertNotEqual(self._raw_left, self._encrypted_left)
        self.assertEqual(self._raw_right, self._encrypted_right)

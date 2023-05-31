"""
/main.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from deamons.connection import CryptionService
from time import time

##################################################
#                     Code                       #
##################################################

if __name__ == '__main__':
    cr1 = CryptionService.new_cryption()
    cr2 = CryptionService.new_cryption()

    cr1.set_key(cr2.get_key())
    cr2.set_key(cr1.get_key())

    t1 = time()
    a = cr1.encrypt(b"ab0{'ad':10}"*10005)

    print("ENCRYPTED IN", time()-t1)

    t1 = time()

    cr2.decrypt(a)

    print("DECRYPTED IN", time() - t1)

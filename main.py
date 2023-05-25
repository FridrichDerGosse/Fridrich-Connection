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

##################################################
#                     Code                       #
##################################################

if __name__ == '__main__':
    cr1 = CryptionService.new_cryption()
    cr2 = CryptionService.new_cryption()

    cr1.set_key(cr2.get_key())
    cr2.set_key(cr1.get_key())

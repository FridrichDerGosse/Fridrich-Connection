"""
/main.py

Project: Fridrich-Connection
Created: 25.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from fridex.connection import CryptionService
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
    a = cr1.encrypt(b'{"time": 1686523174.188933, "data": [{"time": 1686523174.188933, "data": {"type": "key", "value": "-----BEGIN PUBLIC KEY-----\nMIIBZDANBgkqhkiG9w0BAQEFAAOCAVEAMIIBTAKCAUMAx90gp3SqfjfVjZWdghnP\neFch6MRm6cUBwZnM6FS6NHsofsyY1qUrc2/fkzGnSKRvEsUG+yIxSdlYQ2/+LXeh\nkiyeUZjxS+iqghyOtE4SsWBubYeqDfePV0GtaulJKZiROZ4DGVQrJDYut0Aa0+09\nM/WwhDxhu5OC41Kc2cfzvIEjHiJ7Bv+IdqKCYo5mK9Bl1FYeQ5FvRmcBEg17SoJN\nTkQYCRA3aozjBp3o/dtmctLBb6EgxyafH4BpRekaqVLwLONWCTLgy9dIPP84fz4c\n9jJ1Fq8RPyKcwHQynHBvoeyV6jplW1pkHrbAXOT2zx4O7M3hEvyQEPDfQnXcIW0f\nx4PrVB5uyFC58dkcayVrrnAr79XiLiGczQZLWUGdMdU9GddEkwnM0Iz25dd6dxWe\nB/db8oFfo6JmdIVgmlUTA5/KvQIDAQAB\n-----END PUBLIC KEY-----\n"}, "id": 0}], "direction": "response", "kind": "con"}')

    print("ENCRYPTED IN", time()-t1)

    t1 = time()

    cr2.decrypt(a)

    print("DECRYPTED IN", time() - t1)

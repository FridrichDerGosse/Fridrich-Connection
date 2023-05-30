"""
deamons/connection/protocol/_fss_subprotocol.py

Project: Fridrich-Connection
Created: 26.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################


##################################################
#                     Code                       #
##################################################

class FSSP:
    """
    Fridrich-Subscription-Service-Protocol
    """

    __id_range: range
    __id_count: int

    def __init__(
            self,
            id_range: range = range(1000, 1999)
    ) -> None:
        """
        Create subscription protocol
        :param id_range: Num range for subscription ids
        """
        self.__id_range = id_range
        self.__id_count = id_range.start

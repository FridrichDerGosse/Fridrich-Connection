"""
deamons/connection/protocol/_sub_protocol.py

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

class SubscriptionProtocol:
    """
    Special protocol for subscriptions
    """

    __id_range: range
    __id_count: int

    def __init__(
            self,
            id_range: range = range(1, 1000)
    ) -> None:
        """
        Create subscription protocol
        :param id_range: Num range for subscription ids
        """
        self.__id_range = id_range
        self.__id_count = id_range.start

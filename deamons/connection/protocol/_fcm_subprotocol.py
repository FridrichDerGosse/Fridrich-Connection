"""
deamons/connection/protocol/_fcm_subprotocol.py

Project: Fridrich-Connection
Created: 30.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._fdc_protocol import FDCP


##################################################
#                     Code                       #
##################################################

class FCMP:
    """
    Fridrich-Control-Message-Protocol
    Inspired by ICMP
    """
    __fdcp_protocol: FDCP

    def __init__(self, fdcp_protocol: FDCP) -> None:
        self.__fdcp_protocol = fdcp_protocol

    def key(self, key: str) -> str:
        return self.__fdcp_protocol.sub_protocol({"type": "key", "key": key}, _id=0, kind="fcmp")

    def ping(self) -> str:
        return self.__fdcp_protocol.sub_protocol({"type": "ping"}, _id=1, kind="fcmp")

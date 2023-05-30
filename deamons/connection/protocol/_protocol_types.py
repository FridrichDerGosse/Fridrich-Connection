"""
deamons/connection/protocol/_protocol_types.py

Project: Fridrich-Connection
Created: 30.05.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import TypedDict, Literal


##################################################
#                     Code                       #
##################################################

# Defines the different protocols that can be sent
KINDS = Literal["send", "resp", "fssp", "fcmp"]


class MessageDict(TypedDict):
    """
    A MessageDict is always sent in a BulkDict
    """
    id: int
    time: float
    data: list[dict[str | int | float | bool | None, any]]


class BulkDict(MessageDict):
    """
    This is the dict that is really being sent
    """
    kind: KINDS

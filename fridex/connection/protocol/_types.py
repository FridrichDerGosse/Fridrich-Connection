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
KINDS = Literal["data", "sub", "con"]
DIRECTIONS = Literal["request", "response"]
DATAUNIT = dict[str | int | float | bool | None, any]


class _Dict(TypedDict):
    """
    Shared information of MessageDict and BulkDict
    """
    time: float


class MessageDict(_Dict):
    """
    A MessageDict is always sent in a BulkDict
    """
    id: int
    data: DATAUNIT


class BulkDict(_Dict):
    """
    This is the dict that is really being sent
    """
    data: list[MessageDict]
    kind: KINDS
    direction: DIRECTIONS

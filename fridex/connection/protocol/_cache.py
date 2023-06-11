"""
deamons/connection/protocol/_cache.py

Project: Fridrich-Connection
Created: 01.06.2023
Author: Lukas Krahbichler
"""

##################################################
#                    Imports                     #
##################################################

from typing import TypedDict, Type
from datetime import datetime, timedelta

from ._types import DATAUNIT


##################################################
#                     Code                       #
##################################################

class CacheEntry(TypedDict):
    value: Type[DATAUNIT]
    lease_time: datetime


class Cache:
    """
    Caching for subscriptions
    """
    __values: dict[DATAUNIT, CacheEntry]
    __lifetime: float

    def __init__(self, lifetime: float | None = 30.0) -> None:
        """
        Create empty cache
        :param lifetime: The time after a value is dropped if it's not used
        """
        self.__lifetime = lifetime

        self.__values = {}

    def _kill_dead(self) -> None:
        """
        Check all leasetimes and drop old entries
        """
        to_drop: list[DATAUNIT] = []

        for key, value in self.__values.items():
            if datetime.now() > value["lease_time"]:
                to_drop.append(key)

        for drop in to_drop:
            self.__values.pop(drop)

    def set(
        self,
        key: DATAUNIT,
        value: DATAUNIT
    ) -> None:
        """
        Update or create an entry
        :param key: Key to associate the value
        :param value: Data to save
        """
        self.__values[key] = {"value": value, "lease_time": datetime.now() + timedelta(seconds=self.__lifetime)}

        self._kill_dead()

    def get(
        self,
        key: DATAUNIT
    ) -> DATAUNIT | None:
        """
        Get the value of an entry
        :param key: The key to look for
        :return: Value if entry with key exists
        """
        if key in self.__values:
            self.__values[key]["lease_time"] = datetime.now() + timedelta(seconds=self.__lifetime)

            return self.__values[key]
        return None

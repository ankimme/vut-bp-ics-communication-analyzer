"""A simple event handler for events that should change data in UI.

Basically an observer pattern with better event data manipulation.

Author
------
Andrea Chimenti

Date
----
March 2022
"""

from enum import Enum, auto
from typing import Callable
from dataclasses import dataclass
from bidict import bidict
import pandas as pd

from dsmanipulator.utils import FileColumnNames, Direction, Station


# TODO doc


@dataclass(frozen=True)
class EventData:
    df: pd.DataFrame
    df_og: pd.DataFrame
    filtered_df: pd.DataFrame
    fcn: FileColumnNames
    file_path: str
    resample_rate: pd.Timedelta
    attribute_name: str
    station_ids: bidict[int, Station]
    pair_ids: bidict[int, frozenset]
    direction_ids: bidict[int, Direction]
    master_station_id: int
    slave_station_ids: list[int]


class EventType(Enum):
    """Enumeration of types of events."""

    DATAFRAME_CHANGED = auto()
    MASTER_SLAVES_CHANGED = auto()
    RESAMPLE_RATE_CHANGED = auto()
    ATTRIBUTE_CHANGED = auto()


class EventHandler:
    def __init__(self) -> None:
        self.subscribers: dict[EventType, list[Callable]] = dict()

    def subscribe(self, event: EventType, fn: Callable):
        if event not in self.subscribers:
            self.subscribers[event] = []

        self.subscribers[event].append(fn)

    def notify(self, event: EventType, data: EventData):
        if event in self.subscribers:
            for fn in self.subscribers[event]:
                fn(data)

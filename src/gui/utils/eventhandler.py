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
from abc import ABC
from typing import Callable
from dataclasses import dataclass
from bidict import bidict
import pandas as pd

from dsmanipulator.utils import FileColumnNames, Direction, Station


# TODO doc


class EventData(ABC):
    pass


@dataclass(frozen=True)
class DataFrameChangedEventData(EventData):
    df: pd.DataFrame
    fcn: FileColumnNames
    file_path: str
    original_cols: list[str]
    station_ids: bidict[int, Station]
    pair_ids: bidict[int, frozenset]
    direction_ids: bidict[int, Direction]
    master_station_id: int


class EventType(Enum):
    """Enumeration of types of events."""

    DATAFRAME_CHANGED = auto()
    MASTER_STATION_CHANGED = auto()
    SELECTED_PAIRS_CHANGED = auto()


class EventHandler:
    def __init__(self) -> None:
        self.subscribers: dict[EventType, list[Callable]] = dict()

    def subscribe(self, event: EventType, fn: Callable):
        if not event in self.subscribers:
            self.subscribers[event] = []

        self.subscribers[event].append(fn)

    def notify(self, event: EventType, data: EventData):
        if event in self.subscribers:
            for fn in self.subscribers[event]:
                fn(data)

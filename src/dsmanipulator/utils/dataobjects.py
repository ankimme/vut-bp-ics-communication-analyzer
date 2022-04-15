from dataclasses import dataclass
from collections import namedtuple

# Pair of station ids. Source and destination.
Direction = namedtuple("Direction", "src dst")


@dataclass(frozen=True)
class Station:
    # TODO dokumentace
    ip: str
    port: int = None

    def __str__(self) -> str:
        if self.port:
            return f"{self.ip}:{self.port}"
        else:
            return f"{self.ip}"


@dataclass(frozen=True)
class CommunicationPair:
    """Representation of a communication pair.

    Attributes
    ----------
    src_ip : str
        Source IP address.
    dst_ip : str
        Destination IP address.
    src_port : int
        Source port.
    dst_port : int
        Destination port.
    """

    src_ip: str
    dst_ip: str

    src_port: int = None
    dst_port: int = None


@dataclass()
class FileColumnNames:
    """Column names as found in file.

    Attributes
    ----------
    timestamp : str
        Real name of timeStamp column.
    
    src_ip : str
        Real name of srcIp column.
    dst_ip : str
        Real name of dstIp column.
    src_port : str
        Real name of srcPort column.
    dst_port : str
        Real name of dstPort column.

    rel_time : str
        Real name of relTime column.
    src_station_id : str
        Real name of source station id column.
    dst_station_id : str
        Real name of destination station id column.
    pair_id : str
        Real name of pair ID column. (where direction DOES NOT matter).
    direction_id : str
        Real name of direction ID column. (where direction DOES matter).

    rel_day : str
        Real name of relative day column.

    Notes
    -----
    Communication ID = A->B and B->A communications have a different ID.
    Pair ID = A->B and B->A have the same ID.
    """

    timestamp: str = None
    rel_time: str = "*Relative time##"
    src_ip: str = None
    dst_ip: str = None
    src_port: str = None
    dst_port: str = None

    src_station_id: str = "*Source station id##"
    dst_station_id: str = "*Destination station id##"
    pair_id: str = "*Pair id##"
    direction_id: str = "*Direction id##"

    rel_day: str = "*Relative Day##"

    @property
    def double_column_station(self) -> bool:
        """Determine whether both ip and port columns are assigned.

        Returns
        -------
        bool
            True if both ip and port columns are assigned.
            False if only one column is used for describing a station.
        """
        return bool(self.src_port and self.dst_port)

    @property
    def predefined_cols(self) -> list[str]:
        """List of original names of columns that are not attributes.

        These columns are used by the app for manipulating with the data.

        Returns
        -------
        list[str]
            Names of predefined columns as they were in the csv file.
        """
        assert self.timestamp and self.src_ip and self.dst_ip

        result = [self.timestamp, self.src_ip, self.dst_ip]

        if self.rel_time:
            result.append(self.rel_time)

        if self.double_column_station:
            result.append(self.src_port)
            result.append(self.dst_port)

        return result

    # def __str__(self) -> str:
    #     return f"timestamp: {self.timestamp}\nrel_time: {self.rel_time}\nsrc_ip: {self.src_ip}\ndst_ip: {self.dst_ip}\nsrc_port: {self.src_port}\ndst_port: {self.dst_port}"

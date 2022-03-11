from dataclasses import dataclass


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
    rel_time : str
        Real name of relTime column.
    src_ip : str
        Real name of srcIp column.
    dst_ip : str
        Real name of dstIp column.
    src_port : str
        Real name of srcPort column.
    dst_port : str
        Real name of dstPort column.
    rel_day : str
        Real name of relative day column.
    l3_communication_id : str
        Real name of L3 communication ID column.
    l4_communication_id : str
        Real name of L4 communication ID column.
    l4_pair_id : str
        Real name of L4 pair ID column.

    Notes
    -----
    Communication ID = A->B and B->A communications have a different ID.
    Pair ID = A->B and B->A have the same ID.
    """

    timestamp: str = None
    rel_time: str = "Relative time"
    src_ip: str = None
    dst_ip: str = None
    src_port: str = None
    dst_port: str = None
    rel_day: str = "Relative Day"
    l3_communication_id: str = "L3 Communication id"
    l4_communication_id: str = "L4 Communication id"
    l4_pair_id: str = "L4 pair id"

    # def __str__(self) -> str:
    #     return f"timestamp: {self.timestamp}\nrel_time: {self.rel_time}\nsrc_ip: {self.src_ip}\ndst_ip: {self.dst_ip}\nsrc_port: {self.src_port}\ndst_port: {self.dst_port}"

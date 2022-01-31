from dataclasses import dataclass


@dataclass(frozen=True)
class CommunicationPair:
    """ Representation of a communication pair.
    source -> destination
    ip:port -> ip:port
    """
    src_ip: str
    dst_ip: str

    src_port: int = None
    dst_port: int = None

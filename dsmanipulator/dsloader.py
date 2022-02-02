import csv
from numpy import clongdouble
import pandas as pd

from .utils.dataobjects import FileColumnNames


def load_data(file_name: str, col_names: FileColumnNames, delimiter: str = None) -> pd.DataFrame:
    # todo df must have 'srcIP', 'srcPort', 'dstIP', 'dstPort', 'TimeStamp'
    # todo TimeStamp ve fromatu format="%H:%M:%S.%f"
    # todo check if file exists

    if not delimiter:
        delimiter = detect_delimiter(file_name)

    df = pd.read_csv(file_name,
                     sep=delimiter,
                     #  dtype={'asduType': 'category', 'numix': 'category', 'cot': 'category', 'uType': 'category', 'oa': 'category'},
                     #  parse_dates=['TimeStamp']
                     )

    df = df.rename(columns={col_names.timestamp: "timeStamp", col_names.src_ip: "srcIp", col_names.dst_ip: "dstIp", col_names.src_port: "srcPort", col_names.dst_port: "dstPort"})

    # TODO exceptions
    df['timeStamp'] = pd.to_datetime(df['timeStamp'])

    return df


def detect_delimiter(file_name: str) -> str:
    """Detect the delimiter of a CSV file.

    Parameters
    ----------
    file_name : str
        Name of a CSV file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.

    Returns
    -------
    str
        Detected delimiter.
    """
    # TODO exceptions
    with open(file_name, 'r') as file:
        header = file.readline()

    return csv.Sniffer().sniff(header).delimiter


def detect_datetime():
    # TODO
    pass
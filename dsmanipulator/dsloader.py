import csv
import numpy as np
import pandas as pd

from .utils.dataobjects import FileColumnNames


def load_data(file_name: str, dtype: dict[str, str], col_names: FileColumnNames, dialect: csv.Dialect) -> pd.DataFrame:
    # todo df must have 'srcIP', 'srcPort', 'dstIP', 'dstPort', 'TimeStamp'
    # todo TimeStamp ve fromatu format="%H:%M:%S.%f"
    # todo check if file exists
    print(dtype)
    df = pd.read_csv(
        file_name,
        dialect=dialect,
        dtype=dtype,
        # TODO dynamically
        #  dtype={'asduType': 'category', 'numix': 'category',
        #         'cot': 'category', 'uType': 'category', 'oa': 'category'},
        #  parse_dates=['TimeStamp']
    )

    if col_names:
        df = df.rename(
            columns={
                col_names.timestamp: "timeStamp",
                col_names.rel_time: "relTime",
                col_names.src_ip: "srcIp",
                col_names.dst_ip: "dstIp",
                col_names.src_port: "srcPort",
                col_names.dst_port: "dstPort",
            }
        )

    # TODO exceptions
    # df["timeStamp"] = pd.to_datetime(df["timeStamp"])

    return df


def detect_delimiter(file_name: str) -> str:  # TODO delete
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
    with open(file_name, "r") as file:
        header = file.readline()

    return csv.Sniffer().sniff(header).delimiter


def detect_dialect(file_name) -> csv.Dialect:
    """Detect the dialect of a CSV file.

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
    csv.Dialect
        Detected dialect.
    """
    # TODO exceptions
    with open(file_name, "r") as file:
        header = file.readline()

    return csv.Sniffer().sniff(header)


def detect_columns_deprecated(file_name: str, delimiter: str = None, row_limit: int = 10000) -> dict[str, np.dtype]:
    """Try to detect column names and data types.

    Parameters
    ----------
    file_name : str
        Path to CSV file containing data.
    delimiter : str, optional
        Data delimiter. Will be detected automatically if not specified.
    row_limit : int, optional
        Number of rows used for dtype detection, by default 10000.

    Returns
    -------
    dict[str, np.dtype]
        Dictionary of detected columns and data types.
    """

    if not delimiter:
        delimiter = detect_delimiter(file_name)

    df = pd.read_csv(file_name, delimiter=delimiter, nrows=row_limit)

    return df.dtypes.to_dict()


def detect_columns(file_name: str, dialect: csv.Dialect, row_limit: int = 10000) -> dict[str, np.dtype]:
    """Try to detect column names and data types. Using python engine.

    Parameters
    ----------
    file_name : str
        Path to CSV file containing data.
    dialect : csv.Dialect
        CSV dialect.
    row_limit : int, optional
        Number of rows used for dtype detection, by default 10000.

    Raises
    ------
    pd.errors.ParserError
        Raised when csv and dialect are not compatible.

    Returns
    -------
    dict[str, np.dtype]
        Dictionary of detected columns and data types.
    """

    df = pd.read_csv(file_name, dialect=dialect, nrows=row_limit, engine="python")

    return df.dtypes.to_dict()


def detect_datetime():
    # TODO
    pass

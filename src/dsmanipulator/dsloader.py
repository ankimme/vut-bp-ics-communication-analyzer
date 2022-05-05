import csv
import numpy as np
import pandas as pd


def load_data(file_name: str, data_types: dict[str, str], dialect: csv.Dialect, row_limit: int = None) -> pd.DataFrame:
    # todo df must have 'srcIP', 'srcPort', 'dstIP', 'dstPort', 'TimeStamp'
    # todo TimeStamp ve fromatu format="%H:%M:%S.%f"
    # todo check if file exists

    col_types = {k: v for k, v in data_types.items() if v != "datetime"}
    date_time_columns = [k for k, v in data_types.items() if v == "datetime"]

    df = pd.read_csv(file_name, dialect=dialect, dtype=col_types, nrows=row_limit, na_values=[""])

    # df = df.astype({k: "str" for k, v in col_types.items() if v == "object"})

    for col_name in date_time_columns:
        df[col_name] = pd.to_datetime(df[col_name])

    # # TODO accept some Nones
    # if any(value is None for value in col_names.__dict__.values()):
    #     raise Exception()

    # TODO delete
    # df = df.rename(
    #     columns={
    #         col_name.timestamp: "timeStamp",
    #         col_names.rel_time: "relTime",
    #         col_names.src_ip: "srcIp",
    #         col_names.dst_ip: "dstIp",
    #         col_names.src_port: "srcPort",
    #         col_names.dst_port: "dstPort",
    #     }
    # )

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

    detected_cols = df.dtypes.to_dict()

    # cast int to float
    detected_cols = {k: ("float" if v == "int" else v) for k, v in detected_cols.items()}
    # cast unsupported data types (not datetime, float or object) to object
    detected_cols = {k: (v if v in ["datetime", "float", "object"] else "object") for k, v in detected_cols.items()}

    predefined_types: dict[str, str] = {}
    predefined_types["TimeStamp"] = "datetime"
    predefined_types["Relative Time"] = "float"
    predefined_types["srcIP"] = "object"
    predefined_types["dstIP"] = "object"
    predefined_types["srcPort"] = "float"
    predefined_types["dstPort"] = "float"
    predefined_types["ipLen"] = "float"
    predefined_types["len"] = "float"
    predefined_types["fmt"] = "object"
    predefined_types["uType"] = "object"
    predefined_types["asduType"] = "float"
    predefined_types["numix"] = "float"
    predefined_types["cot"] = "float"
    predefined_types["oa"] = "float"
    predefined_types["addr"] = "float"
    predefined_types["ioa"] = "object"

    # change the detected columns to a predefined type. the predefined types are optimal for the datasets provided with the bachelor thesis
    detected_cols.update({k: v for k, v in predefined_types.items() if k in detected_cols.keys()})

    return detected_cols


def detect_datetime():
    # TODO
    pass
